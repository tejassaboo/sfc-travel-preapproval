"""The deterministic verifier: each tool's checks and each task's verdict, on contract instances.

Every entry point returns a verdict and never raises: an unknown task or tool id becomes a failed
``verifier-error`` verdict, because a raise would leave the run with no verdict at all."""

from contract import Task, Tool

from . import audit, book, lookups, search
from .checks import result

# tool -> (verify_input(value), verify_output(input_value, output_value, workspace))
TOOLS = {
    Tool.GET_AUDIT_CASE: (lookups.verify_input, lookups.checker("get_audit_case")),
    Tool.GET_TRIP_REQUEST: (lookups.verify_input, lookups.checker("get_trip_request")),
    Tool.SEARCH_ITINERARIES: (search.verify_input, search.verify_output),
    Tool.COMPUTE_AUDIT: (audit.verify_input, audit.verify_output),
    Tool.COMPUTE_VALID_SET: (book.verify_input, book.verify_output),
}
# task -> its output's check, verify_task(arguments, output, reference, workspace)
TASKS = {Task.SFC_AUDIT: audit.verify_task, Task.SFC_BOOK: book.verify_task}


def _tool(tool):
    """The tool's (verify_input, verify_output), or a verifier-error verdict for an unknown id."""
    try:
        return TOOLS[Tool(tool)], None
    except (ValueError, KeyError, TypeError) as error:
        return None, result(False, f"verifier-error: unknown tool {tool!r} ({error})")


def verify_input(tool, value):
    checks, failed = _tool(tool)
    return failed if checks is None else checks[0](value)


def verify_output(tool, input_value, output_value, workspace):
    checks, failed = _tool(tool)
    return failed if checks is None else checks[1](input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    try:
        check = TASKS[Task(task)]
    except (ValueError, KeyError, TypeError) as error:
        return result(False, f"verifier-error: unknown task {task!r} ({error})")
    return check(arguments, output, reference, workspace)
