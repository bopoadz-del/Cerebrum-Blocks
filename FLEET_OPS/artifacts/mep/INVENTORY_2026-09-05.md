# ORDER K-MEP — STEP 0 INVENTORY
**Date:** 2026-09-05 · **Lane:** mep_coordination (Cerebrum-Blocks) · **Status:** PAUSED, build not started

Every line below was produced by RUNNING the thing, not reading it. Commands and
raw output are quoted. Where something could not be proven, it is recorded as
MISSING, per the order's own rule: unknown = missing, never assume.

---

## 0. Order preconditions — two are not met

| Item | Status | Proof |
|---|---|---|
| `FLEET_OPS/PROMPT_STANDARD_v2.md` | **MISSING** | `find . -name PROMPT_STANDARD_v2.md` across The_Fork, Cerebrum-Blocks, The_Level, CerebrumDev.ai, Cerebrum → no match. `FLEET_OPS/` exists in Cerebrum-Blocks and The_Level but contains only `artifacts/`. |
| Rails R8 / R9 / R10 | **MISSING** | `grep -rn "R8\|R9\|R10" --include=*.md` → no rail definitions anywhere. |
| Lane 2 "restored" clash functions | **MISSING** (see §1) | The order states these were restored. They do not exist. |

I proceeded with STEP 0 because the order is self-describing. **I did not invent
what the standard or the rails say.** If they govern the build, they must be
supplied before build opens.

---

## 1. The four named functions — ALL MISSING

The order says these were "restored by Lane 2 — confirm present and callable".

```
$ for f in _detect_model_clashes _categorize_clash_severity \
           _suggest_clash_resolution _parse_ifc_geometries; do
    grep -rn "def $f" --include=*.py .
  done
  _detect_model_clashes          NOT FOUND ANYWHERE
  _categorize_clash_severity     NOT FOUND ANYWHERE
  _suggest_clash_resolution      NOT FOUND ANYWHERE
  _parse_ifc_geometries          NOT FOUND ANYWHERE
```

Searched The_Fork **and** Cerebrum-Blocks. Zero hits by either name or import.

**This does not mean clash detection is absent.** Equivalent capability exists
under different names (§3). The premise "Lane 2 restored these" is what is false.

---

## 2. IFC extractor — EXISTS + WORKS

```
$ python -c "... BIMExtractorBlock().process({'file_path':'tests/fixtures/sample_office.ifc'})"
  status: success | elements: 27
  mapped IFC types: 24
  categories: windows, doors, slabs, spaces, terminals, pipes, walls, beams, columns, storeys
```

* IfcOpenShell **0.8.5** — pinned in `requirements.txt:151`, imports locally.
* **24** mapped IFC types in `IFC_CATEGORY_MAP` — matches the order's claim exactly.
* `.rvt` / `.nwd` / `.nwc` return an actionable export-to-IFC instruction, not a
  vague failure. That behaviour is correct and must be preserved (FORBIDDEN list).

## 3. Bounding-box clash detector — EXISTS + WORKS

Real names: `_basic_clash_report` → `_geometric_clash_report`, with
`_name_duplicate_clash_fallback` when `ifcopenshell.geom` is unavailable.
Trigger is `run_clash_detection`, **not** `clash_detection` (my first call
returned `{}` silently — worth knowing before wiring the hat).

```
$ ... .process({'file_path': 'tests/fixtures/sample_office.ifc'}, {'run_clash_detection': True})
  clash_count : 1
  sample      : {"type": "aabb_overlap", "category_a": "walls", "category_b": "pipes",
                 "ifc_type_a": "IfcWall", "ifc_type_b": "IfcPipeSegment",
                 "name_a": "Wall-GF-E", "name_b": "Pipe-Storm-001", ...}
  keys        : clash_count, clashes, detection_method, detection_method_disclaimer,
                tolerance_mm, elements_analyzed, elements_without_geometry,
                pair_cap_reached, timed_out, note
```

Same-category overlaps are deliberately skipped (adjacent walls, stacked slabs).
Caps and a timeout are already implemented (`pair_cap_reached`, `timed_out`).

**Disclosure text — EXISTS, verbatim:**

> basic (bounding-box — not geometric intersection. Verify critical clashes in
> Navisworks Clash Detective or Solibri)

This is honest and must survive as the pre-filter's label when block 1 replaces it.

## 4. The two BIM blocks

| Block | Status | Proof |
|---|---|---|
| `bim_extractor` | **EXISTS + WORKS** | `bim_extractor v1.2.0 layer=3`, instantiates bare, runs (§2). |
| `bim` (`BIMBlock`) | **EXISTS, different contract** | `__init__(self, hal_block, config)` — a HAL-mounted block, cannot instantiate bare. Not a stub; a different construction path. Reports `IFC parsing: ENABLED (ifcopenshell 0.8.5)` at init. |

## 5. "BIM clash tolerance" formula — EXISTS + WORKS, but NOT a code rule

```
$ CALCULATORS['bim_clash_tolerance'](lod=200) → clash_tolerance_mm 50.0
                                     (lod=350) → clash_tolerance_mm 12.0
                                     (lod=400) → clash_tolerance_mm  6.0
  standard: "BIM BEP convention (indicative)"
```

Registered among **84** calculators in `app.lib.construction_formulas.CALCULATORS`.
Signature is `(lod: int = 350)` only — no system-pair or diameter input.

**It is a model-tolerance table, not a clearance rule.** Its own `standard` field
says *indicative*. Under the order's test — "a rule without a clause is not a
rule" — this cannot seed block 2.

---

## 6. Rule sources in the knowledge pool — CRITICAL GAP

This is the finding that most affects the build.

```
term                    curated_kb+training   whole RAG
saudi_building_code             13               209
cesmm                           17               872
SBC 501                          1                12
SBC 701                          1                 2
NFPA                             3               714
ASHRAE                           8                88
```

The SBC hits are an **index of part numbers**, not clearance tables:

> `SBC 401 — Electrical. - SBC 501 — Mechanical (including HVAC). - SBC 601 — En…`

Chunks in the knowledge pool containing *clearance* **and** a dimension: **2**.
Both are OSHA construction-safety values (power-line clearance, ladder pitch) —
not MEP service separation.

**Verdict: MISSING.** Block 2 (`clearance_rules`) has no source data. There are no
SBC 501 mechanical, SBC 701 plumbing, NFPA fire-main, or ASHRAE maintenance-access
clearance values in the corpus to cite. Building the rule table as specified would
require inventing values — explicitly FORBIDDEN.

---

## 7. Fixtures — the named sources do not carry a coordination model

**Schependomlaan — MISSING at its documented location.**

```
$ gh api repos/openBIMstandards/DataSetSchependomlaan/contents
  README.md (174 bytes) — "Schependomlaan has moved! Find it at
  buildingSMART/Sample-Test-Files/tree/master/IFC 2x3/Schependomlaan"

$ curl .../contents/IFC%202x3/Schependomlaan  →  404
$ gh api .../git/trees/master                 →  404 (repo default branch is `main`)
```

The forwarding pointer is dead. The dataset is not where either source says.

**buildingSMART Sample-Test-Files — downloads and parses, but inadequate.**

35 IFC files, 15 distinct models. Three are MEP. Downloaded (HTTP 200) and run
through the real extractor:

| Fixture | Size | Elements | Categories | Clashes |
|---|---|---|---|---|
| `Building-Hvac.ifc` | 109 KB | **4** | ducts, terminals, storeys | 0 |
| `Infra-Electrical.ifc` | 117 KB | **2** | footings, terminals | 0 |
| `Infra-Plumbing.ifc` | 343 KB | **24** | pipes only | 0 |
| `Building-Architecture.ifc` | 139 KB | 12 | walls, slabs, roofs, spaces | 7 |

These are **conformance test scenes, not coordination models**. One duct. Two
terminals. Single-discipline files with no cross-system congestion — the plumbing
model contains pipes and nothing else, so a pipe-vs-duct clash is impossible by
construction. All three MEP models produce **zero** clashes.

They are usable for parser and schema regression. They **cannot** exercise
congestion ranking, triage, resolution ordering, or the EXIT criterion
"zero bounding-box false positives in the top-50" — there is no top-50.

Note: `Building-Architecture.ifc` yields **7** clashes across only 12 elements.
Worth investigating as a false-positive sample when block 1 lands.

---

## 8. What STEP 0 concludes

**Ready to build on:** IFC parsing, element extraction, the AABB pre-filter, its
disclosure text, caps/timeouts, proprietary-format guidance, the block/manifest
scaffolding, 84 calculators.

**Two blockers the build cannot proceed through without an owner decision:**

1. **No rule source.** §6. Block 2 is specified as citation-bearing, and there are
   no clauses in the corpus to cite. Options: (a) owner supplies SBC 501/701 and
   the project MEP spec as documents, (b) scope block 2 to project-spec-only rules
   ingested per project, (c) ship rules with an explicit `unsourced` flag and no
   default values — consistent with the resolver's own `unsourced` rule.

2. **No congested fixture.** §7. Options: (a) owner supplies one real model
   (OWNER-GATED), (b) I locate and verify another public dataset before build,
   (c) build a synthetic congested corridor as a declared fixture — it would be a
   *constructed* fixture, not an invented one, and must be labelled as such.

**Also to settle:** `PROMPT_STANDARD_v2.md` and rails R8/R9/R10 (§0), and the fact
that the four named functions never existed (§1) — which suggests the Lane 2
report that claimed them should itself be re-checked.

---

## PAUSE

Build does not open until the owner rules on §8. Nothing has been written to any
kit, no code exists, no PR is open.

Verified-by-running receipts for every claim above are reproducible with the
commands quoted inline.
