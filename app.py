"""A small Flask calculator.

Addition is the only operation that is implemented; the remaining
operations are deliberately left unsupported.
"""

from flask import Flask, jsonify, render_template, request

SUPPORTED_OPERATIONS = ("add",)


class CalculationError(ValueError):
    """Raised when a calculation request cannot be fulfilled."""


def parse_operand(raw, name):
    """Coerce a form/JSON value into a float, or raise CalculationError."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise CalculationError(f"{name} is required")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise CalculationError(f"{name} must be a number")
    if value != value or value in (float("inf"), float("-inf")):
        raise CalculationError(f"{name} must be a finite number")
    return value


def add(a, b):
    """Return the sum of two numbers."""
    return a + b


def calculate(operation, a, b):
    """Dispatch to the implementation for `operation`."""
    if operation != "add":
        raise CalculationError(f"operation '{operation}' is not supported yet")
    return add(a, b)


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html", operations=SUPPORTED_OPERATIONS)

    @app.post("/api/calculate")
    def api_calculate():
        payload = request.get_json(silent=True) or request.form
        operation = (payload.get("operation") or "add").strip().lower()
        try:
            a = parse_operand(payload.get("a"), "First number")
            b = parse_operand(payload.get("b"), "Second number")
            result = calculate(operation, a, b)
        except CalculationError as exc:
            status = 501 if "not supported" in str(exc) else 400
            return jsonify(error=str(exc)), status
        return jsonify(operation=operation, a=a, b=b, result=result)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
