# Dataset Audit Report: legal_australia_victoria_criminal

**Display name:** Legal RAG Bench
**Primary role:** RETRIEVAL_EVAL
**Verdict:** `REJECT`
**Score:** 90/100

## Hard failures
- **commercial_use_prohibited** (licence_review.json): CC BY-NC-SA 4.0 (header) / CC BY-NC 4.0 (body)
- **commercial_use_prohibited** (licence_issues.json): Licence is CC BY-NC-SA 4.0 (header) / CC BY-NC 4.0 (body); both versions prohibit commercial use.
- **conflicting_terms** (licence_issues.json): Dataset card header says cc-by-nc-sa-4.0 while the licence section says CC BY-NC 4.0, creating an inconsistent share-alike requirement.

## Licence
- Licence: CC BY-NC-SA 4.0 (header) / CC BY-NC 4.0 (body)
- Commercial use: prohibited
- Redistribution: permitted

## Quality metrics
- Exact duplicate rate: 0.0000
- Near duplicate rate: 0.0000
- Synthetic status: none
- PII status: none

## Score breakdown
- exact_mapping: 25
- verified_answer: 13
- matching_raw_corpus: 12
- product_relevance: 15
- difficulty_coverage: 8
- negative_cases: 3
- low_duplication: 5
- split_separation: 5
- jurisdiction_version: 4

## Approved / excluded components
**Approved:**
**Excluded:**
- Entire dataset (CC BY-NC prohibits commercial use; conflicting licence terms)

## Required raw sources
- corpus.jsonl

## Reason
Hard rejection gates triggered: commercial_use_prohibited, conflicting_terms. Weak scoring dimensions: negative_cases, low_duplication, split_separation, jurisdiction_version.

## Evidence paths
- `datasets/legal_australia_victoria_criminal/provenance.json`
- `datasets/legal_australia_victoria_criminal/licence_review.json`
- `datasets/legal_australia_victoria_criminal/domain_mapping.json`
- `datasets/legal_australia_victoria_criminal/quality_metrics.json`
- `datasets/legal_australia_victoria_criminal/privacy_review.json`
- `datasets/legal_australia_victoria_criminal/chunkability_report.json`
- `datasets/legal_australia_victoria_criminal/evaluation_report.json`