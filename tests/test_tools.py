"""The tools: what they return, what they refuse, how big their outputs are, and the real MCP server."""

import json
import sys

import anyio
import pytest
from helpers import AUDITS, BOOKINGS, ROOT, arguments
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from slimconfig import build_output, plain_output

import verifier
from contract import SearchInput
from plugin import get_audit_case, get_trip_request, search_itineraries

MAX_OUTPUT_CHARS = 6000  # about 1.5k tokens: every tool output stays far from the hosted 65,536-token budget


def search(origin, destination, date):
    return search_itineraries(build_output({"origin": origin, "destination": destination, "date": date}, SearchInput))


@pytest.mark.parametrize("scenario", AUDITS)
def test_audit_case_matches_the_fixtures_and_stays_small(scenario: str) -> None:
    case = get_audit_case(arguments(scenario))
    assert verifier.verify_output("get_audit_case", arguments(scenario), case, ".")["valid"] is True
    assert len(json.dumps(plain_output(case))) <= MAX_OUTPUT_CHARS
    assert case.chosen.itinerary_id in [item.itinerary_id for item in case.same_day_itineraries]


@pytest.mark.parametrize("scenario", BOOKINGS)
def test_trip_request_and_search_match_the_fixtures_and_stay_small(scenario: str) -> None:
    request = get_trip_request(arguments(scenario))
    assert verifier.verify_output("get_trip_request", arguments(scenario), request, ".")["valid"] is True
    query = build_output({"origin": request.origin.code, "destination": request.destination.code, "date": request.departure_date}, SearchInput)
    found = search_itineraries(query)
    assert len(found.itineraries) >= 8, "the step plan's search finds the scenario's flights, enough that the ranking matters"
    assert verifier.verify_output("search_itineraries", query, found, ".")["valid"] is True
    for output in (request, found):
        assert len(json.dumps(plain_output(output))) <= MAX_OUTPUT_CHARS


def test_lookups_never_leak_an_answer() -> None:
    for scenario in AUDITS:
        text = json.dumps(plain_output(get_audit_case(arguments(scenario))))
        assert not any(word in text for word in ("in_policy", "preauthorization", "COST_OVER", "BOOKED_", "valid"))
    for scenario in BOOKINGS:
        assert "valid" not in json.dumps(plain_output(get_trip_request(arguments(scenario))))


def test_search_applies_no_policy_and_respects_the_date() -> None:
    found = search("DEN", "BOS", "2026-12-02").itineraries
    assert max(item.connections for item in found) == 2  # unreasonable itineraries are listed too
    assert [plain_output(item)["fares_cents"]["economy"] for item in search("DEN", "BOS", "2026-12-01").itineraries] == [19900]
    assert search("BOS", "DEN", "2026-12-02").itineraries == []


@pytest.mark.parametrize(
    ("origin", "destination", "date", "match"),
    [
        ("XXX", "BOS", "2026-12-02", "not an airport"),
        ("DEN", "bos", "2026-12-02", "not an airport"),
        ("DEN", "BOS", "2026-12-32", "calendar date"),
        ("DEN", "BOS", "12/02/2026", "YYYY-MM-DD"),
    ],
)
def test_search_refuses_bad_input(origin, destination, date, match) -> None:
    with pytest.raises(ValueError, match=match):
        search(origin, destination, date)


def test_a_changed_tool_output_is_caught() -> None:
    case = get_audit_case(arguments("honolulu-security-workshop"))
    changed = build_output({**plain_output(case), "booking_date": "2027-01-10"}, type(case))
    result = verifier.verify_output("get_audit_case", arguments("honolulu-security-workshop"), changed, ".")
    assert result["valid"] is False and "booking_date" in result["message"]


def test_the_mcp_server_serves_every_tool() -> None:
    async def session():
        server = StdioServerParameters(command=sys.executable, args=["-m", "plugin"], cwd=str(ROOT))
        async with stdio_client(server) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            names = sorted(tool.name for tool in (await client.list_tools()).tools)
            answer = await client.call_tool("get_audit_case", {"scenario": "san-juan-outreach"})
            refused = await client.call_tool("search_itineraries", {"origin": "XXX", "destination": "SJU", "date": "2027-02-08"})
            return names, answer, refused

    names, answer, refused = anyio.run(session)
    assert names == ["compute_audit", "compute_valid_set", "get_audit_case", "get_trip_request", "search_itineraries"]
    assert answer.isError is False and answer.structuredContent["destination"]["us_50_states_dc"] is False
    assert refused.isError is True
