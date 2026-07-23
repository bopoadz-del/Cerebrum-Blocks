---
language:
- da
license: mit
task_categories:
- text-retrieval
task_ids:
- document-retrieval
pretty_name: DanRAG-Bench
size_categories:
- 1K<n<10K
modalities:
- image
- text
tags:
- danish
- retrieval
- RAG
- multimodal
- benchmark
---

# DanRAG-Bench: A Danish Multimodal Document Retrieval Benchmark Across Five Sectors

DanRAG-Bench is the first Danish multimodal page-level document retrieval benchmark, spanning five sectors (energy, finance, health, legal, and municipalities) across 349 document pages and 471 verified queries. It is designed to evaluate retrieval systems on real-world Danish public-sector documents containing mixed formats including text, tables, and text-based diagrams.

## Dataset Structure

The dataset contains two configs:

### `corpus`
One row per document page.

| Field | Type | Description |
|---|---|---|
| `page_id` | string | Unique page identifier (`{doc_id}_p{page_num:04d}`) |
| `doc_id` | string | Source document identifier |
| `sector` | string | Sector (energy, finance, health, legal, municipality) |
| `title` | string | Document title |
| `page_num` | int | Page number (1-indexed) |
| `text` | string | Extracted page text (PyMuPDF) |
| `image` | image | Rendered page image (300 DPI PNG) |

### `queries`
One row per verified query.

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique query identifier |
| `query` | string | Danish query |
| `answer` | string | Short factual answer |
| `sector` | string | Sector |
| `doc_id` | string | Source document identifier |
| `title` | string | Document title |
| `valid_pages` | list[string] | List of `page_id` values that answer the query (includes promoted false negatives) |

## Usage

```python
from datasets import load_dataset

corpus  = load_dataset("Johanschmidt/DanRAG-Bench", "corpus")["train"]
queries = load_dataset("Johanschmidt/DanRAG-Bench", "queries")["train"]
```

Linking queries to corpus pages:
```python
# Build a lookup from page_id to corpus row
page_lookup = {row["page_id"]: row for row in corpus}

# For each query, retrieve the gold pages
for q in queries:
    gold_pages = [page_lookup[pid] for pid in q["valid_pages"]]
```

## Corpus

| Sector | Document | Pages | Institution |
|---|---|---|---|
| Energy | Energi- og forsyningspolitisk redegørelse 2024 | 19 | Klima-, Energi- og Forsyningsministeriet |
| Energy | Energistatistik 2023 | 60 | Energistyrelsen |
| Finance | Årsrapport 2024 | 76 | Danmarks Nationalbank |
| Finance | Statens låntagning og gæld 2023 | 46 | Danmarks Nationalbank |
| Health | Årsrapport 2023 | 54 | Sundhedsstyrelsen |
| Health | Danskernes sundhed 2023 | 20 | Sundhedsstyrelsen |
| Legal | Revision af statens forvaltning i 2023 | 33 | Rigsrevisionen & Statsrevisorerne |
| Municipality | Regnskab 2023 Årsrapport | 41 | Københavns Kommune |
| **Total** | | **349** | |

All documents are publicly available Danish government publications. All institutions were contacted to confirm permission for academic use and public release.

## Construction Pipeline

Queries were generated using a three-stage LLM pipeline operating on individual pages:

1. **Generator** — GPT-4o-mini produces two question-answer pairs per page, grounded in the page content and free of structural references.
2. **Rephraser** — A second GPT-4o-mini instance rewrites each question into natural Danish while preserving meaning.
3. **Judge** — A third GPT-4o-mini instance verifies answerability and filters structural references.

Following the automated pipeline, all 482 generated pairs were manually verified. 11 were deleted and 74 were modified, resulting in 471 final pairs.

**False negative correction** was performed in two stages. A heuristic token-overlap check (≥6 tokens, ≥55% overlap ratio) during the pipeline flags potential conflicts. After manual verification, GPT-4o cross-referenced every query against all pages in its source document, with Claude Sonnet 4.6 acting as judge. Of 471 queries, 134 were flagged and 84 confirmed as genuine false negatives. Rather than discarding these queries, additional valid pages are promoted to positive labels in `valid_pages`.

## Evaluation Results

Four retrieval systems were evaluated: BM25 (sparse), BGE-M3 (dense), ColPali (visual), and ColQwen2 (visual).

| Sector | BM25 | BGE-M3 | ColQwen2 | ColPali | BM25 R@5 | BGE-M3 R@5 | ColQwen2 R@5 | ColPali R@5 |
|---|---|---|---|---|---|---|---|---|
| Health | 0.838 | 0.897 | **0.919** | 0.107 | 0.902 | 0.957 | **1.000** | 0.174 |
| Municipality | 0.839 | **0.878** | 0.858 | 0.065 | 0.956 | 0.933 | **0.978** | 0.089 |
| Legal | 0.820 | 0.835 | **0.857** | 0.189 | 0.937 | 0.937 | **0.968** | 0.270 |
| Finance | 0.782 | 0.778 | **0.809** | 0.067 | 0.865 | 0.890 | **0.935** | 0.103 |
| Energy | 0.662 | **0.849** | 0.770 | 0.081 | 0.767 | **0.931** | 0.888 | 0.129 |
| **Overall** | 0.774 | **0.836** | 0.832 | 0.094 | 0.867 | 0.924 | **0.945** | 0.144 |

*NDCG@5 (left columns) and Recall@5 (right columns). Bold indicates best per sector per metric.*

ColPali performs near randomly across all sectors, consistent with its underlying language model (Gemma 2B) being trained primarily on English. ColQwen2, which uses Qwen2-VL as its backbone, performs competitively with BGE-M3 despite operating on page images rather than extracted text. BM25 remains a strong baseline, particularly in finance.

## Citation

```bibtex
@misc{schmidt2025danragbench,
  title        = {DanRAG-Bench: A Danish Multimodal Document Retrieval Benchmark Across Five Sectors},
  author       = {Schmidt, Johan Hausted},
  year         = {2025},
  institution  = {IT University of Copenhagen},
}
```
