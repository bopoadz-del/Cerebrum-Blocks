# DanRAG-Bench Audit Report

## Dataset
- **Hub ID:** `Johanschmidt/DanRAG-Bench`
- **Original source:** https://huggingface.co/datasets/Johanschmidt/DanRAG-Bench
- **Publisher:** Johan Hausted Schmidt, IT University of Copenhagen
- **Licence:** MIT (commercial use and redistribution allowed)
- **Language / jurisdiction:** Danish / DK

## What was downloaded
| File | Size | SHA-256 |
|------|------|---------|
| `.gitattributes` | 2,504 | `9e75dd981de037ec3769f24f790e126bc5a160b6871f510214e68dc70649aeeb` |
| `README.md` | 5,666 | `a78796107e67f01550b52ed24b5d64e46fe7f1352c1dfadcff069f7be78b2f45` |
| `queries/train-00000-of-00001.parquet` | 70,274 | `7c80f250a825efeb775f09c9b406e3c7eafbbd144ba6ee6a6f22c34173f634b1` |
| `corpus_text_extracted_for_verification.parquet` | 407,394 | `027a4739078a3867bcb5bc87b52b6763d678b513b0f72f5867743acfec6d43dd` |

The canonical `corpus/train-00000-of-00001.parquet` (298.7 MB, containing 300 DPI page PNGs) and the byte-identical `data/corpus-00000-of-00001.parquet` were **not downloaded** in line with the no-large-image/PDF policy.

## Content inspection
- **Queries:** 471 verified Danish QA pairs across 8 public documents in 5 sectors (energy, finance, health, legal, municipality).
- **Corpus pages:** 349 page records (text-only extract).
- **Schema (queries):** `id`, `query`, `answer`, `sector`, `doc_id`, `title`, `valid_pages` (list of `page_id` strings).
- **Schema (corpus text):** `page_id`, `doc_id`, `sector`, `title`, `page_num`, `text`.
- **Exact duplicates:** 2 duplicate query strings out of 471 (~0.4%).
- **Near duplicates:** 13 query-prefix collisions (~2.8%).
- **Empty text pages:** 9 of 349 (~2.6%).
- **PII:** No emails, CPR numbers, or phone numbers detected in queries/answers.
- **Synthetic status:** Queries/answers were generated with GPT-4o-mini and then manually verified/corrected (11 deleted, 74 modified, 84 false-negative pages promoted); corpus text is extracted from real Danish government publications.

## Verification against source text
Using the text-only corpus extract, all 471 `valid_pages` entries resolved to existing page IDs. Query-term coverage on the mapped pages was high (435/471). Answers are abstractive paraphrases rather than extractive spans, which is consistent with the benchmark design.

## Scoring (RETRIEVAL_EVAL rubric)
| Dimension | Score | Notes |
|-----------|-------|-------|
| Exact question-to-document/passage mapping | 22/25 | `valid_pages` present and verified against page IDs. |
| Verified answer | 12/15 | Manually verified, but LLM-generated. |
| Matching raw corpus available | 12/15 | Text corpus extracted; canonical image-bearing Parquet not downloaded. |
| Product relevance | 12/15 | Strong Denmark public-sector relevance. |
| Difficulty and multi-passage coverage | 9/10 | Multi-page `valid_pages`, promoted false negatives. |
| Negative/insufficient-evidence cases | 0/5 | No explicit hard negatives. |
| Low duplication/leakage | 4/5 | Minimal exact duplicates. |
| Train/dev/test separation | 0/5 | Single `train` split only. |
| Matching jurisdiction/version | 5/5 | Danish sources dated 2023-2024. |
| **Total** | **76/100** | Eval-candidate band. |

## Verdict
**TECHNICALLY_VERIFIED_CANDIDATE**

The query pool and Danish public-sector provenance are solid. The canonical image-bearing corpus file was excluded under the no-large-image/PDF policy; only the text columns were extracted for verification. No hard failures apply, but the missing image modality and lack of a train/dev/test split prevent a higher grade.
