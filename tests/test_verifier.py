"""The verifier against hand-written submissions (no agent): the brief's section 7 matrix for both tasks.
Correct, incorrect, missing, consistency and verifier-caught malformed cases run through verify_task;
shape problems are refused by build_output before any verifier runs, exactly as in NanoAgent."""

import json

import pytest
from helpers import AUDITS, BOOKINGS, SCENARIOS, arguments, case, reference, task_of, verdict
from slimconfig import build_output

import contract
import verifier
from contract import SearchInput, SfcOutput, SfcValidSetOutput

AUDIT_ORDER = [
    "reference-matches-oracle",
    "itinerary-null-for-audit",
    "preauths-unique",
    "in-policy-matches-preauths",
    "in-policy-correct",
    "preauths-correct",
    "fare-correct",
    "lowest-logical-fare-correct",
    "advance-days-correct",
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
    "fare-correct",
    "lowest-logical-fare-correct",
    "advance-days-correct",
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
    assert result["valid"] is False and 0.0 <= result["score"] < 1.0
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
    seattle = verdict("seattle-release-party", {**case("seattle-release-party")["expected"], "itinerary_id": "I525", "fare_cents": 76500})
    assert "itinerary I525 needs COST_OVER_DOMESTIC_750 (economy fare 76500 cents ($765.00) > the $750.00 cap" in seattle["message"]
    assert seattle["message"].endswith("in policy: I177, I219, I730")
    austin = verdict("austin-hackfest", {**case("austin-hackfest")["expected"], "advance_days": 14, "lowest_logical_fare_cents": 29900})
    assert austin["message"].startswith("lowest-logical-fare-correct: lowest_logical_fare_cents should be 33100 (the lowest economy fare")
    assert "advance_days should be 13 (2026-11-15 minus 2026-11-02 in calendar days), not 14" in json.dumps(austin["details"]["constraints"])


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
        {"valid_itinerary_ids": ["I662"], "lowest_logical_fare_cents": 24500, "advance_days": 30, "reimbursable_checked_bags": "one", "rejected": {}},
        SfcValidSetOutput,
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
        ("boston-mentor-summit", {"itinerary_id": "I658", "fare_cents": 51000}, None),  # boundary: band exactly 20000 is valid
        ("boston-mentor-summit", {"itinerary_id": "I158", "fare_cents": 51001}, "itinerary-in-policy"),  # 20001 is not
        ("anchorage-mirror-rollout", {"itinerary_id": "I888", "fare_cents": 75000}, None),  # the domestic cap, exactly
        ("anchorage-mirror-rollout", {"itinerary_id": "I584", "fare_cents": 75001}, "itinerary-in-policy"),  # one cent over
        ("dublin-packaging-summit", {"itinerary_id": "I245", "fare_cents": 150000}, None),  # the international cap and the band, exactly
        ("dublin-packaging-summit", {"itinerary_id": "I452", "fare_cents": 150001}, "itinerary-in-policy"),  # one cent over both
        ("phoenix-kernel-workshop", {"itinerary_id": "I480", "fare_cents": 44900}, None),  # band exactly 20000, 14 days ahead
        ("phoenix-kernel-workshop", {"itinerary_id": "I593", "fare_cents": 44901}, "itinerary-in-policy"),
        ("ponce-archive-migration", {"itinerary_id": "I100", "fare_cents": 98500}, None),  # band exactly 20000, 365 days ahead
        ("ponce-archive-migration", {"itinerary_id": "I716", "fare_cents": 98501}, "itinerary-in-policy"),
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


@pytest.mark.parametrize("task", ["sfc-route", "", None, 7])
def test_an_unknown_task_id_is_a_verdict_not_a_raise(task) -> None:
    good = build_output(GENEVA, SfcOutput)
    result = verifier.verify_task(task, arguments("geneva-licensing-hearing"), good, reference("geneva-licensing-hearing"), ".")
    assert result["valid"] is False and result["score"] == 0.0
    assert result["message"].startswith("verifier-error: unknown task")
    json.dumps(result)


@pytest.mark.parametrize("tool", ["get_booking", "", None, 7])
def test_an_unknown_tool_id_is_a_verdict_not_a_raise(tool) -> None:
    for result in (
        verifier.verify_input(tool, arguments("geneva-licensing-hearing")),
        verifier.verify_output(tool, arguments("geneva-licensing-hearing"), reference("geneva-licensing-hearing"), "."),
    ):
        assert result["valid"] is False and result["message"].startswith("verifier-error: unknown tool")
        json.dumps(result)


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


# ---- partial credit (valid stays strict; see verifier/stages.py) ----------------------------------------------

LAZY_AUDIT = {"in_policy": False, "required_preauthorizations": [], "itinerary_id": None, "fare_cents": 0, "lowest_logical_fare_cents": 0, "advance_days": 0, "reimbursable_checked_bags": "zero"}
LAZY_BOOK = {**LAZY_AUDIT}
ALL_CODES = [member.value for member in contract.SfcPreauth]


def score(scenario, output):
    return verdict(scenario, output)["score"]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_valid_means_score_one_and_a_wrong_answer_never_scores_one(scenario: str) -> None:
    assert score(scenario, case(scenario)["expected"]) == 1.0
    for broken in case(scenario)["broken"]:
        result = verdict(scenario, {**case(scenario)["expected"], **broken["change"]})
        assert result["valid"] is False and result["score"] < 1.0


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_lazy_answers_score_at_most_the_bag_allowance(scenario: str) -> None:
    lazy = LAZY_AUDIT if scenario in AUDITS else LAZY_BOOK
    assert score(scenario, lazy) <= 0.1  # at most the bag allowance, when "zero" happens to be right
    assert score(scenario, {**lazy, "in_policy": True}) <= 0.1 + (0.6 if scenario in AUDITS and case(scenario)["expected"]["in_policy"] else 0.0)
    everything = {**lazy, "required_preauthorizations": ALL_CODES}
    assert score(scenario, everything) <= 0.1 + 0.6 * 4 / 7  # Geneva's four codes are the most any audit needs


def test_the_audit_decision_is_the_jaccard_overlap_of_the_code_sets() -> None:
    four = GENEVA  # COST_OVER_INTL_1500, BOOKED_LT_14_DAYS, ABOVE_LOW_FARE_BAND_200, NON_ECONOMY_CABIN; every magnitude right
    assert score("geneva-licensing-hearing", {**four, "required_preauthorizations": four["required_preauthorizations"][:3]}) == 0.4 + 0.6 * 3 / 4
    assert score("geneva-licensing-hearing", {**four, "required_preauthorizations": [*four["required_preauthorizations"], "TWO_PLUS_CONNECTIONS"]}) == 0.4 + 0.6 * 4 / 5
    one = case("denver-board-retreat")["expected"]  # COST_OVER_DOMESTIC_750
    missing = {**one, "in_policy": True, "required_preauthorizations": []}
    extra = {**one, "required_preauthorizations": ["COST_OVER_DOMESTIC_750", "BOOKED_LT_14_DAYS"]}
    wrong = {**one, "required_preauthorizations": ["COST_OVER_INTL_1500"]}
    assert score("denver-board-retreat", missing) == 0.4  # the decision earns nothing; the magnitudes and bags stand
    assert score("denver-board-retreat", extra) == 0.4 + 0.6 * 1 / 2
    assert score("denver-board-retreat", wrong) == 0.4
    none = case("portland-docs-sprint")["expected"]  # in policy
    assert score("portland-docs-sprint", {**none, "in_policy": False, "required_preauthorizations": ["ABOVE_LOW_FARE_BAND_200"]}) == 0.4


def test_wrong_in_either_direction_scores_the_same() -> None:
    one = case("honolulu-security-workshop")["expected"]
    too_few = {**one, "in_policy": True, "required_preauthorizations": []}
    too_many = {**one, "required_preauthorizations": ["COST_OVER_DOMESTIC_750", "NON_ECONOMY_CABIN", "TWO_PLUS_CONNECTIONS"]}
    assert score("honolulu-security-workshop", too_few) == 0.4 and score("honolulu-security-workshop", too_many) == 0.6
    for delta in (1, -1):
        assert score("honolulu-security-workshop", {**one, "fare_cents": one["fare_cents"] + delta}) == 0.9
        assert score("honolulu-security-workshop", {**one, "advance_days": one["advance_days"] + delta}) == 0.9
        assert score("honolulu-security-workshop", {**one, "lowest_logical_fare_cents": one["lowest_logical_fare_cents"] + delta}) == 0.9


def test_a_self_contradicting_answer_earns_nothing_for_the_decision() -> None:
    assert score("geneva-licensing-hearing", {**GENEVA, "in_policy": True}) == 0.4
    assert score("geneva-licensing-hearing", {**GENEVA, "required_preauthorizations": GENEVA["required_preauthorizations"] * 2}) == 0.4
    assert score("boston-mentor-summit", {**BOSTON, "in_policy": False}) == 0.4
    assert score("boston-mentor-summit", {**BOSTON, "in_policy": False, "required_preauthorizations": ["ABOVE_LOW_FARE_BAND_200"]}) == 0.4


def test_an_audit_that_books_something_is_capped_at_a_half() -> None:
    result = verdict("geneva-licensing-hearing", {**GENEVA, "itinerary_id": "I637"})
    assert result["valid"] is False and result["message"].startswith("itinerary-null-for-audit") and result["score"] == 0.5


def test_a_booking_earns_the_decision_only_for_a_valid_itinerary() -> None:
    expected = case("boston-mentor-summit")["expected"]
    assert score("boston-mentor-summit", {**expected, "itinerary_id": "I658", "fare_cents": 51000}) == 1.0
    assert score("boston-mentor-summit", {**expected, "itinerary_id": "I158", "fare_cents": 51001}) == 0.4  # real, same-day, one cent over: facts only
    assert score("boston-mentor-summit", {**expected, "itinerary_id": "I158", "fare_cents": 51000}) == 0.3  # and its fare misreported
    assert score("boston-mentor-summit", {**expected, "itinerary_id": "I749", "fare_cents": 19900}) == 0.3  # a day early: no fare credit
    assert score("boston-mentor-summit", {**expected, "itinerary_id": "I999"}) == 0.3  # unknown: no fare credit
    assert score("boston-mentor-summit", {**expected, "itinerary_id": None}) == 0.3
    assert score("boston-mentor-summit", {**expected, "itinerary_id": "I658", "fare_cents": 60000}) == 0.9  # right flight, premium economy fare


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_another_scenarios_answer_scores_low(scenario: str) -> None:
    for other in SCENARIOS:
        if other == scenario or task_of(other) != task_of(scenario):
            continue
        answer = case(other)["expected"]
        if answer == case(scenario)["expected"]:
            continue
        result = verdict(scenario, answer)
        assert result["valid"] is False
        # Another trip's slip can share the bag allowance, a code set and at most one coincident magnitude.
        assert result["score"] <= 0.8, (scenario, other, result["score"])


def test_a_wrong_answer_key_scores_zero() -> None:
    wrong = build_output({**case("denver-board-retreat")["expected"], "in_policy": True, "required_preauthorizations": []}, SfcOutput)
    good = build_output(case("denver-board-retreat")["expected"], SfcOutput)
    result = verifier.verify_task("sfc-audit", arguments("denver-board-retreat"), good, wrong, ".")
    assert result["valid"] is False and result["score"] == 0.0
