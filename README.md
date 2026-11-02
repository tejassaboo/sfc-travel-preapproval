# SFC Travel Pre-Approval

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
  - `reimbursable_checked_bags: BagAllowance`, either `zero` or `one`.
- **Success:**
  - **`sfc-audit`:** the exact set of codes and the bag allowance.
  - **`sfc-book`:** any itinerary in the valid set, with `in_policy` true and no codes.
- **Handbook:** `src/plugin/data/handbook.md` is the `instructions` of both tasks in `nanoagent.yaml`, and a test keeps the copies identical. It holds:
  - rules 1–7;
  - the "Clarifications (toy rules)" C1–C12;
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

| Booking scenario | Story and trap | Valid set (any one is correct) |
|---|---|---|
| `boston-mentor-summit` | "Book the cheapest, any number of stops." `I662` has 2 connections, `I158` is $200.01 over the band, and `I749` flies a day early | `I328`, `I577`, `I658` (band exactly $200) |
| `paris-firmware-workshop` | Business was requested; only economy is allowed | `I260`, `I399` |
| `athens-translation-sprint` | The nonstop is "within $200" but over the $1,500 cap | `I256`, `I653` |
| `seattle-release-party` | The nonstop is within the band but over the $750 cap | `I730` only |

## Tools

| Tool | Does | Code |
|---|---|---|
| `get_audit_case` | Returns a booking to audit: the request, booking and departure dates, traveler, both airports with `us_50_states_dc`, the chosen itinerary, cabin and fare, the requested bags, and every same-day itinerary with connections and fares per cabin | `src/plugin/lookups.py` |
| `get_trip_request` | Returns a trip to book: the request, dates, traveler, both airports, the requested cabin and bags | `src/plugin/lookups.py` |
| `search_itineraries` | Lists every itinerary from one airport to another on a date, with route, flights, local times, connections and fares per cabin. It applies no policy | `src/plugin/search.py` |
| `compute_audit` | The `sfc-audit` answer key (`rules.audit_oracle`). It is the task's `reference`, never shown to the agent | `src/plugin/reference.py` |
| `compute_valid_set` | The `sfc-book` answer key (`rules.valid_set`): the valid itineraries, the lowest logical fare, and why each other itinerary is rejected. It is the task's `reference` | `src/plugin/reference.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `sfc-audit` | Audits an air booking and routes every pre-authorization the toy handbook requires | `decide`, with `get_audit_case`; reference `compute_audit` |
| `sfc-book` | Books any flight that needs no pre-authorization | `agent`, with `get_trip_request` and `search_itineraries`; reference `compute_valid_set` |

### Why these runners

**`sfc-audit` uses `decide`.** Every output field can be filled by choice:
- `in_policy` is a bool;
- the codes are a single multi-select `list[Enum]`;
- `itinerary_id` is chosen as null;
- the bag allowance is an Enum.

The bag allowance is deliberately an Enum, not an `int`. Under `decide`, an `int` field may be copied from any int in the state, such as a fare or a connection count.

NanoAgent's own `dataflow.fill` counts **4 model requests** per audit, against the 6-step cap: next, the scenario choice, next, then the output in one batch.

**`sfc-book` uses `agent`.** It takes 3 steps: `get_trip_request`, then `search_itineraries`, then `submit`.

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
- Fixtures come from the seeded generator `src/plugin/tools_dev/generate.py`, which builds on `tools_dev/worldgen.py`. A test checks that it reproduces the committed files byte for byte.
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
5. Codes and bags:
   - `preauths-correct`
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
5. Codes and bags:
   - `preauths-correct`
   - `bags-correct`

Decisions the verifier enforces:

- **Consistency:** `in_policy == (required_preauthorizations == [])`. Checked bags never affect `in_policy`, because excess bags are the traveler's cost and need no sign-off.
- **Codes:** compared as a **set**, with repeats refused. A model may list them in any order; `decide` fills them in declaration order.
- **Booking:** any member of the valid set is accepted.
- **Scoring:** 1.0 when valid, 0.0 otherwise.
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
- the domestic rule for Hawaii and Puerto Rico;
- oracle == the hand-written `tests/cases/<scenario>.json` for every scenario;
- answers unchanged when `request_text` is replaced;
- the `rules.py` and `world.py` identity checks;
- handbook == `instructions` for both tasks;
- the organization's name appears only in the citation;
- fixture invariants recomputed with `zoneinfo`;
- generator reproducibility;
- tool-output size;
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
└── verifier/        # deterministic verifier: audit.py, book.py, stages.py, explain.py, lookups.py, search.py, rules.py, world.py
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run python -m plugin.tools_dev.generate   # rewrite the fixtures; the tests then check them
```

To run a task, use `nanoagent plugin agent config=agent.yaml home=<run folder>`. Set `task` to `sfc-audit` or `sfc-book`, and set `arguments` to a JSON file such as `{"scenario": "geneva-licensing-hearing"}`. It needs `OPENROUTER_API_KEY` in the environment, not in this repo.
