"""What the tests share: paths, the scenarios, the hand-written cases, and values built the way
NanoAgent's sandbox builds them (build_output from plain JSON)."""

import json
from pathlib import Path

from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, AuditScenario, BookScenario, SfcOutput, Task
from plugin import compute_audit, compute_valid_set

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "plugin" / "data"
AUDITS = [member.value for member in AuditScenario]
BOOKINGS = [member.value for member in BookScenario]
SCENARIOS = AUDITS + BOOKINGS
REFERENCES = {"sfc-audit": compute_audit, "sfc-book": compute_valid_set}


def case(scenario):
    """The hand-written case: {scenario, task, note, expected, broken: [{why, change, reason}], ...}."""
    return json.loads((ROOT / "tests" / "cases" / f"{scenario}.json").read_text(encoding="utf-8"))


def task_of(scenario):
    return "sfc-audit" if scenario in AUDITS else "sfc-book"


def arguments(scenario):
    return build_output({"scenario": scenario}, TASKS[Task(task_of(scenario))][0])


def reference(scenario):
    """The pinned reference, as NanoAgent pins it: the reference tool's output, built into its class."""
    made = REFERENCES[task_of(scenario)](arguments(scenario))
    return build_output(plain_output(made), type(made))


def verdict(scenario, output, *, pinned=True):
    """verify_task on a plain-JSON submission, with the reference pinned as in a real run."""
    return verifier.verify_task(
        task_of(scenario), arguments(scenario), build_output(output, SfcOutput), reference(scenario) if pinned else None, "."
    )
