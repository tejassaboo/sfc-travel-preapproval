"""The oracle's rules at every threshold, exactly at the limit and one unit past it, plus the lowest
logical fare, the bag allowance, the code order, and the brief's section 11 cross-policy row for SFC,
on small synthetic worlds."""

import pytest

from contract import BagAllowance, SfcPreauth
from plugin.rules import PREAUTHS, bag_allowance, lowest_logical_fare, preauthorizations, valid_set
from plugin.tools_dev.worldgen import itinerary, segment

AIRPORTS = {
    "JFK": {"code": "JFK", "us_50_states_dc": True, "timezone": "America/New_York"},
    "ORD": {"code": "ORD", "us_50_states_dc": True, "timezone": "America/Chicago"},
    "DEN": {"code": "DEN", "us_50_states_dc": True, "timezone": "America/Denver"},
    "HNL": {"code": "HNL", "us_50_states_dc": True, "timezone": "Pacific/Honolulu"},
    "SJU": {"code": "SJU", "us_50_states_dc": False, "timezone": "America/Puerto_Rico"},
    "NRT": {"code": "NRT", "us_50_states_dc": False, "timezone": "Asia/Tokyo"},
}


def world_of(*specs):
    """A world with the given itineraries: each (id, [(origin, destination, depart_local, minutes)], fares)."""
    segments, itineraries = {}, {}
    for itinerary_id, flights, fare_table in specs:
        records = []
        for origin, destination, depart, minutes in flights:
            record = segment(AIRPORTS, f"S{len(segments) + 1}", f"XX {len(segments) + 1}", "XX", "XX", origin, destination, depart, minutes)
            segments[record["segment_id"]] = record
            records.append(record)
        itineraries[itinerary_id] = itinerary(itinerary_id, records, fare_table)
    return {"airports": AIRPORTS, "carriers": {}, "segments": segments, "itineraries": itineraries, "travelers": {}}


def fares(economy, premium=None, business=None):
    return {"economy": economy, "premium_economy": premium, "business": business, "first": None}


NONSTOP = [("JFK", "DEN", "2026-12-09T08:00", 270)]
ONE_STOP = [("JFK", "ORD", "2026-12-09T06:00", 150), ("ORD", "DEN", "2026-12-09T09:30", 150)]
TWO_STOP = [("JFK", "ORD", "2026-12-09T05:00", 150), ("ORD", "HNL", "2026-12-09T08:00", 540), ("HNL", "DEN", "2026-12-09T20:00", 420)]


def scenario(**facts):
    base = {"scenario": "synthetic", "booking_date": "2026-11-02", "origin": "JFK", "destination": "DEN", "departure_date": "2026-12-09"}
    return {**base, **facts}


def codes(world, facts, itinerary_id="A", cabin="economy"):
    return preauthorizations(world, facts, world["itineraries"][itinerary_id], cabin)


def test_codes_follow_the_contract_order() -> None:
    assert PREAUTHS == tuple(member.value for member in SfcPreauth)
    assert {bag_allowance(0), bag_allowance(1)} == {member.value for member in BagAllowance}


@pytest.mark.parametrize(("fare", "expected"), [(75000, []), (75001, ["COST_OVER_DOMESTIC_750"])])
def test_domestic_cap_750_00_vs_750_01(fare: int, expected: list) -> None:
    world = world_of(("A", NONSTOP, fares(fare)), ("B", ONE_STOP, fares(fare - 100)))
    assert codes(world, scenario()) == expected


@pytest.mark.parametrize(("fare", "expected"), [(150000, []), (150001, ["COST_OVER_INTL_1500"])])
def test_international_cap_1500_00_vs_1500_01(fare: int, expected: list) -> None:
    world = world_of(("A", [("JFK", "NRT", "2026-12-09T12:00", 840)], fares(fare)))
    assert codes(world, scenario(destination="NRT")) == expected


@pytest.mark.parametrize(
    ("destination", "fare", "expected"),
    [("HNL", 80000, ["COST_OVER_DOMESTIC_750"]), ("SJU", 80000, []), ("SJU", 150001, ["COST_OVER_INTL_1500"])],
)
def test_domestic_means_both_ends_in_the_50_states_and_dc(destination: str, fare: int, expected: list) -> None:
    world = world_of(("A", [("JFK", destination, "2026-12-09T09:00", 600)], fares(fare)))
    assert codes(world, scenario(destination=destination)) == expected


@pytest.mark.parametrize(
    ("departure", "expected"),
    [
        ("2026-11-15", ["BOOKED_LT_14_DAYS"]),  # 13 days
        ("2026-11-16", []),  # 14 days
        ("2027-11-02", []),  # 365 days
        ("2027-11-03", ["BOOKED_GT_365_DAYS"]),  # 366 days
    ],
)
def test_advance_purchase_13_14_365_366_days(departure: str, expected: list) -> None:
    flights = [("JFK", "DEN", f"{departure}T08:00", 270)]
    world = world_of(("A", flights, fares(30000)))
    assert codes(world, scenario(departure_date=departure)) == expected


@pytest.mark.parametrize(("fare", "expected"), [(50000, []), (50001, ["ABOVE_LOW_FARE_BAND_200"])])
def test_low_fare_band_200_00_vs_200_01(fare: int, expected: list) -> None:
    world = world_of(("A", NONSTOP, fares(fare)), ("B", ONE_STOP, fares(30000)))
    assert codes(world, scenario()) == expected


def test_two_connections_never_set_the_lowest_logical_fare() -> None:
    world = world_of(("A", NONSTOP, fares(45000)), ("B", ONE_STOP, fares(40000)), ("C", TWO_STOP, fares(10000)))
    assert lowest_logical_fare(world, scenario()) == 40000
    assert codes(world, scenario()) == []  # 5000 over the logical low, not 35000 over the 3-leg fare


@pytest.mark.parametrize(("flights", "expected"), [(ONE_STOP, []), (TWO_STOP, ["TWO_PLUS_CONNECTIONS"])])
def test_one_vs_two_connections(flights, expected: list) -> None:
    world = world_of(("A", flights, fares(30000)), ("B", NONSTOP, fares(30000)))
    assert codes(world, scenario()) == expected


def test_any_cabin_above_economy_needs_pre_authorization() -> None:
    world = world_of(("A", NONSTOP, fares(30000, 31000, 32000)))
    assert codes(world, scenario(), cabin="premium_economy") == ["NON_ECONOMY_CABIN"]  # inside the band, under the cap
    assert codes(world, scenario(), cabin="business") == ["NON_ECONOMY_CABIN"]


def test_several_triggers_at_once_in_code_order() -> None:
    world = world_of(("A", TWO_STOP, fares(30000, None, 200000)), ("B", NONSTOP, fares(30000)))
    found = codes(world, scenario(departure_date="2026-12-09", booking_date="2026-12-01"), cabin="business")
    assert found == ["COST_OVER_DOMESTIC_750", "BOOKED_LT_14_DAYS", "ABOVE_LOW_FARE_BAND_200", "NON_ECONOMY_CABIN", "TWO_PLUS_CONNECTIONS"]


@pytest.mark.parametrize(("requested", "allowance"), [(0, "zero"), (1, "one"), (2, "one"), (3, "one")])
def test_one_checked_bag_at_most(requested: int, allowance: str) -> None:
    assert bag_allowance(requested) == allowance


def test_valid_set_holds_every_equally_valid_itinerary() -> None:
    world = world_of(("A", NONSTOP, fares(30000)), ("B", ONE_STOP, fares(50000)), ("C", TWO_STOP, fares(20000)))
    key = valid_set(world, scenario(checked_bags=2))
    assert key["valid_itinerary_ids"] == ["A", "B"] and key["rejected"] == {"C": ["TWO_PLUS_CONNECTIONS"]}


def test_no_logical_fare_is_an_error_not_a_guess() -> None:
    with pytest.raises(ValueError, match="lowest logical fare"):
        lowest_logical_fare(world_of(("C", TWO_STOP, fares(20000))), scenario())


def test_cross_policy_sanity_row_sfc() -> None:
    # Brief section 11: leg 1 = 360 in air, layover 90, leg 2 = 420 in air (elapsed 870), international:
    # under SFC only economy is in policy, however long the trip.
    flights = [("JFK", "ORD", "2026-12-09T08:00", 360), ("ORD", "NRT", "2026-12-09T14:30", 420)]
    world = world_of(("A", flights, fares(120000, 200000, 400000)))
    record = world["itineraries"]["A"]
    assert (record["layover_minutes"], record["total_elapsed_minutes"], record["total_in_air_minutes"]) == ([90], 870, 780)
    facts = scenario(destination="NRT", checked_bags=1)
    in_policy = [cabin for cabin in ("economy", "premium_economy", "business") if "NON_ECONOMY_CABIN" not in codes(world, facts, cabin=cabin)]
    assert in_policy == ["economy"]
    assert valid_set(world, facts)["valid_itinerary_ids"] == ["A"]
