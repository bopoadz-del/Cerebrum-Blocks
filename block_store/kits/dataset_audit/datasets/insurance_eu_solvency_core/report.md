# Dataset Audit Report: insurance_eu_solvency_core

**Display name:** EIOPA Solvency II Single Rulebook
**Primary role:** RAW_RAG
**Verdict:** `APPROVE_CORE_RAG`
**Score:** 86/100

## Hard failures
None.

## Licence
- Licence: EIOPA Legal Notice (reuse authorised with attribution)
- Commercial use: permitted
- Redistribution: permitted

## Quality metrics
- Exact duplicate rate: 0.0000
- Near duplicate rate: 0.0000
- Synthetic status: none
- PII status: none

## Score breakdown
- authority: 20
- product_relevance: 15
- licence_clarity: 12
- provenance: 9
- coverage_contribution: 6
- currency_versioning: 8
- chunk_quality: 7
- content_integrity: 5
- operational_efficiency: 4

## Approved / excluded components
**Approved:**
- Whole dataset as classified
**Excluded:**

## Reason
Raw RAG score 86/100 maps to APPROVE_CORE_RAG. Weak scoring dimensions: content_integrity, operational_efficiency.

## Evidence paths
- `datasets/insurance_eu_solvency_core/provenance.json`
- `datasets/insurance_eu_solvency_core/licence_review.json`
- `datasets/insurance_eu_solvency_core/domain_mapping.json`
- `datasets/insurance_eu_solvency_core/quality_metrics.json`
- `datasets/insurance_eu_solvency_core/privacy_review.json`
- `datasets/insurance_eu_solvency_core/chunkability_report.json`
- `datasets/insurance_eu_solvency_core/evaluation_report.json`