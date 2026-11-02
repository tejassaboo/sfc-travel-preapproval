from slimconfig import build_output

from contract import AuditInput, BookInput, SfcOutput, SfcValidSetOutput
from plugin.fixtures import scenario, world
from plugin.rules import audit_oracle, valid_set


def compute_audit(given: AuditInput) -> SfcOutput:
    """The sfc-audit answer key: the handbook's rules over the bundled fixtures."""
    return build_output(audit_oracle(world(), scenario(given.scenario.value)), SfcOutput)


def compute_valid_set(given: BookInput) -> SfcValidSetOutput:
    """The sfc-book answer key: every itinerary a correct booking may name, and why the others may not."""
    return build_output(valid_set(world(), scenario(given.scenario.value)), SfcValidSetOutput)
