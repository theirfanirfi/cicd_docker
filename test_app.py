"""Tests for the addition feature of the Flask calculator."""

import pytest

from app import CalculationError, add, calculate, create_app, parse_operand


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


# --- add() unit tests -------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (1, 2, 3),
        (0, 0, 0),
        (-4, 9, 5),
        (-4, -6, -10),
        (2.5, 0.25, 2.75),
        (1_000_000, 2_000_000, 3_000_000),
        (0.1, 0.2, pytest.approx(0.3)),
    ],
)
def test_add_returns_expected_sum(a, b, expected):
    assert add(a, b) == expected


def test_add_is_commutative():
    assert add(7, -3) == add(-3, 7)


def test_add_identity_element():
    assert add(42.5, 0) == 42.5


# --- calculate() dispatch ---------------------------------------------


def test_calculate_dispatches_add():
    assert calculate("add", 3, 4) == 7


@pytest.mark.parametrize("operation", ["subtract", "multiply", "divide", "power"])
def test_calculate_rejects_unimplemented_operations(operation):
    with pytest.raises(CalculationError, match="not supported"):
        calculate(operation, 1, 2)


# --- parse_operand() --------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("5", 5.0), ("-2.5", -2.5), (" 3 ", 3.0), (4, 4.0), ("1e3", 1000.0)],
)
def test_parse_operand_accepts_numbers(raw, expected):
    assert parse_operand(raw, "value") == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "abc", "1,2", [], "nan", "inf"])
def test_parse_operand_rejects_bad_input(raw):
    with pytest.raises(CalculationError):
        parse_operand(raw, "value")


# --- HTTP layer -------------------------------------------------------


def test_index_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Calculator" in response.data


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [(1, 2, 3), ("-5", "5", 0), (2.5, 2.5, 5.0), ("0.1", "0.2", pytest.approx(0.3))],
)
def test_api_addition_returns_sum(client, a, b, expected):
    response = client.post("/api/calculate", json={"a": a, "b": b, "operation": "add"})
    assert response.status_code == 200
    assert response.json["result"] == expected
    assert response.json["operation"] == "add"


def test_api_defaults_to_addition_when_operation_omitted(client):
    response = client.post("/api/calculate", json={"a": 6, "b": 7})
    assert response.status_code == 200
    assert response.json["result"] == 13


def test_api_accepts_form_encoded_data(client):
    response = client.post("/api/calculate", data={"a": "8", "b": "9", "operation": "add"})
    assert response.status_code == 200
    assert response.json["result"] == 17


@pytest.mark.parametrize(
    "payload",
    [
        {"a": 1},
        {"b": 1},
        {},
        {"a": "abc", "b": 1},
        {"a": 1, "b": ""},
    ],
)
def test_api_rejects_invalid_operands(client, payload):
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 400
    assert "error" in response.json


def test_api_reports_unsupported_operation(client):
    response = client.post(
        "/api/calculate", json={"a": 1, "b": 2, "operation": "multiply"}
    )
    assert response.status_code == 501
    assert "not supported" in response.json["error"]


def test_api_rejects_get_requests(client):
    assert client.get("/api/calculate").status_code == 405
