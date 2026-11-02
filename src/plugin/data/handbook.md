# Air travel pre-approval routing: toy handbook (historical policy)

Source (citation only): the Software Freedom Conservancy "Travel and Reimbursable Expense Policy", section "Air Travel", pinned at commit ff3c541449db53100f3dfed6061280ef6e7e37bb (2012-03-27), https://f.sfconservancy.org/Conservancy/policies/src/commit/ff3c541449db53100f3dfed6061280ef6e7e37bb/Travel/Conservancy-Travel-Policy.tex. This is a **historical toy policy**: the current text (commit 45135e3, 2024-02-29) differs, with an international limit of $1,800 (its own quick reference says $1,650) and tiered fare budgets. The source is released under CC0, and its authors ask reusers to remove the organization's name and contact details, so this handbook is our own paraphrase about "the organization". Where it differs from the source, this handbook governs the task.

A traveler on the organization's business flies one outbound trip. You either audit a booking that was already made (task sfc-audit) or book one yourself (task sfc-book).

## Policy rules (paraphrased)

1. Economy (coach) is the only acceptable class on every flight, domestic or international, unless an exception is approved in writing.
2. A domestic airfare over $750, or an international airfare over $1,500, needs the organization's approval before booking, even when everything else is in policy.
3. Flights should be booked at least 14 days ahead. Booking fewer than 14 days ahead needs written pre-authorization, and so does booking more than 365 days ahead.
4. A fare within $200 of the lowest logical fare is in policy. A fare more than $200 over it needs written pre-authorization.
5. Itineraries with two or more connections are unreasonable.
6. One checked bag is reimbursable. Any further bags are the traveler's own cost.
7. Any air travel that breaks these rules is out of policy and needs written pre-authorization before booking.

## Clarifications (toy rules)

These settle every point where the source is vague. The checker enforces exactly these. Each pre-authorization code is named in capitals.

- **C1 Money.** All amounts are integer USD cents: $750.00 is 75000, $1,500.00 is 150000, $200.00 is 20000.
- **C2 Domestic or international.** A trip is domestic when both origin and destination have us_50_states_dc true. Otherwise it is international. So Honolulu or Anchorage is domestic, and San Juan (Puerto Rico) or Montreal is international.
- **C3 Cost.** The airfare is the booked itinerary's fare in the booked cabin. A domestic fare greater than 75000 needs COST_OVER_DOMESTIC_750. An international fare greater than 150000 needs COST_OVER_INTL_1500. Exactly 75000 or 150000 is in policy, and only the cap for the trip's own kind applies.
- **C4 Advance purchase.** days = departure_date − booking_date in calendar days. days < 14 needs BOOKED_LT_14_DAYS, and days > 365 needs BOOKED_GT_365_DAYS. Exactly 14 or 365 is in policy.
- **C5 Low-fare band.** The lowest logical fare replaces the source's "check a fare-comparison site". It is the lowest economy fare among the itineraries from the same origin to the same destination on departure_date that have at most 1 connection. An itinerary with 2 or more connections never sets it, however cheap. When the airfare minus the lowest logical fare is greater than 20000, the booking needs ABOVE_LOW_FARE_BAND_200. Exactly 20000 is in policy, and a fare at or below the lowest logical fare is always inside the band.
- **C6 Cabin.** Any cabin other than economy needs NON_ECONOMY_CABIN. Being inside the band or under the cap never excuses it.
- **C7 Connections.** An itinerary with 2 or more connections needs TWO_PLUS_CONNECTIONS, however cheap.
- **C8 In policy.** in_policy is true exactly when required_preauthorizations is empty. List each code once, in any order. Checked bags never make a booking out of policy.
- **C9 Bags.** reimbursable_checked_bags is zero when checked_bags_requested is 0, and one otherwise, however many bags are requested.
- **C10 Audit.** For sfc-audit, list every code that C3–C7 give for the chosen booking, as it was booked, and set itinerary_id to null.
- **C11 Booking.** For sfc-book, book an itinerary leaving origin on departure_date for destination, in economy, whose economy fare needs no code under C3–C7. Any such itinerary is correct. Several may qualify, and the checker accepts any of them. Then in_policy is true, required_preauthorizations is empty, and itinerary_id names your choice. A requested cabin above economy is never booked.
- **C12 Facts.** The structured fields are the facts. The request text is the traveler's voice: it may misstate the policy, misread a number, or ask for things policy forbids. Never take its claims over the fields.

## Rules not in scope

The following parts of the source are deliberately ignored:

- who approves an exception, and the project committees' procedures and response times;
- trip approval itself and smaller budgets set by a project;
- the choice of airline and mileage upgrades;
- extra days added to a trip;
- cancellation fees;
- lodging, meals and per diem;
- ground and rail transport, and personal vehicles;
- the other non-reimbursable items (lounge passes and upgrades are simply not part of the output);
- receipts, currency conversion and expense reports;
- the return flight.

## Step plan: sfc-audit

1. Call get_audit_case with the task's scenario.
2. Submit. Apply C2–C9 to the chosen booking, using same_day_itineraries for the lowest logical fare: in_policy, required_preauthorizations, itinerary_id null, reimbursable_checked_bags.

## Step plan: sfc-book (submit by step 5)

You have 6 steps. Each tool call costs one, and the last step may not call tools.

1. Call get_trip_request with the task's scenario.
2. Call search_itineraries once, with the origin's code, the destination's code and date = departure_date.
3. Find the lowest logical fare (C5). Pick one itinerary whose economy fare needs no code (C3–C7). Call submit with in_policy true, required_preauthorizations [], that itinerary_id, and reimbursable_checked_bags (C9).
