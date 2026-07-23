import json
import zipfile
import re
from pathlib import Path
from collections import Counter

kit_dir = Path.home() / "Cerebrum-Blocks/block_store/kits/enterpriserag_benchmark"
zip_path = kit_dir / "all_documents.zip"

# Validate top-level JSONL files
def validate_jsonl(path):
    records = []
    malformed = 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                malformed += 1
                print(f"Malformed line {i} in {path}: {e}")
    return records, malformed

questions, q_malformed = validate_jsonl(kit_dir / "questions.jsonl")
extra, e_malformed = validate_jsonl(kit_dir / "extra_questions.jsonl")

print(f"questions.jsonl: {len(questions)} records, {q_malformed} malformed")
print(f"extra_questions.jsonl: {len(extra)} records, {e_malformed} malformed")

# Check schema completeness
required_q_fields = {"question_id", "question_type", "source_types", "question", "expected_doc_ids", "gold_answer", "answer_facts"}
missing_fields = []
for q in questions:
    missing = required_q_fields - set(q.keys())
    if missing:
        missing_fields.append((q.get("question_id"), missing))
print(f"Questions missing required fields: {len(missing_fields)}")
if missing_fields[:5]:
    print(missing_fields[:5])

# Extract all doc IDs from corpus
with zipfile.ZipFile(zip_path, "r") as zf:
    doc_id_pattern = re.compile(r"dsid_[a-f0-9]{32}")
    corpus_doc_ids = set()
    for info in zf.infolist():
        if info.is_dir():
            continue
        m = doc_id_pattern.search(info.filename)
        if m:
            corpus_doc_ids.add(m.group())

# Check question doc IDs
q_doc_ids = set()
for q in questions:
    q_doc_ids.update(q.get("expected_doc_ids", []))
for q in extra:
    q_doc_ids.update(q.get("expected_doc_ids", []))

missing = q_doc_ids - corpus_doc_ids
print(f"Doc IDs referenced by questions/extra: {len(q_doc_ids)}")
print(f"Missing from corpus: {len(missing)}")

# Check for duplicated question IDs
q_ids = [q["question_id"] for q in questions]
dup_qids = [item for item, count in Counter(q_ids).items() if count > 1]
print(f"Duplicate question IDs: {len(dup_qids)}")

# Check duplicated expected_doc_ids within same question
same_doc_in_q = []
for q in questions:
    ids = q.get("expected_doc_ids", [])
    if len(ids) != len(set(ids)):
        same_doc_in_q.append(q["question_id"])
print(f"Questions with duplicated expected_doc_ids: {len(same_doc_in_q)}")
if same_doc_in_q:
    print(same_doc_in_q[:10])

# Language check on sample of docs
import random
random.seed(7)
sample_paths = random.sample([info.filename for info in zipfile.ZipFile(zip_path, "r").infolist() if not info.is_dir() and info.filename.endswith(".txt")], 100)
with zipfile.ZipFile(zip_path, "r") as zf:
    texts = [zf.read(p).decode("utf-8", errors="ignore") for p in sample_paths]

# Very simple English heuristic
english_markers = ["the", "and", "of", "to", "a", "in", "is", "for", "that", "with"]
def looks_english(text):
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words:
        return False
    count = sum(1 for w in words if w in english_markers)
    return count / len(words) > 0.05

english_count = sum(1 for t in texts if looks_english(t))
print(f"English-looking sample docs: {english_count}/100")

summary = {
    "questions_count": len(questions),
    "extra_questions_count": len(extra),
    "questions_malformed": q_malformed,
    "extra_malformed": e_malformed,
    "questions_missing_fields": len(missing_fields),
    "unique_question_doc_ids": len(q_doc_ids),
    "missing_question_doc_ids": len(missing),
    "duplicate_question_ids": len(dup_qids),
    "questions_with_repeated_expected_doc_ids": len(same_doc_in_q),
    "english_sample_ratio": english_count / 100
}
with open(kit_dir / "validation_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
