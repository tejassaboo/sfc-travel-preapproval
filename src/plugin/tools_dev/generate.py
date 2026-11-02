"""The seeded generator of this plugin's fixtures (development only): `uv run python -m plugin.tools_dev.generate`
rewrites src/plugin/data/ (except handbook.md). The committed files are the source of truth; a test checks
this generator still reproduces them byte for byte.

Each scenario's flights are written out by hand, because each one sits on a boundary of the brief
(TRAVEL_POLICY_TASKS_CONTEXT.md section 4, T4); the seed only scatters the itinerary ids, so an answer is
never simply the first or lowest id. Carriers, travelers and member projects are fictional, and so are all
fares. Expected answers are not written here: they live in tests/cases/.
"""

import random
from pathlib import Path

from plugin.tools_dev.worldgen import itinerary, json_text, segment

SEED = 20120327  # the pinned policy commit's date
DATA = Path(__file__).resolve().parents[1] / "data"

AIRPORTS = [
    # code, city, country, continental US, US 50 states + DC, IANA timezone
    ("AMS", "Amsterdam", "NL", False, False, "Europe/Amsterdam"),
    ("ATH", "Athens", "GR", False, False, "Europe/Athens"),
    ("ATL", "Atlanta", "US", True, True, "America/New_York"),
    ("AUS", "Austin", "US", True, True, "America/Chicago"),
    ("BER", "Berlin", "DE", False, False, "Europe/Berlin"),
    ("BOS", "Boston", "US", True, True, "America/New_York"),
    ("CDG", "Paris Charles de Gaulle", "FR", False, False, "Europe/Paris"),
    ("CLT", "Charlotte", "US", True, True, "America/New_York"),
    ("DEN", "Denver", "US", True, True, "America/Denver"),
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
]


def fares(economy, premium_economy, business, first=None):
    return {"economy": economy, "premium_economy": premium_economy, "business": business, "first": first}


def audit(facts, itineraries):
    return {"facts": {**facts, "task": "sfc-audit"}, "itineraries": itineraries}


def book(facts, itineraries):
    return {"facts": {**facts, "task": "sfc-book"}, "itineraries": itineraries}


# Per scenario: its facts, and its itineraries as (key, segments, fares), each segment
# (flight, marketing carrier, operating carrier, origin, destination, local departure, in-air minutes).
# An audit's chosen_itinerary_id names one of its own itineraries by key; build() swaps in the seeded id.
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
    ),
]


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
    count = sum(len(scenario["itineraries"]) for scenario in SCENARIOS)
    numbers = random.Random(SEED).sample(range(100, 1000), count)
    segments, itineraries, files = {}, [], {}
    for scenario in SCENARIOS:
        ids = {}
        for key, flights, fare_table in scenario["itineraries"]:
            records = []
            for spec in flights:
                if spec not in segments:
                    segments[spec] = segment(airports, f"S{len(segments) + 1:03d}", *spec)
                records.append(segments[spec])
            ids[key] = f"I{numbers[len(itineraries)]}"
            itineraries.append(itinerary(ids[key], records, fare_table))
        facts = dict(scenario["facts"])
        if "chosen_itinerary_id" in facts:
            facts["chosen_itinerary_id"] = ids[facts["chosen_itinerary_id"]]
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
