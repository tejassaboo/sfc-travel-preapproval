"""The staged judgment both tasks share: ordered constraints with stable ids (the reason codes), and the
partial score.

A stage is checked only when every earlier stage holds; later constraints are recorded as not checked.
Each constraint is {id, constraint, ok: True|False|None, expected, actual, message}. The message of a
failed verdict names the first failing constraint and how many more fail. ``valid`` is strict: true only
when every constraint holds, and then the score is 1.0.

The score is partial credit in [0, 1], computed over the whole answer whatever stage failed, as a sum of
weighted components (integer percents, so a right answer is exactly 1.0):

- decision, 60: for an audit, the Jaccard overlap of the submitted and required code sets (both empty
  counts as 1), and 0 when the answer contradicts itself (in_policy disagrees with the codes, or a code is
  listed twice); for a booking, 1 when the itinerary is in the valid set with in_policy true and no code,
  else 0;
- fare_cents, lowest_logical_fare_cents, advance_days, reimbursable_checked_bags, 10 each, when right.

Wrong in either direction scores the same (Jaccard is symmetric; a magnitude is right or not). A lazy or
empty answer earns at most the bag allowance. Integrity caps: an audit that names an itinerary is capped at
0.5; a booking that names no itinerary, an unknown one, or one for another trip earns nothing for the
decision or the fare. A pinned answer key that differs from the oracle (the plugin is broken) scores 0.
"""

from .checks import result

DECISION_WEIGHT = 60
FACT_WEIGHT = 10
FACTS = ("fare_cents", "lowest_logical_fare_cents", "advance_days", "reimbursable_checked_bags")
AUDIT_BOOKS_SOMETHING_CAP = 0.5


def judge(stages, text, success, score):
    """``stages``: lists of (id, check); a check returns None, or (expected, actual, message) on failure.
    ``score``: the partial score of the answer, in [0, 1]; it is replaced by 1.0 when every constraint holds."""
    constraints, blocked = [], None
    for stage in stages:
        for identifier, check in stage:
            if blocked is not None:
                constraints.append(entry(text, identifier, None, None, None, f"not checked: {blocked} failed"))
                continue
            problem = check()
            if problem is None:
                constraints.append(entry(text, identifier, True, None, None, ""))
            else:
                constraints.append(entry(text, identifier, False, *problem))
        failed = [item for item in constraints if item["ok"] is False]
        if failed and blocked is None:
            blocked = failed[0]["id"]
    failed = [item for item in constraints if item["ok"] is False]
    if not failed:
        return result(True, success, constraints=constraints)
    more = f" (+{len(failed) - 1} more)" if len(failed) > 1 else ""
    return result(False, f"{failed[0]['id']}: {failed[0]['message']}{more}", score=min(score, 0.99), constraints=constraints)


def entry(text, identifier, ok, expected, actual, message):
    return {"id": identifier, "constraint": text[identifier], "ok": ok, "expected": expected, "actual": actual, "message": message}


def jaccard(wanted, given):
    """|wanted ∩ given| / |wanted ∪ given| over the two code sets; 1.0 when both are empty."""
    wanted, given = set(wanted), set(given)
    union = wanted | given
    return 1.0 if not union else len(wanted & given) / len(union)


def partial_score(decision, facts, cap=1.0):
    """The partial score: ``decision`` in [0, 1] weighted DECISION_WEIGHT, each right fact FACT_WEIGHT, capped."""
    points = DECISION_WEIGHT * decision + FACT_WEIGHT * sum(1 for right in facts if right)
    return round(min(points / 100, cap), 4)


def unique_problem(items):
    repeated = sorted({item for item in items if items.count(item) > 1})
    if repeated:
        return None, repeated, f"listed more than once: {', '.join(repeated)}"
    return None


def consistent(given):
    """in_policy is true exactly when no pre-authorization is listed, and none is listed twice (C8)."""
    codes = given["required_preauthorizations"]
    return given["in_policy"] == (codes == []) and len(set(codes)) == len(codes)


def consistency_problem(given):
    """in_policy is true exactly when no pre-authorization is listed (C8)."""
    codes = given["required_preauthorizations"]
    if given["in_policy"] != (codes == []):
        state = "lists no pre-authorization" if not codes else f"lists {', '.join(sorted(codes))}"
        return codes == [], given["in_policy"], f"in_policy is {str(given['in_policy']).lower()} but the answer {state}"
    return None


def magnitude_problem(name, wanted, given, meaning):
    if given == wanted:
        return None
    return wanted, given, f"{name} should be {wanted} ({meaning}), not {given}"


def bags_problem(requested, wanted, given):
    if given == wanted:
        return None
    return wanted, given, f"{requested} checked bag(s) requested: reimbursable is {wanted}, never more than one (C9)"
