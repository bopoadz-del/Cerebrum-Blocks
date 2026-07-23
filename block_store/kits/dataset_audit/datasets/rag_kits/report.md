# Dataset Audit Report: rag_kits

**Display name:** RAG Kits (mixed regulatory and financial corpora)
**Primary role:** RETRIEVAL_EVAL
**Verdict:** `REJECT`
**Score:** 74/100

## Hard failures
- **unknown_licence** (licence_review.json): Mixed per-component licence with unresolved top-level terms
- **unknown_licence** (licence_issues.json): No licence file for the link-index CSV; reuse terms for the compilation are not stated.
- **commercial_use_prohibited** (licence_issues.json): OpenSanctions is free for non-commercial users; businesses must acquire a data licence (https://www.opensanctions.org/docs/commercial/exemption/).

## Licence
- Licence: Mixed per-component
- Commercial use: mixed
- Redistribution: mixed

## Quality metrics
- Exact duplicate rate: 0.0371
- Near duplicate rate: 0.0000
- Synthetic status: majority
- PII status: none

## Score breakdown
- exact_mapping: 10
- verified_answer: 13
- matching_raw_corpus: 12
- product_relevance: 15
- difficulty_coverage: 9
- negative_cases: 3
- low_duplication: 3
- split_separation: 5
- jurisdiction_version: 4

## Approved / excluded components
**Approved:**
- tatqa_dataset_test.json
- tatqa_dataset_dev.json
**Excluded:**
- opensanctions_sample_1000.json (commercial prohibited)
- IrishFinance_prompt_completion.jsonl (unknown licence)
- Regulations_Link_Retrieval.csv (unknown licence)

## Required raw sources
- raw_regulations/ (harvested regulation texts)
- harvest_manifest.json

## Reason
Hard rejection gates triggered: unknown_licence, commercial_use_prohibited. Weak scoring dimensions: negative_cases, low_duplication, split_separation, jurisdiction_version.

## Evidence paths
- `datasets/rag_kits/provenance.json`
- `datasets/rag_kits/licence_review.json`
- `datasets/rag_kits/domain_mapping.json`
- `datasets/rag_kits/quality_metrics.json`
- `datasets/rag_kits/privacy_review.json`
- `datasets/rag_kits/chunkability_report.json`
- `datasets/rag_kits/evaluation_report.json`