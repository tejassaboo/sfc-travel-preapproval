from slimconfig import build_output

from contract import SearchInput, SearchOutput
from plugin.fixtures import world
from plugin.rules import option_view
from plugin.world import IATA, day_number, search


def search_itineraries(given: SearchInput) -> SearchOutput:
    """Every itinerary from the origin to the destination on the date. It applies no policy."""
    airports = world()["airports"]
    for code in (given.origin, given.destination):
        if not IATA.fullmatch(code) or code not in airports:
            raise ValueError(f"{code!r} is not an airport in this inventory")
    day_number(given.date)
    found = search(world(), [given.origin], given.destination, given.date)
    return build_output({"itineraries": [option_view(world(), item) for item in found]}, SearchOutput)
