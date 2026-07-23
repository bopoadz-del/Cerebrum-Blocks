import json
import zipfile
import random
import re
from pathlib import Path
from collections import Counter, defaultdict
import hashlib

kit_dir = Path.home() / "Cerebrum-Blocks/block_store/kits/enterpriserag_benchmark"
zip_path = kit_dir / "all_documents.zip"

# Load inventory
print("Loading inventory...")
records = []
with open(kit_dir / "file_inventory.jsonl") as f:
    for line in f:
        records.append(json.loads(line))

print(f"Loaded {len(records)} records")

# Exact duplicates by hash
hashes = Counter(r["sha256"] for r in records if r["sha256"])
exact_dup_groups = {h: c for h, c in hashes.items() if c > 1}
exact_dup_files = sum(c - 1 for c in exact_dup_groups.values())
exact_dup_rate = exact_dup_files / len(records)
print(f"Exact duplicate groups: {len(exact_dup_groups)}")
print(f"Exact duplicate files (excluding first): {exact_dup_files}")
print(f"Exact duplicate rate: {exact_dup_rate:.4f}")

# Source type distribution
source_types = Counter()
for r in records:
    parts = r["path"].split("/")
    if parts:
        source_types[parts[0]] += 1
print("Source type distribution:")
for st, cnt in source_types.most_common():
    print(f"  {st}: {cnt}")

# Sample documents stratified by source type
sample_size_per_source = 20
sampled = []
by_source = defaultdict(list)
for r in records:
    parts = r["path"].split("/")
    st = parts[0] if parts else "unknown"
    by_source[st].append(r)

random.seed(42)
with zipfile.ZipFile(zip_path, "r") as zf:
    for st, items in by_source.items():
        chosen = random.sample(items, min(sample_size_per_source, len(items)))
        for r in chosen:
            try:
                content = zf.read(r["path"]).decode("utf-8", errors="replace")
                sampled.append({
                    "path": r["path"],
                    "size": r["size"],
                    "source_type": st,
                    "content": content[:2000]
                })
            except Exception as e:
                print(f"Error reading {r['path']}: {e}")

with open(kit_dir / "sample_docs.json", "w", encoding="utf-8") as f:
    json.dump(sampled, f, ensure_ascii=False, indent=2)

print(f"Sampled {len(sampled)} documents")

# Analyze questions
print("Analyzing questions...")
questions = []
with open(kit_dir / "questions.jsonl", encoding="utf-8") as f:
    for line in f:
        questions.append(json.loads(line))

q_types = Counter(q["question_type"] for q in questions)
print("Question types:")
for qt, cnt in q_types.most_common():
    print(f"  {qt}: {cnt}")

# Check expected_doc_ids coverage
all_doc_ids_in_questions = set()
for q in questions:
    all_doc_ids_in_questions.update(q.get("expected_doc_ids", []))
print(f"Unique doc IDs referenced in questions: {len(all_doc_ids_in_questions)}")

# Extract doc IDs from file paths
doc_id_pattern = re.compile(r"dsid_[a-f0-9]{32}")
doc_ids_in_corpus = set()
for r in records:
    m = doc_id_pattern.search(r["path"])
    if m:
        doc_ids_in_corpus.add(m.group())
print(f"Unique doc IDs in corpus paths: {len(doc_ids_in_corpus)}")

missing_doc_ids = all_doc_ids_in_questions - doc_ids_in_corpus
print(f"Question doc IDs missing from corpus paths: {len(missing_doc_ids)}")
if missing_doc_ids:
    print(f"  Examples: {list(missing_doc_ids)[:10]}")

# Write summary
summary = {
    "total_files": len(records),
    "total_bytes": sum(r["size"] for r in records),
    "exact_duplicate_groups": len(exact_dup_groups),
    "exact_duplicate_files": exact_dup_files,
    "exact_duplicate_rate": exact_dup_rate,
    "source_type_distribution": dict(source_types.most_common()),
    "question_count": len(questions),
    "question_type_distribution": dict(q_types.most_common()),
    "question_doc_ids": len(all_doc_ids_in_questions),
    "corpus_doc_ids": len(doc_ids_in_corpus),
    "missing_question_doc_ids": len(missing_doc_ids)
}
with open(kit_dir / "analysis_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
