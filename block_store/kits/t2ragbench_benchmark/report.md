# T²-RAGBench Audit Report

**Benchmark:** T2RAGBench (`grasson/t2-ragbench`)  
**Kit folder:** `Cerebrum-Blocks/block_store/kits/t2ragbench_benchmark/`  
**Canonical source:** https://huggingface.co/datasets/grasson/t2-ragbench  
**Primary role:** REASONING_EVAL (also usable for RETRIEVAL_EVAL)  
**Licence:** CC BY 4.0  
**Evaluation score:** 93 / 100  
**Verdict:** APPROVE_GOLDEN_EVAL

---

## 1. Dataset download & inventory

The repository is public on Hugging Face. It contains **13,187 files** totalling **~2.98 GB**:

| Extension | Files | Approx. bytes |
|-----------|------:|--------------:|
| pdf       | 7,353 | 2.50 GB       |
| png       | 3,067 | 63.5 MB       |
| json      | 2,758 | 250.7 MB      |
| jsonl     | 7     | 165.0 MB      |
| md        | 1     | 9 KB          |
| gitattributes | 1 | 2.5 KB      |

Because the binary source corpus is large and Hugging Face rate-limited the unauthenticated connection, the kit mirrors:

- All QA metadata `.jsonl` files (FinQA, ConvFinQA, TAT-DQA)
- All TAT-DQA per-document `.json` annotations (1,903 files)
- `README.md` and `.gitattributes`
- A complete `file_inventory.json`/`file_inventory.csv` for the full repository, including LFS pointer SHA-256 hashes and sizes for every PDF/PNG page

All 1,910 locally-held files were verified against their LFS SHA-256/size metadata; **0 malformed files** were found.

---

## 2. Schema, record counts & splits

Records are line-delimited JSON objects. Common fields include `id`, `context_id`, `split`, `question`, `program_answer`, `original_answer`, `context`, `file_name`, `company_name`, `report_year`. FinQA/ConvFinQA add `table`, `pre_text`, `post_text`, company sector/industry/headquarters/CIK, etc.

| Subset    | Split        | Records |
|-----------|-------------:|--------:|
| FinQA     | train        | 6,251   |
| FinQA     | dev          | 883     |
| FinQA     | test         | 1,147   |
| ConvFinQA | turn_0       | 3,458   |
| TAT-DQA   | train        | 9,063   |
| TAT-DQA   | dev          | 1,142   |
| TAT-DQA   | test         | 1,144   |
| **Total** |              | **23,088** |

- **Language:** English
- **Jurisdiction:** US (documents are SEC filings / public company annual reports)
- **Report years:** 1999–2019
- **Distinct companies:** 309

---

## 3. Quality checks

- **Exact duplicate question rate:** ~0.29 %
- **Near-duplicate question rate:** ~0.34 %
- **Malformed JSON lines:** 0
- **PII:** None (only public company names, tickers, CIKs, and SEC filing content)
- **Synthetic content:** **Partial**. The authors disclose that questions were reformulated with Llama 3.3-70B to make them context-independent; human annotators verified a random subset. Answers are derived from the original verified gold datasets (FinQA, ConvFinQA, TAT-DQA). This is documented, not presented as authoritative source material.

---

## 4. Licence & provenance

- **Dataset publisher:** `grasson` on Hugging Face (T²-RAGBench authors, University of Hamburg HCDS).
- **Original sources:**
  - [FinQA](https://github.com/czyssrs/FinQA) (MIT licence)
  - [ConvFinQA](https://github.com/czyssrs/ConvFinQA) (MIT licence)
  - [TAT-DQA](https://nextplusplus.github.io/TAT-DQA/) (CC BY 4.0)
  - PDF pages from SEC EDGAR filings (US public domain / freely redistributable government filings)
- **Aggregated dataset licence:** CC BY 4.0 — commercial use and redistribution are allowed with attribution.

No unknown-rights or non-commercial sub-licences were identified.

---

## 5. Rubric scoring (REASONING_EVAL / RETRIEVAL_EVAL)

| Criterion | Max | Score | Notes |
|-----------|----:|------:|-------|
| Exact question-to-document/passage mapping | 25 | 25 | Every record contains `file_name`, `context_id`, and extracted `context` pointing to the source PDF page. |
| Verified answer | 15 | 14 | Answers are normalized from verified gold datasets; 74 `original_answer` fields are null but `program_answer` is always present. |
| Matching raw corpus available | 15 | 15 | PDF/PNG source pages are part of the canonical repository and listed in the inventory. |
| Product relevance | 15 | 14 | Highly relevant for financial-document RAG; domain-specific. |
| Difficulty & multi-passage coverage | 10 | 9 | Requires locating tables, extracting numbers, and arithmetic/logical reasoning. |
| Negative / insufficient-evidence cases | 5 | 2 | No explicit negative retrieval examples; all questions have an answerable source page. |
| Low duplication / leakage | 5 | 4 | Very low duplicate question rate; some company overlap may exist across splits. |
| Train/dev/test separation | 5 | 5 | FinQA and TAT-DQA retain explicit splits; ConvFinQA only provides `turn_0`. |
| Matching jurisdiction / version | 5 | 5 | US SEC filings, report years 1999-2019; pinned to repo commit `3ed612d6`. |
| **Total** | **100** | **93** | |

---

## 6. Hard-rejection gate review

No hard failures were found:

- Licence is known and commercial-friendly (CC BY 4.0).
- Redistribution is allowed with attribution.
- Publisher and original sources are documented.
- No private, confidential, or personal data.
- No material corruption or truncation in inspected files.
- Synthetic content is disclosed and limited to question reformulation; it is not presented as authoritative source evidence.
- Domain relevance is strong.
- Jurisdiction and effective dates are present.
- Rights to mirrored source data are clear (MIT, CC BY 4.0, public SEC filings).

---

## 7. Approved / excluded components

**Approved for domain-kit use:**
- QA metadata JSONL files for all three subsets.
- TAT-DQA per-document JSON annotations.
- Source corpus manifest with SHA-256/size for every PDF/PNG page.

**Excluded / left in canonical source:**
- VQAonBD subset (removed by authors for low-quality reformulations).
- Full binary PDF/PNG source corpus (~2.5 GB of PDFs + 63 MB of PNGs). These can be fetched on demand from the canonical Hugging Face repository.

---

## 8. One-line summary

T²-RAGBench is an approved golden evaluation candidate: 23,088 context-independent financial QA triples with verified answers, strong source mapping, permissive CC BY 4.0 licensing, and clear US SEC-filing provenance; the binary source pages remain in the canonical repository and are catalogued locally.
