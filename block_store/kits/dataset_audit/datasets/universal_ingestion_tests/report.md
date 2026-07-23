# Dataset Audit Report: universal_ingestion_tests

**Display name:** Universal Ingestion Tests
**Primary role:** OPERATIONAL_DEMO_DATA
**Verdict:** `REJECT`
**Score:** 0/100

## Hard failures
- **unknown_licence** (licence_review.json): Unknown (no local licence file)
- **unknown_licence** (licence_issues.json): No LICENSE, LICENCE or README file exists; reuse terms are unstated.

## Licence
- Licence: Unknown (no local licence file)
- Commercial use: unknown
- Redistribution: unknown

## Quality metrics
- Exact duplicate rate: 0.0000
- Near duplicate rate: 0.0455
- Synthetic status: none
- PII status: none

## Score breakdown

## Approved / excluded components
**Approved:**
**Excluded:**
- Entire dataset (no licence file; reuse terms unstated)

## Reason
Hard rejection gates triggered: unknown_licence.

## Evidence paths
- `datasets/universal_ingestion_tests/provenance.json`
- `datasets/universal_ingestion_tests/licence_review.json`
- `datasets/universal_ingestion_tests/domain_mapping.json`
- `datasets/universal_ingestion_tests/quality_metrics.json`
- `datasets/universal_ingestion_tests/privacy_review.json`
- `datasets/universal_ingestion_tests/chunkability_report.json`
- `datasets/universal_ingestion_tests/evaluation_report.json`