# Dataset Audit Report: medical_pubmedqa_eval

**Display name:** PubMedQA
**Primary role:** RETRIEVAL_EVAL
**Verdict:** `APPROVE_EVAL_CANDIDATE`
**Score:** 73/100

## Hard failures
None.

## Licence
- Licence: MIT
- Commercial use: permitted
- Redistribution: permitted

## Quality metrics
- Exact duplicate rate: 0.0000
- Near duplicate rate: 0.0000
- Synthetic status: none
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
- ori_pqal.json (questions, contexts, labels)
- PubMed abstracts corresponding to PMIDs

## Reason
Evaluation score 73/100 maps to APPROVE_EVAL_CANDIDATE. Weak scoring dimensions: negative_cases, low_duplication, split_separation, jurisdiction_version.

## Evidence paths
- `datasets/medical_pubmedqa_eval/provenance.json`
- `datasets/medical_pubmedqa_eval/licence_review.json`
- `datasets/medical_pubmedqa_eval/domain_mapping.json`
- `datasets/medical_pubmedqa_eval/quality_metrics.json`
- `datasets/medical_pubmedqa_eval/privacy_review.json`
- `datasets/medical_pubmedqa_eval/chunkability_report.json`
- `datasets/medical_pubmedqa_eval/evaluation_report.json`