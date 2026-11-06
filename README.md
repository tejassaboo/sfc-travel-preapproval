# SFC Travel Pre-Approval

**No affiliation with Software Freedom Conservancy.**

A `nanoagent.plugin/v0001` plugin for **pre-approval routing**, with two tasks. The agent audits an air booking that a traveler already made and routes it to every written pre-authorization it needs. Or it books a trip that needs none. The rules come from a toy handbook paraphrased from a **historical** nonprofit travel policy. A deterministic Python verifier, with no LLM, checks each answer against an oracle that it computes itself.

**Source (citation only):** the Software Freedom Conservancy "Travel and Reimbursable Expense Policy", "Air Travel" section, pinned at commit [`ff3c541449db53100f3dfed6061280ef6e7e37bb`](https://f.sfconservancy.org/Conservancy/policies/src/commit/ff3c541449db53100f3dfed6061280ef6e7e37bb/Travel/Conservancy-Travel-Policy.tex) (2012-03-27). This is a **historical toy policy**. The current policy (commit `45135e3`, 2024-02-29) differs: its international limit is $1,800, though its own quick reference says $1,650, and it uses tiered fare budgets. The source repository is CC0, and its README asks reusers to remove the organization's name and contact details. So the handbook is our own paraphrase about "the organization", and the name appears only in this citation.

## Task

- **Inputs:** each is a single Enum field, `scenario`:
  - `AuditInput` for `sfc-audit`, for example `{"scenario": "honolulu-security-workshop"}`;
  - `BookInput` for `sfc-book`, for example `{"scenario": "boston-mentor-summit"}`.
- **Output:** both tasks share `SfcOutput`, which has these fields:
  - `in_policy: bool`;
  - `required_preauthorizations: list[SfcPreauth]`, with seven codes;
  - `itinerary_id: str | None`, which is null for an audit;
  - `fare_cents: int`, the airfare judged (C10a): the chosen fare in the booked cabin for an audit, the booked itinerary's economy fare for a booking;
  - `lowest_logical_fare_cents: int`, C5's lowest logical fare;
  - `advance_days: int`, C4's calendar days from booking to departure;
  - `reimbursable_checked_bags: BagAllowance`, either `zero` or `one`.

  The three magnitudes were added in 0.2.0 so that a travel desk reads the overage and the notice off the slip, and so that the verifier can give partial credit. None of them is nullable.
- **Success:**
  - **`sfc-audit`:** the exact set of codes, the three magnitudes and the bag allowance.
  - **`sfc-book`:** any itinerary in the valid set, with `in_policy` true, no codes, its own economy fare, and the right lowest logical fare, days and bag allowance.
- **Handbook:** `src/plugin/data/handbook.md` is the `instructions` of both tasks in `nanoagent.yaml`, and a test keeps the copies identical. It holds:
  - rules 1–7;
  - the "Clarifications (toy rules)" C1–C12, with C10a for the magnitudes;
  - the rules not in scope;
  - both step plans.
- **Structured facts:** every fact the policy decides on is a typed field. `request_text` is only the traveler's voice and carries distractors. A test checks that answers do not change when it is replaced.

| Audit scenario | Story and trap | Expected `required_preauthorizations` (bags) |
|---|---|---|
| `portland-docs-sprint` | Four at-limit values at once: $750.00, 14 days, a band of exactly $200 and 1 connection. The cheaper 3-stop fare never sets the lowest logical fare | none, in policy (one) |
| `denver-board-retreat` | $750.01 domestic: "nobody routes a penny" | `COST_OVER_DOMESTIC_750` (one) |
| `berlin-keynote` | International fare of exactly $1,500.00, booked exactly 365 days ahead, with 2 bags | none, in policy (one) |
| `lisbon-community-summit` | $1,500.01 international. The 2-stop 118000 fare is not the low fare | `COST_OVER_INTL_1500` (one) |
| `chicago-foundation-briefing` | A band of $200.01: "my colleague always takes it". No bags | `ABOVE_LOW_FARE_BAND_200` (zero) |
| `austin-hackfest` | Booked 13 days ahead: "basically two weeks" | `BOOKED_LT_14_DAYS` (one) |
| `tokyo-standards-meeting` | Booked 366 days ahead | `BOOKED_GT_365_DAYS` (one) |
| `raleigh-maintainers-meetup` | The cheapest fare has 2 connections | `TWO_PLUS_CONNECTIONS` (one) |
| `montreal-accessibility-keynote` | Premium economy: inside the band and under the cap, but not economy | `NON_ECONOMY_CABIN` (one) |
| `geneva-licensing-hearing` | Business, 10 days ahead, $4,200, plus a lounge pass, and 3 bags | `COST_OVER_INTL_1500`, `BOOKED_LT_14_DAYS`, `ABOVE_LOW_FARE_BAND_200`, `NON_ECONOMY_CABIN` (one) |
| `honolulu-security-workshop` | "Hawaii is overseas": no, both ends are in the 50 states, so $825 is over $750 | `COST_OVER_DOMESTIC_750` (one) |
| `san-juan-outreach` | "Puerto Rico is domestic": no, it is outside the 50 states + DC, so $810 is under $1,500 | none, in policy (one) |

Every audit now shows 5 or 6 same-day options; the magnitudes expected on each slip are in `tests/cases/`.

| Booking scenario | Options | Story and trap | Valid set (any one is correct) |
|---|---|---|---|
| `boston-mentor-summit` | 8 | "Book the cheapest, any number of stops." `I662` has 2 connections, `I158` is $200.01 over the band, `I123` further, and `I749` flies a day early | `I328`, `I874`, `I577`, `I825`, `I658` (band exactly $200) |
| `paris-firmware-workshop` | 8 | Business was requested; only economy is allowed. `I174` is $210 over the band | `I399`, `I183`, `I260`, `I714` (band exactly $200) |
| `athens-translation-sprint` | 8 | The nonstop is "within $200" but over the $1,500 cap; `I359` is over the cap with a band of exactly $200, `I649` one cent over both | `I653`, `I971`, `I256` |
| `seattle-release-party` | 8 | The nonstop is within the band but over the $750 cap; `I502` is $750.01 | `I730`, `I177`, `I219` |
| `anchorage-mirror-rollout` | 9 | "Alaska is international, so book the $750.01 nonstop." Both ends are in the 50 states: `I888` at exactly $750.00 is valid, `I584` at $750.01 is not; `I482` sits at a band of exactly $200 but over the cap, `I323` one cent over both | `I973`, `I307`, `I373`, `I101`, `I888` |
| `dublin-packaging-summit` | 8 | Business was requested. The Meridian nonstop `I245` is exactly $1,500.00 and exactly $200 over the lowest logical fare: valid; `I452` at $1,500.01 is one cent over both lines | `I886`, `I153`, `I519`, `I107`, `I245` |
| `phoenix-kernel-workshop` | 9 | Booked exactly 14 days ahead: "inside two weeks, so it needs a code anyway". No code; `I480` is a band of exactly $200, the requested `I593` is $200.01 | `I620`, `I858`, `I249`, `I641`, `I480` |
| `ponce-archive-migration` | 8 | Booked exactly 365 days ahead to Puerto Rico: "domestic, so everything is over $750; book the two-stop". International, so every nonstop is under the cap; `I723` has 2 connections, `I716` is $200.01 over the band | `I204`, `I885`, `I719`, `I266`, `I100` |

Each booking straddles a line inside its own option list, one cent apart: $750.00 vs $750.01 (Anchorage, Seattle), $1,500.00 vs $1,500.01 (Dublin, Athens), a band of $200.00 vs $200.01 (Boston, Phoenix, Ponce, Dublin), and the two dates sit exactly on 14 and 365 days (Phoenix, Ponce). Five of the eight bookings have five in-policy options, so the search and the ranking decide, not the arithmetic alone.

## Tools

| Tool | Does | Code |
|---|---|---|
| `get_audit_case` | Returns a booking to audit: the request, booking and departure dates, traveler, both airports with `us_50_states_dc`, the chosen itinerary, cabin and fare, the requested bags, and every same-day itinerary with connections and fares per cabin | `src/plugin/lookups.py` |
| `get_trip_request` | Returns a trip to book: the request, dates, traveler, both airports, the requested cabin and bags | `src/plugin/lookups.py` |
| `search_itineraries` | Lists every itinerary from one airport to another on a date, with route, flights, local times, connections and fares per cabin. It applies no policy | `src/plugin/search.py` |
| `compute_audit` | The `sfc-audit` answer key (`rules.audit_oracle`). It is the task's `reference`, never shown to the agent | `src/plugin/reference.py` |
| `compute_valid_set` | The `sfc-book` answer key (`rules.valid_set`): the valid itineraries, the lowest logical fare, the days ahead, and why each other itinerary is rejected. It is the task's `reference` | `src/plugin/reference.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `sfc-audit` | Audits an air booking and routes every pre-authorization the toy handbook requires | `agent`, with `get_audit_case`; reference `compute_audit` |
| `sfc-book` | Books any flight that needs no pre-authorization | `agent`, with `get_trip_request` and `search_itineraries`; reference `compute_valid_set` |

### Why these runners

**Both tasks use `agent`.** `sfc-audit` takes 2 steps: `get_audit_case`, then `submit`. `sfc-book` takes 3: `get_trip_request`, then `search_itineraries`, then `submit`.

`sfc-audit` was first built on `decide`: every output field can be filled by choice (`in_policy` is a bool, the codes are one multi-select `list[Enum]`, `itinerary_id` is chosen as null, the bag allowance is an Enum), and NanoAgent's `dataflow.fill` counts only 4 model requests per audit. In paid runs with DeepSeek V4 Flash, though, the model's reply to the final question batch is mostly hidden reasoning that counts against the 2,048-token reply cap: 11 of 12 audits passed, with up to 2,017 completion tokens, and `san-juan-outreach` was cut off at the cap twice (temperature 0, before and during the audit), leaving no verdict. The T3 plugin saw the same failure. So `sfc-audit` was switched to `agent`, with the contract and the verifier unchanged (BUILDER_BRIEF: "`decide` runner: avoid it").

The bag allowance stays an Enum, not an `int`, so that an agent cannot answer with a count it copied from the state, such as `checked_bags_requested`; the verifier would accept only `zero` or `one` anyway.

## Environment

- Offline and self-contained:
  - `hosts: []`, an empty `.env`, and `write: []`;
  - no clock: "today" is each scenario's `booking_date`.
- Fixtures are in `src/plugin/data/`:
  - `airports.json`
  - `carriers.json`, all fictional: Cascadia Air, Harborline, Northstar Airways and others
  - `segments.json`, with UTC times and `in_air_minutes` precomputed
  - `itineraries.json`
  - `travelers.json`: fictional volunteers of fictional member projects
  - `scenarios/<id>.json`, which holds facts only and never an answer
- Fares are fictional, in integer USD cents.
- Fixtures come from the seeded generator `src/plugin/tools_dev/generate.py`, which builds on `tools_dev/worldgen.py`. A test checks that it reproduces the committed files byte for byte. Itinerary ids are drawn from one seeded stream in a fixed order (the 0.1.0 inventory first, then the options added in 0.2.0), so the inventory grew from 49 to 128 itineraries without renaming one.
- Each tool output stays under 6,000 characters (about 1.5k tokens): a test checks it.
- The shared core `src/plugin/world.py` is vendored byte-identical into `verifier/world.py`, and the oracle `rules.py` is likewise byte-identical in `src/plugin/` and `verifier/`.
- Python 3.12 or later, with dependencies pinned by `uv.lock`.

## Verifier

`verifier/audit.py` and `verifier/book.py` read the fixtures through `Path(__file__)`. They compute the answer with the shared `rules.py` and check the submission in ordered stages, through `verifier/stages.py`.

Every check has a stable reason code. Each entry records `{id, constraint, ok, expected, actual, message}`. Later stages are skipped once a stage fails, and the message names the first failure and counts the rest. Messages name the rule and the numbers, for example:

```text
preauths-correct: missing COST_OVER_DOMESTIC_750 (economy fare 82500 cents ($825.00) > the $750.00 cap; the trip is domestic: SFO and HNL are both in the 50 states + DC)
```

**`sfc-audit` stages:**

1. `reference-matches-oracle`
2. `itinerary-null-for-audit`
3. Consistency:
   - `preauths-unique`
   - `in-policy-matches-preauths`
4. `in-policy-correct`
5. Codes, magnitudes and bags:
   - `preauths-correct`
   - `fare-correct`
   - `lowest-logical-fare-correct`
   - `advance-days-correct`
   - `bags-correct`

**`sfc-book` stages:**

1. `reference-matches-valid-set`
2. Referential integrity:
   - `itinerary-named`
   - `itinerary-exists`
   - `itinerary-serves-request`
3. Consistency:
   - `preauths-unique`
   - `in-policy-matches-preauths`
4. Decision:
   - `itinerary-in-policy`, which tests membership of the valid set
   - `in-policy-correct`
5. Magnitudes and bags:
   - `fare-correct`, against the economy fare of the itinerary named
   - `lowest-logical-fare-correct`
   - `advance-days-correct`
   - `bags-correct`

A valid booking lists no code, but that needs no constraint of its own: once stages 3 and 4 hold, `in_policy` is true and the list is empty. 0.1.0 carried a `preauths-correct` constraint here that could never fail first; 0.2.0 drops it.

Decisions the verifier enforces:

- **Consistency:** `in_policy == (required_preauthorizations == [])`. Checked bags never affect `in_policy`, because excess bags are the traveler's cost and need no sign-off.
- **Codes:** compared as a **set**, with repeats refused. A model may list them in any order.
- **Booking:** any member of the valid set is accepted.
- **Scoring:** `valid` is strict: true only when every constraint holds, and then `score` is 1.0. Otherwise `score` is partial credit in [0, 1] over the whole answer, whatever stage failed (`verifier/stages.py`):
  - the decision is worth 0.6: for an audit, the Jaccard overlap of the submitted and required code sets (both empty counts as 1; an answer that contradicts itself, with `in_policy` disagreeing with the codes or a code listed twice, gets 0); for a booking, 1 when the itinerary is in the valid set with `in_policy` true and no code, else 0;
  - `fare_cents`, `lowest_logical_fare_cents`, `advance_days` and `reimbursable_checked_bags` are worth 0.1 each when right;
  - wrong in either direction scores the same: a missing code and an extra code cost the same overlap, and a magnitude is right or not;
  - an empty or lazy answer earns at most the bag allowance (0.1); another scenario's answer at most the parts that happen to coincide;
  - integrity caps: an audit that names an itinerary is capped at 0.5; a booking that names no itinerary, an unknown one, or one for another trip earns nothing for the decision or the fare; a pinned answer key that differs from the oracle scores 0.
  - In the engine's own runs, a wrong answer never scores 1.0.
- **Shape errors** never reach the verifier, because NanoAgent's `build_output` refuses them first. These include a wrong type, an unknown Enum value, a missing or extra field, and `null` for a required field.
- **Robustness:** the verifier is pure stdlib and never raises. An unexpected value becomes a `verifier-error` verdict.
- **Tool outputs** are also checked against the fixtures (`verify_output`).

## Validation

`tests/` covers the brief's test matrix:

- correct, incorrect, missing and malformed outputs, with malformed cases as `build_output` rejections;
- consistency and uniqueness;
- every boundary pair, on synthetic worlds and in the scenarios:
  - $750.00 vs $750.01
  - $1,500.00 vs $1,500.01
  - a band of exactly $200 vs $200.01
  - 14 vs 13 days
  - 365 vs 366 days
  - 1 vs 2 connections
  - a non-economy cabin
  - multiple simultaneous triggers
  - a bags request of 3
  - membership of a valid set with several equally valid itineraries;
  - in the bundled bookings, options one cent apart on each line, and bookings exactly 14 and 365 days ahead;
- partial credit: lazy, self-contradicting, cross-scenario and one-unit-off answers, the Jaccard overlap and both caps;
- coverage: every code occurs in a bundled audit, every code an itinerary can trigger on its own rejects a bundled booking option, and every reachable reason code is the first failure of some bundled broken variant (the two date codes and the cabin code never reject a booking option, because they turn on the trip's dates or a non-economy cabin, which no economy same-day itinerary changes; the two answer-key checks fail only when the plugin itself is broken);
- the domestic rule for Hawaii and Puerto Rico;
- oracle == the hand-written `tests/cases/<scenario>.json` for every scenario;
- answers unchanged when `request_text` is replaced;
- the `rules.py` and `world.py` identity checks;
- handbook == `instructions` for both tasks;
- the organization's name appears only in the citation;
- fixture invariants recomputed with `zoneinfo`;
- generator reproducibility;
- tool-output size (under about 1.5k tokens) and richness (5 or more options per audit, 8 or more per booking);
- the brief's §11 cross-policy row for SFC: 360+90+420 minutes allows economy only;
- a real MCP server round trip;
- a scripted, no-LLM end-to-end run per scenario: an agent written from the handbook alone follows the step plan, its answer passes, and broken answers fail with the expected reason code.

## Layout

```text
.
├── nanoagent.yaml   # manifest: id, runtime, permissions, tools, the sfc-audit and sfc-book tasks and their handbook instructions
├── contract.py      # typed inputs and outputs of every tool and task (Enums, int cents)
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # empty: the plugin needs no environment variables
├── src/plugin/      # MCP server (__main__.py), tools, world.py (shared core), rules.py (oracle), fixtures
│   ├── data/        # handbook.md, the fixture JSON files and scenarios/
│   └── tools_dev/   # the seeded fixture generator (development only)
├── tests/           # verifier matrix, oracle cases, scripted agent, rules, tools, fixtures
├── ui/              # renderers.js: a pre-approval slip for SfcOutput; renderers.css
├── product/         # product.yaml and icon.svg
└── verifier/        # deterministic verifier: audit.py, book.py, stages.py, checks.py, explain.py, lookups.py, search.py, rules.py, world.py
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run python -m plugin.tools_dev.generate   # rewrite the fixtures; the tests then check them
```

To run a task with a model, write a NanoAgent run config (a `PluginOpenRouterAgentConfig`; this repo ships none) whose `plugin` is this folder, then run `nanoagent plugin agent config=<run.yaml> home=<run folder> -- task=sfc-audit arguments=<args.json>`, where the arguments file holds a scenario such as `{"scenario": "geneva-licensing-hearing"}`. Use `task=sfc-book` for a booking. It needs `OPENROUTER_API_KEY` in the environment, not in this repo.
