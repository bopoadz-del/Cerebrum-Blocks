# Dataset Audit Report: medical_clinical_guidelines

**Display name:** Clinical Guidelines (Meditron subset)
**Primary role:** RAW_RAG
**Verdict:** `REJECT`
**Score:** 79/100

## Hard failures
- **unknown_licence** (licence_review.json): Common Crawl Foundation Terms of Use: commercial and redistribution rights unclear

## Licence
- Licence: Common Crawl Foundation Terms of Use
- Commercial use: unknown
- Redistribution: unknown

## Quality metrics
- Exact duplicate rate: 0.0000
- Near duplicate rate: 0.0000
- Synthetic status: none
- PII status: none

## Score breakdown
- authority: 16
- product_relevance: 15
- licence_clarity: 8
- provenance: 9
- coverage_contribution: 10
- currency_versioning: 8
- chunk_quality: 7
- content_integrity: 2
- operational_efficiency: 4

## Approved / excluded components
**Approved:**
**Excluded:**
- Entire dataset (unknown redistribution rights under Common Crawl ToU)

## Reason
Hard rejection gates triggered: unknown_licence. Weak scoring dimensions: content_integrity, operational_efficiency.

## Evidence paths
- `datasets/medical_clinical_guidelines/provenance.json`
- `datasets/medical_clinical_guidelines/licence_review.json`
- `datasets/medical_clinical_guidelines/domain_mapping.json`
- `datasets/medical_clinical_guidelines/quality_metrics.json`
- `datasets/medical_clinical_guidelines/privacy_review.json`
- `datasets/medical_clinical_guidelines/chunkability_report.json`
- `datasets/medical_clinical_guidelines/evaluation_report.json`