"""The staged judgment both tasks share: ordered constraints with stable ids (the reason codes).

A stage is checked only when every earlier stage holds; later constraints are recorded as not checked.
Each constraint is {id, constraint, ok: True|False|None, expected, actual, message}. The message of a
failed verdict names the first failing constraint and how many more fail. The score is 1.0 when every
constraint holds, else 0.0.
"""

from .checks import result


def judge(stages, text, success):
    """``stages``: lists of (id, check); a check returns None, or (expected, actual, message) on failure."""
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
    return result(False, f"{failed[0]['id']}: {failed[0]['message']}{more}", constraints=constraints)


def entry(text, identifier, ok, expected, actual, message):
    return {"id": identifier, "constraint": text[identifier], "ok": ok, "expected": expected, "actual": actual, "message": message}


def unique_problem(items):
    repeated = sorted({item for item in items if items.count(item) > 1})
    if repeated:
        return None, repeated, f"listed more than once: {', '.join(repeated)}"
    return None


def consistency_problem(given):
    """in_policy is true exactly when no pre-authorization is listed (C8)."""
    codes = given["required_preauthorizations"]
    if given["in_policy"] != (codes == []):
        state = "lists no pre-authorization" if not codes else f"lists {', '.join(sorted(codes))}"
        return codes == [], given["in_policy"], f"in_policy is {str(given['in_policy']).lower()} but the answer {state}"
    return None


def bags_problem(requested, wanted, given):
    if given == wanted:
        return None
    return wanted, given, f"{requested} checked bag(s) requested: reimbursable is {wanted}, never more than one (C9)"
