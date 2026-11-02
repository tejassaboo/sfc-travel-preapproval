"""The sfc-audit verdict, and the checks of its reference tool compute_audit.

The verifier computes the correct audit itself (rules.audit_oracle over the bundled fixtures) and checks
the submitted one in stages, each a list of constraints with stable ids (the reason codes):

0. answer key: the pinned reference equals the verifier's own oracle (else the plugin is broken);
1. referential integrity: an audit books nothing, so itinerary_id is null;
2. internal consistency: no code twice; in_policy is true exactly when no code is listed;
3. policy decision against the oracle: in_policy;
4. approvals and flags against the oracle: the set of pre-authorizations, the bag allowance.

The pre-authorizations are compared as a set (order never matters; repeats are refused at stage 2).
Shape problems (types, Enum values, missing or extra fields) never get here: NanoAgent's build_output
refuses them first.
"""

from .checks import UNEXPECTED, fixtures, plain, result
from .explain import set_problem, why
from .rules import audit_oracle
from .stages import bags_problem, consistency_problem, judge, unique_problem

TEXT = {
    "reference-matches-oracle": "The pinned answer key equals the verifier's own oracle",
    "itinerary-null-for-audit": "An audit books nothing: itinerary_id is null (C10)",
    "preauths-unique": "No pre-authorization is listed twice",
    "in-policy-matches-preauths": "in_policy is true exactly when required_preauthorizations is empty (C8)",
    "in-policy-correct": "in_policy is what C2-C7 give for the booking under audit",
    "preauths-correct": "required_preauthorizations is exactly the set C2-C7 give",
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

    stages = [
        [("reference-matches-oracle", reference)],
        [("itinerary-null-for-audit", null_itinerary)],
        [("preauths-unique", lambda: unique_problem(codes)), ("in-policy-matches-preauths", lambda: consistency_problem(given))],
        [("in-policy-correct", decision)],
        [
            ("preauths-correct", lambda: set_problem(world, scenario, itinerary, cabin, key["required_preauthorizations"], codes)),
            ("bags-correct", lambda: bags_problem(scenario["checked_bags"], key["reimbursable_checked_bags"], given["reimbursable_checked_bags"])),
        ],
    ]
    listed = ", ".join(key["required_preauthorizations"]) or "no pre-authorization"
    success = f"the audit is right: {itinerary['itinerary_id']} in {cabin} needs {listed}; bags {key['reimbursable_checked_bags']}"
    return judge(stages, TEXT, success)
