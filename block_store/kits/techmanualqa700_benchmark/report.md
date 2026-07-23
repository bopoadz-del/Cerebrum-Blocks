# TechManualQA-700 Dataset Audit Report

## Benchmark
- **Name:** TechManualQA-700
- **Folder:** `techmanualqa700_benchmark`
- **Source:** https://zenodo.org/records/17410809
- **DOI:** 10.5281/zenodo.17410809
- **Publisher:** Tomislav Duricic, Graz University of Technology / Know-Center GmbH
- **Paper:** ECIR 2026 — "A Semi-Automated Pipeline for Synthetic Generation of Grounded, Structurally-Aware QA Datasets for Technical Manuals"
- **Code repository:** https://github.com/tduricic/techmanualqa

## Licence & Provenance
- **Licence:** CC-BY 4.0
- **Commercial use:** Allowed
- **Redistribution:** Allowed
- **Original source:** Zenodo record 17410809, published 2025-10-22
- No private, confidential, or sensitive personal data detected.

## File Inventory
| Path | Size (bytes) | Extension | SHA-256 |
|------|--------------|-----------|---------|
| TechManualQA_700/LICENSE | 577 | — | `b2cfddee2735c28643eb177dafac1f16d755d130d457aca49b6d47c2766b15f9` |
| TechManualQA_700/README.md | 1,580 | .md | `a3ac8330db5670bdbc546f488e2a447b31994cdaa6f9053362c8c58531818793` |
| TechManualQA_700/TechManualQA_700.jsonl | 693,107 | .jsonl | `775d776cf5e40815f2e0a80e5d02987d4ff9b2265ab728c20181d81fe3f9af9e` |
| TechManualQA_700/human_annotation/general_audit_A.xlsx | 27,433 | .xlsx | `a1e7403a57a14034ce6ec2d9e83ed524d13720a456eacf8ecb94ccc37aee39df` |
| TechManualQA_700/human_annotation/general_audit_B.xlsx | 27,548 | .xlsx | `745f67b02338be419d5555ebf35b2ef3ff41b964d44557ef73745baebe18c89f` |
| TechManualQA_700/human_annotation/procedural_audit_A.xlsx | 30,827 | .xlsx | `499523e51a423d0d2eb41487c6247f5b8fe3900f7201580750fe0de79866a306` |
| TechManualQA_700/human_annotation/procedural_audit_B.xlsx | 30,751 | .xlsx | `4637984d324f233453a8d9ce8f4407e2e0c2850b065c72d1827675ba6ee3f90d` |

*Provenance/download artifacts also present:* `TechManualQA_700.zip` (167,389 bytes), `zenodo_page.html` (85,981 bytes).

## Dataset Inspection
- **Records parsed:** 700 (0 malformed JSONL lines)
- **Schema:** 26 fields per record, including `question_id`, `doc_id`, `question_text`, `category`, `gt_answer_snippet`, `gt_page_number`, `parsed_steps`, `ragas_faithfulness`, `ragas_correctness`, `judge_score`, and dual-annotator labels.
- **Language:** English (`en`) for all records.
- **Documents covered:** 20 technical manuals (35 questions per manual), spanning consumer electronics, appliances, power tools, vehicles, drones/robotics, and medical devices.
- **Question categories:**
  - Specification Lookup: 100
  - Tool/Material Identification: 100
  - Procedural Step Inquiry: 100
  - Location/Definition: 100
  - Conditional Logic/Causal Reasoning: 100
  - Safety Information Lookup: 100
  - Unanswerable: 100
- **Answer types:** direct answer (500), procedural steps (100), unanswerable (100).
- **Personas:** Technician (272), Novice User (268), SafetyOfficer (160).
- **Quality scores:** 600 records have `judge_score=5`; 100 unanswerable records have `judge_score=-1`. RAGAS faithfulness=1.0 for 595 records.
- **Human audit:** ~262 questions audited across general (161) and procedural (101) Excel files; reported inter-annotator agreement κ=0.82.
- **Duplicates:** 0 exact duplicate records, 0 duplicate `question_id`s, 0 near-duplicate question texts. Some answer snippets repeat (e.g., 100 "Not Answered" entries), which is expected by design.
- **Corruption/truncation:** None detected.
- **Synthetic content:** Semi-automated generation via Gemini 2.5 Pro, filtered with RAGAS and GPT-4.1 judge, then human-validated. Disclosed transparently; not presented as authoritative raw corpus.

## Classification
- **Primary role:** RETRIEVAL_EVAL
- **Secondary role:** REASONING_EVAL

## Scoring (RETRIEVAL_EVAL rubric)
| Dimension | Score | Notes |
|-----------|-------|-------|
| Exact question-to-document/passage mapping | 22/25 | `doc_id` for all; `gt_page_number` for 600 answerable records. Not a byte-level passage span. |
| Verified answer | 11/15 | Automated RAGAS + LLM judge for all; human audit on ~262 questions. |
| Matching raw corpus available | 5/15 | Source PDFs are **not** included; must be obtained separately. |
| Product relevance | 14/15 | Highly relevant to product-support / technical-manual RAG. |
| Difficulty and multi-passage coverage | 8/10 | Diverse categories, personas, procedural steps, causal/safety reasoning. |
| Negative/insufficient-evidence cases | 5/5 | 100 unanswerable questions included. |
| Low duplication/leakage | 4/5 | No duplicate records/questions; some repeated answer snippets. |
| Train/dev/test separation | 0/5 | No predefined split. |
| Matching jurisdiction/version | 2/5 | Mixed manufacturers/regions; no explicit jurisdiction metadata. |
| **Total** | **71/100** | **APPROVE_EVAL_CANDIDATE** |

## Hard Rejection Gates
No hard failures triggered. Source PDFs are intentionally excluded to respect manufacturer rights; this is recorded as an excluded/required-raw-source item rather than a licence failure.

## Verdict
- **Score:** 71/100
- **Rubric verdict:** APPROVE_EVAL_CANDIDATE
- **Maximum status:** technically_verified_candidate
- **Approved components:** TechManualQA_700.jsonl benchmark file; human_annotation audit spreadsheets.
- **Excluded/required raw sources:** The 20 original manufacturer PDFs must be sourced independently for end-to-end retrieval experiments.

## One-line Reason
Well-licensed, transparently generated technical-manual QA benchmark with strong mapping and validation, held back only by the absence of bundled source PDFs and no predefined split.
