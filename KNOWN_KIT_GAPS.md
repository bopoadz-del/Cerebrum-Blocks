# Known kit composition gaps

Registered findings from `scripts/audit_kit_composition.py`. A gap listed
here does not block CI. It is still a gap — registration makes it countable
and dated, not acceptable.

Format matches `KNOWN_INCOMPLETE.md`: `- <kit> :: <code>  <note>`.

## Why these are registered rather than fixed

Every domain kit below declares its blocks and says nothing about how they
compose. That is the finding the audit exists to surface: **silence is not
permission.** A kit with six blocks and no `flow` is not a kit whose steps
may run in any order — it is a kit whose ordering was never written down,
and the two are indistinguishable to anything that reads the manifest.

They are registered rather than fixed in one sweep because the ordering is
domain knowledge, not a mechanical edit. Guessing a `flow` and committing it
would convert an honest blank into a confident wrong answer, which is the
failure mode this repo is built to avoid. Each is authored when its domain
is next touched, or by the kit pipeline that generates `flow`-complete kits
going forward.

`universal_kernel` is the worked example and is NOT registered: it declares
`waves` covering all 24 of its blocks, in agreement with its `blocks` list.

Registered 2026-08-24.

- agriculture :: no_composition  6 blocks; flow unauthored
- automotive :: no_composition  6 blocks; flow unauthored
- aviation :: no_composition  6 blocks; flow unauthored
- construction :: no_composition  18 blocks; largest kit, flow unauthored
- education :: no_composition  6 blocks; flow unauthored
- finance :: no_composition  6 blocks; flow unauthored
- finance_ops :: no_composition  11 blocks; flow unauthored
- hotel_management :: no_composition  6 blocks; flow unauthored
- hr :: no_composition  6 blocks; flow unauthored
- insurance :: no_composition  15 blocks; flow unauthored
- legal :: no_composition  6 blocks; flow unauthored
- manufacturing :: no_composition  6 blocks; flow unauthored
- medical :: no_composition  6 blocks; flow unauthored
- oil_gas :: no_composition  6 blocks; flow unauthored
- pharma :: no_composition  6 blocks; flow unauthored
- real_estate :: no_composition  6 blocks; flow unauthored
- retail :: no_composition  6 blocks; flow unauthored
- supply_chain :: no_composition  6 blocks; flow unauthored

## Provenance gaps

An encoded rate, threshold or limit with no recorded origin is not
"probably fine" — it is a number nobody can check. These files carry
figures whose source was never written down.

They are registered rather than filled in because **I cannot supply a
provenance I do not have.** Writing `"kind": "regulator"` above rates whose
origin is unknown would be worse than the blank: it would make an unchecked
number look checked, which is the exact failure this field exists to
prevent. Each needs its actual source recorded by whoever knows it.

`gn16_ruleset.json` is the worked example and is NOT registered: all 12 of
its rules carry a `citation` naming the HKIA GL16/GN16 section they came
from. `hkia_gn16_corpus.json` and `construction_kb.json` likewise cite per
entry.

Registered 2026-08-24.

- insurance :: data_provenance_missing  6 files: commission_formulas, routing_sops, retention_playbook, incentive_playbook, sample_bordereaux, hierarchy_model. commission_formulas.json is the priority — it holds live commission rates (0.5–1.2 of annualized premium) consumed by agency_commission_engine.
- construction :: data_provenance_missing  app/data/procedures/procedures_db.json
- automotive :: data_provenance_missing  source_manifest.json
- automotive :: data_file_missing  manifest declares "evaluation/", which is not on disk
