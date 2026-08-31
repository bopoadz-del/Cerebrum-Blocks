# Lane 2 — migration plan

**Plan only. Nothing in this document has been executed, and nothing in it may
be executed before `PRODUCTION_ROADMAP.md` marks P7 DONE.**

Lane 2 built the block contract beside the existing code: `BlockResult`
(#89), the manifest fields (#90), the three template tests (#91), the
report-only conformance table (#92), and Config injection with the fallback
ladder (#93). None of it changed how a single existing block behaves.

This is the plan for the part that does.

---

## 1. Where these numbers come from

Every count below is from the `Lane 2 conformance (report-only)` workflow,
run [33410243029](https://github.com/bopoadz-del/Cerebrum-Blocks/actions/runs/33410243029),
recorded in [`baseline.md`](baseline.md). **Zero blocks failed to import in
that run**, so the numbers are properties of the store rather than of the
machine that measured it.

79 blocks, three checks:

| check | pass | fail |
| --- | ---: | ---: |
| `constructor` | 75 | **4** |
| `smoke` | 40 | **39** |
| `three_tests` | 0 | **79** |

`three_tests` is 0 of 79 *by construction*: the three mandatory tests were
only defined in #91, so nothing predating it can have them. That number is a
backlog, not a regression, and it is the only one of the three that is
expected to start at zero.

---

## 2. The finding that should be read first

**40 blocks return `ok` when invoked with an empty input.**

That is not a footnote. Of The Fork's last 100 merges, ~24 were failures that
still looked like answers — and a block that reports success when it was
given nothing at all is that failure in its purest form. The smoke check
sends each block its *declared* minimal input, and for a block declaring no
`requires_inputs` that is `{}`. Forty of them said `ok`.

```
adaptive_router  agent_swarm  analytics  audit  auth  billing  capture  chat
context_broker  dashboard  database  discovery  documentation  email
error_tracking  failover  health_check  historical_benchmark  knowledge
library_container  local_drive  mcp_adapter  migration  monitoring  ocr_v2
onedrive  orchestrator  payment_split  pdf_v2  queue  rate_limiter  review
sandbox  secrets  storage  team  traffic_manager  validation
validation_pipeline  version
```

For some of these `ok` is correct: `health_check`, `monitoring`, `version`
and other status-reporting blocks answer a question that needs no input.

For others — `database`, `email`, `payment_split`, `storage`, `knowledge`,
`billing`, `analytics` — "success" on an empty request needs an explanation,
and it is not one this lane can supply. **Only the block's author can say
which of the forty is which.** That judgment is Wave 3 below, and it is
deliberately *not* pre-answered here: guessing which ones are defects would
manufacture exactly the confident-but-unsourced claim the contract exists to
prevent.

---

## 3. What the 39 smoke failures actually are

They are not one problem. Grouped by what the block said:

### 3a. Already honest, wrong vocabulary — 23 blocks

```
aviation_chat_server  aviation_v2  code  document_engine  google_drive
image  marker  mcp_consumer  medical_ehr_connector  notification  ocr  pdf
search  skills  translate  vector_search  video_anomaly_trigger
video_metadata_ingest  voice  web  workbench  workflow  zvec
```

These reported things like `No PDF provided`, `Query is required`,
`A URL is required`. **That is the correct behaviour.** They declined because
they had nothing to work on, said why, and invented nothing. They fail the
smoke check only because `{"status": "error"}` is the sole vocabulary
available to them.

Under the contract every one of these is `refused`, not `failed` — and
`refused` is scored as a pass. This is the largest bucket and the cheapest:
the behaviour is already right, only the label is wrong.

### 3b. An error that says nothing — 6 blocks

```
aviation_cargo_kit  aviation_cx_kit  aviation_grounding_gate
aviation_loyalty_kit  aviation_pss_kit  aviation_revenue_kit
```

All six returned an error with **no reason of any kind** — the adapter had to
fall back to "the block reported an error without saying why". These are real
defects, not vocabulary. A caller gets a failure it cannot act on and cannot
report.

### 3c. No default action — 5 blocks

```
async_processor  cache_manager  event_bus  file_hasher  llm_enhancer
```

`Unknown action: None`. These are action-routed blocks invoked without one.
The fix is declarative, not behavioural: name the action in
`requires_inputs`, so a planner that cannot supply it fails at plan time with
the field named rather than at run time with a shrug.

### 3d. Cannot be constructed at all — 4 blocks

```
config  memory  vector  webhook
```

```
ConfigBlock.__init__() missing 2 required positional arguments
```

**This is #88, still live in four more blocks than #88 fixed.** Each requires
positional arguments the base class never promised, so no pipeline can build
them — which is exactly how `DatabaseBlock` reached a zip that would not
boot. This is the most urgent item in the document.

### 3e. Genuinely unimplemented — 1 block

`android_drive` returns `not_implemented`. Correct and honest; it becomes
`refused` with the same reason.

---

## 4. The waves

Each wave is a set of PRs, one concern each, and **each wave's exit criterion
is a number in `baseline.md` moving** — not "the work looks done".

### Wave 0 — the four that cannot be built *(blocking, do first)*

`config` · `memory` · `vector` · `webhook`

Widen each constructor to the base signature
(`__init__(self, hal_block=None, config=None)`), keeping any current
positional call sites working. No behaviour change beyond becoming
constructible.

- **Exit:** `constructor` 79/79.
- **Risk:** low. Widening a signature cannot break a caller that already
  passes the arguments.
- **Why first:** these blocks are unusable *today*. Everything else on this
  list is a labelling or reporting improvement; this one is a boot failure
  waiting for the wrong zip.

### Wave 1 — the six silent errors

The aviation kit blocks in §3b. Give every error exit a reason. Adopt
`BlockResult` at the same time, since the work touches every exit anyway.

- **Exit:** no block in the table reports "without saying why".
- **Risk:** low. Adding a reason to an existing error changes no control flow.

### Wave 2 — `error` → `refused`, the 23 already-honest blocks

Subclass `ContractBlock`, return `BlockResult.refused(...)` where the block
currently returns `{"status": "error", "error": "No PDF provided"}`.

Mechanical, but **not** a blind find-and-replace: each exit needs a human to
confirm it is a refusal (nothing to work on) rather than a failure (something
broke). Getting that backwards in either direction is worse than leaving it
alone — a failure relabelled `refused` disappears from the scoreboard.

- **Exit:** `smoke` failures down to Wave 3's residue.
- **Risk:** medium. `execute()` still wraps results in the same envelope, but
  any caller reading `result["status"] == "error"` directly must be found
  first. **That grep is a prerequisite of this wave, not part of it.**

### Wave 3 — the 40 that answer with nothing

Per block, its author answers one question: *is `ok` on an empty input
correct here?* Then either it stays and gains a test saying why, or it becomes
`refused`.

- **Exit:** every one of the forty is either tested-as-correct or migrated.
- **Risk:** medium, and it is the wave most likely to find real bugs.

### Wave 4 — the three tests, 79 blocks

The largest and the slowest. Per block: happy path, planted failure, mutation
probe (#91's template is the shape). Ordered by blast radius — kernel-tier
and infrastructure blocks first, since they ship inside every generated
platform.

- **Exit:** `three_tests` at whatever number the owner sets as the floor. **79
  of 79 is not a realistic gate for the first enforcement PR** and should not
  be written into one.

---

## 5. Blocks that need a fallback rung

**32 block modules make 99 `os.getenv` / `os.environ` calls** (counted by
parsing, not grepping — `cache_manager`'s docstring mentions the call it no
longer makes, and a substring search cannot tell those apart).

Heaviest first:

| block | calls | dependency | ladder rung |
| --- | ---: | --- | --- |
| `agent_swarm` | 14 | LLM provider | `refuse` |
| `onedrive` | 11 | object store | local directory |
| `medical_ehr_connector` | 8 | FHIR service | refuse — **no local fallback is honest for clinical data** |
| `capture` | 7 | object store / device | local directory |
| `google_drive` | 7 | object store | local directory |
| `notification` | 7 | channel APIs | refuse |
| `config` | 5 | — | reads its own settings; Wave 0 anyway |
| `knowledge` | 4 | vector store + LLM | local index, then `refuse` |
| `formula_executor` | 3 | LLM provider | `refuse` |
| `workflow` | 3 | mixed | per-step |

The remaining 22 modules make one or two calls each and are mostly `ENV` /
`DATA_DIR` reads that move to `Config` unchanged.

The most-read variables across the store are `MOONSHOT_API_KEY` /
`KIMI_API_KEY` (6 each), `DATA_DIR` (5), `SANDBOX_RUNNER_URL` (4) and
`GOOGLE_ACCESS_TOKEN` (4).

**The LLM rung is the one to get right.** Its fallback is a stub returning
`refused` — never a canned answer, never a smaller model. A fallback that
answers anyway converts "this platform has no LLM" into "this platform is
confidently wrong".

`medical_ehr_connector` is called out because it is the case where the ladder
should *not* be climbed down: there is no honest local substitute for a
patient record, and the correct fallback is refusal.

---

## 6. Manifests that need `requires_inputs` — and who may fill them

The 23 blocks in §3a plus the 5 in §3c all declined for a nameable reason,
which means each of them knows what it needed and no manifest says so. Those
28 manifests are where `requires_inputs` pays for itself first: *"if you
assign it, you feed it"* is only enforceable at plan time if the field is
declared.

**Only the block's author may fill it.** Not this lane, and not a script.

This follows the policy already in force for `KNOWN_KIT_GAPS.md`: an
assertion about what a block needs is a claim someone is answerable for.
Inferring `requires_inputs` from an error string would produce a manifest
that *looks* authoritative and was written by a regex — the planner would
then reject valid plans, or accept invalid ones, citing a field nobody
stands behind.

The honest intermediate state is a manifest with no `requires_inputs`, which
is why the field is optional and why the conformance table reports adoption
rather than enforcing it.

---

## 7. Explicitly not in scope

- **No Fork harvest.** That needs the owner's `HARVEST_AUTHORIZED` ritual and
  is post-gate. Lane 2 built the contract a harvest would land into;
  `source_commit` (#90) is the field that will record where harvested code
  came from.
- **No new blocks and no new kits.**
- **No changes to CerebrumDev.ai or The_Fork.**
- **No stranger walks from this lane.** Zip-boot verification is coordinated
  with Cowork.

---

## 8. The enforcement flip

Ready to open **after P7 is DONE and with the owner's explicit tick**, and
not before. Reproduced here so the decision is a yes/no on written text
rather than an argument at the time.

### Preconditions — all four, checked against `baseline.md`

1. `PRODUCTION_ROADMAP.md` marks **P7 DONE**.
2. **Wave 0 complete**: `constructor` at 79/79. This one is not negotiable —
   flipping the constructor check to a gate while four blocks fail it reds
   `main` on the first push.
3. Waves 1 and 2 complete, so the `smoke` number reflects real defects rather
   than vocabulary.
4. A floor agreed for `three_tests`. **Do not flip that check to a gate at
   79/79.**

### Draft PR description

> **ci: the conformance checks stop reporting and start gating**
>
> Flips `.github/workflows/lane2-conformance.yml` from report-only to
> enforcing. Until now the workflow returned 0 no matter what it found; from
> here a regression fails the build.
>
> **Why now.** P7 is DONE, so this no longer sits on the critical path.
> `constructor` is at 79/79 (Wave 0, PRs _____), the silent-error blocks
> report reasons (Wave 1, PRs _____), and the 23 already-honest blocks speak
> `refused` (Wave 2, PRs _____). The numbers being gated are numbers the
> store already meets.
>
> **What changes.** `scripts/lane2_conformance.py` gains `--enforce`, under
> which it returns 1 if any check falls below its floor. Without the flag it
> behaves exactly as it does today, so a local run stays a report.
>
> **The floors**, and why each is where it is:
>
> | check | floor | reasoning |
> | --- | --- | --- |
> | `constructor` | 79 / 79 | Any failure means a block a pipeline cannot build. There is no acceptable non-zero number. |
> | `smoke` | no regression against `baseline.md` | An absolute floor would gate on blocks whose minimal input nobody has declared yet. |
> | `three_tests` | _____ (owner sets) | 79/79 is not reachable in one step and must not be written in as if it were. |
>
> **What this does not do.** It does not make `requires_inputs` required —
> that is a separate flip, and it cannot happen until authors have filled the
> field, because only they may.
>
> Two tests are **deleted** by this PR:
> `test_the_report_returns_zero_even_when_every_check_fails` and
> `test_the_workflow_does_not_gate_anything`. They exist to stop the
> report-only promise being revoked quietly. This PR revokes it loudly, on
> purpose, which is the only way it was ever meant to go.

---

## 9. Open questions for the owner

Raised on MORNING_LIST with the `Lane 2:` prefix.

1. **`provenance_policy` has no vocabulary.** KERNEL_DEFAULTS §1.2 names the
   field; nothing defines its accepted values. #90 validates it as a
   non-empty string rather than inventing a set. Pinning one is a decision,
   not a task.
2. **The `three_tests` floor.** Someone has to choose a number that is not
   79.
3. **Wave 3's forty blocks** need their authors, and this lane does not know
   who they are.
4. **`FLEET_OPS/BOARD.md` does not exist.** The lane order says to read it
   before each PR; the board of record is `PRODUCTION_ROADMAP.md`. I used
   that, plus the live open-PR list, and both said the same thing: no Cowork
   PR was open. Worth reconciling the two names.
