# ParseBench Audit Report

**Benchmark:** ParseBench  
**Kit folder:** `parsebench_benchmark`  
**Source:** https://huggingface.co/datasets/huggingworld/ParseBench  
**Downloaded:** 2,113 files, 592,182,175 bytes (~565 MiB)

## 1. Dataset Overview

ParseBench is a document-parsing evaluation benchmark for AI agents. It supplies 169,011 test rules across five capability dimensions, each rule pointing to a specific source page in the included raw corpus.

| File | Records | Dimension |
|---|---|---|
| `chart.jsonl` | 4,864 | Chart data-point extraction |
| `table.jsonl` | 503 | Ground-truth HTML table structure |
| `text_content.jsonl` | 141,322 | Content faithfulness (omissions, hallucinations, reading order) |
| `text_formatting.jsonl` | 5,997 | Semantic formatting preservation |
| `layout.jsonl` | 16,325 | Visual grounding / layout analysis |
| `docs/` | 2,079 pages | Source PDFs, JPGs, PNGs |

Total unique pages per README: 2,078. Local inventory counts 2,079 docs files (2037 PDF, 23 JPG, 19 PNG); the difference is within normal file-count rounding.

## 2. File Inventory & Integrity

- **Files inventoried:** 2,113
- **Malformed/unreadable files:** 0
- **SHA-256 computed:** all files
- **Inventory written to:** `inventory.json`

Top file types:

- `.pdf`: 2,037
- `.png`: 44
- `.jpg`: 23
- `.jsonl`: 5
- `.md`, `.yaml`, `.gitattributes`, `.gitignore`: 4

## 3. Schema & Corruption

All five JSONL files parse cleanly (0 malformed lines). Common schema per rule:

```json
{
  "pdf": "docs/...",
  "category": "...",
  "id": "...",
  "type": "...",
  "rule": "{...}",
  "page": null | int,
  "expected_markdown": null | html,
  "tags": [...]
}
```

All 169,011 `pdf` references resolve to existing files in `docs/`.

**Data-quality observations:**
- **Duplicate IDs:** 53 rule IDs appear more than once (23 unique IDs in `chart.jsonl`, 30 unique IDs in `layout.jsonl`; no ID is duplicated across the two files). In every case the *rule payload* is identical but the referenced page/PDF differs—e.g., the same chart data point appears on pages 17 and 95 of the same report, or the same page-header bounding box appears on multiple pages. The IDs appear to be content hashes, not globally unique rule identifiers. This is a metadata issue, not record duplication.
- **Exact duplicate records:** 0
- **Near-duplicates (same pdf + category + type + rule):** 0
- **Languages:** predominantly English; README documents 47 multi-language documents covering 20+ scripts. Spot checks confirm CJK and other non-Latin text.

## 4. Provenance & Licence

- **Original publisher:** ParseBench team / LlamaIndex (`run-llama/ParseBench`)
- **Canonical HF dataset:** `llamaindex/ParseBench`
- **Mirrored/downloaded HF dataset:** `huggingworld/ParseBench`
- **Paper:** arXiv:2604.08538
- **Website:** https://parsebench.ai
- **Licence:** Apache-2.0 (stated in README header and Copyright Statement)
- **Commercial use:** allowed
- **Redistribution:** allowed
- **Source documents:** "All documents are sourced from public online channels."

Because Apache-2.0 permits redistribution, the `huggingworld` mirror does not create a rights issue.

## 5. Synthetic & PII Assessment

- **Synthetic status:** **partial**. README states annotations are produced by "frontier VLM auto-labeling followed by targeted human correction." The source pages are real public documents; the test rules are machine-generated then human-refined.
- **PII status:** **business contact info only**. A regex scan found public investor-relations emails and public phone numbers in corporate/government documents. No SSNs or obviously sensitive personal data were detected. This is consistent with public enterprise filings.

## 6. Classification & Score

**Primary role:** `REASONING_EVAL` (document understanding / parsing benchmark with verified answers mapped to source pages). `VISION_DATA` is a secondary role because the task is visually grounded.

**Evaluation rubric scoring:**

| Criterion | Score | Notes |
|---|---|---|
| Exact question-to-document/passage mapping | 25/25 | Every rule references a specific `docs/` page. |
| Verified answer | 10/15 | Human-corrected, but initially VLM-generated, not human-authored from scratch. |
| Matching raw corpus available | 15/15 | Full source pages included. |
| Product relevance | 13/15 | Strong relevance to RAG and agentic document workflows. |
| Difficulty & multi-passage coverage | 9/10 | Adversarial examples, diverse layouts, OCR, multi-language, charts, tables. |
| Negative/insufficient-evidence cases | 3/5 | Some "missing"/"unexpected" rules test absence; not a classical negative-evidence QA set. |
| Low duplication / leakage | 3/5 | No exact duplicates, but non-unique IDs and repeated rules across pages. |
| Train/dev/test separation | 2/5 | Test-only benchmark; no split provided. |
| Matching jurisdiction / version | 2/5 | Mixed jurisdictions and publication dates; no per-record authority metadata. |
| **Total** | **81/100** | |

**Verdict:** `APPROVE_EVAL_CANDIDATE` (capped at candidate status per policy; no dataset is promoted to fully domain-approved).

## 7. Hard Rejection Gates

No hard failures triggered:
- Licence is known and commercial/redistribution-friendly.
- Publisher is identifiable.
- No private/customer data or unnecessary sensitive PII detected.
- No material corruption or truncation.
- Synthetic origin is disclosed; not presented as authority.
- Raw corpus rights are covered by Apache-2.0.
- Mixed jurisdiction is noted but does not make the benchmark unusable for evaluation.

## 8. Approved / Excluded Components

- **Approved:** all JSONL rule files, `docs/` source pages, `README.md`, `eval.yaml`, thumbnails.
- **Excluded:** none.
- **Required raw sources for evaluation:** `docs/` (rules are meaningless without the source pages).

## 9. Recommendations

1. Treat ParseBench as a **candidate evaluation benchmark**, not a golden eval, until the ID-uniqueness issue and VLM-generated-annotation lineage are acceptable to downstream consumers.
2. If used for domain kits, tag each rule with the document’s publisher/domain and effective/publication date where possible, because the corpus mixes jurisdictions and report vintages.
3. Do not use this dataset as a raw RAG corpus; it is an evaluation suite with ground-truth rules, not a reference knowledge base.
