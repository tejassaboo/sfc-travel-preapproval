from .checks import UNEXPECTED, compared, fixtures, plain, result
from .rules import audit_case, trip_request

VIEWS = {"get_audit_case": audit_case, "get_trip_request": trip_request}


def verify_input(value):
    return result(True, "input is valid")  # a scenario Enum member is all the input there is


def checker(name):
    """verify_output for the lookup ``name``: its output equals the view of the bundled fixtures."""

    def verify_output(input_value, output_value, workspace):
        try:
            world, scenario = fixtures(plain(input_value)["scenario"])
            return compared(name, plain(output_value), VIEWS[name](world, scenario))
        except UNEXPECTED as error:
            return result(False, f"verifier-error: {error!r}")

    return verify_output
