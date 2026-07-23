# Dataset Audit Domain Summary

**Datasets judged:** 17
**Generated:** 2026-07-23T06:37:44.663987+00:00

## Verdict counts
- APPROVE_CANDIDATE_RAG: 1
- APPROVE_CORE_RAG: 1
- APPROVE_EVAL_CANDIDATE: 3
- APPROVE_GOLDEN_EVAL: 1
- QUESTION_POOL_ONLY: 2
- REJECT: 9

## Role counts
- OPERATIONAL_DEMO_DATA: 2
- RAW_RAG: 4
- REASONING_EVAL: 2
- REFERENCE_DATA: 2
- RETRIEVAL_EVAL: 7

## Dataset verdicts
| Dataset | Role | Verdict | Score | Hard failures |
|---|---|---|---|---|
| construction_bim_core | REASONING_EVAL | REJECT | 75 | conflicting_terms |
| legal_general_retrieval_eval | RETRIEVAL_EVAL | APPROVE_GOLDEN_EVAL | 90 | none |
| legal_australia_victoria_criminal | RETRIEVAL_EVAL | REJECT | 90 | commercial_use_prohibited, conflicting_terms |
| insurance_eu_solvency_core | RAW_RAG | APPROVE_CORE_RAG | 86 | none |
| insurance_eu_regulatory_qa | RETRIEVAL_EVAL | QUESTION_POOL_ONLY | 66 | none |
| aviation_faa_core_rag | RAW_RAG | REJECT | 79 | unknown_licence |
| aviation_faa_eval | RETRIEVAL_EVAL | APPROVE_EVAL_CANDIDATE | 73 | none |
| medical_clinical_guidelines | RAW_RAG | REJECT | 79 | unknown_licence |
| medical_pubmedqa_eval | RETRIEVAL_EVAL | APPROVE_EVAL_CANDIDATE | 73 | none |
| retail_product_search_eval | RETRIEVAL_EVAL | APPROVE_EVAL_CANDIDATE | 81 | none |
| supply_chain_logic_eval | REASONING_EVAL | QUESTION_POOL_ONLY | 63 | none |
| supply_chain_raw_rag_candidates | RAW_RAG | APPROVE_CANDIDATE_RAG | 83 | none |
| rag_kits | RETRIEVAL_EVAL | REJECT | 74 | commercial_use_prohibited, unknown_licence |
| universal_reference_data | REFERENCE_DATA | REJECT | 0 | unknown_licence |
| universal_ingestion_tests | OPERATIONAL_DEMO_DATA | REJECT | 0 | unknown_licence |
| universal_api_reference | REFERENCE_DATA | REJECT | 0 | unknown_licence |
| financeops_demo_fixtures | OPERATIONAL_DEMO_DATA | REJECT | 0 | pii_detected, unknown_licence |

## Source harvest plan
### construction_bim_core
- Verdict: REJECT
- Required raw sources:
  - projects/ (IFC model files)
### legal_general_retrieval_eval
- Verdict: APPROVE_GOLDEN_EVAL
- Required raw sources:
  - contractnli
  - cuad
  - maud
  - privacy_qa
### legal_australia_victoria_criminal
- Verdict: REJECT
- Required raw sources:
  - corpus.jsonl
### insurance_eu_regulatory_qa
- Verdict: QUESTION_POOL_ONLY
- Required raw sources:
  - eiopa-qa-archive.xlsx (full EIOPA Q&A archive)
  - referenced Solvency II regulations
### aviation_faa_eval
- Verdict: APPROVE_EVAL_CANDIDATE
- Required raw sources:
  - aviation_faa_core_rag/ (AIM PDF, CFR XML parts 61/91/121/135)
### medical_pubmedqa_eval
- Verdict: APPROVE_EVAL_CANDIDATE
- Required raw sources:
  - ori_pqal.json (questions, contexts, labels)
  - PubMed abstracts corresponding to PMIDs
### retail_product_search_eval
- Verdict: APPROVE_EVAL_CANDIDATE
- Required raw sources:
  - amazon_esci/products/
  - amazon_esci/retrieval/
  - wands/data/data.jsonl.gz
### rag_kits
- Verdict: REJECT
- Required raw sources:
  - raw_regulations/ (harvested regulation texts)
  - harvest_manifest.json