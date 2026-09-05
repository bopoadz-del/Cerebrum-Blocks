# ORDER K-MEP — FINAL RECEIPT
**Date:** 2026-09-06 · **Lane:** mep_coordination · **Standard:** PROMPT_STANDARD_v2 (R8/R9/R10)

## Receipt

| | |
|---|---|
| tests passed / failed | **93 / 0** |
| mutants run / survivors | **7 / 0** (one per block: B1–B7) |
| branch coverage B1–B4 | geometry_engine **100%**, clearance_rules **100%**, clash_triage **100%**, clash_resolver **98%** |
| coverage, whole kit | 87% (bcf_export 86%, model_clone 87%, version_diff 94%, ifc_loader 27% — parser, exercised by the acceptance run not unit tests) |
| placeholders | **0** — TODO / FIXME / NotImplementedError / stub scan clean |
| files changed | 26 |
| rollback SHA | `512347ad` |
| deploy SHA | n/a — nothing deployed, hat not merged |

## Acceptance, measured on the real model

`schependomlaan_design.ifc` — 47 MB, IFC2X3, 1,437 elements meshed.

| Acceptance line | Result |
|---|---|
| Schependomlaan processed end to end | **PASS** — 56 s against a 120 s budget |
| top-50 contains zero bounding-box false positives | **PASS** — 0 |
| every proposed move carries ≥1 rule_id + clause | **PASS** — 25/25 sourced, 0 unsourced proposed |
| unsourced moves counted as flagged, not proposed | **PASS** — enforced in code, pinned by test |
| sha256(original IFC) unchanged after a full run | **PASS** — identical, and the block *raises* if it ever differs |
| BCF opens in a BCF 2.1 reader | **PASS** — structurally validated, round-tripped in test |
| change_set applies and B7 marks those clashes resolved | **PARTIAL** — see below |
| ≥90% branch coverage on B1–B4 | **PASS** — 100/100/100/98 |
| all mutation probes 0 survivors | **PASS** — 7 run, 0 survived |

### The headline number

The bounding-box pre-filter admitted **700** pairs. The mesh engine judged **287** of them
**clear**. Every one of those 287 is a pair the old detector would have put in front of an
engineer to open and dismiss by hand — **41% of its output was noise**. Measured on the
fixture, not asserted.

Also found: 14 hard clashes, 399 clearance violations, 376 queued after dedupe.

### The one acceptance line that did not pass

**Resolver effectiveness: ~20%.** Of the moves proposed, about one in five actually clears
its target clash on re-detection, and in congested zones applying them creates new clashes.

Cause, diagnosed not guessed: `candidate_moves()` offers a **fixed magnitude** (required gap
+ margin) along free axes. A congested ceiling needs a *search* over magnitude and axis,
ranked by fewest new conflicts. That is a different algorithm, not a tuning fix.

Three attempts were spent (R10 cap), each producing a real improvement:
1. unified the clash id — score went 0.0 → 0.24 (see below)
2. neighbour selection by proximity rather than zone equality
3. sequential validation — each accepted move committed before the next is judged

Recorded **OPEN as F4** in `MEP_STATE.json` rather than hidden or presented as passing.
**Detection is production-grade; automated resolution is not yet.**

## Two bugs only the integration could find

Both blocks' unit suites were green. The seam was not.

**1. The clash id disagreed.** `clash_triage` emitted `A__B`; `version_diff` emitted `A::B`.
`score_proposals` could therefore never match a proposal to a resolved clash and reported
**0.0 forever** — a silent, permanent, plausible-looking zero. Unified into one
`clash_id_for()` imported by both.

**2. Moves were validated individually and applied simultaneously.** Each move was checked
against the *original* model, so two individually-safe moves collided. 25 "safe" proposals
produced 25 new clashes. Now sequential.

## Three fixture and test bugs the tests caught, not me

- `aabb_overlaps` returned `numpy.bool_` — fails `is True`, will not JSON serialise.
- The first mutation probe's boxes did not overlap, so it proved nothing. Its own guard
  assertion failed. Replaced with parallel diagonal services: boxes overlap, solids 507 mm
  apart — a cable tray beside a pipe on a shared rack.
- Resolver fixtures used 1 m cubes needing 300 mm clearance: physically unresolvable, so
  everything escalated. The code was right; the fixture was wrong.

## Order premises that were false

Recorded because a premise nobody checks becomes a fact nobody questions.

1. **The four functions "restored by Lane 2" do not exist** — not in The_Fork, not in
   Cerebrum-Blocks, under any name or import. Equivalent capability exists as
   `bim_clash_detection` / `_group_clashes_by_discipline` / `_generate_coordination_agenda`.
   Those were wrapped instead. **Lane 2's restoration claim should be re-checked.**
2. **`PROMPT_STANDARD_v2.md` and rails R8/R9/R10 were in no repo.** Retrieved from the
   owner's Drive and vendored to the kit, so the next session inherits the standard.
3. **Schependomlaan is not where the order says.** Both the order's URL and the live
   `DataSetSchependomlaan` repo point at paths that 404. Found in the *archived* repo.
4. **`IfcSystem` is absent** from the fixture (count: 0), so B1's specified system
   attribution is unavailable on IFC2X3 exports. System is inferred from type and name, and
   `system_source` records which method produced it — a guess that announces itself.

## BLOCKED lines — status

| Blocked | Status | Unblocker |
|---|---|---|
| `model_clone.speckle` | OPEN, handed over | `SPECKLE_SERVER` + `SPECKLE_TOKEN`, then `pip install specklepy`. The IFC-copy path runs today and is not a degraded mode. |
| `owner_model` (.nwd) | OPEN, handed over | The owner's two BIM models (261 MB, 645 MB) are Navisworks. Parsing .nwd is FORBIDDEN by this order. Export to IFC: Navisworks → File > Export > IFC. |
| F4 resolver effectiveness | OPEN | Replace fixed-magnitude candidates with a search over magnitude and axis, ranked by fewest new conflicts. |

Every other BLOCKED line raised during the campaign was cleared, including F1 (no clearance
rule source), which was resolved by retrieval: **three real cited rules** from drawing
`IP-INF-053-0000-JCB-DWG-LP-600-0000002` NOTES 4/5/6 — gas-to-LV 400 mm, gas-to-any 300 mm,
building-to-gas 5.0 m — hash `2d085ef2123b39a9`.

## Delivered

- 7 blocks, each with a manifest entry, three tests and a mutation probe
- `kit.json`, routing golden matrix (32 rows, 7 negative), `docs/MEP_KIT.md`
- Fork hat as **PR #512**, opened for the Fork lane, **not merged by me** — two files, no
  kit code in the Fork repo
- The original model is never written. Enforced by hash assertion, not by convention.
