---
license: cc-by-4.0
pretty_name: T2-RAGBench
task_categories:
- table-question-answering
- question-answering
language:
- en
tags:
- pdf
- finance
- rag
arxiv: 2506.12071
configs:
- config_name: FinQA
  data_files:
  - split: train
    path: data/FinQA/train/*
  - split: dev
    path: data/FinQA/dev/*
  - split: test
    path: data/FinQA/test/*
- config_name: ConvFinQA
  data_files:
  - split: turn_0
    path: data/ConvFinQA/*
- config_name: TAT-DQA
  data_files:
  - split: train
    path: data/TAT-DQA/train/*
  - split: dev
    path: data/TAT-DQA/dev/*
  - split: test
    path: data/TAT-DQA/test/*
---

# Dataset Card for T2-RAGBench

[**Project Page**](https://t2ragbench.demo.hcds.uni-hamburg.de) | [**Paper**](https://huggingface.co/papers/2506.12071) | [**Code**](https://github.com/uhh-hcds/g4kmu-paper)

## Table of Contents

- [Dataset Card for T2-RAGBench](#dataset-card-for-t2-ragbench)
  - [Table of Contents](#table-of-contents)
  - [Dataset Description](#dataset-description)
    - [Dataset Summary](#dataset-summary)
    - [Supported Tasks](#supported-tasks)
    - [Leaderboards](#leaderboards)
    - [PDF Files](#pdf-files)
    - [Languages](#languages)
  - [Dataset Structure](#dataset-structure)
    - [Data Instances](#data-instances)
    - [Data Fields](#data-fields)
      - [FinQA and ConvFinQA Only](#finqa-and-convfinqa-only)
      - [TAT-DQA Only](#tat-dqa-only)
    - [Data Splits](#data-splits)
  - [Dataset Creation](#dataset-creation)
    - [Curation Rationale](#curation-rationale)
    - [Source Data](#source-data)
    - [Annotations](#annotations)
  - [Personal and Sensitive Information](#personal-and-sensitive-information)
  - [Considerations for Using the Data](#considerations-for-using-the-data)
    - [Social Impact of Dataset](#social-impact-of-dataset)
    - [Discussion of Biases](#discussion-of-biases)
    - [Other Known Limitations](#other-known-limitations)
  - [Additional Information](#additional-information)
    - [Licensing Information](#licensing-information)
    - [Citation Information](#citation-information)
    - [Contributions](#contributions)

---

## IMPORTANT NOTICE:
We deleted VQAonBD from the dataset due to low quality of the question reformulations. If you still want to use it you will find the data in the previous commit history.

## Dataset Description

### Dataset Summary

T2-RAGBench is a benchmark dataset designed to evaluate Retrieval-Augmented Generation (RAG) on financial documents containing both text and tables. It consists of **23,088** context-independent question-answer pairs and over **7300** documents derived from three curated datasets: FinQA, ConvFinQA, and TAT-DQA. Each instance includes a reformulated question, a verified answer, and its supporting context composed of textual and tabular information. It is also possible to use the pdfs directly, as the dataset includes the original PDF files.

### Supported Tasks

- Question Answering (QA)
- Table-based Question Answering (TableQA)
- Retrieval-Augmented Generation (RAG)

### Leaderboards

You can submit your results to the [T2-RAGBench leaderboard](https://t2ragbench.demo.hcds.uni-hamburg.de) to compare your model's performance against others.
The submission guidelines are available on the leaderboard page.

### PDF Files

The dataset includes original PDF files from which the text and tables were extracted. These files can be used for direct document-based tasks or to verify the context of the questions. To download the PDF files clone the this repository and all files will be available in the `data` directory. The files are organized by dataset and split, matching the structure of the dataset.

### Languages

- English

---

## Dataset Structure

### Data Instances

Each instance contains a unique identifier, a question, a context (text and table), and a verified answer.

### Data Fields

For each subset, each sample contains the following fields:

- `id`: Unique identifier for the sample  
- `context_id`: Identifier for the context document  
- `split`: Dataset split (`train`, `dev`, `test`, `turn_0`, or `validation_5`)  
- `question`: Context-independent QA query  
- `program_answer`: Reformulated numeric answer used for evaluation  
- `original_answer`: Original answer from the source dataset  
- `context`: Extracted document text including both textual and tabular information  
- `file_name`: Name of the source PDF file  

#### FinQA and ConvFinQA Only

- `table`: Table content extracted from the PDF in Markdown format  
- `pre_text`: Document text located before the table  
- `post_text`: Document text located after the table  
- `company_name`: Name of the company from the financial report  
- `company_symbol`: Stock ticker symbol of the company  
- `report_year`: Year of the financial report  
- `page_number`: Page number in the PDF where the table was found  
- `company_sector`: Sector classification of the company (e.g., Financials, Energy)  
- `company_industry`: Industry classification of the company  
- `company_headquarters`: Location of the company's headquarters  
- `company_date_added`: Date the company was added to the reference index (e.g., S&P 500)  
- `company_cik`: Central Index Key used by the SEC for company identification  
- `company_founded`: Year the company was founded  


#### TAT-DQA Only

- `company_name`: Name of the company from the financial report  
- `report_year`: Year of the financial report  
- `company_sector`: Sector classification of the company  

### Data Splits

| Subset     | Domain  | # Documents | # QA Pairs | Avg. Tokens/Doc | Avg. Tokens/Question |
|------------|---------|-------------|------------|------------------|-----------------------|
| FinQA      | Finance | 2,789       | 8,281      | 950.4            | 39.2                  |
| ConvFinQA  | Finance | 1,806       | 3,458      | 890.9            | 30.9                  |
| TAT-DQA    | Finance | 2,723       | 11,349     | 915.3            | 31.7                  |
| **Total**  |         | **8,095**   | **32,908** | **803.2**        | **36.3**              |

---

## Dataset Creation

### Curation Rationale

Most existing QA datasets rely on oracle-contexts, which limit their ability to evaluate retrieval quality. T2-RAGBench transforms questions into a context-independent form to evaluate both retrieval and reasoning.

### Source Data

Selected from existing QA datasets: FinQA, ConvFinQA, TAT-DQA. FinQA and ConvFinQA are based on FinTabNet. TAT-DQA is a diverse QA set with a focus on numerical answers.

### Annotations

Questions were reformulated with LLaMA 3.3-70B to ensure context-independence. Human annotators verified a random subset of examples. Reformulated questions showed >80% context-independence compared to <10% in the originals.

---

## Personal and Sensitive Information

Documents originate from public financial filings. No sensitive or personal user data is included. Entity names are real company names extracted from SEC filings.

---

## Considerations for Using the Data

### Social Impact of Dataset

T2-RAGBench encourages the development of RAG systems capable of reasoning over complex, real-world documents, such as those found in finance.

### Discussion of Biases

The dataset focuses on financial documents, and domain-specific biases such as consistent formats or terminology may limit generalizability.

### Other Known Limitations

- Reformulated questions are LLM-generated  
- Performance evaluations may be influenced by prompt templates  
- Dataset focused on finance domain only  

---

## Additional Information

We also have converted other SOTA benchmark in the same format.
They can be found in our collection:
https://huggingface.co/collections/G4KMU/rag-datasets

### Licensing Information

CC-BY-4.0

### Citation Information

```bibtex
@inproceedings{strich-etal-2026-t2,
    title = "T$^2$-{RAGB}ench: Text-and-Table Benchmark for Evaluating Retrieval-Augmented Generation",
    author = "Strich, Jan  and
      Isgorur, Enes Kutay  and
      Trescher, Maximilian  and
      Biemann, Chris  and
      Semmann, Martin",
    editor = "Demberg, Vera  and
      Inui, Kentaro  and
      Marquez, Llu{\'i}s",
    booktitle = "Proceedings of the 19th Conference of the {E}uropean Chapter of the {A}ssociation for {C}omputational {L}inguistics (Volume 1: Long Papers)",
    month = mar,
    year = "2026",
    address = "Rabat, Morocco",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2026.eacl-long.8/",
    doi = "10.18653/v1/2026.eacl-long.8",
    pages = "165--191",
    ISBN = "979-8-89176-380-7"
}
```

### Contributions
This benchmark builds upon the following datasets:

- [FinQA](https://github.com/czyssrs/FinQA): Numerical reasoning over financial documents  
- [ConvFinQA](https://github.com/czyssrs/ConvFinQA): Conversational QA extension of FinQA  
- [TAT-DQA](https://nextplusplus.github.io/TAT-DQA/): Hybrid document QA with tables and text