"""The seeded generator of this plugin's fixtures (development only): `uv run python -m plugin.tools_dev.generate`
rewrites src/plugin/data/ (except handbook.md). The committed files are the source of truth; a test checks
this generator still reproduces them byte for byte.

Each scenario's flights are written out by hand, because each one sits on a boundary of the brief
(TRAVEL_POLICY_TASKS_CONTEXT.md section 4, T4); the seed only scatters the itinerary ids, so an answer is
never simply the first or lowest id. Carriers, travelers and member projects are fictional, and so are all
fares. Expected answers are not written here: they live in tests/cases/.

Itinerary ids come from one seeded stream of distinct numbers, drawn in a fixed order: first every
scenario's original options (the 0.1.0 inventory, in scenario order), then the options added in 0.2.0
(each scenario's third list). So growing the inventory never renames an itinerary that a case already cites.
"""

import random
from pathlib import Path

from plugin.tools_dev.worldgen import itinerary, json_text, segment

SEED = 20120327  # the pinned policy commit's date
DATA = Path(__file__).resolve().parents[1] / "data"

AIRPORTS = [
    # code, city, country, continental US, US 50 states + DC, IANA timezone
    ("AMS", "Amsterdam", "NL", False, False, "Europe/Amsterdam"),
    ("ANC", "Anchorage", "US", False, True, "America/Anchorage"),
    ("ATH", "Athens", "GR", False, False, "Europe/Athens"),
    ("ATL", "Atlanta", "US", True, True, "America/New_York"),
    ("AUS", "Austin", "US", True, True, "America/Chicago"),
    ("BER", "Berlin", "DE", False, False, "Europe/Berlin"),
    ("BOS", "Boston", "US", True, True, "America/New_York"),
    ("CDG", "Paris Charles de Gaulle", "FR", False, False, "Europe/Paris"),
    ("CLT", "Charlotte", "US", True, True, "America/New_York"),
    ("DEN", "Denver", "US", True, True, "America/Denver"),
    ("DUB", "Dublin", "IE", False, False, "Europe/Dublin"),
    ("EWR", "Newark", "US", True, True, "America/New_York"),
    ("FRA", "Frankfurt", "DE", False, False, "Europe/Berlin"),
    ("GVA", "Geneva", "CH", False, False, "Europe/Zurich"),
    ("HND", "Tokyo Haneda", "JP", False, False, "Asia/Tokyo"),
    ("HNL", "Honolulu", "US", False, True, "Pacific/Honolulu"),
    ("IAD", "Washington Dulles", "US", True, True, "America/New_York"),
    ("JFK", "New York JFK", "US", True, True, "America/New_York"),
    ("LAX", "Los Angeles", "US", True, True, "America/Los_Angeles"),
    ("LHR", "London Heathrow", "GB", False, False, "Europe/London"),
    ("LIS", "Lisbon", "PT", False, False, "Europe/Lisbon"),
    ("MIA", "Miami", "US", True, True, "America/New_York"),
    ("MSP", "Minneapolis", "US", True, True, "America/Chicago"),
    ("ORD", "Chicago O'Hare", "US", True, True, "America/Chicago"),
    ("PDX", "Portland", "US", True, True, "America/Los_Angeles"),
    ("PHX", "Phoenix", "US", True, True, "America/Phoenix"),
    ("PSE", "Ponce", "PR", False, False, "America/Puerto_Rico"),
    ("RDU", "Raleigh-Durham", "US", True, True, "America/New_York"),
    ("SEA", "Seattle", "US", True, True, "America/Los_Angeles"),
    ("SFO", "San Francisco", "US", True, True, "America/Los_Angeles"),
    ("SJU", "San Juan", "PR", False, False, "America/Puerto_Rico"),
    ("SLC", "Salt Lake City", "US", True, True, "America/Denver"),
    ("YUL", "Montreal", "CA", False, False, "America/Toronto"),
    ("ZRH", "Zurich", "CH", False, False, "Europe/Zurich"),
]

CARRIERS = [
    # code, fictional name, US flag carrier, carriers whose flight numbers it operates as a code-share
    ("AU", "Aurora Nordic", False, []),
    ("BL", "Boreal Canada", False, []),
    ("CQ", "Cascadia Air", True, []),
    ("HB", "Harborline", True, []),
    ("LK", "Lakeshore Express", True, []),
    ("MX", "Meridian Atlantic", False, []),
    ("NS", "Northstar Airways", True, []),
    ("PC", "Pacific Crest", False, []),
    ("SI", "Sol Iberica", False, []),
]

TRAVELERS = [
    # id, name, role and fictional member project, home city
    ("P201", "Wren Takahashi", "Documentation lead, Larkspur Docs", "Boston, MA"),
    ("P202", "Dmitri Albescu", "Board secretary, Quillwork Foundation", "New York, NY"),
    ("P203", "Priya Natarajan", "Core maintainer, Ferrolith compiler", "San Francisco, CA"),
    ("P204", "Tomasz Wierzbicki", "Community manager, Kestrel Linux", "Chicago, IL"),
    ("P205", "Amara Osei", "Treasurer, Oakmoss Project", "Austin, TX"),
    ("P206", "Lucas Ferreira", "Release engineer, Tidepool CI", "Seattle, WA"),
    ("P207", "Hana Kowalczyk", "Standards liaison, Glimmer Unicode tools", "Los Angeles, CA"),
    ("P208", "Jonah Whitfield", "Volunteer maintainer, Burrow package index", "Minneapolis, MN"),
    ("P209", "Selin Aydin", "Accessibility lead, Lanternfish desktop", "Boston, MA"),
    ("P210", "Ruth Abernathy", "Licensing counsel volunteer, Quillwork Foundation", "Washington, DC"),
    ("P211", "Kai Mahoe", "Security response lead, Ironbark crypto library", "San Francisco, CA"),
    ("P212", "Marisol Vega", "Outreach coordinator, Tinderbox education", "Chicago, IL"),
    ("P213", "Odette Lindqvist", "Mentor coordinator, Kestrel Linux", "Denver, CO"),
    ("P214", "Bashir Haddad", "Firmware maintainer, Copperleaf bootloader", "New York, NY"),
    ("P215", "Eleni Papadakis", "Translation lead, Larkspur Docs", "Boston, MA"),
    ("P216", "Gideon Mbeki", "Release manager, Tidepool CI", "Atlanta, GA"),
    ("P217", "Ingrid Solberg", "Infrastructure volunteer, Burrow package index", "Boston, MA"),
    ("P218", "Niamh Byrne", "Packaging lead, Kestrel Linux", "Chicago, IL"),
    ("P219", "Marcus Oyelaran", "Kernel maintainer, Ferrolith compiler", "Chicago, IL"),
    ("P220", "Carmen Alvarado", "Archivist, Tinderbox education", "Atlanta, GA"),
]


def fares(economy, premium_economy, business, first=None):
    return {"economy": economy, "premium_economy": premium_economy, "business": business, "first": first}


def audit(facts, itineraries, more=()):
    return {"facts": {**facts, "task": "sfc-audit"}, "itineraries": itineraries, "more": list(more)}


def book(facts, itineraries, more=()):
    return {"facts": {**facts, "task": "sfc-book"}, "itineraries": itineraries, "more": list(more)}


# Per scenario: its facts, its original itineraries, and (third list) the itineraries added in 0.2.0, each
# (key, segments, fares), each segment (flight, marketing carrier, operating carrier, origin, destination,
# local departure, in-air minutes). An audit's chosen_itinerary_id names one of its own itineraries by key;
# build() swaps in the seeded id. Added options never undercut a scenario's lowest logical fare, so every
# original boundary story stands.
SCENARIOS = [
    audit(
        {
            "scenario": "portland-docs-sprint",
            "request_text": (
                "Booked for the Larkspur docs sprint in Portland. I took the 7:05 Harborline via O'Hare so I land "
                "before the kickoff dinner. Before anyone asks: yes, there is a $410 Northstar fare, but it stops "
                "in Denver AND Salt Lake, and I am not spending my whole day in airports. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P201",
            "origin": "BOS",
            "destination": "PDX",
            "departure_date": "2026-11-16",
            "chosen_itinerary_id": "b",
            "chosen_cabin": "economy",
            "checked_bags": 1,
        },
        [
            ("a", [("CQ 411", "CQ", "CQ", "BOS", "PDX", "2026-11-16T08:15", 385)], fares(55000, 98000, 214000)),
            (
                "b",
                [
                    ("HB 1207", "HB", "HB", "BOS", "ORD", "2026-11-16T07:05", 155),
                    ("HB 388", "HB", "HB", "ORD", "PDX", "2026-11-16T10:20", 285),
                ],
                fares(75000, 121000, 248000),
            ),
            (
                "c",
                [
                    ("NS 902", "NS", "NS", "BOS", "DEN", "2026-11-16T06:00", 270),
                    ("NS 1440", "NS", "NS", "DEN", "SLC", "2026-11-16T09:30", 75),
                    ("NS 615", "NS", "NS", "SLC", "PDX", "2026-11-16T11:40", 105),
                ],
                fares(41000, None, 165000),
            ),
        ],
        [
            ("d", [("NS 1121", "NS", "NS", "BOS", "PDX", "2026-11-16T13:30", 390)], fares(61000, 99000, 220000)),
            (
                "e",
                [
                    ("CQ 980", "CQ", "CQ", "BOS", "DEN", "2026-11-16T09:20", 275),
                    ("CQ 1452", "CQ", "CQ", "DEN", "PDX", "2026-11-16T13:40", 160),
                ],
                fares(58500, None, 190000),
            ),
        ],
    ),
    audit(
        {
            "scenario": "denver-board-retreat",
            "request_text": (
                "Quillwork board retreat in Denver starts at 2pm on December 9, so I booked the 8:30 Northstar "
                "nonstop. It came to $750.01 with taxes, which is one cent over the line; surely nobody routes a "
                "penny for approval. Carry-on plus one checked bag for the printed board packets."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P202",
            "origin": "JFK",
            "destination": "DEN",
            "departure_date": "2026-12-09",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "economy",
            "checked_bags": 1,
        },
        [
            ("a", [("NS 233", "NS", "NS", "JFK", "DEN", "2026-12-09T08:30", 275)], fares(75001, 112000, 189000)),
            (
                "b",
                [
                    ("HB 1102", "HB", "HB", "JFK", "ORD", "2026-12-09T06:45", 165),
                    ("HB 761", "HB", "HB", "ORD", "DEN", "2026-12-09T10:05", 155),
                ],
                fares(62000, None, 171000),
            ),
            ("c", [("CQ 1890", "CQ", "CQ", "JFK", "DEN", "2026-12-09T17:10", 280)], fares(69900, 104000, 182000)),
        ],
        [
            (
                "d",
                [
                    ("LK 2240", "LK", "LK", "JFK", "MSP", "2026-12-09T07:20", 190),
                    ("LK 2611", "LK", "LK", "MSP", "DEN", "2026-12-09T11:15", 135),
                ],
                fares(66000, None, 158000),
            ),
            (
                "e",
                [
                    ("LK 2008", "LK", "LK", "JFK", "CLT", "2026-12-09T06:00", 125),
                    ("LK 2777", "LK", "LK", "CLT", "ORD", "2026-12-09T09:30", 135),
                    ("LK 2902", "LK", "LK", "ORD", "DEN", "2026-12-09T12:30", 160),
                ],
                fares(48000, None, 150000),
            ),
        ],
    ),
    audit(
        {
            "scenario": "berlin-keynote",
            "request_text": (
                "I'm giving the opening keynote at the Ferrolith compiler conference in Berlin next November and "
                "booked today, exactly a year out, to lock in the fare: economy via Frankfurt, $1,500.00 on the "
                "nose. Bringing two checked bags because the demo hardware travels with me."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P203",
            "origin": "SFO",
            "destination": "BER",
            "departure_date": "2027-11-02",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "economy",
            "checked_bags": 2,
        },
        [
            (
                "a",
                [
                    ("HB 58", "HB", "HB", "SFO", "FRA", "2027-11-02T15:40", 650),
                    ("MX 1716", "MX", "MX", "FRA", "BER", "2027-11-03T12:15", 70),
                ],
                fares(150000, 255000, 610000),
            ),
            (
                "b",
                [
                    ("MX 286", "MX", "MX", "SFO", "LHR", "2027-11-02T16:20", 620),
                    ("MX 992", "MX", "MX", "LHR", "BER", "2027-11-03T12:10", 115),
                ],
                fares(132500, 240000, 585000),
            ),
            ("c", [("AU 471", "AU", "AU", "SFO", "BER", "2027-11-02T13:30", 655)], fares(158000, 262000, 640000)),
        ],
        [
            (
                "d",
                [
                    ("AU 115", "AU", "AU", "SFO", "AMS", "2027-11-02T14:10", 640),
                    ("AU 1206", "AU", "AU", "AMS", "BER", "2027-11-03T10:30", 75),
                ],
                fares(139000, 244000, 590000),
            ),
            (
                "e",
                [
                    ("HB 24", "HB", "HB", "SFO", "JFK", "2027-11-02T08:00", 330),
                    ("MX 100", "MX", "MX", "JFK", "LHR", "2027-11-02T18:30", 425),
                    ("MX 990", "MX", "MX", "LHR", "BER", "2027-11-03T07:40", 115),
                ],
                fares(110000, None, 520000),
            ),
        ],
    ),
    audit(
        {
            "scenario": "lisbon-community-summit",
            "request_text": (
                "Kestrel Linux community summit in Lisbon. I booked Harborline to Newark connecting to Sol Iberica: "
                "$1,500.01. The one-stop via Boston was a bit cheaper but leaves at lunchtime, and there's an even "
                "cheaper two-stop through Charlotte and JFK. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P204",
            "origin": "ORD",
            "destination": "LIS",
            "departure_date": "2027-03-10",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "economy",
            "checked_bags": 1,
        },
        [
            (
                "a",
                [
                    ("HB 1530", "HB", "HB", "ORD", "EWR", "2027-03-10T08:00", 130),
                    ("SI 204", "SI", "SI", "EWR", "LIS", "2027-03-10T18:30", 400),
                ],
                fares(150001, 236000, 512000),
            ),
            (
                "b",
                [
                    ("NS 744", "NS", "NS", "ORD", "BOS", "2027-03-10T12:15", 140),
                    ("SI 236", "SI", "SI", "BOS", "LIS", "2027-03-10T18:45", 390),
                ],
                fares(141000, 229000, 498000),
            ),
            (
                "c",
                [
                    ("LK 3310", "LK", "LK", "ORD", "CLT", "2027-03-10T06:10", 115),
                    ("LK 1802", "LK", "LK", "CLT", "JFK", "2027-03-10T10:40", 110),
                    ("SI 210", "SI", "SI", "JFK", "LIS", "2027-03-10T19:55", 395),
                ],
                fares(118000, None, 455000),
            ),
        ],
        [
            ("d", [("SI 400", "SI", "SI", "ORD", "LIS", "2027-03-10T17:20", 500)], fares(162000, 250000, 540000)),
            (
                "e",
                [
                    ("NS 1024", "NS", "NS", "ORD", "JFK", "2027-03-10T11:00", 140),
                    ("SI 210", "SI", "SI", "JFK", "LIS", "2027-03-10T19:55", 395),
                ],
                fares(145500, 232000, 505000),
            ),
        ],
    ),
    audit(
        {
            "scenario": "chicago-foundation-briefing",
            "request_text": (
                "Briefing a funder in Chicago on December 3. I took the 17:30 Harborline nonstop; the 7am flight "
                "means a 4am alarm. My colleague always takes this evening flight and it's only about $200 more "
                "than the early one, so it's within the band. No checked bags, carry-on only."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P205",
            "origin": "AUS",
            "destination": "ORD",
            "departure_date": "2026-12-03",
            "chosen_itinerary_id": "b",
            "chosen_cabin": "economy",
            "checked_bags": 0,
        },
        [
            ("a", [("CQ 1622", "CQ", "CQ", "AUS", "ORD", "2026-12-03T07:00", 165)], fares(32000, None, 98000)),
            ("b", [("HB 845", "HB", "HB", "AUS", "ORD", "2026-12-03T17:30", 165)], fares(52001, None, 121000)),
            (
                "c",
                [
                    ("NS 1011", "NS", "NS", "AUS", "DEN", "2026-12-03T09:15", 140),
                    ("NS 1520", "NS", "NS", "DEN", "ORD", "2026-12-03T12:10", 145),
                ],
                fares(38800, None, 112000),
            ),
        ],
        [
            ("d", [("LK 3030", "LK", "LK", "AUS", "ORD", "2026-12-03T12:30", 160)], fares(39500, None, 105000)),
            (
                "e",
                [
                    ("CQ 2210", "CQ", "CQ", "AUS", "DEN", "2026-12-03T06:10", 140),
                    ("CQ 1388", "CQ", "CQ", "DEN", "MSP", "2026-12-03T09:00", 125),
                    ("CQ 1570", "CQ", "CQ", "MSP", "ORD", "2026-12-03T13:30", 85),
                ],
                fares(27000, None, 95000),
            ),
        ],
    ),
    audit(
        {
            "scenario": "austin-hackfest",
            "request_text": (
                "The Tidepool CI hackfest in Austin got moved up a week, so I booked the Cascadia nonstop today for "
                "the 15th. That's basically two weeks out, and the fare is tiny. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P206",
            "origin": "SEA",
            "destination": "AUS",
            "departure_date": "2026-11-15",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "economy",
            "checked_bags": 1,
        },
        [
            ("a", [("CQ 540", "CQ", "CQ", "SEA", "AUS", "2026-11-15T09:45", 245)], fares(38900, 61000, 129000)),
            (
                "b",
                [
                    ("NS 380", "NS", "NS", "SEA", "DEN", "2026-11-15T06:30", 150),
                    ("NS 1688", "NS", "NS", "DEN", "AUS", "2026-11-15T11:50", 125),
                ],
                fares(33100, None, 118000),
            ),
        ],
        [
            ("c", [("HB 2250", "HB", "HB", "SEA", "AUS", "2026-11-15T14:20", 240)], fares(45000, 66000, 135000)),
            (
                "d",
                [
                    ("NS 1702", "NS", "NS", "SEA", "SLC", "2026-11-15T07:10", 115),
                    ("NS 2244", "NS", "NS", "SLC", "AUS", "2026-11-15T11:40", 170),
                ],
                fares(36700, None, 120000),
            ),
            (
                "e",
                [
                    ("LK 4410", "LK", "LK", "SEA", "SLC", "2026-11-15T05:50", 115),
                    ("LK 4133", "LK", "LK", "SLC", "DEN", "2026-11-15T10:15", 80),
                    ("LK 4580", "LK", "LK", "DEN", "AUS", "2026-11-15T13:05", 125),
                ],
                fares(29900, None, 110000),
            ),
            ("f", [("NS 560", "NS", "NS", "SEA", "AUS", "2026-11-15T18:10", 240)], fares(41500, 62000, 128000)),
        ],
    ),
    audit(
        {
            "scenario": "tokyo-standards-meeting",
            "request_text": (
                "The Unicode tooling working group meets in Tokyo on November 4 next year. Booking way ahead always "
                "saves money, so I grabbed the Pacific Crest nonstop today. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P207",
            "origin": "LAX",
            "destination": "HND",
            "departure_date": "2027-11-03",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "economy",
            "checked_bags": 1,
        },
        [
            ("a", [("PC 7", "PC", "PC", "LAX", "HND", "2027-11-03T11:20", 705)], fares(112000, 186000, 498000)),
            (
                "b",
                [
                    ("CQ 1801", "CQ", "CQ", "LAX", "SEA", "2027-11-03T07:00", 165),
                    ("PC 15", "PC", "PC", "SEA", "HND", "2027-11-03T12:30", 640),
                ],
                fares(98000, 171000, 455000),
            ),
        ],
        [
            (
                "c",
                [
                    ("CQ 1412", "CQ", "CQ", "LAX", "SFO", "2027-11-03T08:30", 85),
                    ("PC 21", "PC", "PC", "SFO", "HND", "2027-11-03T11:45", 665),
                ],
                fares(103000, 176000, 470000),
            ),
            ("d", [("PC 9", "PC", "PC", "LAX", "HND", "2027-11-03T17:00", 700)], fares(125000, 198000, 510000)),
            (
                "e",
                [
                    ("CQ 1801", "CQ", "CQ", "LAX", "SEA", "2027-11-03T07:00", 165),
                    ("CQ 77", "CQ", "CQ", "SEA", "HNL", "2027-11-03T11:30", 380),
                    ("PC 403", "PC", "PC", "HNL", "HND", "2027-11-03T16:30", 530),
                ],
                fares(88000, None, 410000),
            ),
        ],
    ),
    audit(
        {
            "scenario": "raleigh-maintainers-meetup",
            "request_text": (
                "Burrow maintainers meetup in Raleigh. I'm a volunteer and wanted to save the project money, so I "
                "booked the cheapest fare on the board: Lakeshore Express through O'Hare and Charlotte, $219. "
                "Cheapest possible has to be in policy, right? One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P208",
            "origin": "MSP",
            "destination": "RDU",
            "departure_date": "2026-12-07",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "economy",
            "checked_bags": 1,
        },
        [
            (
                "a",
                [
                    ("LK 2101", "LK", "LK", "MSP", "ORD", "2026-12-07T06:00", 85),
                    ("LK 2384", "LK", "LK", "ORD", "CLT", "2026-12-07T08:40", 120),
                    ("LK 2950", "LK", "LK", "CLT", "RDU", "2026-12-07T13:05", 60),
                ],
                fares(21900, None, 88000),
            ),
            (
                "b",
                [
                    ("NS 1290", "NS", "NS", "MSP", "ATL", "2026-12-07T07:30", 155),
                    ("NS 2215", "NS", "NS", "ATL", "RDU", "2026-12-07T12:20", 75),
                ],
                fares(28400, None, 96000),
            ),
            ("c", [("HB 677", "HB", "HB", "MSP", "RDU", "2026-12-07T10:10", 150)], fares(35600, None, 104000)),
        ],
        [
            ("d", [("CQ 1766", "CQ", "CQ", "MSP", "RDU", "2026-12-07T15:40", 150)], fares(38000, None, 110000)),
            (
                "e",
                [
                    ("HB 1511", "HB", "HB", "MSP", "ORD", "2026-12-07T09:00", 85),
                    ("HB 1690", "HB", "HB", "ORD", "RDU", "2026-12-07T12:00", 115),
                ],
                fares(30200, None, 99000),
            ),
        ],
    ),
    audit(
        {
            "scenario": "montreal-accessibility-keynote",
            "request_text": (
                "Keynote on accessible desktops in Montreal. I booked premium economy on the Boreal nonstop: it's "
                "only $150 more than the cheapest economy seat, comfortably inside the $200 band, and the fare is "
                "nowhere near any cap. Add the lounge pass if you can. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P209",
            "origin": "BOS",
            "destination": "YUL",
            "departure_date": "2026-12-14",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "premium_economy",
            "checked_bags": 1,
        },
        [
            ("a", [("BL 615", "BL", "BL", "BOS", "YUL", "2026-12-14T09:00", 80)], fares(33000, 48000, 91000)),
            (
                "b",
                [
                    ("HB 1340", "HB", "HB", "BOS", "JFK", "2026-12-14T07:00", 75),
                    ("BL 803", "BL", "BL", "JFK", "YUL", "2026-12-14T10:30", 95),
                ],
                fares(36500, 52000, 99000),
            ),
        ],
        [
            ("c", [("HB 1360", "HB", "HB", "BOS", "YUL", "2026-12-14T13:15", 85)], fares(35500, 50000, 94000)),
            (
                "d",
                [
                    ("LK 1222", "LK", "LK", "BOS", "EWR", "2026-12-14T06:30", 80),
                    ("BL 821", "BL", "BL", "EWR", "YUL", "2026-12-14T09:40", 95),
                ],
                fares(34900, 49500, 96000),
            ),
            ("e", [("BL 619", "BL", "BL", "BOS", "YUL", "2026-12-14T17:30", 80)], fares(39000, 54000, 98000)),
        ],
    ),
    audit(
        {
            "scenario": "geneva-licensing-hearing",
            "request_text": (
                "Urgent: I'm testifying at the licensing hearing in Geneva on November 13, so I booked business via "
                "Zurich today. My colleague always flies business on this route, the lounge pass is included, and "
                "I need three checked bags for the exhibit binders. Please confirm this is all fine."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P210",
            "origin": "IAD",
            "destination": "GVA",
            "departure_date": "2026-11-12",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "business",
            "checked_bags": 3,
        },
        [
            (
                "a",
                [
                    ("HB 52", "HB", "HB", "IAD", "ZRH", "2026-11-12T17:35", 485),
                    ("AU 1660", "AU", "AU", "ZRH", "GVA", "2026-11-13T09:15", 55),
                ],
                fares(128000, 236000, 420000),
            ),
            (
                "b",
                [
                    ("MX 418", "MX", "MX", "IAD", "FRA", "2026-11-12T18:00", 470),
                    ("MX 1208", "MX", "MX", "FRA", "GVA", "2026-11-13T09:50", 75),
                ],
                fares(119500, 221000, 398000),
            ),
            (
                "c",
                [
                    ("MX 216", "MX", "MX", "IAD", "LHR", "2026-11-12T18:20", 415),
                    ("AU 330", "AU", "AU", "LHR", "AMS", "2026-11-13T08:30", 75),
                    ("AU 1934", "AU", "AU", "AMS", "GVA", "2026-11-13T11:30", 95),
                ],
                fares(99000, None, 365000),
            ),
        ],
        [
            ("d", [("MX 60", "MX", "MX", "IAD", "GVA", "2026-11-12T18:45", 490)], fares(131000, 240000, 430000)),
            (
                "e",
                [
                    ("AU 2", "AU", "AU", "IAD", "AMS", "2026-11-12T17:10", 465),
                    ("AU 1930", "AU", "AU", "AMS", "GVA", "2026-11-13T08:40", 95),
                ],
                fares(124000, 230000, 405000),
            ),
        ],
    ),
    audit(
        {
            "scenario": "honolulu-security-workshop",
            "request_text": (
                "Ironbark crypto security workshop in Honolulu. Hawaii is five hours over the ocean, so the "
                "international $1,500 limit applies and my $825 Cascadia nonstop is well under it. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P211",
            "origin": "SFO",
            "destination": "HNL",
            "departure_date": "2027-01-18",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "economy",
            "checked_bags": 1,
        },
        [
            ("a", [("CQ 1135", "CQ", "CQ", "SFO", "HNL", "2027-01-18T09:40", 330)], fares(82500, 129000, 196000)),
            ("b", [("HB 1717", "HB", "HB", "SFO", "HNL", "2027-01-18T13:15", 335)], fares(79000, 124000, 188000)),
        ],
        [
            (
                "c",
                [
                    ("CQ 1301", "CQ", "CQ", "SFO", "LAX", "2027-01-18T07:00", 85),
                    ("CQ 1133", "CQ", "CQ", "LAX", "HNL", "2027-01-18T10:10", 350),
                ],
                fares(80500, 126000, 190000),
            ),
            ("d", [("NS 1540", "NS", "NS", "SFO", "HNL", "2027-01-18T16:30", 335)], fares(91000, 138000, 205000)),
            (
                "e",
                [
                    ("HB 1409", "HB", "HB", "SFO", "SEA", "2027-01-18T06:15", 125),
                    ("HB 1721", "HB", "HB", "SEA", "HNL", "2027-01-18T10:00", 370),
                ],
                fares(84000, 131000, 198000),
            ),
        ],
    ),
    audit(
        {
            "scenario": "san-juan-outreach",
            "request_text": (
                "Tinderbox school outreach week in San Juan. Puerto Rico is part of the US, so I assume the domestic "
                "$750 rule applies and my $810 Harborline fare via Miami needs sign-off. Can you route it? One "
                "checked bag of workshop kits."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P212",
            "origin": "ORD",
            "destination": "SJU",
            "departure_date": "2027-02-08",
            "chosen_itinerary_id": "a",
            "chosen_cabin": "economy",
            "checked_bags": 1,
        },
        [
            (
                "a",
                [
                    ("HB 1912", "HB", "HB", "ORD", "MIA", "2027-02-08T06:30", 185),
                    ("HB 2471", "HB", "HB", "MIA", "SJU", "2027-02-08T12:10", 160),
                ],
                fares(81000, None, 214000),
            ),
            ("b", [("NS 1406", "NS", "NS", "ORD", "SJU", "2027-02-08T08:45", 290)], fares(77500, None, 205000)),
        ],
        [
            (
                "c",
                [
                    ("NS 1300", "NS", "NS", "ORD", "ATL", "2027-02-08T07:10", 115),
                    ("NS 2290", "NS", "NS", "ATL", "SJU", "2027-02-08T11:50", 200),
                ],
                fares(79900, None, 208000),
            ),
            (
                "d",
                [
                    ("HB 1402", "HB", "HB", "ORD", "JFK", "2027-02-08T08:00", 140),
                    ("HB 2501", "HB", "HB", "JFK", "SJU", "2027-02-08T13:10", 235),
                ],
                fares(83500, None, 218000),
            ),
            (
                "e",
                [
                    ("LK 3100", "LK", "LK", "ORD", "ATL", "2027-02-08T05:45", 115),
                    ("LK 3622", "LK", "LK", "ATL", "MIA", "2027-02-08T10:15", 115),
                    ("LK 3899", "LK", "LK", "MIA", "SJU", "2027-02-08T13:45", 165),
                ],
                fares(69000, None, 185000),
            ),
        ],
    ),
    book(
        {
            "scenario": "boston-mentor-summit",
            "request_text": (
                "Mentor summit in Boston on December 3; I fly out the 2nd. Just book whatever is cheapest, I truly "
                "don't care how many stops. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P213",
            "origin": "DEN",
            "destination": "BOS",
            "departure_date": "2026-12-02",
            "requested_cabin": "economy",
            "checked_bags": 1,
        },
        [
            ("a", [("CQ 650", "CQ", "CQ", "DEN", "BOS", "2026-12-02T07:10", 235)], fares(31000, 52000, 142000)),
            ("b", [("NS 1188", "NS", "NS", "DEN", "BOS", "2026-12-02T12:40", 230)], fares(45500, 68000, 151000)),
            (
                "c",
                [
                    ("HB 902", "HB", "HB", "DEN", "ORD", "2026-12-02T06:00", 145),
                    ("HB 1415", "HB", "HB", "ORD", "BOS", "2026-12-02T11:05", 130),
                ],
                fares(51000, None, 160000),
            ),
            (
                "d",
                [
                    ("LK 4120", "LK", "LK", "DEN", "MSP", "2026-12-02T08:20", 115),
                    ("LK 3388", "LK", "LK", "MSP", "BOS", "2026-12-02T13:00", 170),
                ],
                fares(51001, None, 158000),
            ),
            (
                "e",
                [
                    ("LK 2210", "LK", "LK", "DEN", "ORD", "2026-12-02T05:45", 145),
                    ("LK 1904", "LK", "LK", "ORD", "CLT", "2026-12-02T10:30", 120),
                    ("LK 2766", "LK", "LK", "CLT", "BOS", "2026-12-02T14:45", 130),
                ],
                fares(24500, None, 120000),
            ),
            ("f", [("CQ 650", "CQ", "CQ", "DEN", "BOS", "2026-12-01T07:10", 235)], fares(19900, 41000, 130000)),
        ],
        [
            ("g", [("HB 1660", "HB", "HB", "DEN", "BOS", "2026-12-02T16:30", 230)], fares(38500, 60000, 148000)),
            (
                "h",
                [
                    ("NS 1420", "NS", "NS", "DEN", "MSP", "2026-12-02T09:50", 115),
                    ("NS 1575", "NS", "NS", "MSP", "BOS", "2026-12-02T14:30", 170),
                ],
                fares(49900, None, 156000),
            ),
            (
                "i",
                [
                    ("CQ 1210", "CQ", "CQ", "DEN", "ORD", "2026-12-02T13:15", 145),
                    ("CQ 1490", "CQ", "CQ", "ORD", "BOS", "2026-12-02T18:20", 130),
                ],
                fares(55000, None, 162000),
            ),
        ],
    ),
    book(
        {
            "scenario": "paris-firmware-workshop",
            "request_text": (
                "Copperleaf bootloader workshop in Paris, leaving January 25. Business class please: my colleague "
                "always flies business on this route and it's an overnight flight. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P214",
            "origin": "JFK",
            "destination": "CDG",
            "departure_date": "2027-01-25",
            "requested_cabin": "business",
            "checked_bags": 1,
        },
        [
            ("a", [("MX 9", "MX", "MX", "JFK", "CDG", "2027-01-25T18:30", 435)], fares(118000, 212000, 545000)),
            ("b", [("HB 44", "HB", "HB", "JFK", "CDG", "2027-01-25T21:55", 430)], fares(136000, 228000, 560000)),
            (
                "c",
                [
                    ("NS 802", "NS", "NS", "JFK", "BOS", "2027-01-25T13:00", 75),
                    ("AU 640", "AU", "AU", "BOS", "CDG", "2027-01-25T17:20", 410),
                ],
                fares(141500, 235000, 575000),
            ),
            (
                "d",
                [
                    ("LK 2290", "LK", "LK", "JFK", "IAD", "2027-01-25T11:00", 80),
                    ("MX 422", "MX", "MX", "IAD", "LHR", "2027-01-25T18:00", 415),
                    ("MX 1104", "MX", "MX", "LHR", "CDG", "2027-01-26T08:20", 75),
                ],
                fares(97000, None, 470000),
            ),
        ],
        [
            ("e", [("AU 20", "AU", "AU", "JFK", "CDG", "2027-01-25T19:40", 430)], fares(125000, 215000, 540000)),
            (
                "f",
                [
                    ("LK 2300", "LK", "LK", "JFK", "IAD", "2027-01-25T13:30", 80),
                    ("MX 640", "MX", "MX", "IAD", "CDG", "2027-01-25T17:20", 450),
                ],
                fares(139000, 230000, 565000),
            ),
            (
                "g",
                [
                    ("NS 802", "NS", "NS", "JFK", "BOS", "2027-01-25T13:00", 75),
                    ("AU 610", "AU", "AU", "BOS", "AMS", "2027-01-25T17:50", 420),
                    ("AU 1310", "AU", "AU", "AMS", "CDG", "2027-01-26T08:30", 80),
                ],
                fares(105000, None, 490000),
            ),
            ("h", [("NS 30", "NS", "NS", "JFK", "CDG", "2027-01-25T22:40", 425)], fares(138000, 226000, 555000)),
        ],
    ),
    book(
        {
            "scenario": "athens-translation-sprint",
            "request_text": (
                "Translation sprint in Athens, departing May 12. Please book the Aurora nonstop: it's within $200 "
                "of the cheapest fare, so it's in policy, and I'd rather not connect. No checked bags."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P215",
            "origin": "BOS",
            "destination": "ATH",
            "departure_date": "2027-05-12",
            "requested_cabin": "economy",
            "checked_bags": 0,
        },
        [
            (
                "a",
                [
                    ("SI 238", "SI", "SI", "BOS", "LIS", "2027-05-12T18:30", 390),
                    ("SI 1820", "SI", "SI", "LIS", "ATH", "2027-05-13T09:10", 235),
                ],
                fares(142000, 238000, 520000),
            ),
            (
                "b",
                [
                    ("MX 290", "MX", "MX", "BOS", "LHR", "2027-05-12T19:15", 400),
                    ("MX 1440", "MX", "MX", "LHR", "ATH", "2027-05-13T09:30", 225),
                ],
                fares(149900, 246000, 535000),
            ),
            ("c", [("AU 1702", "AU", "AU", "BOS", "ATH", "2027-05-12T17:05", 600)], fares(150100, 251000, 560000)),
            (
                "d",
                [
                    ("LK 1150", "LK", "LK", "BOS", "JFK", "2027-05-12T12:00", 75),
                    ("SI 212", "SI", "SI", "JFK", "LIS", "2027-05-12T19:55", 395),
                    ("SI 1822", "SI", "SI", "LIS", "ATH", "2027-05-13T12:40", 235),
                ],
                fares(121000, None, 480000),
            ),
        ],
        [
            (
                "e",
                [
                    ("MX 320", "MX", "MX", "BOS", "FRA", "2027-05-12T17:40", 450),
                    ("MX 1620", "MX", "MX", "FRA", "ATH", "2027-05-13T09:00", 170),
                ],
                fares(148000, 244000, 530000),
            ),
            (
                "f",
                [
                    ("AU 300", "AU", "AU", "BOS", "ZRH", "2027-05-12T18:10", 440),
                    ("AU 1750", "AU", "AU", "ZRH", "ATH", "2027-05-13T09:20", 165),
                ],
                fares(162000, 255000, 545000),
            ),
            (
                "g",
                [
                    ("AU 160", "AU", "AU", "BOS", "AMS", "2027-05-12T18:40", 425),
                    ("AU 1870", "AU", "AU", "AMS", "ATH", "2027-05-13T09:40", 190),
                ],
                fares(162001, 256000, 548000),
            ),
            (
                "h",
                [
                    ("LK 1150", "LK", "LK", "BOS", "JFK", "2027-05-12T12:00", 75),
                    ("MX 110", "MX", "MX", "JFK", "FRA", "2027-05-12T17:30", 455),
                    ("MX 1624", "MX", "MX", "FRA", "ATH", "2027-05-13T10:15", 170),
                ],
                fares(128000, None, 500000),
            ),
        ],
    ),
    book(
        {
            "scenario": "seattle-release-party",
            "request_text": (
                "Tidepool 4.0 release party in Seattle on February 15. Premium economy on the Cascadia nonstop "
                "would be lovely; the nonstop is within the $200 band anyway. Two checked bags (swag boxes)."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P216",
            "origin": "ATL",
            "destination": "SEA",
            "departure_date": "2027-02-15",
            "requested_cabin": "premium_economy",
            "checked_bags": 2,
        },
        [
            (
                "a",
                [
                    ("NS 1550", "NS", "NS", "ATL", "DEN", "2027-02-15T07:15", 205),
                    ("NS 1830", "NS", "NS", "DEN", "SEA", "2027-02-15T10:10", 165),
                ],
                fares(69800, 98000, 165000),
            ),
            ("b", [("CQ 712", "CQ", "CQ", "ATL", "SEA", "2027-02-15T09:05", 330)], fares(76500, 105000, 178000)),
            (
                "c",
                [
                    ("HB 1610", "HB", "HB", "ATL", "ORD", "2027-02-15T08:00", 125),
                    ("HB 1977", "HB", "HB", "ORD", "SEA", "2027-02-15T10:40", 270),
                ],
                fares(89900, None, 190000),
            ),
            (
                "d",
                [
                    ("LK 1001", "LK", "LK", "ATL", "CLT", "2027-02-15T06:00", 75),
                    ("LK 1188", "LK", "LK", "CLT", "MSP", "2027-02-15T08:10", 165),
                    ("LK 1660", "LK", "LK", "MSP", "SEA", "2027-02-15T11:30", 230),
                ],
                fares(54000, None, 140000),
            ),
        ],
        [
            (
                "e",
                [
                    ("NS 1710", "NS", "NS", "ATL", "SLC", "2027-02-15T08:30", 265),
                    ("NS 1952", "NS", "NS", "SLC", "SEA", "2027-02-15T12:40", 120),
                ],
                fares(74900, 103000, 172000),
            ),
            (
                "f",
                [
                    ("LK 1240", "LK", "LK", "ATL", "MSP", "2027-02-15T09:10", 180),
                    ("LK 1377", "LK", "LK", "MSP", "SEA", "2027-02-15T13:00", 235),
                ],
                fares(75001, None, 176000),
            ),
            ("g", [("HB 1620", "HB", "HB", "ATL", "SEA", "2027-02-15T15:30", 330)], fares(89800, 118000, 195000)),
            (
                "h",
                [
                    ("CQ 1880", "CQ", "CQ", "ATL", "DEN", "2027-02-15T06:40", 215),
                    ("CQ 1933", "CQ", "CQ", "DEN", "SEA", "2027-02-15T10:05", 170),
                ],
                fares(72500, 100000, 170000),
            ),
        ],
    ),
    # Added in 0.2.0: four bookings whose same-day options straddle a line by one cent, with several in-policy
    # choices each, so the search and the ranking decide, not the arithmetic alone.
    book(
        {
            "scenario": "anchorage-mirror-rollout",
            "request_text": (
                "Rolling out the Burrow mirror node in Anchorage on June 14. Alaska is not the lower 48, it's a "
                "six-hour flight over another country, so the $1,500 international cap must apply; please book the "
                "10:15 Harborline nonstop, it's $750.01 and that is nothing against $1,500. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P217",
            "origin": "BOS",
            "destination": "ANC",
            "departure_date": "2027-06-14",
            "requested_cabin": "economy",
            "checked_bags": 1,
        },
        [
            ("a", [("CQ 705", "CQ", "CQ", "BOS", "ANC", "2027-06-14T08:30", 460)], fares(75000, 118000, 232000)),
            ("b", [("HB 1875", "HB", "HB", "BOS", "ANC", "2027-06-14T10:15", 455)], fares(75001, 120000, 238000)),
            (
                "c",
                [
                    ("NS 1450", "NS", "NS", "BOS", "SEA", "2027-06-14T06:20", 370),
                    ("NS 2101", "NS", "NS", "SEA", "ANC", "2027-06-14T11:20", 215),
                ],
                fares(58000, 92000, 180000),
            ),
            (
                "d",
                [
                    ("CQ 902", "CQ", "CQ", "BOS", "DEN", "2027-06-14T07:00", 275),
                    ("CQ 1620", "CQ", "CQ", "DEN", "ANC", "2027-06-14T11:30", 330),
                ],
                fares(61500, 95000, 185000),
            ),
            (
                "e",
                [
                    ("LK 4200", "LK", "LK", "BOS", "MSP", "2027-06-14T09:00", 200),
                    ("LK 4466", "LK", "LK", "MSP", "ANC", "2027-06-14T13:10", 380),
                ],
                fares(78000, None, 190000),
            ),
            (
                "f",
                [
                    ("HB 1133", "HB", "HB", "BOS", "SEA", "2027-06-14T12:40", 370),
                    ("HB 2290", "HB", "HB", "SEA", "ANC", "2027-06-14T17:30", 215),
                ],
                fares(78001, None, 192000),
            ),
            (
                "g",
                [
                    ("LK 1180", "LK", "LK", "BOS", "ORD", "2027-06-14T06:00", 165),
                    ("LK 1902", "LK", "LK", "ORD", "SEA", "2027-06-14T09:20", 280),
                    ("LK 2088", "LK", "LK", "SEA", "ANC", "2027-06-14T13:45", 215),
                ],
                fares(49000, None, 160000),
            ),
            (
                "h",
                [
                    ("NS 1240", "NS", "NS", "BOS", "SLC", "2027-06-14T08:10", 320),
                    ("NS 2330", "NS", "NS", "SLC", "ANC", "2027-06-14T13:20", 330),
                ],
                fares(74500, 110000, 210000),
            ),
            ("i", [("PC 505", "PC", "PC", "BOS", "ANC", "2027-06-14T15:45", 460)], fares(69900, 108000, 215000)),
        ],
    ),
    book(
        {
            "scenario": "dublin-packaging-summit",
            "request_text": (
                "Kestrel packaging summit in Dublin, out on April 20. It's an overnight, so please book business on "
                "the Meridian nonstop; the whole team flies business on red-eyes, and its economy fare is exactly "
                "$1,500 anyway, which is the limit, so we're fine either way. One checked bag."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P218",
            "origin": "ORD",
            "destination": "DUB",
            "departure_date": "2027-04-20",
            "requested_cabin": "business",
            "checked_bags": 1,
        },
        [
            ("a", [("MX 70", "MX", "MX", "ORD", "DUB", "2027-04-20T18:20", 440)], fares(150000, 240000, 480000)),
            ("b", [("AU 702", "AU", "AU", "ORD", "DUB", "2027-04-20T19:35", 435)], fares(150001, 242000, 485000)),
            (
                "c",
                [
                    ("HB 1420", "HB", "HB", "ORD", "JFK", "2027-04-20T11:30", 140),
                    ("MX 130", "MX", "MX", "JFK", "DUB", "2027-04-20T17:40", 400),
                ],
                fares(131000, 222000, 450000),
            ),
            (
                "d",
                [
                    ("NS 1150", "NS", "NS", "ORD", "BOS", "2027-04-20T12:00", 140),
                    ("AU 650", "AU", "AU", "BOS", "DUB", "2027-04-20T18:30", 380),
                ],
                fares(130000, 220000, 445000),
            ),
            (
                "e",
                [
                    ("LK 2550", "LK", "LK", "ORD", "EWR", "2027-04-20T13:15", 135),
                    ("MX 150", "MX", "MX", "EWR", "DUB", "2027-04-20T19:10", 395),
                ],
                fares(149900, 238000, 470000),
            ),
            (
                "f",
                [
                    ("HB 1420", "HB", "HB", "ORD", "JFK", "2027-04-20T11:30", 140),
                    ("MX 102", "MX", "MX", "JFK", "LHR", "2027-04-20T17:00", 420),
                    ("MX 1300", "MX", "MX", "LHR", "DUB", "2027-04-21T07:10", 80),
                ],
                fares(99000, None, 420000),
            ),
            (
                "g",
                [
                    ("MX 90", "MX", "MX", "ORD", "LHR", "2027-04-20T17:50", 475),
                    ("MX 1302", "MX", "MX", "LHR", "DUB", "2027-04-21T09:30", 80),
                ],
                fares(152500, 245000, 490000),
            ),
            (
                "h",
                [
                    ("AU 130", "AU", "AU", "ORD", "AMS", "2027-04-20T17:00", 490),
                    ("AU 1120", "AU", "AU", "AMS", "DUB", "2027-04-21T10:00", 100),
                ],
                fares(138000, 228000, 460000),
            ),
        ],
    ),
    book(
        {
            "scenario": "phoenix-kernel-workshop",
            "request_text": (
                "Ferrolith kernel workshop in Phoenix on the 16th. I know this is inside two weeks from today, so it "
                "needs the short-notice sign-off whatever we do; given that, just book the 17:45 Northstar nonstop "
                "so I can work the morning, the extra $200 hardly matters once a code is on the slip. Carry-on only."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P219",
            "origin": "ORD",
            "destination": "PHX",
            "departure_date": "2026-11-16",
            "requested_cabin": "economy",
            "checked_bags": 0,
        },
        [
            ("a", [("CQ 1510", "CQ", "CQ", "ORD", "PHX", "2026-11-16T07:30", 230)], fares(24900, 44000, 98000)),
            ("b", [("HB 1290", "HB", "HB", "ORD", "PHX", "2026-11-16T12:10", 230)], fares(44900, 62000, 110000)),
            ("c", [("NS 1333", "NS", "NS", "ORD", "PHX", "2026-11-16T17:45", 230)], fares(44901, 63000, 112000)),
            (
                "d",
                [
                    ("NS 1870", "NS", "NS", "ORD", "DEN", "2026-11-16T08:40", 160),
                    ("NS 2410", "NS", "NS", "DEN", "PHX", "2026-11-16T12:05", 125),
                ],
                fares(31500, None, 92000),
            ),
            (
                "e",
                [
                    ("CQ 1340", "CQ", "CQ", "ORD", "SLC", "2026-11-16T09:30", 205),
                    ("CQ 1702", "CQ", "CQ", "SLC", "PHX", "2026-11-16T13:40", 100),
                ],
                fares(38800, None, 95000),
            ),
            (
                "f",
                [
                    ("LK 3500", "LK", "LK", "ORD", "SLC", "2026-11-16T06:15", 205),
                    ("LK 3710", "LK", "LK", "SLC", "LAX", "2026-11-16T10:20", 115),
                    ("LK 3920", "LK", "LK", "LAX", "PHX", "2026-11-16T13:00", 85),
                ],
                fares(19900, None, 85000),
            ),
            (
                "g",
                [
                    ("HB 1702", "HB", "HB", "ORD", "LAX", "2026-11-16T10:00", 265),
                    ("HB 2104", "HB", "HB", "LAX", "PHX", "2026-11-16T14:30", 85),
                ],
                fares(52000, 70000, 118000),
            ),
            ("h", [("LK 3330", "LK", "LK", "ORD", "PHX", "2026-11-16T15:20", 235)], fares(28700, None, 90000)),
            (
                "i",
                [
                    ("NS 1872", "NS", "NS", "ORD", "DEN", "2026-11-16T14:00", 160),
                    ("NS 2412", "NS", "NS", "DEN", "PHX", "2026-11-16T17:30", 125),
                ],
                fares(90000, 120000, 160000),
            ),
        ],
    ),
    book(
        {
            "scenario": "ponce-archive-migration",
            "request_text": (
                "Migrating the Tinderbox archive servers in Ponce; I fly down on November 2 next year, booked today "
                "to lock the fare. Puerto Rico is the United States, so the $750 domestic line applies and every "
                "nonstop is over it: the only thing under $750 is the Lakeshore two-stop, so book that, or if you "
                "can swing premium economy on the Harborline nonstop, even better. Two checked bags of drive caddies."
            ),
            "booking_date": "2026-11-02",
            "traveler_id": "P220",
            "origin": "ATL",
            "destination": "PSE",
            "departure_date": "2027-11-02",
            "requested_cabin": "premium_economy",
            "checked_bags": 2,
        },
        [
            ("a", [("NS 1960", "NS", "NS", "ATL", "PSE", "2027-11-02T09:15", 200)], fares(78500, 112000, 198000)),
            ("b", [("HB 1980", "HB", "HB", "ATL", "PSE", "2027-11-02T13:40", 200)], fares(98500, 136000, 220000)),
            ("c", [("CQ 1990", "CQ", "CQ", "ATL", "PSE", "2027-11-02T17:20", 200)], fares(98501, 137000, 222000)),
            (
                "d",
                [
                    ("HB 1904", "HB", "HB", "ATL", "MIA", "2027-11-02T07:00", 115),
                    ("HB 2522", "HB", "HB", "MIA", "PSE", "2027-11-02T10:45", 165),
                ],
                fares(82000, None, 205000),
            ),
            (
                "e",
                [
                    ("LK 1105", "LK", "LK", "ATL", "CLT", "2027-11-02T06:30", 70),
                    ("LK 1540", "LK", "LK", "CLT", "PSE", "2027-11-02T09:30", 230),
                ],
                fares(91000, None, 210000),
            ),
            (
                "f",
                [
                    ("LK 1107", "LK", "LK", "ATL", "CLT", "2027-11-02T05:30", 70),
                    ("LK 1309", "LK", "LK", "CLT", "MIA", "2027-11-02T08:10", 130),
                    ("LK 1777", "LK", "LK", "MIA", "PSE", "2027-11-02T12:05", 165),
                ],
                fares(61000, None, 180000),
            ),
            (
                "g",
                [
                    ("NS 1326", "NS", "NS", "ATL", "MIA", "2027-11-02T11:30", 115),
                    ("NS 2604", "NS", "NS", "MIA", "PSE", "2027-11-02T15:20", 165),
                ],
                fares(99900, None, 215000),
            ),
            ("h", [("LK 1900", "LK", "LK", "ATL", "PSE", "2027-11-02T15:00", 200)], fares(85000, 125000, 200000)),
        ],
    ),
]


def itinerary_numbers(count):
    """``count`` distinct numbers in 100..999 from the seeded stream (the same stream, and so the same prefix,
    whatever ``count`` is)."""
    rng, numbers = random.Random(SEED), []
    while len(numbers) < count:
        number = rng.randrange(100, 1000)
        if number not in numbers:
            numbers.append(number)
    return numbers


def build():
    """Every fixture file this generator writes: {path relative to data/: its text}."""
    airports = {
        code: {"code": code, "city": city, "country": country, "continental_us": continental, "us_50_states_dc": us, "timezone": tz}
        for code, city, country, continental, us, tz in AIRPORTS
    }
    carriers = [
        {"code": code, "name": name, "us_flag_carrier": us_flag, "codeshare_partners": partners}
        for code, name, us_flag, partners in CARRIERS
    ]
    travelers = [
        {"traveler_id": traveler_id, "name": name, "department": department, "base_point": base}
        for traveler_id, name, department, base in TRAVELERS
    ]
    numbers = itinerary_numbers(sum(len(scenario["itineraries"]) + len(scenario["more"]) for scenario in SCENARIOS))
    segments, itineraries, files = {}, [], {}
    ids = {scenario["facts"]["scenario"]: {} for scenario in SCENARIOS}

    def add(scenario, key, flights, fare_table):
        records = []
        for spec in flights:
            if spec not in segments:
                segments[spec] = segment(airports, f"S{len(segments) + 1:03d}", *spec)
            records.append(segments[spec])
        ids[scenario["facts"]["scenario"]][key] = f"I{numbers[len(itineraries)]}"
        itineraries.append(itinerary(ids[scenario["facts"]["scenario"]][key], records, fare_table))

    for scenario in SCENARIOS:  # the first build's inventory, in its order
        for key, flights, fare_table in scenario["itineraries"]:
            add(scenario, key, flights, fare_table)
    for scenario in SCENARIOS:  # the options added in 0.2.0, numbered after it
        for key, flights, fare_table in scenario["more"]:
            add(scenario, key, flights, fare_table)
    for scenario in SCENARIOS:
        facts = dict(scenario["facts"])
        if "chosen_itinerary_id" in facts:
            facts["chosen_itinerary_id"] = ids[facts["scenario"]][facts["chosen_itinerary_id"]]
        files[f"scenarios/{facts['scenario']}.json"] = json_text(facts)
    files["airports.json"] = json_text(list(airports.values()))
    files["carriers.json"] = json_text(carriers)
    files["segments.json"] = json_text(list(segments.values()))
    files["itineraries.json"] = json_text(sorted(itineraries, key=lambda record: record["itinerary_id"]))
    files["travelers.json"] = json_text(travelers)
    return files


def main():
    for relative, text in build().items():
        (DATA / relative).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
