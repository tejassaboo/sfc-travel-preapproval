"""The deterministic verifier: each tool's checks and each task's verdict, on contract instances."""

from contract import Task, Tool

from . import audit, book, lookups, search

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


def verify_input(tool, value):
    return TOOLS[Tool(tool)][0](value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)][1](input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
