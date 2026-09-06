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

---

# ADDENDUM — 2026-09-06, items 1–5

## 1. Resolver: fixed distance replaced with a ranked search

`candidate_moves()` now searches **distance × direction**: four distances from
`gap+margin` to `3×` that, across the free axes both signs **plus the in-plane
diagonals** — 72 candidates for a free service, 32 for a gravity run (still no
vertical). Ordered smallest-displacement-first, so the least invasive move that
passes every monitor wins, and a larger move is only ever chosen because the
smaller ones were actually rejected.

Diagonals earn their place: a pure X or Y move walks a pipe into the neighbouring
run, while a diagonal slips it into the gap between two.

### Resolve rate per zone — the exit criterion

Five most-congested zones on Schependomlaan, batch-verified, 35.8 s:

| zone | clashes | sourced | escalated | batch | outcome |
|---|---|---|---|---|---|
| 00 begane grond\|2_0 | 8 | 8 | 0 | accepted | **cleared** |
| 00 begane grond\|1_0 | 8 | 8 | 0 | accepted | **cleared** |
| 00 begane grond\|3_1 | 8 | 8 | 0 | accepted | **cleared** |
| 00 begane grond\|0_1 | 8 | 8 | 0 | accepted | **cleared** |
| 02 tweede verdieping\|3_0 | 8 | 8 | 0 | accepted | **cleared** |

**5 of 5 cleared** against a bar of 3 of 5. **Silently unresolved: 0** — every
zone lands in cleared, escalated-with-alternatives, or batch-rejected. Original
model hash unchanged.

This closes **F4**. The previous ~20% was a fixed distance being blocked on the
first free axis in a congested ceiling; one distance is not a search.

## 2. Batch verification — moves judged as a set

`verify_batch()` applies a zone's proposals **together**, re-judges the whole
zone, and if the batch introduces any new hard clash or violation it **fails as
a unit and rolls back**, leaving the zone byte-for-byte as found. Partial
acceptance is deliberately not offered: "three of these five are fine" is how a
model drifts into a state nobody verified.

Pinned by `test_two_individually_safe_moves_that_collide_reject_the_whole_batch`
— two 200 mm services 1 m apart, one moving +500 mm and one −500 mm. Each is
clear of everything it was checked against; together they meet in the middle.

## 3. Identity normalisation

`identity.py` holds the single `element_key` / `pair_key` / `clash_id`.
`test_cross_block_integration.py` runs **B1 → B3 → B4 → B7** on constructed
geometry in CI and asserts a **non-zero** score, with a failure message naming id
drift as the cause. The "green units, silent zero" class now has a permanent
test. All three derivations are pinned byte-identical.

## 4. Fixture provenance

`README.md` records the archived source, the path, and
sha256 `2c3565ca1904f2aa61adab92024cf3755b2c5b21a498144d3094d7cb58cebec7`,
with the reason the archived repo is used: both the order's URL and the live
repo's own README point at paths that 404.

## 5. Second fixture — `Infra-Plumbing.ifc`

| fixture | MB | elements | MEP | admitted | hard | clearance | false pos. eliminated | runtime |
|---|---|---|---|---|---|---|---|---|
| schependomlaan_design | 47 | 1,437 | 73 | 700 | 14 | 399 | **287** | 56 s |
| Infra-Plumbing | 0.35 | 26 | 26 | 48 | **48** | 0 | **0** | 4.8 s |

**This row is unflattering and it is filed as measured.** Every one of the 48
admitted pairs reads as a hard clash and none is a false positive — because the
model is single-discipline and its pipe segments are *connected*. Segments that
join genuinely interpenetrate; that is assembly, not conflict.

The workflow-noise filter misses them: it requires a fitting name hint
(`bend`, `tee`, `elbow`), and these are plain `IfcFlowSegment` with no such
name. **NEW OPEN ITEM F5:** same-system segment-to-segment contact should be
classified workflow noise on topology (a shared connection), not on the name.
Recorded rather than tuned away, because a filter that hides real clashes to
flatter a number is the failure this kit exists to remove.

It also confirms the earlier judgement that these conformance scenes cannot
substitute for a coordination model: with one discipline, a cross-system clash
is impossible by construction.

## Owner models — still blocked, now drop-and-go

Navisworks is **not installed on this machine**, and `.nwd` is a closed format
with no library and no converter, so the export cannot be automated from here.
Everything downstream of it is ready:

    fixtures/owner_models/          drop the exported .ifc here (gitignored)
    fixtures/owner_models/README.md the export steps
    bundle/run_owner_models.py      auto-detects and runs the full pipeline

A model exporting with zero MEP elements is reported as such and skipped, not
processed into an empty report.

## Receipt (addendum)

| | |
|---|---|
| tests | **112 passed**, 0 failed |
| resolve rate | **5/5 zones cleared**, 0 silently unresolved |
| open items | **F5** only (F4 closed) |

---

# ADDENDUM 2 — F5 closed by topology, 2026-09-06

## The finding that shaped the fix

**Neither fixture carries any port data at all.** Verified before writing code:

    Infra-Plumbing.ifc (IFC4)      IfcRelConnectsPorts 0  IfcDistributionPort 0  IfcRelNests 0
    schependomlaan_design (IFC2X3) IfcRelConnectsPorts 0  IfcDistributionPort 0  IfcRelNests 0

So the specified signal exists in neither model. The port graph is still built —
it is the correct answer and real IFC4 exports usually carry it, and where the
model speaks it **outranks any measurement**. But it cannot be the only signal,
or every joint in a model that omits ports is reported as a clash.

## The second signal, and why it is not proximity

Two solids that **touch** share a surface and enclose no meaningful common
volume. Two solids that **conflict** enclose real volume. That is exact
geometry, not nearness.

Calibrated rather than chosen, on the 24 touching pairs in the fixture and a
constructed pipe-through-pipe crossing:

| | shared volume | as fraction of the smaller element |
|---|---|---|
| joints (24 real pairs) | 4.2e-17 … 1.6e-8 m³ | **< 1e-6** |
| real crossing | 5.2e-3 m³ | **0.0844** |

The band between them is empty by five orders of magnitude — a real conflict is
**84,000×** the joint ceiling. The threshold sits inside that gap.

**Absolute volume was tried first and rejected.** A 1e-9 floor excluded only 3
of 24 joints, because triangulated cylinders that merely touch still enclose a
faceting volume that scales with diameter. A fraction is scale-invariant: it
means the same thing for a 50 mm pipe and a 2 m culvert.

The fallback is deliberately narrow — same system, exact backend present, and a
measurable volume. **A cross-system contact is never a joint, whatever the
volume.**

## The discriminating test

One test, both assertions, so passing the first by breaking the second fails CI:

* two same-system pipes meeting **end to end** → excluded, `connected_joint`
* a pipe driven **through** another, same system, no port link → **still hard**,
  with a failure message saying the filter has been relaxed until it hides real
  clashes

Plus a mutation probe: widening the floor to something a person might call
"small" excuses a 2-litre overlap, and the probe asserts it.

## Fixture rows, re-filed

| fixture | MB | elements | MEP | ports | admitted | **joints** | **hard** | clearance | false pos. eliminated | queued |
|---|---|---|---|---|---|---|---|---|---|---|
| Infra-Plumbing | 0.35 | 26 | 26 | 0 | 48 | **48** | **0** | 0 | 0 | 0 |
| schependomlaan_design | 47 | 1,437 | 73 | 0 | 700 | **5** | **9** | 399 | **287** | 371 |

Fixture 2 meets the exit criterion exactly: **48 joint pairs → 0 hard clashes.**
On the real model the filter is appropriately quiet — 5 genuine joints removed,
every one of the 399 clearance findings and 287 false-positive eliminations
untouched. A filter that had "improved" the real model's numbers would have been
the warning sign.

**F5 CLOSED.**

## Speckle — not needed

Asked and answered: the IFC path already produces the change set, the clone and
BCF issues that open in BIMcollab or Solibri, and version_diff works on two IFC
exports without it. Speckle earns its place when several people need to review
proposals in a shared space with history. No token required.

## Owner models — honest refusal, not a stub

Navisworks is not installed here and `.nwd` has no library or converter, so the
export cannot be automated from this machine. The path is a real, tested refusal
carrying the export instruction — not a placeholder, which CI forbids. Drop an
exported `.ifc` into `fixtures/owner_models/` and `run_owner_models.py` runs the
full pipeline and posts its row; an export containing zero MEP is reported and
skipped rather than processed into an empty report.

| | |
|---|---|
| tests | **119 passed**, 0 failed |
| open items | **none** |
