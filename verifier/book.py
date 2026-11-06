"""The sfc-book verdict, and the checks of its reference tool compute_valid_set.

Any member of the valid set is a correct booking (brief rule 11): the verifier computes the valid set
itself (rules.valid_set over the bundled fixtures) and checks membership, in stages of constraints with
stable ids (the reason codes):

0. answer key: the pinned valid set equals the verifier's own (else the plugin is broken);
1. referential integrity: an itinerary is named, exists, and leaves the origin on the date for the destination;
2. internal consistency: no code twice; in_policy is true exactly when no code is listed;
3. policy decision: the itinerary is in the valid set, and in_policy is true;
4. magnitudes and flags: the booked itinerary's economy fare, the lowest logical fare, the days ahead, the
   bag allowance.

A valid booking lists no pre-authorization, but that needs no constraint of its own: once stages 2 and 3
hold, in_policy is true and so the list is empty (0.1.0 carried an unreachable ``preauths-correct`` here).
The score is stages.partial_score: the decision is all or nothing (a valid itinerary, in policy, no code),
and each right magnitude and the bag allowance adds a tenth; the fare is right only for an itinerary that
serves the trip, so a fantasy or another trip's itinerary earns nothing for it.
"""

from .checks import UNEXPECTED, fixtures, plain, result
from .explain import why
from .rules import valid_set
from .stages import (
    FACTS,
    bags_problem,
    consistency_problem,
    consistent,
    judge,
    magnitude_problem,
    partial_score,
    unique_problem,
)
from .world import itinerary_segments

TEXT = {
    "reference-matches-valid-set": "The pinned valid set equals the verifier's own",
    "itinerary-named": "A booking names an itinerary",
    "itinerary-exists": "The itinerary id names an itinerary in the inventory",
    "itinerary-serves-request": "The itinerary leaves the origin on the departure date and lands at the destination",
    "preauths-unique": "No pre-authorization is listed twice",
    "in-policy-matches-preauths": "in_policy is true exactly when required_preauthorizations is empty (C8)",
    "itinerary-in-policy": "The itinerary is in the valid set: its economy fare needs no pre-authorization (C11)",
    "in-policy-correct": "A valid booking is in policy",
    "fare-correct": "fare_cents is the booked itinerary's economy fare (C11, C10a)",
    "lowest-logical-fare-correct": "lowest_logical_fare_cents is C5's lowest logical fare",
    "advance-days-correct": "advance_days is departure_date minus booking_date in calendar days (C4)",
    "bags-correct": "reimbursable_checked_bags is what C9 gives",
}


def verify_input(value):
    return result(True, "input is valid")  # a scenario Enum member is all the input there is


def verify_output(input_value, output_value, workspace):
    try:
        world, scenario = fixtures(plain(input_value)["scenario"])
        key = valid_set(world, scenario)
    except UNEXPECTED as error:
        return result(False, f"verifier-error: {error!r}")
    if plain(output_value) != key:
        return result(False, "compute_valid_set differs from the verifier's valid set", expected=key)
    return result(True, "the valid set matches the verifier's own")


def verify_task(arguments, output, reference, workspace):
    try:
        world, scenario = fixtures(plain(arguments)["scenario"])
        key = valid_set(world, scenario)
        pinned = None if reference is None else plain(reference)
        verdict = judge_book(world, scenario, key, pinned, plain(output))
        verdict["details"]["valid_set"] = key
        return verdict
    except UNEXPECTED as error:
        return result(False, f"verifier-error: {error!r}")


def serves(world, scenario, itinerary):
    """Whether ``itinerary`` leaves the trip's origin on its departure date for its destination."""
    segments = itinerary_segments(world, itinerary)
    wanted = [scenario["origin"], scenario["departure_date"], scenario["destination"]]
    actual = [segments[0]["origin"], segments[0]["depart_local"][:10], segments[-1]["destination"]]
    return actual == wanted, wanted, actual


def book_score(world, scenario, key, pinned, given):
    """The partial score of a booking (see stages): 0 when the pinned key is wrong."""
    if pinned is not None and pinned != key:
        return 0.0
    booked = world["itineraries"].get(given["itinerary_id"]) if given["itinerary_id"] is not None else None
    served = booked is not None and serves(world, scenario, booked)[0]
    decision = 1.0 if given["itinerary_id"] in key["valid_itinerary_ids"] and given["in_policy"] is True and consistent(given) else 0.0
    facts = [served and given["fare_cents"] == booked["fares_cents"]["economy"]]
    facts += [given[name] == key[name] for name in FACTS[1:]]
    return partial_score(decision, facts)


def judge_book(world, scenario, key, pinned, given):
    itinerary_id = given["itinerary_id"]
    codes = given["required_preauthorizations"]
    valid = key["valid_itinerary_ids"]

    def booked():
        return world["itineraries"].get(itinerary_id) if itinerary_id is not None else None

    def reference():
        if pinned is not None and pinned != key:
            return key, pinned, "the pinned valid set differs from the verifier's own, so the plugin itself is broken"
        return None

    def named():
        if itinerary_id is None:
            return valid, None, f"nothing booked, but {len(valid)} itinerary(ies) are in policy: {', '.join(valid)}"
        return None

    def exists():
        if itinerary_id is not None and itinerary_id not in world["itineraries"]:
            return None, itinerary_id, f"itinerary {itinerary_id!r} is not in the inventory"
        return None

    def serves_request():
        if booked() is None:
            return None  # nothing booked, or itinerary-exists already fails
        ok, wanted, actual = serves(world, scenario, booked())
        if not ok:
            return wanted, actual, (
                f"itinerary {itinerary_id} leaves {actual[0]} on {actual[1]} for {actual[2]}, "
                f"but the trip leaves {wanted[0]} on {wanted[1]} for {wanted[2]}"
            )
        return None

    def in_valid_set():
        if itinerary_id in valid:
            return None
        itinerary = booked()
        if itinerary["fares_cents"]["economy"] is None:
            return valid, itinerary_id, f"itinerary {itinerary_id} sells no economy fare; in policy: {', '.join(valid)}"
        needed = key["rejected"][itinerary_id]
        reasons = "; ".join(f"{code} ({why(world, scenario, itinerary, 'economy', code)})" for code in needed)
        return valid, itinerary_id, f"itinerary {itinerary_id} needs {reasons}; in policy: {', '.join(valid)}"

    def in_policy():
        if given["in_policy"] is not True:
            return True, given["in_policy"], f"itinerary {itinerary_id} is in the valid set, so the booking is in policy"
        return None

    def fare():
        wanted = booked()["fares_cents"]["economy"]
        return magnitude_problem("fare_cents", wanted, given["fare_cents"], f"{itinerary_id}'s economy fare")

    def lowest():
        return magnitude_problem(
            "lowest_logical_fare_cents", key["lowest_logical_fare_cents"], given["lowest_logical_fare_cents"],
            "the lowest economy fare among same-day itineraries with at most 1 connection",
        )

    def days():
        return magnitude_problem(
            "advance_days", key["advance_days"], given["advance_days"],
            f"{scenario['departure_date']} minus {scenario['booking_date']} in calendar days",
        )

    stages = [
        [("reference-matches-valid-set", reference)],
        [("itinerary-named", named), ("itinerary-exists", exists), ("itinerary-serves-request", serves_request)],
        [("preauths-unique", lambda: unique_problem(codes)), ("in-policy-matches-preauths", lambda: consistency_problem(given))],
        [("itinerary-in-policy", in_valid_set), ("in-policy-correct", in_policy)],
        [
            ("fare-correct", fare),
            ("lowest-logical-fare-correct", lowest),
            ("advance-days-correct", days),
            ("bags-correct", lambda: bags_problem(scenario["checked_bags"], key["reimbursable_checked_bags"], given["reimbursable_checked_bags"])),
        ],
    ]
    success = (
        f"the booking is in policy: {itinerary_id} at {given['fare_cents']} cents is one of {len(valid)} valid itineraries "
        f"({', '.join(valid)}); lowest logical fare {key['lowest_logical_fare_cents']}, {key['advance_days']} days ahead, "
        f"bags {key['reimbursable_checked_bags']}"
    )
    return judge(stages, TEXT, success, book_score(world, scenario, key, pinned, given))
