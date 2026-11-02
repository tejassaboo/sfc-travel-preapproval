from .checks import DATA, UNEXPECTED, compared, plain, result
from .rules import option_view
from .world import IATA, day_number, load_world, search


def verify_input(value):
    try:
        given = plain(value)
        for code in (given["origin"], given["destination"]):
            if not IATA.fullmatch(code):
                return result(False, f"{code!r} is not a three-letter IATA code")
        day_number(given["date"])
        return result(True, "input is valid")
    except UNEXPECTED as error:
        return result(False, f"input is invalid: {error}")


def verify_output(input_value, output_value, workspace):
    try:
        given = plain(input_value)
        world = load_world(DATA)
        found = search(world, [given["origin"]], given["destination"], given["date"])
        return compared("search_itineraries", plain(output_value), {"itineraries": [option_view(world, item) for item in found]})
    except UNEXPECTED as error:
        return result(False, f"verifier-error: {error!r}")
