# EnterpriseRAG-Bench Audit Report

## Benchmark
- **Name:** EnterpriseRAG-Bench
- **Folder:** `enterpriserag_benchmark`
- **Paper:** [arXiv:2605.05253](https://arxiv.org/abs/2605.05253)
- **Repository:** [https://github.com/onyx-dot-app/EnterpriseRAG-Bench](https://github.com/onyx-dot-app/EnterpriseRAG-Bench)
- **Release:** v1.0.0

## Downloaded Files
| File | Size | SHA-256 |
|------|------|---------|
| `all_documents.zip` | 1,256,181,062 | `9d1174928696ad08bc15f3f104739519de633c1605a4ec2034e0e3c0087bc5cd` |
| `questions.jsonl` | 764,927 | `f9524b9157cd43aae36b99333a124738804306ea6d07f332d49faa6d3d147905` |
| `extra_questions.jsonl` | 57,726 | `26e23e5ade467512433e0fc012b30ea14b079dde11ad6f93cf380eed1bd96807` |
| `LICENSE` | 1,072 | `9eab95dae84867fa8ba1450e4bf34addf74e841923f4b6877f4d2df82bed3508` |
| `README.md` | 8,302 | `f38f53da1ce310a60ac6a6e49657d4815b006e9e967fdf6cbd7915d328c62bb7` |

## Corpus Inventory
- **Archive:** `all_documents.zip` (1.17 GB compressed, 2.47 GB uncompressed)
- **Documents inside archive:** 511,963 files
  - 511,962 `.txt` documents
  - 1 `questions.jsonl` (identical to the separately downloaded questions file)
- **Total on-disk kit size:** ~1.26 GB
- **Malformed files:** 0
- **Exact duplicate groups:** 1,300 (1,312 duplicate files, 0.26%)
- **Near-duplicates:** Present by construction at low rate; estimated ~0.5% (controlled pairs with factual divergence used for conflicting-info questions)

## Source Type Distribution
| Source | Count |
|--------|-------|
| slack | 285,605 |
| gmail | 121,390 |
| linear | 35,308 |
| google_drive | 25,108 |
| hubspot | 15,017 |
| fireflies | 10,173 |
| github | 8,052 |
| jira | 6,120 |
| confluence | 5,189 |

## Question Set
- **Core questions:** 500 (`questions.jsonl`)
- **Excluded questions:** 100 (`extra_questions.jsonl`, metadata-dependent, excluded from core benchmark by publisher)
- **Question types:** basic (175), semantic (125), intra_document_reasoning (40), project_related (40), constrained (30), conflicting_info (20), completeness (20), miscellaneous (20), info_not_found (20), high_level (10)
- **Unique document IDs referenced:** 722 in core, 812 including extra
- **Missing referenced documents:** 0
- **Malformed JSONL lines:** 0
- **Schema completeness:** 100% of required fields present
- **Data quality note:** One question (`qst_0413`) lists the same document ID twice in `expected_doc_ids`.

## Content Inspection
- **Language:** English (100% of sampled documents)
- **Synthetic status:** Majority / fully synthetic
- **PII status:** Contains synthetic fictional personal identifiers (names, email addresses, phone numbers of fictional employees and customers). No real private, confidential, or customer data detected.
- **Corruption/truncation:** No material corruption detected in sampled or validated files. The paper notes that initial generation artifacts (control characters, malformed metadata) were manually removed before release.

## Licence and Provenance
- **Publisher:** Onyx (DanswerAI, Inc.)
- **Original source:** GitHub release v1.0.0 of `onyx-dot-app/EnterpriseRAG-Bench`
- **Licence:** MIT
- **Commercial use:** Allowed
- **Redistribution:** Allowed
- **Jurisdiction:** Not applicable (synthetic benchmark)
- **Effective dates:** Not applicable; content contains fictional future dates

## Classification and Scoring
- **Primary role:** `RETRIEVAL_EVAL`
- **Secondary role:** `REASONING_EVAL`
- **Rubric:** RETRIEVAL_EVAL (out of 100)
  - Exact question-to-document/passage mapping: 18/25
  - Verified answer: 10/15
  - Matching raw corpus available: 15/15
  - Product relevance: 12/15
  - Difficulty and multi-passage coverage: 9/10
  - Negative/insufficient-evidence cases: 4/5
  - Low duplication/leakage: 4/5
  - Train/dev/test separation: 2/5
  - Matching jurisdiction/version: 3/5
- **Total score:** 77/100
- **Rubric verdict:** APPROVE_EVAL_CANDIDATE
- **Kit status:** `technically_verified_candidate` (capped per policy)

## Hard Rejection Gates
No hard failures. Concerns noted but not fatal:
- Fully synthetic corpus (transparently disclosed).
- Gold answers/document sets are revisable hypotheses, not exhaustively human-verified.
- No train/dev/test split provided.
- One question repeats a document ID in its expected-doc list.

## Approved / Excluded Components
- **Approved:** `questions.jsonl`, `all_documents.zip` corpus, evaluation harness reference code in the GitHub repository.
- **Excluded:** `extra_questions.jsonl` (metadata-dependent, excluded from core benchmark by publisher).
