---
license: apache-2.0
language:
  - en
pretty_name: AEC-Bench
multilinguality:
  - monolingual
annotations_creators:
  - expert-generated
language_creators:
  - expert-generated
tags:
  - aec-bench
  - architecture
  - engineering
  - construction
  - vision-language
  - multimodal
  - text
  - image
  - benchmark
  - document-understanding
  - agentic
  - "arxiv:2603.29199"
task_categories:
  - visual-question-answering
  - question-answering
---

# AEC-Bench: A Multimodal Dataset for Architecture, Engineering, and Construction

<div align="center">

[![GitHub](https://img.shields.io/badge/GitHub-nomic--ai%2Faec--bench-181717?logo=github)](https://github.com/nomic-ai/aec-bench) [![arXiv](https://img.shields.io/badge/arXiv-2603.29199-b31b1b.svg)](https://arxiv.org/abs/2603.29199) [![Blog](https://img.shields.io/badge/Blog-Nomic-6366f1)](https://www.nomic.ai/news/aec-bench-a-multimodal-benchmark-for-agentic-systems-in-architecture-engineering-and-construction)

</div>

## Table of contents

| Section | What it covers |
|:--------|:---------------|
| [**Overview**](#overview) | What the dataset contains |
| [**Task taxonomy**](#task-taxonomy) | Scopes, task families, instance counts |
| [**Accessing the dataset**](#accessing-the-dataset) | `manifest.jsonl`, prefetching files from URLs |
| [**License**](#license) | Apache 2.0 |
| [**Citation**](#citation) | BibTeX |

---

## Overview

AEC-Bench is a multimodal dataset of real-world Architecture, Engineering, and Construction (AEC) documents — construction drawings, floor plans, schedules, specifications, and submittals — packaged as **196 task instances** for evaluation and research.

Instances span **9 task types** and three scope levels: **intrasheet** (single-sheet reasoning), **intradrawing** (cross-sheet within a drawing set), and **intraproject** (cross-document project-level reasoning).

---

## Task taxonomy

Tasks are organized in three scope levels, each containing multiple task types:

<table>
  <tr>
    <th align="center">📄 Intra-Sheet<br><sub>Single drawing sheet</sub></th>
    <th align="center">📑 Intra-Drawing<br><sub>Multiple sheets, one set</sub></th>
    <th align="center">🗂 Intra-Project<br><sub>Drawings, specs &amp; submittals</sub></th>
  </tr>
  <tr>
    <td>
      <b>Detail Technical Review</b> — <code>14</code><br>
      <sub>Answer localized technical questions about details</sub><br><br>
      <b>Detail Title Accuracy</b> — <code>15</code><br>
      <sub>Verify whether detail titles match drawn content</sub><br><br>
      <b>Note Callout Accuracy</b> — <code>14</code><br>
      <sub>Check callout text against the referenced element</sub>
    </td>
    <td>
      <b>Cross-Ref Resolution</b> — <code>51</code><br>
      <sub>Identify cross-references that do not resolve to valid targets</sub><br><br>
      <b>Cross-Ref Tracing</b> — <code>24</code><br>
      <sub>Find all source locations referencing a given target detail</sub><br><br>
      <b>Sheet Index Consistency</b> — <code>14</code><br>
      <sub>Compare sheet index entries against title blocks for mismatches</sub>
    </td>
    <td>
      <b>Drawing Navigation</b> — <code>12</code><br>
      <sub>Locate the correct file, sheet, and detail given a query</sub><br><br>
      <b>Spec-Drawing Sync</b> — <code>16</code><br>
      <sub>Identify conflicts between specifications and drawings</sub><br><br>
      <b>Submittal Review</b> — <code>36</code><br>
      <sub>Evaluate submittals for compliance with specs and drawings</sub>
    </td>
  </tr>
  <tr>
    <td align="center"><b>43 instances</b></td>
    <td align="center"><b>89 instances</b></td>
    <td align="center"><b>64 instances</b></td>
  </tr>
</table>

<p align="center">
  <code>196 instances</code> · <code>9 task families</code> · <code>3 scopes</code>
</p>

All instances live under `tasks/<scope>/<type>/<instance>/`.

---

## Accessing the dataset

Each instance directory contains **task data**: **instructions and prompts** (for example `instruction.md`), **configuration** and **grading** material (such as `task.toml`, `gt.json`), **tests**, and **`environment/`**—usually a `Dockerfile` plus **`manifest.jsonl`** listing where to fetch inputs.

**Drawings, specifications, submittals, and other large binaries** are **not stored in this repository**. Obtain them from each **`environment/manifest.jsonl`**: follow the **`key`** URLs and save files under **`environment/<dest>`** as given on each line.

### `environment/manifest.jsonl`

Each instance directory includes **`environment/manifest.jsonl`**: one JSON object per line. Fields:

| Field | Meaning |
|:------|:--------|
| **`key`** | HTTPS URL of the object on `nomic-public-data.com` |
| **`dest`** | Relative path/filename under **`environment/`** where that file should exist locally |

Example (structure only):

```json
{"key": "https://nomic-public-data.com/data/aec-bench-v1/cross-reference-resolution/lear-theater-landscape-01/Bid_set_-_Lear_Theater_240610_new.pdf", "dest": "Bid_set_-_Lear_Theater_240610.pdf"}
```

See for instance [`tasks/intradrawing/cross-reference-resolution/cross-reference-resolution-example/environment/manifest.jsonl`](./tasks/intradrawing/cross-reference-resolution/cross-reference-resolution-example/environment/manifest.jsonl).


**Download every `key` into `environment/<dest>`** for that instance (create parent directories under `environment/` as needed). Use **`curl`** or **`wget`** against each URL in `manifest.jsonl`.

---

## License

This project is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). See [`LICENSE`](./LICENSE) for the full text.

---

## Citation

```bibtex
@misc{mankodiya2026aecbenchmultimodalbenchmarkagentic,
      title={AEC-Bench: A Multimodal Benchmark for Agentic Systems in Architecture, Engineering, and Construction},
      author={Harsh Mankodiya and Chase Gallik and Theodoros Galanos and Andriy Mulyar},
      year={2026},
      eprint={2603.29199},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2603.29199},
}
```
