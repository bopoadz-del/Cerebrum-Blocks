# Dataset Audit Report: financeops_demo_fixtures

**Display name:** FinanceOps Demo Fixtures
**Primary role:** OPERATIONAL_DEMO_DATA
**Verdict:** `REJECT`
**Score:** 0/100

## Hard failures
- **unknown_licence** (licence_review.json): Unknown (no local licence file)
- **unknown_licence** (licence_issues.json): No LICENSE, LICENCE or README file exists; reuse terms are unstated.
- **pii_detected** (privacy_review.json): Demo users.json contains synthetic but realistic PII: names, email addresses, ages, and account metadata. transactions.json links to account IDs. Recommend redaction or replacement with clearly synthetic placeholders before any public release.
- **pii_detected** (privacy_issues.json): Demo users.json contains synthetic but realistic PII: names, email addresses, ages, and account metadata. transactions.json links to account IDs. Recommend redaction or replacement with clearly synthetic placeholders before any public release.

## Licence
- Licence: Unknown (no local licence file)
- Commercial use: unknown
- Redistribution: unknown

## Quality metrics
- Exact duplicate rate: 0.0000
- Near duplicate rate: 0.0000
- Synthetic status: none
- PII status: detected

## Score breakdown

## Approved / excluded components
**Approved:**
- Schema definitions after PII redaction
**Excluded:**
- users.json (synthetic PII)
- transactions.json (links to PII)

## Reason
Hard rejection gates triggered: unknown_licence, pii_detected.

## Evidence paths
- `datasets/financeops_demo_fixtures/provenance.json`
- `datasets/financeops_demo_fixtures/licence_review.json`
- `datasets/financeops_demo_fixtures/domain_mapping.json`
- `datasets/financeops_demo_fixtures/quality_metrics.json`
- `datasets/financeops_demo_fixtures/privacy_review.json`
- `datasets/financeops_demo_fixtures/chunkability_report.json`
- `datasets/financeops_demo_fixtures/evaluation_report.json`