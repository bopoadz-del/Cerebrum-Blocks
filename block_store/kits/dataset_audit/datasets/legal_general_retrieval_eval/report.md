# Dataset Audit Report: legal_general_retrieval_eval

**Display name:** LegalBench-RAG
**Primary role:** RETRIEVAL_EVAL
**Verdict:** `APPROVE_GOLDEN_EVAL`
**Score:** 90/100

## Hard failures
None.

## Licence
- Licence: MIT
- Commercial use: permitted
- Redistribution: permitted

## Quality metrics
- Exact duplicate rate: 0.0005
- Near duplicate rate: 0.0200
- Synthetic status: none
- PII status: none

## Score breakdown
- exact_mapping: 25
- verified_answer: 13
- matching_raw_corpus: 12
- product_relevance: 15
- difficulty_coverage: 9
- negative_cases: 3
- low_duplication: 4
- split_separation: 5
- jurisdiction_version: 4

## Approved / excluded components
**Approved:**
- Whole dataset as classified
**Excluded:**

## Required raw sources
- contractnli
- cuad
- maud
- privacy_qa

## Reason
Evaluation score 90/100 maps to APPROVE_GOLDEN_EVAL. Weak scoring dimensions: negative_cases, low_duplication, split_separation, jurisdiction_version.

## Evidence paths
- `datasets/legal_general_retrieval_eval/provenance.json`
- `datasets/legal_general_retrieval_eval/licence_review.json`
- `datasets/legal_general_retrieval_eval/domain_mapping.json`
- `datasets/legal_general_retrieval_eval/quality_metrics.json`
- `datasets/legal_general_retrieval_eval/privacy_review.json`
- `datasets/legal_general_retrieval_eval/chunkability_report.json`
- `datasets/legal_general_retrieval_eval/evaluation_report.json`