---
license: mit
task_categories:
  - question-answering
  - text-retrieval
language:
  - en
tags:
  - conversational-ir
  - information-retrieval
  - multi-turn
  - reasoning
  - benchmark
size_categories:
  - 1K<n<10K
pretty_name: RECOR Benchmark
dataset_info:
  - config_name: benchmark
    description: Multi-turn conversational queries with reasoning
  - config_name: corpus
    description: Document corpus (positive and negative documents combined)
viewer: true
configs:
  - config_name: benchmark
    data_files:
      - split: biology
        path: "data/benchmark/biology_benchmark.jsonl"
      - split: earth_science
        path: "data/benchmark/earth_science_benchmark.jsonl"
      - split: economics
        path: "data/benchmark/economics_benchmark.jsonl"
      - split: psychology
        path: "data/benchmark/psychology_benchmark.jsonl"
      - split: robotics
        path: "data/benchmark/robotics_benchmark.jsonl"
      - split: sustainable_living
        path: "data/benchmark/sustainable_living_benchmark.jsonl"
      - split: Drones
        path: "data/benchmark/Drones_benchmark.jsonl"
      - split: hardware
        path: "data/benchmark/hardware_benchmark.jsonl"
      - split: law
        path: "data/benchmark/law_benchmark.jsonl"
      - split: medicalsciences
        path: "data/benchmark/medicalsciences_benchmark.jsonl"
      - split: politics
        path: "data/benchmark/politics_benchmark.jsonl"
  - config_name: corpus
    data_files:
      - split: biology
        path: "data/corpus/biology_documents.jsonl"
      - split: earth_science
        path: "data/corpus/earth_science_documents.jsonl"
      - split: economics
        path: "data/corpus/economics_documents.jsonl"
      - split: psychology
        path: "data/corpus/psychology_documents.jsonl"
      - split: robotics
        path: "data/corpus/robotics_documents.jsonl"
      - split: sustainable_living
        path: "data/corpus/sustainable_living_documents.jsonl"
      - split: Drones
        path: "data/corpus/Drones_documents.jsonl"
      - split: hardware
        path: "data/corpus/hardware_documents.jsonl"
      - split: law
        path: "data/corpus/law_documents.jsonl"
      - split: medicalsciences
        path: "data/corpus/medicalsciences_documents.jsonl"
      - split: politics
        path: "data/corpus/politics_documents.jsonl"
---

# RECOR: Reasoning-focused Multi-turn Conversational Retrieval Benchmark

A benchmark for evaluating reasoning-intensive conversational information retrieval systems.

## Statistics

| Metric | Value |
|--------|-------|
| Total Conversations | 707 |
| Total Turns | 2,971 |
| Domains | 11 |
| Avg. Turns per Conversation | 4.2 |

## Domains

| Source | Domains |
|--------|---------|
| BRIGHT | biology, earth_science, economics, psychology, robotics, sustainable_living |
| StackExchange | Drones, hardware, law, medicalsciences, politics |

### Per-Domain Statistics

| Domain | Conversations | Turns |
|--------|---------------|-------|
| biology | 85 | 362 |
| earth_science | 98 | 454 |
| economics | 74 | 288 |
| psychology | 84 | 333 |
| robotics | 68 | 259 |
| sustainable_living | 78 | 319 |
| Drones | 37 | 142 |
| hardware | 46 | 188 |
| law | 50 | 230 |
| medicalsciences | 44 | 183 |
| politics | 43 | 213 |

## Dataset Structure

### Subsets and Splits

| Subset | Description |
|--------|-------------|
| `benchmark` | 707 multi-turn conversations |
| `corpus` | Document corpus (positive + negative) |

Each subset has **11 domain splits**:

| Source | Splits |
|--------|--------|
| BRIGHT | `biology`, `earth_science`, `economics`, `psychology`, `robotics`, `sustainable_living` |
| StackExchange | `Drones`, `hardware`, `law`, `medicalsciences`, `politics` |

### Data Fields

**Benchmark (conversations):**

| Field | Description |
|-------|-------------|
| `id` | Unique conversation identifier |
| `task` | Domain name |
| `original_query` | Initial user question |
| `original_answer` | Answer to the initial question |
| `turns` | List of conversation turns |
| `metadata` | Conversation metadata (see below) |

**Metadata fields:**

| Field | Description |
|-------|-------------|
| `num_turns` | Number of conversation turns |
| `gold_doc_count` | Total number of relevant documents |
| `version` | Dataset version |
| `created_at` | Timestamp of creation |
| `source` | Data source (bright or annotated_data) |
| `method` | Generation method |

**Each turn contains:**

| Field | Description |
|-------|-------------|
| `turn_id` | Turn number (1-indexed) |
| `query` | User question for this turn |
| `answer` | Gold answer |
| `gold_doc_ids` | List of relevant document IDs |
| `conversation_history` | Previous turns context |
| `subquestion_reasoning` | Reasoning for the follow-up question |
| `subquestion_reasoning_metadata` | Structured reasoning metadata (see below) |

**subquestion_reasoning_metadata:**

| Field | Description |
|-------|-------------|
| `target_information` | What information the query seeks |
| `relevance_signals` | Keywords/concepts indicating relevance |
| `irrelevance_signals` | Keywords/concepts indicating irrelevance |

**Corpus (documents):**

| Field | Description |
|-------|-------------|
| `doc_id` | Unique document identifier |
| `content` | Document text |

## Usage

```python
from datasets import load_dataset

# Load a specific domain
biology_benchmark = load_dataset("RECOR-Benchmark/RECOR", "benchmark", split="biology")
biology_corpus = load_dataset("RECOR-Benchmark/RECOR", "corpus", split="biology")

# Load all domains for a subset
all_benchmarks = load_dataset("RECOR-Benchmark/RECOR", "benchmark")  # Returns all splits
all_corpus = load_dataset("RECOR-Benchmark/RECOR", "corpus")  # Returns all splits
# Access specific domain: all_benchmarks["biology"], all_corpus["economics"], etc.

# Get relevant documents for a conversation turn
conv = biology_benchmark[0]
turn = conv["turns"][0]
gold_ids = turn["gold_doc_ids"]
relevant_docs = [doc for doc in biology_corpus if doc["doc_id"] in gold_ids]

# Available splits (domains):
# biology, earth_science, economics, psychology, robotics, sustainable_living
# Drones, hardware, law, medicalsciences, politics
```

### Iterate Through Conversations

```python
for conv in biology_benchmark:
    print(f"ID: {conv['id']}")
    for turn in conv["turns"]:
        print(f"  Turn {turn['turn_id']}: {turn['query']}")
```

## File Structure

```
data/
├── benchmark/           # Conversations (11 files)
│   └── {domain}_benchmark.jsonl
└── corpus/              # Documents (11 files)
    └── {domain}_documents.jsonl
```

## Evaluation

For evaluation code and metrics, see the [GitHub Repository](https://github.com/RECOR-Benchmark/RECOR).

## License

MIT License
