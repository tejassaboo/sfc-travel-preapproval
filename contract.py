"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    GET_AUDIT_CASE = "get_audit_case"
    GET_TRIP_REQUEST = "get_trip_request"
    SEARCH_ITINERARIES = "search_itineraries"
    COMPUTE_AUDIT = "compute_audit"
    COMPUTE_VALID_SET = "compute_valid_set"


class Task(Enum):
    SFC_AUDIT = "sfc-audit"
    SFC_BOOK = "sfc-book"


class AuditScenario(Enum):
    """One booking to audit per member; its facts are bundled with the plugin."""

    PORTLAND_DOCS_SPRINT = "portland-docs-sprint"
    DENVER_BOARD_RETREAT = "denver-board-retreat"
    BERLIN_KEYNOTE = "berlin-keynote"
    LISBON_COMMUNITY_SUMMIT = "lisbon-community-summit"
    CHICAGO_FOUNDATION_BRIEFING = "chicago-foundation-briefing"
    AUSTIN_HACKFEST = "austin-hackfest"
    TOKYO_STANDARDS_MEETING = "tokyo-standards-meeting"
    RALEIGH_MAINTAINERS_MEETUP = "raleigh-maintainers-meetup"
    MONTREAL_ACCESSIBILITY_KEYNOTE = "montreal-accessibility-keynote"
    GENEVA_LICENSING_HEARING = "geneva-licensing-hearing"
    HONOLULU_SECURITY_WORKSHOP = "honolulu-security-workshop"
    SAN_JUAN_OUTREACH = "san-juan-outreach"


class BookScenario(Enum):
    """One trip to book per member; its facts are bundled with the plugin."""

    BOSTON_MENTOR_SUMMIT = "boston-mentor-summit"
    PARIS_FIRMWARE_WORKSHOP = "paris-firmware-workshop"
    ATHENS_TRANSLATION_SPRINT = "athens-translation-sprint"
    SEATTLE_RELEASE_PARTY = "seattle-release-party"


class Cabin(Enum):
    """The cabin ladder, lowest first."""

    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


class SfcPreauth(Enum):
    """Each written pre-authorization a booking can need, in the handbook's order (C3-C7)."""

    COST_OVER_DOMESTIC_750 = "COST_OVER_DOMESTIC_750"
    COST_OVER_INTL_1500 = "COST_OVER_INTL_1500"
    BOOKED_LT_14_DAYS = "BOOKED_LT_14_DAYS"
    BOOKED_GT_365_DAYS = "BOOKED_GT_365_DAYS"
    ABOVE_LOW_FARE_BAND_200 = "ABOVE_LOW_FARE_BAND_200"
    NON_ECONOMY_CABIN = "NON_ECONOMY_CABIN"
    TWO_PLUS_CONNECTIONS = "TWO_PLUS_CONNECTIONS"


class BagAllowance(Enum):
    """Checked bags the organization pays for: never more than one."""

    ZERO = "zero"
    ONE = "one"


@dataclass
class AuditInput(Output):
    scenario: Annotated[AuditScenario, "Which booking to audit, e.g. denver-board-retreat"]


@dataclass
class BookInput(Output):
    scenario: Annotated[BookScenario, "Which trip to book, e.g. boston-mentor-summit"]


@dataclass
class Traveler(Output):
    traveler_id: Annotated[str, "Traveler id, e.g. P204"]
    name: Annotated[str, "The traveler's full name (flavour only)"]
    department: Annotated[str, "Role and (fictional) member project (flavour only)"]
    base_point: Annotated[str, "Home city and state or country (flavour only)"]


@dataclass
class Airport(Output):
    code: Annotated[str, "Three-letter IATA airport code, e.g. SJU"]
    city: Annotated[str, "The city the airport serves (flavour only)"]
    country: Annotated[str, "ISO 3166-1 alpha-2 country code, e.g. US or PR; C2 reads us_50_states_dc, not this"]
    us_50_states_dc: Annotated[bool, "In one of the 50 US states or DC (Puerto Rico and Canada are not); C2 reads this"]


@dataclass
class ItineraryOption(Output):
    itinerary_id: Annotated[str, "Itinerary id, e.g. I457"]
    route: Annotated[list[str], "Airports in flying order, origin first"]
    flights: Annotated[list[str], "Flight numbers in flying order"]
    depart_local: Annotated[str, "First departure, origin local YYYY-MM-DDTHH:MM"]
    arrive_local: Annotated[str, "Final arrival, destination local YYYY-MM-DDTHH:MM"]
    connections: Annotated[int, "Number of connections (flights minus one)"]
    fares_cents: Annotated[dict[Cabin, int | None], "Ticket price per cabin in USD cents; null when not sold"]


@dataclass
class ChosenBooking(Output):
    itinerary_id: Annotated[str, "The booked itinerary"]
    cabin: Annotated[Cabin, "The booked cabin"]
    fare_cents: Annotated[int, "Its fare in that cabin, USD cents"]


@dataclass
class AuditCaseOutput(Output):
    scenario: Annotated[AuditScenario, "The scenario this case belongs to"]
    request_text: Annotated[str, "The traveler's words; they may claim things that are not so"]
    booking_date: Annotated[str, "The day the ticket is bought, YYYY-MM-DD"]
    departure_date: Annotated[str, "Outbound departure date, YYYY-MM-DD, origin local"]
    traveler: Annotated[Traveler, "The traveler (flavour only)"]
    origin: Annotated[Airport, "Where the trip starts"]
    destination: Annotated[Airport, "Where the trip goes"]
    chosen: Annotated[ChosenBooking, "The booking under audit"]
    checked_bags_requested: Annotated[int, "Checked bags the traveler is taking"]
    same_day_itineraries: Annotated[
        list[ItineraryOption], "Every itinerary from origin to destination on departure_date, by itinerary_id"
    ]


@dataclass
class TripRequestOutput(Output):
    scenario: Annotated[BookScenario, "The scenario this request belongs to"]
    request_text: Annotated[str, "The traveler's words; they may ask for things policy forbids"]
    booking_date: Annotated[str, "The day the ticket is bought, YYYY-MM-DD"]
    departure_date: Annotated[str, "Outbound departure date, YYYY-MM-DD, origin local"]
    traveler: Annotated[Traveler, "The traveler (flavour only)"]
    origin: Annotated[Airport, "Where the trip starts"]
    destination: Annotated[Airport, "Where the trip goes"]
    requested_cabin: Annotated[Cabin, "Cabin the traveler asked for"]
    checked_bags_requested: Annotated[int, "Checked bags the traveler is taking"]


@dataclass
class SearchInput(Output):
    origin: Annotated[str, "IATA code to depart from"]
    destination: Annotated[str, "IATA code to arrive at"]
    date: Annotated[str, "Departure date, YYYY-MM-DD, origin local"]


@dataclass
class SearchOutput(Output):
    itineraries: Annotated[list[ItineraryOption], "Every itinerary from origin to destination on date, by itinerary_id"]


@dataclass
class SfcOutput(Output):
    """One output class for both tasks."""

    in_policy: Annotated[bool, "True exactly when required_preauthorizations is empty"]
    required_preauthorizations: Annotated[
        list[SfcPreauth], "Every written pre-authorization the booking needs, each once, any order; empty if none"
    ]
    itinerary_id: Annotated[str | None, "sfc-book: the booked itinerary; sfc-audit: null"]
    reimbursable_checked_bags: Annotated[BagAllowance, "zero when no bag is checked, else one"]


@dataclass
class SfcValidSetOutput(Output):
    """The sfc-book answer key: every itinerary a correct answer may book."""

    valid_itinerary_ids: Annotated[list[str], "Every in-policy itinerary, sorted"]
    lowest_logical_fare_cents: Annotated[int, "Lowest economy fare among same-day itineraries with at most 1 connection, USD cents"]
    reimbursable_checked_bags: Annotated[BagAllowance, "zero when no bag is checked, else one"]
    rejected: Annotated[
        dict[str, list[SfcPreauth]], "Each other same-day itinerary, by itinerary_id, and the codes its economy fare needs, in C3-C7 order"
    ]


TOOLS = {
    Tool.GET_AUDIT_CASE: (AuditInput, AuditCaseOutput),
    Tool.GET_TRIP_REQUEST: (BookInput, TripRequestOutput),
    Tool.SEARCH_ITINERARIES: (SearchInput, SearchOutput),
    Tool.COMPUTE_AUDIT: (AuditInput, SfcOutput),
    Tool.COMPUTE_VALID_SET: (BookInput, SfcValidSetOutput),
}
TASKS = {
    Task.SFC_AUDIT: (AuditInput, SfcOutput),
    Task.SFC_BOOK: (BookInput, SfcOutput),
}
