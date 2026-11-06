"""A scripted agent with no LLM, written from the handbook (src/plugin/data/handbook.md) alone: it imports
nothing of the plugin's rules, and never reads request_text (C12: the structured fields are the facts).
It follows each task's step plan through a ``call(tool, arguments)`` function and returns the submission
it would make, so the tests can run each scenario end to end."""

from datetime import date

CODES = [
    "COST_OVER_DOMESTIC_750",
    "COST_OVER_INTL_1500",
    "BOOKED_LT_14_DAYS",
    "BOOKED_GT_365_DAYS",
    "ABOVE_LOW_FARE_BAND_200",
    "NON_ECONOMY_CABIN",
    "TWO_PLUS_CONNECTIONS",
]


def days(start, end):
    return (date.fromisoformat(end) - date.fromisoformat(start)).days


def lowest_logical(itineraries):
    return min(item["fares_cents"]["economy"] for item in itineraries if item["connections"] <= 1 and item["fares_cents"]["economy"] is not None)


def codes(request, itineraries, itinerary, cabin):
    """C2-C7 for booking ``itinerary`` in ``cabin``."""
    fare = itinerary["fares_cents"][cabin]
    domestic = request["origin"]["us_50_states_dc"] and request["destination"]["us_50_states_dc"]
    ahead = days(request["booking_date"], request["departure_date"])
    found = []
    if domestic and fare > 75000:
        found.append("COST_OVER_DOMESTIC_750")
    if not domestic and fare > 150000:
        found.append("COST_OVER_INTL_1500")
    if ahead < 14:
        found.append("BOOKED_LT_14_DAYS")
    if ahead > 365:
        found.append("BOOKED_GT_365_DAYS")
    if fare - lowest_logical(itineraries) > 20000:
        found.append("ABOVE_LOW_FARE_BAND_200")
    if cabin != "economy":
        found.append("NON_ECONOMY_CABIN")
    if itinerary["connections"] >= 2:
        found.append("TWO_PLUS_CONNECTIONS")
    return found


def bags(requested):
    return "one" if requested >= 1 else "zero"


def run_audit(scenario, call):
    """(the tool calls made, in order, as (tool, arguments); the submission)."""
    calls = [("get_audit_case", {"scenario": scenario})]
    case = call(*calls[-1])
    options = case["same_day_itineraries"]
    chosen = next(item for item in options if item["itinerary_id"] == case["chosen"]["itinerary_id"])
    found = codes(case, options, chosen, case["chosen"]["cabin"])
    return calls, {
        "in_policy": not found,
        "required_preauthorizations": found,
        "itinerary_id": None,
        "fare_cents": chosen["fares_cents"][case["chosen"]["cabin"]],
        "lowest_logical_fare_cents": lowest_logical(options),
        "advance_days": days(case["booking_date"], case["departure_date"]),
        "reimbursable_checked_bags": bags(case["checked_bags_requested"]),
    }


def run_book(scenario, call):
    """(the tool calls made; the submission): the cheapest in-policy economy fare, then the lowest id."""
    calls = [("get_trip_request", {"scenario": scenario})]
    request = call(*calls[-1])
    calls.append(("search_itineraries", {"origin": request["origin"]["code"], "destination": request["destination"]["code"], "date": request["departure_date"]}))
    options = call(*calls[-1])["itineraries"]
    valid = [item for item in options if item["fares_cents"]["economy"] is not None and not codes(request, options, item, "economy")]
    best = min(valid, key=lambda item: (item["fares_cents"]["economy"], item["itinerary_id"]))
    return calls, {
        "in_policy": True,
        "required_preauthorizations": [],
        "itinerary_id": best["itinerary_id"],
        "fare_cents": best["fares_cents"]["economy"],
        "lowest_logical_fare_cents": lowest_logical(options),
        "advance_days": days(request["booking_date"], request["departure_date"]),
        "reimbursable_checked_bags": bags(request["checked_bags_requested"]),
    }


def run(scenario, task, call):
    return (run_audit if task == "sfc-audit" else run_book)(scenario, call)
