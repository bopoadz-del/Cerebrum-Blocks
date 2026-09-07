# Owner-model drop folder — watcher armed

This folder is the live intake for the owner's IFC export. The watcher is
**armed**. There is no disarm flag and no second switch.

```
python bundle/run_owner_models.py
```

from `block_store/kits/mep_coordination/`.

## What happens on the first real IFC

1. **Re-calibration table first.** The joint threshold is PROVISIONAL
   (24+1 set, 10⁻⁶ vs 0.0844, band ~84,000×, two fixtures, no port data).
   The first row states that model's own distributions **before any verdict**.
   If the empty band has closed, the verdict is withheld.
2. **Battery-format row** written to `acceptance_out/BATTERY_ROWS.json` so
   The Level can grade later. Per zone: `hard` / `clearance` / `joints` /
   `resolve_rate` / `escalated`.
3. Clone + BCF package only when the verdict is not withheld.

## What to drop

- **Accepted:** `.ifc` (IFC4 or IFC2X3).
- **Owner-gated:** `.nwd` / `.nwc` / `.rvt` — one log line, then skip.
  Export from Navisworks/Revit as IFC (File > Export > IFC) and drop that.

Client model files are gitignored. This README is not.
