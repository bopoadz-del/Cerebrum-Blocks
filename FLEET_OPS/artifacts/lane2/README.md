# Lane 2 artifacts

Evidence for the block-contract lane (`FLEET_OPS/LANE2_KERNEL_DEFAULTS.md`,
spec of record `FLEET_OPS/KERNEL_DEFAULTS.md`, both on Drive).

**Why these live in the repo rather than only on Drive.** The lane's fence is
"every change via PR, green CI, no bypass". Evidence that lands in a PR is
reviewable next to the code it describes and is versioned with it; a file
uploaded to Drive is neither. Copies can be taken to Drive at any time, but
the repo holds the one a reviewer can check against the commit that produced
it.

| file | what it is |
| --- | --- |
| `baseline.md` | Non-conformer counts at the moment the report-only checks landed. Regenerated from CI, never hand-edited. |
| `MIGRATION_PLAN.md` | L2.6 — which blocks move to `BlockResult`, in what order, after P7. Plan only. |

Regenerate the baseline with:

```
python scripts/lane2_conformance.py --baseline FLEET_OPS/artifacts/lane2/baseline.md
```

Read the numbers from a CI run. A local run on a machine missing a block's
dependency reports import failures that are not defects.
