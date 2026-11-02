"""The sfc-book verdict, and the checks of its reference tool compute_valid_set.

Any member of the valid set is a correct booking (brief rule 11): the verifier computes the valid set
itself (rules.valid_set over the bundled fixtures) and checks membership, in stages of constraints with
stable ids (the reason codes):

0. answer key: the pinned valid set equals the verifier's own (else the plugin is broken);
1. referential integrity: an itinerary is named, exists, and leaves the origin on the date for the destination;
2. internal consistency: no code twice; in_policy is true exactly when no code is listed;
3. policy decision: the itinerary is in the valid set, and in_policy is true;
4. approvals and flags: no pre-authorization is listed (a valid booking needs none), the bag allowance.
"""

from .checks import UNEXPECTED, fixtures, plain, result
from .explain import set_problem, why
from .rules import valid_set
from .stages import bags_problem, consistency_problem, judge, unique_problem
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
    "preauths-correct": "A valid booking lists no pre-authorization",
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

    def serves():
        if booked() is None:
            return None  # nothing booked, or itinerary-exists already fails
        segments = itinerary_segments(world, booked())
        wanted = [scenario["origin"], scenario["departure_date"], scenario["destination"]]
        actual = [segments[0]["origin"], segments[0]["depart_local"][:10], segments[-1]["destination"]]
        if actual != wanted:
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

    stages = [
        [("reference-matches-valid-set", reference)],
        [("itinerary-named", named), ("itinerary-exists", exists), ("itinerary-serves-request", serves)],
        [("preauths-unique", lambda: unique_problem(codes)), ("in-policy-matches-preauths", lambda: consistency_problem(given))],
        [("itinerary-in-policy", in_valid_set), ("in-policy-correct", in_policy)],
        [
            ("preauths-correct", lambda: set_problem(world, scenario, booked(), "economy", [], codes)),
            ("bags-correct", lambda: bags_problem(scenario["checked_bags"], key["reimbursable_checked_bags"], given["reimbursable_checked_bags"])),
        ],
    ]
    success = (
        f"the booking is in policy: {itinerary_id} is one of {len(valid)} valid itineraries ({', '.join(valid)}); "
        f"bags {key['reimbursable_checked_bags']}"
    )
    return judge(stages, TEXT, success)
