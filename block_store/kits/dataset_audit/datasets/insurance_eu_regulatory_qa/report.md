# Dataset Audit Report: insurance_eu_regulatory_qa

**Display name:** EIOPA Questions and Answers on regulation
**Primary role:** RETRIEVAL_EVAL
**Verdict:** `QUESTION_POOL_ONLY`
**Score:** 66/100

## Hard failures
None.

## Licence
- Licence: EIOPA Legal Notice (reuse authorised with attribution)
- Commercial use: permitted
- Redistribution: permitted

## Quality metrics
- Exact duplicate rate: 0.0531
- Near duplicate rate: 0.0000
- Synthetic status: none
- PII status: none

## Score breakdown
- exact_mapping: 10
- verified_answer: 11
- matching_raw_corpus: 8
- product_relevance: 15
- difficulty_coverage: 6
- negative_cases: 3
- low_duplication: 3
- split_separation: 5
- jurisdiction_version: 5

## Approved / excluded components
**Approved:**
- Whole dataset as classified
**Excluded:**

## Required raw sources
- eiopa-qa-archive.xlsx (full EIOPA Q&A archive)
- referenced Solvency II regulations

## Reason
Evaluation score 66/100 maps to QUESTION_POOL_ONLY. Weak scoring dimensions: negative_cases, low_duplication, split_separation, jurisdiction_version.

## Evidence paths
- `datasets/insurance_eu_regulatory_qa/provenance.json`
- `datasets/insurance_eu_regulatory_qa/licence_review.json`
- `datasets/insurance_eu_regulatory_qa/domain_mapping.json`
- `datasets/insurance_eu_regulatory_qa/quality_metrics.json`
- `datasets/insurance_eu_regulatory_qa/privacy_review.json`
- `datasets/insurance_eu_regulatory_qa/chunkability_report.json`
- `datasets/insurance_eu_regulatory_qa/evaluation_report.json`