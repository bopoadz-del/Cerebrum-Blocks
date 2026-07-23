# Dataset Audit Report: construction_bim_core

**Display name:** IFC-Bench
**Primary role:** REASONING_EVAL
**Verdict:** `REJECT`
**Score:** 75/100

## Hard failures
- **conflicting_terms** (licence_issues.json): Dataset is CC BY 4.0 but four IFC model files are GPLv3; combined redistribution triggers copyleft obligations that conflict with the permissive dataset licence.

## Licence
- Licence: CC BY 4.0 (dataset); mixed per-model licences
- Commercial use: permitted
- Redistribution: permitted

## Quality metrics
- Exact duplicate rate: 0.0093
- Near duplicate rate: 0.0000
- Synthetic status: none
- PII status: none

## Score breakdown
- exact_mapping: 10
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
- QA pairs (ifc-bench-v1.csv) under CC BY 4.0 after removing GPLv3 IFC models
**Excluded:**
- projects/ IFC model files (GPLv3/CC BY 3.0 conflicting terms)

## Required raw sources
- projects/ (IFC model files)

## Reason
Hard rejection gates triggered: conflicting_terms. Weak scoring dimensions: negative_cases, low_duplication, split_separation, jurisdiction_version.

## Evidence paths
- `datasets/construction_bim_core/provenance.json`
- `datasets/construction_bim_core/licence_review.json`
- `datasets/construction_bim_core/domain_mapping.json`
- `datasets/construction_bim_core/quality_metrics.json`
- `datasets/construction_bim_core/privacy_review.json`
- `datasets/construction_bim_core/chunkability_report.json`
- `datasets/construction_bim_core/evaluation_report.json`