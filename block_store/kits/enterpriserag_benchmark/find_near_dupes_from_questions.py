import json
import zipfile
import re
from pathlib import Path
from collections import defaultdict

kit_dir = Path.home() / "Cerebrum-Blocks/block_store/kits/enterpriserag_benchmark"
zip_path = kit_dir / "all_documents.zip"

# Load questions
questions = []
with open(kit_dir / "questions.jsonl", encoding="utf-8") as f:
    for line in f:
        questions.append(json.loads(line))

# Find conflicting_info questions
conflict_qs = [q for q in questions if q["question_type"] == "conflicting_info"]
print(f"Conflicting info questions: {len(conflict_qs)}")

# Map doc_id to path in zip
with zipfile.ZipFile(zip_path, "r") as zf:
    path_by_doc_id = {}
    doc_id_pattern = re.compile(r"dsid_[a-f0-9]{32}")
    for info in zf.infolist():
        if info.is_dir():
            continue
        m = doc_id_pattern.search(info.filename)
        if m:
            path_by_doc_id[m.group()] = info.filename

    def normalize(text):
        text = re.sub(r"\s+", " ", text.lower())
        return text

    def shingles(text, k=5):
        words = text.split()
        return set(" ".join(words[i:i+k]) for i in range(max(0, len(words)-k+1)))

    def jaccard(a, b):
        return len(a & b) / len(a | b) if (a | b) else 0

    results = []
    for q in conflict_qs[:10]:
        doc_ids = q.get("expected_doc_ids", [])
        print(f"\nQuestion {q['question_id']}: {doc_ids}")
        docs = []
        for did in doc_ids:
            path = path_by_doc_id.get(did)
            if path:
                text = normalize(zf.read(path).decode("utf-8", errors="ignore"))
                docs.append((did, path, text))
                print(f"  {did}: {path} ({len(text)} chars)")
        for i in range(len(docs)):
            for j in range(i+1, len(docs)):
                sim = jaccard(shingles(docs[i][2]), shingles(docs[j][2]))
                print(f"  Similarity {docs[i][0]} <-> {docs[j][0]}: {sim:.3f}")
                results.append({
                    "qid": q["question_id"],
                    "doc1": docs[i][0],
                    "doc2": docs[j][0],
                    "similarity": sim
                })

with open(kit_dir / "conflict_similarities.json", "w") as f:
    json.dump(results, f, indent=2)
