from slimconfig import build_output

from contract import AuditCaseOutput, AuditInput, BookInput, TripRequestOutput
from plugin.fixtures import scenario, world
from plugin.rules import audit_case, trip_request


def get_audit_case(given: AuditInput) -> AuditCaseOutput:
    """The booking under audit with its request and every same-day alternative: facts, never an answer."""
    return build_output(audit_case(world(), scenario(given.scenario.value)), AuditCaseOutput)


def get_trip_request(given: BookInput) -> TripRequestOutput:
    """The trip to book: the traveler's words and the structured facts, never an answer."""
    return build_output(trip_request(world(), scenario(given.scenario.value)), TripRequestOutput)
