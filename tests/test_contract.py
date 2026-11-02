"""Structured input and structured output: every contract field is typed and described, dates and amounts
say their format and unit, nullable fields say what null means, and nothing the verifier grades is free
text (only Enums, a bool and an inventory id)."""

import dataclasses
import typing
from enum import Enum

import contract
from contract import (
    TASKS,
    TOOLS,
    AuditCaseOutput,
    BagAllowance,
    Cabin,
    ChosenBooking,
    ItineraryOption,
    SfcOutput,
    SfcPreauth,
    SfcValidSetOutput,
    TripRequestOutput,
)

CONTRACT_CLASSES = [
    value
    for value in vars(contract).values()
    if isinstance(value, type) and dataclasses.is_dataclass(value) and value.__module__ == contract.__name__
]


def annotated_fields(cls):
    """(name, type, description) for every field, from the class's Annotated hints."""
    hints = typing.get_type_hints(cls, include_extras=True)
    for field in dataclasses.fields(cls):
        hint = hints[field.name]
        assert typing.get_origin(hint) is typing.Annotated, f"{cls.__name__}.{field.name} is not Annotated"
        base, *metadata = typing.get_args(hint)
        yield field.name, base, metadata[0]


def test_every_field_is_annotated_with_a_description() -> None:
    assert len(CONTRACT_CLASSES) >= 12
    for cls in CONTRACT_CLASSES:
        for name, _, description in annotated_fields(cls):
            assert isinstance(description, str) and len(description.split()) >= 3, f"{cls.__name__}.{name}"


def test_every_task_input_is_a_single_scenario_enum() -> None:
    for given, _ in TASKS.values():
        fields = list(annotated_fields(given))
        assert len(fields) == 1 and fields[0][0] == "scenario" and issubclass(fields[0][1], Enum)
    assert all(made is SfcOutput for _, made in TASKS.values())
    assert {tool.value for tool in TOOLS} == {"get_audit_case", "get_trip_request", "search_itineraries", "compute_audit", "compute_valid_set"}


def test_every_policy_fact_reaches_the_agent_in_a_typed_field() -> None:
    audit = {name: base for name, base, _ in annotated_fields(AuditCaseOutput)}
    trip = {name: base for name, base, _ in annotated_fields(TripRequestOutput)}
    chosen = {name: base for name, base, _ in annotated_fields(ChosenBooking)}
    option = {name: base for name, base, _ in annotated_fields(ItineraryOption)}
    airport = {name: base for name, base, _ in annotated_fields(contract.Airport)}
    assert audit["booking_date"] is str and audit["departure_date"] is str  # YYYY-MM-DD, stated in the descriptions
    assert audit["checked_bags_requested"] is int and trip["checked_bags_requested"] is int
    assert audit["same_day_itineraries"] == list[ItineraryOption] and audit["chosen"] is ChosenBooking
    assert chosen["cabin"] is Cabin and chosen["fare_cents"] is int
    assert option["connections"] is int and option["fares_cents"] == dict[Cabin, int | None]
    assert trip["requested_cabin"] is Cabin
    assert airport["us_50_states_dc"] is bool


def test_the_graded_output_has_no_free_text() -> None:
    fields = {name: base for name, base, _ in annotated_fields(SfcOutput)}
    assert fields == {
        "in_policy": bool,
        "required_preauthorizations": list[SfcPreauth],
        "itinerary_id": str | None,  # an inventory id, checked against the fixtures
        "reimbursable_checked_bags": BagAllowance,
    }
    assert [member.value for member in BagAllowance] == ["zero", "one"]
    assert len(SfcPreauth) == 7
    key = {name: base for name, base, _ in annotated_fields(SfcValidSetOutput)}
    assert key["valid_itinerary_ids"] == list[str] and key["lowest_logical_fare_cents"] is int
    assert key["rejected"] == dict[str, list[SfcPreauth]]


def test_dates_and_stamps_say_their_format_and_amounts_their_unit() -> None:
    for cls in CONTRACT_CLASSES:
        for name, base, description in annotated_fields(cls):
            if name.endswith(("_date", "_local", "_utc")):
                assert "YYYY-MM-DD" in description, f"{cls.__name__}.{name}"
            if name.endswith("_cents"):
                assert "cents" in description, f"{cls.__name__}.{name}"
            if typing.get_origin(base) in (typing.Union, type(int | None)) and type(None) in typing.get_args(base):
                assert "null" in description, f"{cls.__name__}.{name} does not say what null means"
            if typing.get_origin(base) is list:
                assert any(word in description for word in ("order", "sorted", "by itinerary_id", "flying")), (
                    f"{cls.__name__}.{name} does not say its ordering"
                )
            inner = typing.get_args(base)[1] if typing.get_origin(base) is dict else base
            if typing.get_origin(inner) in (typing.Union, type(int | None)) and type(None) in typing.get_args(inner):
                assert "null" in description, f"{cls.__name__}.{name} does not say what null means"
