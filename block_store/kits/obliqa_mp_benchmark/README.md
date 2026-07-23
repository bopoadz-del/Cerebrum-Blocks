---
license: apache-2.0
task_categories:
- question-answering
- text-retrieval
language:
- en
pretty_name: ObliQA-MP
size_categories:
- 1K<n<10K
tags:
- regulatory-nlp
- legal-nlp
- compliance
- rag
- multi-hop
- retrieval
- synthetic-data
- benchmark
---

# ObliQA-MP

ObliQA-MP is a **strict multi-passage** regulatory QA benchmark for evaluating retrieval and evidence grounding in **dispersed-evidence compliance queries**.

It contains **2,976 synthetic QA pairs**, derived from ObliQA, and keeps only questions that satisfy strict evidence constraints:

- at least **two connected passages**
- at least **one directly answer-supporting passage**

ObliQA-MP is the **Stage 2 / Tier 2** dataset in the **Synthetic Compliance for Regulatory RAG** benchmark suite.

---

## Dataset Summary

- **Name:** ObliQA-MP
- **Domain:** Financial regulation / compliance
- **Language:** English
- **Format:** JSON (shared schema with ObliQA + additional connectivity labels)
- **Size:** 2,976 QA pairs
- **Source corpus:** same 40-document regulatory corpus used in ObliQA
- **Construction:** derived from ObliQA + LLM-based passage connectivity labeling + strict filtering

ObliQA-MP is designed to be **harder** than ObliQA by focusing on questions whose evidence is genuinely distributed across multiple passages.

---

## Why ObliQA-MP?

In regulatory QA, many retrieval systems can find a topically related passage, but still miss the **actual answer-bearing obligation** or supporting conditions.

ObliQA-MP addresses this by enforcing **precision-oriented multi-passage supervision**. It is suitable for evaluating systems that must:

- retrieve multiple jointly relevant passages,
- distinguish direct vs indirect evidence,
- generate grounded answers from dispersed evidence,
- avoid topical but non-evidentiary retrieval.

---

## Construction Overview (Stage 2)

ObliQA-MP is derived from ObliQA through an additional strict filtering stage.

### Stage 2 pipeline (after ObliQA)

1. **Multi-passage candidate selection**
   - Retain only questions linked to multiple passages
   - Candidate pool: **13,191 questions** (31,037 question–passage pairs)

2. **LLM-based connectivity labeling**
   Each question–passage pair is labeled as:
   - `Directly Connected`
   - `Indirectly Connected`
   - `Not Connected`

   A short textual justification (`ShortReason`) is also produced.

3. **Strict evidence filtering**
   Keep a question only if:
   - it has **≥2 connected passages** (`Direct` or `Indirect`)
   - and **≥1 Directly Connected passage**

This yields the final **2,976 QA pairs**.

---

## Data Splits

ObliQA-MP is released with train / validation / test splits.

### Split Sizes (Total QA pairs)

- **Train:** 2,083
- **Validation:** 446
- **Test:** 447

### Distribution by number of associated passages

ObliQA-MP includes only questions with **2 or more associated passages** by construction.

---

## Schema

ObliQA-MP uses the same base schema as ObliQA, with two additional passage-level fields.

### Top-level fields

- `QuestionID` (string, UUID)
- `Question` (string)
- `Passages` (list of objects)

### `Passages[]` fields

- `DocumentID` (int)
- `PassageID` (string)
- `Passage` (string)
- `Connection` (enum)
  - `Directly Connected`
  - `Indirectly Connected`
  - `Not Connected`
- `ShortReason` (string)

These labels allow more fine-grained retrieval and grounding analysis.

---

## Example Format

```json
{
  "QuestionID": "uuid-string",
  "Question": "Under what conditions must a firm ...?",
  "Passages": [
    {
      "DocumentID": 5,
      "PassageID": "GEN_2.4.1",
      "Passage": "A firm must ...",
      "Connection": "Directly Connected",
      "ShortReason": "Contains the obligation and actor required to answer the question."
    },
    {
      "DocumentID": 5,
      "PassageID": "GEN_2.4.2",
      "Passage": "This applies when ...",
      "Connection": "Indirectly Connected",
      "ShortReason": "Provides a condition/exception that supports the answer context."
    }
  ]
} 
```

## Intended Uses

ObliQA-MP is intended for:

### 1) Strict retrieval benchmarking (multi-passage)

Evaluate systems on:
-   multi-passage retrieval
-   evidence precision
-   ranking quality under dispersed supervision
    
**Recommended metrics:**

-   **Recall@10**
-   **MAP@10**
-   **nDCG@10** (optional) 

### 2) Grounded answer generation from dispersed evidence

Use top-k retrieved passages and evaluate whether the generated answer:
-   captures all obligations/conditions 
-   avoids unsupported statements   
-   reflects evidence across multiple passages  

### 3) Error diagnosis with connectivity labels

The `Connection` field enables analysis such as:
-   retrieving topically related but non-connected passages    
-   missing direct evidence while retrieving only indirect support   
-   over-reliance on one passage in a multi-passage question
----------

## Benchmark Difficulty

ObliQA-MP is intentionally more challenging than ObliQA.
In the benchmark paper, under the same BM25 retrieval setting, **Recall@10** drops substantially when moving from ObliQA to ObliQA-MP, quantifying the difficulty of strict multi-passage supervision and dispersed evidence retrieval.

This makes ObliQA-MP useful for testing:
-   stronger retrievers  
-   re-rankers  
-   graph-aware retrieval
-   evidence selection modules
-   multi-hop RAG pipelines
    
----------

## Recommended Evaluation Setup

For reproducibility and cross-tier comparison, report:

-   **Tier:** `ObliQA-MP`
-   **Split:** train / validation / test
-   **Retrieval unit:** passage 
-   **Cutoff k:** typically `k=10`   
-   **Generation setup:** model + prompting (if applicable)
-   **Grounding metrics:** e.g., RePASs (or equivalent)

If you compare to ObliQA, use the same retrieval/generation configuration.

----------

## Limitations

-   **Synthetic benchmark:** question phrasing may not fully match real compliance users
-   **LLM-based connectivity labels:** high-precision filtering, but not expert adjudication
-   **Passage-level supervision:** no span-level evidence annotations  
-   **Jurisdiction/style dependence:** built from one regulatory authority corpus; transfer should be validated    

ObliQA-MP should be viewed as a strict synthetic benchmark for method comparison, not legal advice.

----------

## Relationship to ObliQA

ObliQA-MP is the strict multi-passage companion to ObliQA:

-   **ObliQA:** larger, broader, easier tier (obligation-grounded; NLI-filtered)
-   **ObliQA-MP:** smaller, stricter, harder tier (connectivity-labeled multi-passage)
    

A common workflow is:
1.  Tune retrieval/generation on **ObliQA** 
2.  Stress-test evidence precision and multi-passage grounding on **ObliQA-MP**
----------

## Citation
```
@inproceedings{gokhan-briscoe-2026-synthetic-compliance,
  title={Synthetic Compliance for Regulatory RAG: A Progressive Benchmark Suite from Simple to Complex Queries},
  author={Tuba Gokhan and Ted Briscoe},
  year={2026}
}

@inproceedings{gokhan-briscoe-2025-grounded,
    title = "Grounded Answers from Multi-Passage Regulations: Learning-to-Rank for Regulatory {RAG}",
    author = "Gokhan, Tuba  and
      Briscoe, Ted",
    editor = "Aletras, Nikolaos  and
      Chalkidis, Ilias  and
      Barrett, Leslie  and
      Goanț{\u{a}}, C{\u{a}}t{\u{a}}lina  and
      Preoțiuc-Pietro, Daniel  and
      Spanakis, Gerasimos",
    booktitle = "Proceedings of the Natural Legal Language Processing Workshop 2025",
    month = nov,
    year = "2025",
    address = "Suzhou, China",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.nllp-1.10/",
    doi = "10.18653/v1/2025.nllp-1.10",
    pages = "135--146",
    ISBN = "979-8-89176-338-8",
}
```