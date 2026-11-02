"""The verifier against hand-written submissions (no agent): the brief's section 7 matrix for both tasks.
Correct, incorrect, missing, consistency and verifier-caught malformed cases run through verify_task;
shape problems are refused by build_output before any verifier runs, exactly as in NanoAgent."""

import json

import pytest
from helpers import AUDITS, BOOKINGS, SCENARIOS, arguments, case, reference, task_of, verdict
from slimconfig import build_output

import verifier
from contract import SearchInput, SfcOutput, SfcValidSetOutput

AUDIT_ORDER = [
    "reference-matches-oracle",
    "itinerary-null-for-audit",
    "preauths-unique",
    "in-policy-matches-preauths",
    "in-policy-correct",
    "preauths-correct",
    "bags-correct",
]
BOOK_ORDER = [
    "reference-matches-valid-set",
    "itinerary-named",
    "itinerary-exists",
    "itinerary-serves-request",
    "preauths-unique",
    "in-policy-matches-preauths",
    "itinerary-in-policy",
    "in-policy-correct",
    "preauths-correct",
    "bags-correct",
]
GENEVA = case("geneva-licensing-hearing")["expected"]
BOSTON = case("boston-mentor-summit")["expected"]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_the_hand_written_answer_passes(scenario: str) -> None:
    result = verdict(scenario, case(scenario)["expected"])
    assert result["valid"] is True and result["score"] == 1.0, result["message"]
    order = AUDIT_ORDER if scenario in AUDITS else BOOK_ORDER
    assert [entry["id"] for entry in result["details"]["constraints"]] == order
    assert all(entry["ok"] is True for entry in result["details"]["constraints"])


def test_preauthorizations_are_compared_as_a_set() -> None:
    flipped = {**GENEVA, "required_preauthorizations": GENEVA["required_preauthorizations"][::-1]}
    assert verdict("geneva-licensing-hearing", flipped)["valid"] is True


@pytest.mark.parametrize(
    ("scenario", "index"), [(scenario, index) for scenario in SCENARIOS for index in range(len(case(scenario)["broken"]))]
)
def test_each_broken_answer_fails_with_its_reason_code(scenario: str, index: int) -> None:
    broken = case(scenario)["broken"][index]
    result = verdict(scenario, {**case(scenario)["expected"], **broken["change"]})
    assert result["valid"] is False and result["score"] == 0.0
    assert result["message"].split(":")[0] == broken["reason"], (broken["why"], result["message"])
    failing = [entry for entry in result["details"]["constraints"] if entry["ok"] is False]
    assert failing[0]["id"] == broken["reason"]
    assert all(set(entry) == {"id", "constraint", "ok", "expected", "actual", "message"} for entry in result["details"]["constraints"])


def test_messages_name_the_rule_and_the_numbers() -> None:
    honolulu = verdict("honolulu-security-workshop", {**case("honolulu-security-workshop")["expected"], "required_preauthorizations": ["COST_OVER_INTL_1500"]})
    assert "missing COST_OVER_DOMESTIC_750 (economy fare 82500 cents ($825.00) > the $750.00 cap" in honolulu["message"]
    assert "not required COST_OVER_INTL_1500 (the trip is domestic: SFO and HNL are both in the 50 states + DC" in honolulu["message"]
    chicago = verdict("chicago-foundation-briefing", {**case("chicago-foundation-briefing")["expected"], "in_policy": True, "required_preauthorizations": []})
    assert chicago["message"].startswith("in-policy-correct: in_policy should be false: it needs ABOVE_LOW_FARE_BAND_200")
    assert "52001 - lowest logical fare 32000" in chicago["message"] and "= 20001 cents, which > 20000" in chicago["message"]
    seattle = verdict("seattle-release-party", {**case("seattle-release-party")["expected"], "itinerary_id": "I525"})
    assert "itinerary I525 needs COST_OVER_DOMESTIC_750 (economy fare 76500 cents ($765.00) > the $750.00 cap" in seattle["message"]
    assert seattle["message"].endswith("in policy: I730")


def test_a_failed_stage_leaves_later_stages_unchecked() -> None:
    result = verdict("boston-mentor-summit", {**BOSTON, "itinerary_id": "I999"})
    states = {entry["id"]: entry["ok"] for entry in result["details"]["constraints"]}
    assert states["itinerary-exists"] is False and states["itinerary-named"] is True
    assert all(states[identifier] is None for identifier in BOOK_ORDER[4:])


def test_a_message_counts_the_other_failures() -> None:
    # Right decision, a missing code and a wrong bag allowance: both stage-4 checks fail.
    result = verdict("geneva-licensing-hearing", {**GENEVA, "required_preauthorizations": GENEVA["required_preauthorizations"][:3], "reimbursable_checked_bags": "zero"})
    assert result["message"].startswith("preauths-correct: missing NON_ECONOMY_CABIN (the booked cabin is business)")
    assert result["message"].endswith("(+1 more)")


def test_a_wrong_answer_key_is_caught_before_the_submission() -> None:
    wrong = build_output({**case("denver-board-retreat")["expected"], "in_policy": True, "required_preauthorizations": []}, SfcOutput)
    good = build_output(case("denver-board-retreat")["expected"], SfcOutput)
    result = verifier.verify_task("sfc-audit", arguments("denver-board-retreat"), good, wrong, ".")
    assert result["valid"] is False and result["message"].startswith("reference-matches-oracle")
    key = case("boston-mentor-summit")
    wrong_set = build_output(
        {"valid_itinerary_ids": ["I662"], "lowest_logical_fare_cents": 24500, "reimbursable_checked_bags": "one", "rejected": {}}, SfcValidSetOutput
    )
    result = verifier.verify_task("sfc-book", arguments("boston-mentor-summit"), build_output(key["expected"], SfcOutput), wrong_set, ".")
    assert result["valid"] is False and result["message"].startswith("reference-matches-valid-set")


@pytest.mark.parametrize("scenario", ["portland-docs-sprint", "boston-mentor-summit"])
def test_without_a_pinned_reference_the_oracle_still_decides(scenario: str) -> None:
    assert verdict(scenario, case(scenario)["expected"], pinned=False)["valid"] is True
    broken = case(scenario)["broken"][0]
    assert verdict(scenario, {**case(scenario)["expected"], **broken["change"]}, pinned=False)["valid"] is False


@pytest.mark.parametrize(
    ("scenario", "change", "reason"),
    [
        ("geneva-licensing-hearing", {"required_preauthorizations": []}, "in-policy-matches-preauths"),  # missing: empty where required
        ("geneva-licensing-hearing", {"in_policy": True}, "in-policy-matches-preauths"),
        ("portland-docs-sprint", {"itinerary_id": "I999"}, "itinerary-null-for-audit"),
        ("boston-mentor-summit", {"itinerary_id": "I232"}, "itinerary-serves-request"),  # an existing itinerary of another trip
        ("boston-mentor-summit", {"in_policy": False, "required_preauthorizations": ["ABOVE_LOW_FARE_BAND_200"]}, "in-policy-correct"),
        ("boston-mentor-summit", {"itinerary_id": "I658"}, None),  # boundary: band exactly 20000 is valid
        ("boston-mentor-summit", {"itinerary_id": "I158"}, "itinerary-in-policy"),  # 20001 is not
    ],
)
def test_incorrect_missing_and_inconsistent_answers(scenario: str, change: dict, reason) -> None:
    result = verdict(scenario, {**case(scenario)["expected"], **change})
    if reason is None:
        assert result["valid"] is True, result["message"]
    else:
        assert result["valid"] is False and result["message"].split(":")[0] == reason, result["message"]


@pytest.mark.parametrize(
    "raw",
    [
        {**GENEVA, "in_policy": "false"},  # a string for a bool
        {**GENEVA, "in_policy": 0},
        {**GENEVA, "reimbursable_checked_bags": 3},  # an int for the bag allowance
        {**GENEVA, "reimbursable_checked_bags": "three"},
        {**GENEVA, "reimbursable_checked_bags": "One"},  # wrong case
        {**GENEVA, "required_preauthorizations": ["COST_OVER_750"]},  # unknown code
        {**GENEVA, "required_preauthorizations": "NON_ECONOMY_CABIN"},  # a string, not a list
        {**BOSTON, "itinerary_id": 328},
        {key: value for key, value in GENEVA.items() if key != "in_policy"},  # missing field
        {key: value for key, value in GENEVA.items() if key != "itinerary_id"},  # nullable still required
        {**GENEVA, "rationale": "urgent hearing"},  # extra field: no graded free text
        {**GENEVA, "in_policy": None},  # null for a non-optional field
        ["in_policy", True],  # not an object
    ],
)
def test_malformed_outputs_are_refused_before_the_verifier(raw) -> None:
    with pytest.raises(ValueError):
        build_output(raw, SfcOutput)


def test_non_json_output_never_parses() -> None:
    with pytest.raises(json.JSONDecodeError):
        json.loads("{in_policy: true, itinerary_id: I328}")


@pytest.mark.parametrize("task", ["sfc-audit", "sfc-book"])
@pytest.mark.parametrize(
    ("arguments_value", "output_value"),
    [(None, None), ("nonsense", 7), (arguments("geneva-licensing-hearing"), None), (arguments("boston-mentor-summit"), {"in_policy": True})],
)
def test_the_verifier_never_raises(task, arguments_value, output_value) -> None:
    result = verifier.verify_task(task, arguments_value, output_value, None, ".")
    assert result["valid"] is False and result["message"].startswith("verifier-error")


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_verdicts_are_deterministic_plain_json(scenario: str) -> None:
    broken = {**case(scenario)["expected"], **case(scenario)["broken"][0]["change"]}
    for output in (case(scenario)["expected"], broken):
        first, second = verdict(scenario, output), verdict(scenario, output)
        assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)  # no default=: plain JSON only
        assert isinstance(first["score"], float) and 0.0 <= first["score"] <= 1.0


@pytest.mark.parametrize(
    ("raw", "valid"),
    [
        ({"origin": "DEN", "destination": "BOS", "date": "2026-12-02"}, True),
        ({"origin": "den", "destination": "BOS", "date": "2026-12-02"}, False),
        ({"origin": "DEN", "destination": "BOST", "date": "2026-12-02"}, False),
        ({"origin": "DEN", "destination": "BOS", "date": "2027-02-29"}, False),
    ],
)
def test_search_input_checks(raw: dict, valid: bool) -> None:
    assert verifier.verify_input("search_itineraries", build_output(raw, SearchInput))["valid"] is valid


@pytest.mark.parametrize(("good", "other"), [("geneva-licensing-hearing", "san-juan-outreach"), ("paris-firmware-workshop", "seattle-release-party")])
def test_the_reference_tool_output_is_checked_against_the_oracle(good: str, other: str) -> None:
    tool = "compute_audit" if task_of(good) == "sfc-audit" else "compute_valid_set"
    assert verifier.verify_output(tool, arguments(good), reference(good), ".")["valid"] is True
    assert verifier.verify_output(tool, arguments(good), reference(other), ".")["valid"] is False


@pytest.mark.parametrize("scenario", BOOKINGS)
def test_a_booking_names_an_itinerary(scenario: str) -> None:
    result = verdict(scenario, {**case(scenario)["expected"], "itinerary_id": None})
    assert result["message"].startswith("itinerary-named: nothing booked")
