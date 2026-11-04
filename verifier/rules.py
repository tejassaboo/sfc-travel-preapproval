"""The historical (2012) toy travel policy as this plugin's handbook states it (src/plugin/data/handbook.md):
the oracle that the reference tools and the verifier both run on the bundled fixtures.

Byte-identical in src/plugin/ and verifier/ (a test checks the two copies), so it keeps to the
verifier's pure-stdlib rules. Every function is a pure function of the fixtures and one scenario.
Money is integer USD cents throughout.
"""

from .world import days_between, itinerary_segments, search

DOMESTIC_CAP = 75000  # C3: a domestic fare over $750.00 needs approval before booking
INTERNATIONAL_CAP = 150000  # C3: an international fare over $1,500.00 does too
MIN_ADVANCE_DAYS = 14  # C4: booked fewer days ahead than this needs pre-authorization
MAX_ADVANCE_DAYS = 365  # C4: ... and so does booking more days ahead than this
LOW_FARE_BAND = 20000  # C5: a fare more than $200.00 over the lowest logical fare needs pre-authorization
MAX_LOGICAL_CONNECTIONS = 1  # C5/C7: more connections than this is unreasonable
# C3-C7, in the order of contract.SfcPreauth (a test checks the two agree).
PREAUTHS = (
    "COST_OVER_DOMESTIC_750",
    "COST_OVER_INTL_1500",
    "BOOKED_LT_14_DAYS",
    "BOOKED_GT_365_DAYS",
    "ABOVE_LOW_FARE_BAND_200",
    "NON_ECONOMY_CABIN",
    "TWO_PLUS_CONNECTIONS",
)
AIRPORT_VIEW = ("code", "city", "country", "us_50_states_dc")


def is_domestic(world, scenario):
    """C2: domestic when both endpoints are in the 50 US states or DC."""
    airports = world["airports"]
    return airports[scenario["origin"]]["us_50_states_dc"] and airports[scenario["destination"]]["us_50_states_dc"]


def advance_days(scenario):
    return days_between(scenario["booking_date"], scenario["departure_date"])


def same_day(world, scenario):
    """Every itinerary from the scenario's origin to its destination on its departure date, by id."""
    return search(world, [scenario["origin"]], scenario["destination"], scenario["departure_date"])


def lowest_logical_fare(world, scenario):
    """C5: the lowest economy fare among same-day itineraries with at most one connection."""
    fares = [
        itinerary["fares_cents"]["economy"]
        for itinerary in same_day(world, scenario)
        if itinerary["connections"] <= MAX_LOGICAL_CONNECTIONS and itinerary["fares_cents"]["economy"] is not None
    ]
    if not fares:
        raise ValueError(f"scenario {scenario['scenario']}: no same-day itinerary sets a lowest logical fare")
    return min(fares)


def preauthorizations(world, scenario, itinerary, cabin):
    """Every pre-authorization booking ``itinerary`` in ``cabin`` needs, in PREAUTHS order."""
    fare = itinerary["fares_cents"][cabin]
    if fare is None:
        raise ValueError(f"itinerary {itinerary['itinerary_id']} sells no {cabin} fare")
    domestic = is_domestic(world, scenario)
    days = advance_days(scenario)
    needed = {
        "COST_OVER_DOMESTIC_750": domestic and fare > DOMESTIC_CAP,
        "COST_OVER_INTL_1500": not domestic and fare > INTERNATIONAL_CAP,
        "BOOKED_LT_14_DAYS": days < MIN_ADVANCE_DAYS,
        "BOOKED_GT_365_DAYS": days > MAX_ADVANCE_DAYS,
        "ABOVE_LOW_FARE_BAND_200": fare - lowest_logical_fare(world, scenario) > LOW_FARE_BAND,
        "NON_ECONOMY_CABIN": cabin != "economy",
        "TWO_PLUS_CONNECTIONS": itinerary["connections"] > MAX_LOGICAL_CONNECTIONS,
    }
    return [code for code in PREAUTHS if needed[code]]


def bag_allowance(requested):
    """C9: one checked bag is reimbursable, never more."""
    if requested < 0:
        raise ValueError(f"{requested} checked bags")
    return "one" if requested >= 1 else "zero"


def airport_view(world, code):
    return {key: world["airports"][code][key] for key in AIRPORT_VIEW}


def option_view(world, itinerary):
    """An itinerary as the tools show it: route, flights, local times, connections, fares."""
    segments = itinerary_segments(world, itinerary)
    return {
        "itinerary_id": itinerary["itinerary_id"],
        "route": [segments[0]["origin"], *(segment["destination"] for segment in segments)],
        "flights": [segment["flight"] for segment in segments],
        "depart_local": segments[0]["depart_local"],
        "arrive_local": segments[-1]["arrive_local"],
        "connections": itinerary["connections"],
        "fares_cents": dict(itinerary["fares_cents"]),
    }


def request_view(world, scenario):
    """What both lookups share: the traveler's words, dates, traveler, endpoints and bags."""
    return {
        "scenario": scenario["scenario"],
        "request_text": scenario["request_text"],
        "booking_date": scenario["booking_date"],
        "departure_date": scenario["departure_date"],
        "traveler": dict(world["travelers"][scenario["traveler_id"]]),
        "origin": airport_view(world, scenario["origin"]),
        "destination": airport_view(world, scenario["destination"]),
    }


def audit_case(world, scenario):
    """What get_audit_case shows: the request, the booking under audit and every same-day alternative."""
    itinerary = world["itineraries"][scenario["chosen_itinerary_id"]]
    return {
        **request_view(world, scenario),
        "chosen": {
            "itinerary_id": itinerary["itinerary_id"],
            "cabin": scenario["chosen_cabin"],
            "fare_cents": itinerary["fares_cents"][scenario["chosen_cabin"]],
        },
        "checked_bags_requested": scenario["checked_bags"],
        "same_day_itineraries": [option_view(world, item) for item in same_day(world, scenario)],
    }


def trip_request(world, scenario):
    """What get_trip_request shows for a trip to book: never an answer."""
    return {
        **request_view(world, scenario),
        "requested_cabin": scenario["requested_cabin"],
        "checked_bags_requested": scenario["checked_bags"],
    }


def audit_oracle(world, scenario):
    """The one correct sfc-audit output, as plain JSON."""
    itinerary = world["itineraries"][scenario["chosen_itinerary_id"]]
    needed = preauthorizations(world, scenario, itinerary, scenario["chosen_cabin"])
    return {
        "in_policy": not needed,
        "required_preauthorizations": needed,
        "itinerary_id": None,
        "reimbursable_checked_bags": bag_allowance(scenario["checked_bags"]),
    }


def valid_set(world, scenario):
    """The sfc-book answer key: each same-day itinerary whose economy fare needs no pre-authorization."""
    valid, rejected = [], {}
    for itinerary in same_day(world, scenario):
        if itinerary["fares_cents"]["economy"] is None:
            continue  # nothing to book in economy
        needed = preauthorizations(world, scenario, itinerary, "economy")
        if needed:
            rejected[itinerary["itinerary_id"]] = needed
        else:
            valid.append(itinerary["itinerary_id"])
    if not valid:
        raise ValueError(f"scenario {scenario['scenario']}: no itinerary can be booked in policy")
    return {
        "valid_itinerary_ids": sorted(valid),
        "lowest_logical_fare_cents": lowest_logical_fare(world, scenario),
        "reimbursable_checked_bags": bag_allowance(scenario["checked_bags"]),
        "rejected": rejected,
    }
