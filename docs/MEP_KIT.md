# MEP Coordination kit

Canonical kit documentation lives at
[`block_store/kits/mep_coordination/docs/MEP_KIT.md`](../block_store/kits/mep_coordination/docs/MEP_KIT.md).
This file exists so `docs/MEP_KIT.md` is a stable house path; do not fork the
spec here.

## Joint filter — PROVISIONAL

**Status: PROVISIONAL.** Calibrated on **two fixtures with no port data**.
When the owner's real model lands, the watcher's first row **must** include
a re-calibration table **before any verdict**.

| | fraction of smaller element |
|---|---|
| 24 joints (`Infra-Plumbing.ifc`) | **< 10⁻⁶** |
| 1 constructed pipe-through-pipe crossing | **0.0844** |

The empty band is about **84,000×**. The working threshold
(`TOUCH_VOLUME_FRACTION = 1e-4`) sits inside that gap. It is not a settled
fact about a real building.

The watcher on `fixtures/owner_models/` is **armed**. On the first real IFC
it files a battery-format row (hard / clearance / joints / resolve rate /
escalated, per zone) so The Level can grade later.
