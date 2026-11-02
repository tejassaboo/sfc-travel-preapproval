"""Why a pre-authorization applies or not to one booking, in words with the numbers (verdict messages)."""

from .rules import (
    DOMESTIC_CAP,
    INTERNATIONAL_CAP,
    LOW_FARE_BAND,
    MAX_ADVANCE_DAYS,
    MAX_LOGICAL_CONNECTIONS,
    MIN_ADVANCE_DAYS,
    advance_days,
    is_domestic,
    lowest_logical_fare,
)


def dollars(cents):
    return f"${cents // 100:,}.{cents % 100:02d}"


def region(world, scenario):
    origin, destination = scenario["origin"], scenario["destination"]
    if is_domestic(world, scenario):
        return f"domestic: {origin} and {destination} are both in the 50 states + DC"
    outside = [code for code in (origin, destination) if not world["airports"][code]["us_50_states_dc"]]
    return f"international: {' and '.join(outside)} is outside the 50 states + DC"


def why(world, scenario, itinerary, cabin, code):
    """The fact that decides ``code`` for booking ``itinerary`` in ``cabin``."""
    fare = itinerary["fares_cents"][cabin]
    days = advance_days(scenario)
    if code in ("COST_OVER_DOMESTIC_750", "COST_OVER_INTL_1500"):
        domestic = is_domestic(world, scenario)
        if domestic != (code == "COST_OVER_DOMESTIC_750"):
            return f"the trip is {region(world, scenario)}, so {code} never applies"
        cap = DOMESTIC_CAP if domestic else INTERNATIONAL_CAP
        side = ">" if fare > cap else "is not >"
        return f"{cabin} fare {fare} cents ({dollars(fare)}) {side} the {dollars(cap)} cap; the trip is {region(world, scenario)}"
    if code == "BOOKED_LT_14_DAYS":
        side = "<" if days < MIN_ADVANCE_DAYS else "is not <"
        return f"departure is {days} days after booking, which {side} {MIN_ADVANCE_DAYS}"
    if code == "BOOKED_GT_365_DAYS":
        side = ">" if days > MAX_ADVANCE_DAYS else "is not >"
        return f"departure is {days} days after booking, which {side} {MAX_ADVANCE_DAYS}"
    if code == "ABOVE_LOW_FARE_BAND_200":
        lowest = lowest_logical_fare(world, scenario)
        gap = fare - lowest
        side = ">" if gap > LOW_FARE_BAND else "is not >"
        return (
            f"{cabin} fare {fare} - lowest logical fare {lowest} (economy, at most {MAX_LOGICAL_CONNECTIONS} connection) "
            f"= {gap} cents, which {side} {LOW_FARE_BAND}"
        )
    if code == "NON_ECONOMY_CABIN":
        return f"the booked cabin is {cabin}" + ("" if cabin != "economy" else ", which is economy")
    if code == "TWO_PLUS_CONNECTIONS":
        count = itinerary["connections"]
        side = ">" if count > MAX_LOGICAL_CONNECTIONS else "is not >"
        return f"itinerary {itinerary['itinerary_id']} has {count} connection(s), which {side} {MAX_LOGICAL_CONNECTIONS}"
    raise ValueError(f"unknown pre-authorization {code!r}")


def set_problem(world, scenario, itinerary, cabin, wanted, given):
    """None when ``given`` names exactly ``wanted``; else (expected, actual, message) explaining each difference."""
    missing = [code for code in wanted if code not in given]
    extra = sorted(code for code in set(given) if code not in wanted)
    if not missing and not extra:
        return None
    parts = [f"missing {code} ({why(world, scenario, itinerary, cabin, code)})" for code in missing]
    parts += [f"not required {code} ({why(world, scenario, itinerary, cabin, code)})" for code in extra]
    return list(wanted), sorted(given), "; ".join(parts)
