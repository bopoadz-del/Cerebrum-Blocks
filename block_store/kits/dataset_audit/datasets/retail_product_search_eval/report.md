# Dataset Audit Report: retail_product_search_eval

**Display name:** Retail Product Search Evaluation
**Primary role:** RETRIEVAL_EVAL
**Verdict:** `APPROVE_EVAL_CANDIDATE`
**Score:** 81/100

## Hard failures
None.

## Licence
- Licence: Apache 2.0 (both sub-datasets)
- Commercial use: permitted
- Redistribution: permitted

## Quality metrics
- Exact duplicate rate: 0.0000
- Near duplicate rate: 0.0000
- Synthetic status: none
- PII status: none

## Score breakdown
- exact_mapping: 18
- verified_answer: 13
- matching_raw_corpus: 12
- product_relevance: 15
- difficulty_coverage: 9
- negative_cases: 3
- low_duplication: 5
- split_separation: 2
- jurisdiction_version: 4

## Approved / excluded components
**Approved:**
- Whole dataset as classified
**Excluded:**

## Required raw sources
- amazon_esci/products/
- amazon_esci/retrieval/
- wands/data/data.jsonl.gz

## Reason
Evaluation score 81/100 maps to APPROVE_EVAL_CANDIDATE. Weak scoring dimensions: negative_cases, low_duplication, split_separation, jurisdiction_version.

## Evidence paths
- `datasets/retail_product_search_eval/provenance.json`
- `datasets/retail_product_search_eval/licence_review.json`
- `datasets/retail_product_search_eval/domain_mapping.json`
- `datasets/retail_product_search_eval/quality_metrics.json`
- `datasets/retail_product_search_eval/privacy_review.json`
- `datasets/retail_product_search_eval/chunkability_report.json`
- `datasets/retail_product_search_eval/evaluation_report.json`