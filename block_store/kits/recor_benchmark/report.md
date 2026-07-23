# RECOR Benchmark Audit Report

## Dataset
- **Name:** RECOR: Reasoning-focused Multi-turn Conversational Retrieval Benchmark
- **Folder:** `recor_benchmark`
- **Source:** https://huggingface.co/datasets/RECOR-Benchmark/RECOR
- **Paper:** arXiv:2601.05461
- **GitHub:** https://github.com/RECOR-Benchmark/RECOR

## Files Downloaded
Cloned the full HuggingFace dataset repository (22 JSONL data files + `README.md` + `.gitattributes`).

| Metric | Value |
|--------|-------|
| Total files (excl. `.git`) | 24 |
| Total bytes | 283,437,448 (~270 MiB) |
| Benchmark files | 11 |
| Corpus files | 11 |
| Malformed JSON lines | 0 |

Full file inventory with SHA-256 hashes is in `file_inventory.json`. Parse summary is in `parse_summary.json`.

## Dataset Structure
- **Benchmark:** 707 multi-turn conversations, 2,971 turns across 11 domains.
- **Corpus:** 507,141 documents with `doc_id` and `content`.
- **Per-domain splits:** biology, earth_science, economics, psychology, robotics, sustainable_living (sourced from BRIGHT); Drones, hardware, law, medicalsciences, politics (sourced from StackExchange).
- **Schema:**
  - Conversation: `id`, `task`, `original_query`, `original_answer`, `turns`, `metadata`.
  - Turn: `turn_id`, `query`, `answer`, `gold_doc_ids`, `subquestion_reasoning`, `subquestion_reasoning_metadata`, `conversation_history`.
  - Document: `doc_id`, `content`.

## Quality Findings
- **Duplicates:** 0 exact-duplicate conversations. ~65,823 exact-duplicate document contents (~12.98% of corpus). Conversation IDs are unique within a domain but collide across domains (e.g., ID `0` appears in every BRIGHT domain); this is a namespace issue, not content duplication.
- **Synthetic content:** All benchmark conversations list `method: unified_bright_workflow` and are generated/annotated, while the underlying corpus documents are derived from real-world sources (StackExchange, BRIGHT). Status: **partial** synthetic.
- **Answer-source alignment:** Spot checks show gold answers are consistent with the cited gold documents.
- **Gold coverage:** Sampled `biology` gold doc IDs are all present in the matching corpus.
- **PII:** Minimal. A small number of institutional email addresses and numeric patterns (many likely IDs, not phone numbers) were found in a corpus sample; no obvious bulk personal data.
- **Language:** English.
- **Corruption/truncation:** None detected.

## Licence & Provenance
- **Declared licence:** MIT License (HuggingFace card and GitHub `LICENSE`).
- **Original publishers:** RECOR Benchmark authors (anonymous ACL submission).
- **Underlying sources:**
  - BRIGHT benchmark corpus: https://github.com/xlang-ai/BRIGHT (CC BY 4.0).
  - StackExchange network dumps: CC BY-SA 4.0.
- **Commercial use:** Allowed under all applicable licences (MIT, CC BY 4.0, CC BY-SA 4.0).
- **Redistribution:** Allowed, but the StackExchange-derived corpus requires Share-Alike and attribution, and BRIGHT requires attribution. The dataset is mirrored under a declared MIT licence that may not be fully compatible with the underlying CC BY-SA corpus content. Downstream redistribution should satisfy the stricter source terms.

## Classification & Score
- **Primary role:** `REASONING_EVAL`
- **Secondary role:** `RETRIEVAL_EVAL`
- **Evaluation rubric score:** 74 / 100
  - Exact question-to-document mapping: 25/25
  - Verified answer: 10/15
  - Matching raw corpus available: 15/15
  - Product relevance: 6/15
  - Difficulty & multi-passage coverage: 9/10
  - Negative/insufficient-evidence cases: 5/5
  - Low duplication/leakage: 2/5
  - Train/dev/test separation: 0/5 (none provided)
  - Matching jurisdiction/version: 2/5 (version `unified_v1`; no jurisdiction metadata)
- **Verdict:** `APPROVE_EVAL_CANDIDATE`

## Hard Failure Review
No hard-rejection gates triggered. Noted risks:
1. Licence provenance mismatch between declared MIT and underlying CC BY/CC BY-SA sources.
2. ~13% exact-duplicate corpus documents.
3. No predefined train/dev/test splits.
4. Cross-domain conversation ID collisions.
5. Broad general-domain focus; limited direct relevance to Cerebrum vertical kits.

## Approved / Excluded Components
- **Approved:** Benchmark conversational queries, gold answers, subquestion reasoning metadata, per-domain document corpora, and gold `doc_id` mappings.
- **Excluded:** None fully excluded; however, the dataset should be used as a candidate eval set and not treated as domain-authoritative RAG content.
