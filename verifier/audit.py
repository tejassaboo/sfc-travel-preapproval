"""The sfc-audit verdict, and the checks of its reference tool compute_audit.

The verifier computes the correct audit itself (rules.audit_oracle over the bundled fixtures) and checks
the submitted one in stages, each a list of constraints with stable ids (the reason codes):

0. answer key: the pinned reference equals the verifier's own oracle (else the plugin is broken);
1. referential integrity: an audit books nothing, so itinerary_id is null;
2. internal consistency: no code twice; in_policy is true exactly when no code is listed;
3. policy decision against the oracle: in_policy;
4. approvals, magnitudes and flags against the oracle: the set of pre-authorizations, the fare judged, the
   lowest logical fare, the days ahead, the bag allowance.

The pre-authorizations are compared as a set (order never matters; repeats are refused at stage 2).
The score is stages.partial_score: Jaccard overlap of the code sets (0 when the answer contradicts itself),
plus each right magnitude and the bag allowance; an audit that names an itinerary is capped at 0.5.
Shape problems (types, Enum values, missing or extra fields) never get here: NanoAgent's build_output
refuses them first.
"""

from .checks import UNEXPECTED, fixtures, plain, result
from .explain import set_problem, why
from .rules import audit_oracle
from .stages import (
    AUDIT_BOOKS_SOMETHING_CAP,
    FACTS,
    bags_problem,
    consistency_problem,
    consistent,
    jaccard,
    judge,
    magnitude_problem,
    partial_score,
    unique_problem,
)

TEXT = {
    "reference-matches-oracle": "The pinned answer key equals the verifier's own oracle",
    "itinerary-null-for-audit": "An audit books nothing: itinerary_id is null (C10)",
    "preauths-unique": "No pre-authorization is listed twice",
    "in-policy-matches-preauths": "in_policy is true exactly when required_preauthorizations is empty (C8)",
    "in-policy-correct": "in_policy is what C2-C7 give for the booking under audit",
    "preauths-correct": "required_preauthorizations is exactly the set C2-C7 give",
    "fare-correct": "fare_cents is the chosen fare in the booked cabin (C3, C10a)",
    "lowest-logical-fare-correct": "lowest_logical_fare_cents is C5's lowest logical fare",
    "advance-days-correct": "advance_days is departure_date minus booking_date in calendar days (C4)",
    "bags-correct": "reimbursable_checked_bags is what C9 gives",
}


def verify_input(value):
    return result(True, "input is valid")  # a scenario Enum member is all the input there is


def verify_output(input_value, output_value, workspace):
    try:
        world, scenario = fixtures(plain(input_value)["scenario"])
        key = audit_oracle(world, scenario)
    except UNEXPECTED as error:
        return result(False, f"verifier-error: {error!r}")
    if plain(output_value) != key:
        return result(False, "compute_audit differs from the verifier's oracle", expected=key)
    return result(True, "the answer key matches the verifier's oracle")


def verify_task(arguments, output, reference, workspace):
    try:
        world, scenario = fixtures(plain(arguments)["scenario"])
        key = audit_oracle(world, scenario)
        pinned = None if reference is None else plain(reference)
        verdict = judge_audit(world, scenario, key, pinned, plain(output))
        verdict["details"]["expected"] = key
        return verdict
    except UNEXPECTED as error:
        return result(False, f"verifier-error: {error!r}")


def audit_score(key, pinned, given):
    """The partial score of an audit (see stages): 0 when the pinned key is wrong, capped when it books."""
    if pinned is not None and pinned != key:
        return 0.0
    decision = jaccard(key["required_preauthorizations"], given["required_preauthorizations"]) if consistent(given) else 0.0
    facts = [given[name] == key[name] for name in FACTS]
    return partial_score(decision, facts, cap=1.0 if given["itinerary_id"] is None else AUDIT_BOOKS_SOMETHING_CAP)


def judge_audit(world, scenario, key, pinned, given):
    itinerary = world["itineraries"][scenario["chosen_itinerary_id"]]
    cabin = scenario["chosen_cabin"]
    codes = given["required_preauthorizations"]

    def reference():
        if pinned is not None and pinned != key:
            return key, pinned, "the pinned answer key differs from the verifier's oracle, so the plugin itself is broken"
        return None

    def null_itinerary():
        if given["itinerary_id"] is not None:
            return None, given["itinerary_id"], f"an audit books nothing, but itinerary_id is {given['itinerary_id']!r}"
        return None

    def decision():
        if given["in_policy"] == key["in_policy"]:
            return None
        if key["in_policy"]:
            reason = "the booking triggers no pre-authorization"
        else:
            first = key["required_preauthorizations"][0]
            reason = f"it needs {first}: {why(world, scenario, itinerary, cabin, first)}"
        return key["in_policy"], given["in_policy"], f"in_policy should be {str(key['in_policy']).lower()}: {reason}"

    def fare():
        return magnitude_problem("fare_cents", key["fare_cents"], given["fare_cents"], f"{itinerary['itinerary_id']}'s {cabin} fare")

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
        [("reference-matches-oracle", reference)],
        [("itinerary-null-for-audit", null_itinerary)],
        [("preauths-unique", lambda: unique_problem(codes)), ("in-policy-matches-preauths", lambda: consistency_problem(given))],
        [("in-policy-correct", decision)],
        [
            ("preauths-correct", lambda: set_problem(world, scenario, itinerary, cabin, key["required_preauthorizations"], codes)),
            ("fare-correct", fare),
            ("lowest-logical-fare-correct", lowest),
            ("advance-days-correct", days),
            ("bags-correct", lambda: bags_problem(scenario["checked_bags"], key["reimbursable_checked_bags"], given["reimbursable_checked_bags"])),
        ],
    ]
    listed = ", ".join(key["required_preauthorizations"]) or "no pre-authorization"
    success = (
        f"the audit is right: {itinerary['itinerary_id']} in {cabin} at {key['fare_cents']} cents needs {listed}; "
        f"lowest logical fare {key['lowest_logical_fare_cents']}, {key['advance_days']} days ahead, bags {key['reimbursable_checked_bags']}"
    )
    return judge(stages, TEXT, success, audit_score(key, pinned, given))
