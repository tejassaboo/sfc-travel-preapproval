"""The environment: the vendored copies stay identical, the handbook is both tasks' instructions, the
generator reproduces the committed fixtures, the fixtures hold their invariants (recomputed here with
zoneinfo, which the plugin itself never uses at evaluation time), and every fact the policy decides on
is a typed field of a tool output."""

import json
import re
from datetime import datetime
from itertools import pairwise
from zoneinfo import ZoneInfo

import pytest
from helpers import AUDITS, BOOKINGS, DATA, ROOT, SCENARIOS

from contract import AuditCaseOutput, ItineraryOption, SfcPreauth, TripRequestOutput
from plugin.fixtures import world
from plugin.rules import same_day
from plugin.tools_dev.generate import build
from plugin.world import schema_problems

AUDIT_KEYS = ["scenario", "request_text", "booking_date", "traveler_id", "origin", "destination", "departure_date",
              "chosen_itinerary_id", "chosen_cabin", "checked_bags", "task"]
BOOK_KEYS = ["scenario", "request_text", "booking_date", "traveler_id", "origin", "destination", "departure_date",
             "requested_cabin", "checked_bags", "task"]


@pytest.mark.parametrize("module", ["rules.py", "world.py"])
def test_the_verifier_runs_the_same_code(module: str) -> None:
    assert (ROOT / "verifier" / module).read_bytes() == (ROOT / "src" / "plugin" / module).read_bytes()


def test_the_shared_core_is_vendored_unchanged() -> None:
    core = ROOT.parent / "_shared_core"
    if not core.is_dir():
        pytest.skip("outside the development tree: the shared core is not alongside")
    assert (core / "world.py").read_bytes() == (ROOT / "src" / "plugin" / "world.py").read_bytes()
    assert (core / "worldgen.py").read_bytes() == (ROOT / "src" / "plugin" / "tools_dev" / "worldgen.py").read_bytes()


def instructions(manifest_text, task):
    """A task's instructions: the `|-` block scalar under it, unindented."""
    lines = manifest_text.split("\n")
    start = lines.index(f"  {task}:")
    start = lines.index("    instructions: |-", start) + 1
    block = []
    for line in lines[start:]:
        if line and not line.startswith("      "):
            break
        block.append(line[6:])
    return "\n".join(block).rstrip("\n")


@pytest.mark.parametrize("task", ["sfc-audit", "sfc-book"])
def test_the_handbook_is_the_task_instructions(task: str) -> None:
    handbook = (DATA / "handbook.md").read_text(encoding="utf-8")
    assert instructions((ROOT / "nanoagent.yaml").read_text(encoding="utf-8"), task) == handbook.rstrip("\n")
    assert len(handbook.split()) <= 1500


def test_both_tasks_run_on_the_agent_runner() -> None:
    # sfc-audit was switched from decide after its final question batch was cut off at the 2,048-token reply
    # cap in two paid runs (san-juan-outreach, temperature 0); both step plans say "submit by step 5".
    manifest = (ROOT / "nanoagent.yaml").read_text(encoding="utf-8")
    assert manifest.count("    runner: agent") == 2 and "runner: decide" not in manifest
    handbook = (DATA / "handbook.md").read_text(encoding="utf-8")
    assert "## Step plan: sfc-audit (submit by step 5)" in handbook
    assert "## Step plan: sfc-book (submit by step 5)" in handbook


def test_the_handbook_pins_its_source_and_states_the_toy_rules() -> None:
    handbook = (DATA / "handbook.md").read_text(encoding="utf-8")
    for needle in (
        "ff3c541449db53100f3dfed6061280ef6e7e37bb",
        "2012-03-27",
        "historical toy policy",
        "45135e3",
        "$1,800",
        "$1,650",
        "tiered fare budgets",
        "CC0",
        "## Clarifications (toy rules)",
        "## Rules not in scope",
        "## Step plan: sfc-audit",
        "## Step plan: sfc-book",
        *(f"C{number} " for number in range(1, 13)),
    ):
        assert needle in handbook, needle


def test_the_organization_is_named_only_in_the_citation() -> None:
    handbook = (DATA / "handbook.md").read_text(encoding="utf-8")
    citation, rest = handbook.split("\n\n", 2)[1], handbook.split("\n\n", 2)[2]
    assert "Software Freedom Conservancy" in citation
    assert not re.search(r"Conservancy|sfconservancy|SFC\b", rest)


def test_every_code_is_in_the_handbook() -> None:
    handbook = (DATA / "handbook.md").read_text(encoding="utf-8")
    assert all(member.value in handbook for member in SfcPreauth)


def test_the_generator_reproduces_the_committed_fixtures() -> None:
    files = build()
    assert sorted(files) == sorted(path.relative_to(DATA).as_posix() for path in DATA.rglob("*.json"))
    for relative, text in files.items():
        assert (DATA / relative).read_text(encoding="utf-8") == text, relative


def test_the_fixtures_follow_the_schema() -> None:
    assert schema_problems(world()) == []


def local(stamp, timezone):
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M").replace(tzinfo=ZoneInfo(timezone))


def utc(stamp):
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%MZ").replace(tzinfo=ZoneInfo("UTC"))


def test_segment_times_are_consistent() -> None:
    airports = world()["airports"]
    for segment in world()["segments"].values():
        depart = local(segment["depart_local"], airports[segment["origin"]]["timezone"])
        arrive = local(segment["arrive_local"], airports[segment["destination"]]["timezone"])
        assert depart == utc(segment["depart_utc"]) and arrive == utc(segment["arrive_utc"]), segment["segment_id"]
        assert (arrive - depart).total_seconds() == segment["in_air_minutes"] * 60


def test_itinerary_totals_and_fares() -> None:
    data = world()
    for record in data["itineraries"].values():
        segments = [data["segments"][segment_id] for segment_id in record["segment_ids"]]
        layovers = [int((utc(b["depart_utc"]) - utc(a["arrive_utc"])).total_seconds() // 60) for a, b in pairwise(segments)]
        assert record["layover_minutes"] == layovers and record["connections"] == len(segments) - 1
        assert all(45 <= minutes <= 24 * 60 for minutes in layovers), record["itinerary_id"]
        assert record["total_in_air_minutes"] == sum(segment["in_air_minutes"] for segment in segments)
        assert record["fares_cents"]["economy"] is not None, record["itinerary_id"]
        assert all(isinstance(fare, int) and fare > 0 for fare in record["fares_cents"].values() if fare is not None)


def test_carriers_and_travelers_are_fictional_and_unique() -> None:
    data = world()
    assert len({carrier["name"] for carrier in data["carriers"].values()}) == len(data["carriers"])
    used = {json.loads((DATA / "scenarios" / f"{scenario}.json").read_text())["traveler_id"] for scenario in SCENARIOS}
    assert used == set(data["travelers"]) and len(used) == len(SCENARIOS)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_scenario_files_hold_facts_only(scenario: str) -> None:
    facts = json.loads((DATA / "scenarios" / f"{scenario}.json").read_text(encoding="utf-8"))
    assert list(facts) == (AUDIT_KEYS if scenario in AUDITS else BOOK_KEYS) and facts["scenario"] == scenario
    assert facts["traveler_id"] in world()["travelers"]
    assert facts["origin"] in world()["airports"] and facts["destination"] in world()["airports"]
    found = same_day(world(), facts)
    assert len(found) >= (8 if scenario in BOOKINGS else 5)  # always alternatives to compare against
    if scenario in AUDITS:
        assert facts["chosen_itinerary_id"] in [item["itinerary_id"] for item in found]
        assert world()["itineraries"][facts["chosen_itinerary_id"]]["fares_cents"][facts["chosen_cabin"]] is not None


def fields(cls):
    return set(cls.__dataclass_fields__)


def test_every_policy_fact_is_a_typed_field() -> None:
    # C2 endpoints' us_50_states_dc, C3 fare in the booked cabin, C4 the two dates, C5 every same-day
    # itinerary's connections and economy fare, C6 the cabin, C7 connections, C9 bags, C11 the requested
    # cabin: each is a typed field (test_cases.py also shows the answers ignore request_text).
    assert {"booking_date", "departure_date", "origin", "destination", "chosen", "checked_bags_requested", "same_day_itineraries"} <= fields(AuditCaseOutput)
    assert {"booking_date", "departure_date", "origin", "destination", "requested_cabin", "checked_bags_requested"} <= fields(TripRequestOutput)
    assert {"connections", "fares_cents", "itinerary_id"} <= fields(ItineraryOption)


def test_gitignore_keeps_the_bundled_data() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    assert not any(pattern in ("*.json", "*.md", "data/", "src/") for pattern in ignored)
