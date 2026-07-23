# Dataset Audit Report: aviation_faa_core_rag

**Display name:** FAA Aviation Core RAG documents
**Primary role:** RAW_RAG
**Verdict:** `REJECT`
**Score:** 79/100

## Hard failures
- **unknown_licence** (licence_review.json): Unknown (no local licence file)
- **unknown_licence** (licence_issues.json): No LICENSE, LICENCE or README file exists. Source material is U.S. government work, but no local licence text records the rights.

## Licence
- Licence: Unknown (no local licence file)
- Commercial use: unknown
- Redistribution: unknown

## Quality metrics
- Exact duplicate rate: 0.0000
- Near duplicate rate: 0.0000
- Synthetic status: none
- PII status: none

## Score breakdown
- authority: 20
- product_relevance: 15
- licence_clarity: 8
- provenance: 6
- coverage_contribution: 8
- currency_versioning: 8
- chunk_quality: 5
- content_integrity: 5
- operational_efficiency: 4

## Approved / excluded components
**Approved:**
- Documents if local public-domain licence file is added
**Excluded:**
- Current package (no local licence file)

## Reason
Hard rejection gates triggered: unknown_licence. Weak scoring dimensions: chunk_quality, content_integrity, operational_efficiency.

## Evidence paths
- `datasets/aviation_faa_core_rag/provenance.json`
- `datasets/aviation_faa_core_rag/licence_review.json`
- `datasets/aviation_faa_core_rag/domain_mapping.json`
- `datasets/aviation_faa_core_rag/quality_metrics.json`
- `datasets/aviation_faa_core_rag/privacy_review.json`
- `datasets/aviation_faa_core_rag/chunkability_report.json`
- `datasets/aviation_faa_core_rag/evaluation_report.json`