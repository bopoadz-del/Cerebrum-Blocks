# Dataset Audit Report: aviation_faa_eval

**Display name:** FAA Aviation Training Dataset
**Primary role:** RETRIEVAL_EVAL
**Verdict:** `APPROVE_EVAL_CANDIDATE`
**Score:** 73/100

## Hard failures
None.

## Licence
- Licence: Apache 2.0
- Commercial use: permitted
- Redistribution: permitted

## Quality metrics
- Exact duplicate rate: 0.0000
- Near duplicate rate: 0.0000
- Synthetic status: majority
- PII status: none

## Score breakdown
- exact_mapping: 10
- verified_answer: 13
- matching_raw_corpus: 10
- product_relevance: 15
- difficulty_coverage: 8
- negative_cases: 3
- low_duplication: 5
- split_separation: 5
- jurisdiction_version: 4

## Approved / excluded components
**Approved:**
- Whole dataset as classified
**Excluded:**

## Required raw sources
- aviation_faa_core_rag/ (AIM PDF, CFR XML parts 61/91/121/135)

## Reason
Evaluation score 73/100 maps to APPROVE_EVAL_CANDIDATE. Weak scoring dimensions: negative_cases, low_duplication, split_separation, jurisdiction_version.

## Evidence paths
- `datasets/aviation_faa_eval/provenance.json`
- `datasets/aviation_faa_eval/licence_review.json`
- `datasets/aviation_faa_eval/domain_mapping.json`
- `datasets/aviation_faa_eval/quality_metrics.json`
- `datasets/aviation_faa_eval/privacy_review.json`
- `datasets/aviation_faa_eval/chunkability_report.json`
- `datasets/aviation_faa_eval/evaluation_report.json`