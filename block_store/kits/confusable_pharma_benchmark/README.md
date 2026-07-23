---
license: apache-2.0
language:
- en
tags:
- medical
- biology
- information-retrieval
- benchmark
- pharmaceutical
- rag-evaluation
size_categories:
- 1K<n<10K
pretty_name: Confusable Pharmaceutical Product Names Retrieval Benchmark
configs:
- config_name: corpus
  data_files:
  - split: test
    path: "data/corpus.jsonl"
- config_name: queries
  default: true
  data_files:
  - split: test
    path: "data/queries.jsonl"
- config_name: qrels
  data_files:
  - split: test
    path: "data/qrels.jsonl"
---

# Confusable Pharmaceutical Product Names: A Retrieval Benchmark

## Dataset Description

A retrieval benchmark for evaluating systems' ability to distinguish between pharmaceutical products with similar-sounding names. This addresses a critical challenge in pharmaceutical RAG systems where confusable drug names (e.g., "Abacavir" vs. "Abametapir") can lead to retrieval errors with regulatory and safety implications.

### Summary

- **931 validated exclusive queries** from FDA Product-Specific Guidance (PSG) documents
- **7,123 corpus chunks** covering 119 pharmaceutical ingredients
- Each query is answerable by exactly one target chunk, testing retrieval precision on confusable entities

### Supported Tasks

- Information Retrieval evaluation on confusable entity disambiguation
- RAG system retrieval component testing
- Hard negative benchmarking

## Dataset Structure

### Files

| File | Entries | Description |
|------|---------|-------------|
| `corpus.jsonl` | 7,123 | FDA PSG document chunks |
| `queries.jsonl` | 931 | Validated exclusive queries |
| `qrels.jsonl` | 931 | Query-document relevance judgments |

### Usage

```python
from datasets import load_dataset

corpus = load_dataset("i-was-here/confusable-pharma-retrieval", "corpus")["test"]
queries = load_dataset("i-was-here/confusable-pharma-retrieval", "queries")["test"]
qrels = load_dataset("i-was-here/confusable-pharma-retrieval", "qrels")["test"]
```

### Data Fields

**queries.jsonl:**
```json
{
  "query_id": "0_0",
  "text": "What is the study design for Abacavir Sulfate?",
  "metadata": {
    "expected_answer": "One in vivo bioequivalence study with pharmacokinetic endpoints.",
    "target_ingredient": "Abacavir Sulfate",
    "is_exclusive": true
  }
}
```

**corpus.jsonl:**
```json
{
  "doc_id": "0",
  "title": "Abacavir Sulfate - Tablet",
  "text": "Draft - Not for Implementation...",
  "metadata": {
    "active_ingredient": "Abacavir Sulfate",
    "dosage_form": "Tablet",
    "route": "Oral",
    "source_url": "https://www.accessdata.fda.gov/drugsatfda_docs/psg/PSG_020977.pdf",
    "document_type": "Draft"
  }
}
```

**qrels.jsonl:**
```json
{"query_id": "0_0", "doc_id": "0", "score": 1}
```

## Validation Statistics

| Status | Count | Percentage |
|--------|-------|------------|
| EXCLUSIVE | 931 | 84.2% |
| NOT_EXCLUSIVE | 173 | 15.6% |
| AMBIGUOUS | 2 | 0.1% |
| **Total** | **1,106** | **100%** |

Only EXCLUSIVE queries (answerable by exactly one chunk) are included in the final dataset.

### Confusable Product Examples

| Product A | Product B | Edit Distance |
|-----------|-----------|---------------|
| Abacavir | Abametapir | 4 |
| Acitretin | Acyclovir | 5 |
| Acetaminophen | Acetazolamide | 5 |
| Albuterol | Atenolol | 4 |

## Dataset Creation

### Pipeline

1. **Corpus Preparation**: Chunked FDA guidance documents
2. **Hard Negative Mining**: Identified confusable pairs via Levenshtein distance (1-5 edits) and embedding similarity
3. **Question Generation**: GPT-4o-mini generated discriminative queries
4. **Validation**: Claude 3 Haiku agent verified query exclusivity

### Source Data

FDA Product-Specific Guidance (PSG) documents containing:
- Study design requirements
- Analytical methods
- Dissolution testing protocols
- Bioequivalence criteria

### Hard Negative Mining

Confusable products identified using:
- Same initial character
- Levenshtein distance: 1 ≤ d ≤ 5
- Top-8 semantically similar chunks by cosine similarity

### Question Generation

- **Model**: GPT-4o-mini
- **Constraints**: Must include target product name, 8-12 words, natural phrasing

### Validation

- **Model**: Claude 3 Haiku (Amazon Bedrock)
- **Method**: Agentic tool-based validation with semantic search
- **Criteria**: Question must be exclusively answerable by target chunk

## Baseline Results

| Method | Recall@20 |
|--------|-----------|
| Embedding Only | 47.4% |
| Contextual Hybrid + Rerank | 89.9% |

## Limitations

- **Domain-Specific**: Limited to FDA pharmaceutical guidance; generalization requires validation
- **LLM Validation**: May have false positives/negatives despite systematic approach
- **Static Corpus**: Based on fixed snapshot; FDA updates require re-run

## Citation

```bibtex
@dataset{confusable_pharma_benchmark_2025,
  author = {Ritivel Labs Inc.},
  title = {Confusable Pharmaceutical Product Names: A Retrieval Benchmark},
  year = {2025},
  publisher = {Hugging Face}
}
```

## License

Apache 2.0

## Contact

For questions and feedback: nirmit@ritivel.com
