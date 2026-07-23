import json
import zipfile
import random
import re
import hashlib
from pathlib import Path
from collections import defaultdict

kit_dir = Path.home() / "Cerebrum-Blocks/block_store/kits/enterpriserag_benchmark"
zip_path = kit_dir / "all_documents.zip"

# Load inventory, sample docs
with open(kit_dir / "file_inventory.jsonl") as f:
    records = [json.loads(line) for line in f]

# Filter to actual .txt documents
txt_records = [r for r in records if r["path"].endswith(".txt")]
print(f"Total .txt documents: {len(txt_records)}")

random.seed(123)
sample_size = 2000
sample = random.sample(txt_records, min(sample_size, len(txt_records)))

# Read sample contents
print("Reading sample...")
contents = {}
with zipfile.ZipFile(zip_path, "r") as zf:
    for r in sample:
        try:
            text = zf.read(r["path"]).decode("utf-8", errors="ignore")
            # normalize
            text = re.sub(r"\s+", " ", text.lower())
            contents[r["path"]] = text
        except Exception as e:
            print(f"Error reading {r['path']}: {e}")

print(f"Read {len(contents)} sample docs")

# Build word shingles (5-word)
def get_shingles(text, k=5):
    words = text.split()
    return set(" ".join(words[i:i+k]) for i in range(max(0, len(words)-k+1)))

# MinHash with 128 permutations, LSH with 16 bands x 8 rows
num_hashes = 64
num_bands = 8
rows_per_band = num_hashes // num_bands

# Generate random hash functions (using sha256 of shingle + salt)
salts = [str(i).encode() for i in range(num_hashes)]

def minhash(shingles):
    sig = []
    for salt in salts:
        m = float('inf')
        for s in shingles:
            h = hash((s, salt)) & 0xFFFFFFFFFFFFFFFF
            if h < m:
                m = h
        sig.append(m)
    return sig

# Build signatures and LSH buckets
print("Building signatures...")
sigs = {}
buckets = defaultdict(set)
for idx, (path, text) in enumerate(contents.items()):
    shingles = get_shingles(text)
    if not shingles:
        continue
    sig = minhash(shingles)
    sigs[path] = sig
    for b in range(num_bands):
        band = tuple(sig[b*rows_per_band:(b+1)*rows_per_band])
        buckets[(b, band)].add(path)

# Candidate pairs from same bucket
candidates = set()
for bucket_paths in buckets.values():
    bp = sorted(bucket_paths)
    for i in range(len(bp)):
        for j in range(i+1, len(bp)):
            candidates.add((bp[i], bp[j]))

print(f"Candidate pairs: {len(candidates)}")

# Compute exact Jaccard for candidates
def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0

near_duplicates = []
for p1, p2 in candidates:
    s1 = get_shingles(contents[p1])
    s2 = get_shingles(contents[p2])
    sim = jaccard(s1, s2)
    if sim >= 0.8:
        near_duplicates.append((p1, p2, sim))

print(f"Near-duplicate pairs (>=0.8): {len(near_duplicates)}")

# Estimate near-duplicate rate: unique docs involved
involved = set()
for p1, p2, _ in near_duplicates:
    involved.add(p1)
    involved.add(p2)

estimated_rate = len(involved) / len(contents)
print(f"Docs involved in near-duplicates: {len(involved)} / {len(contents)} = {estimated_rate:.4f}")

summary = {
    "sample_size": len(contents),
    "candidate_pairs": len(candidates),
    "near_duplicate_pairs": len(near_duplicates),
    "docs_involved": len(involved),
    "estimated_near_duplicate_rate": estimated_rate
}
with open(kit_dir / "near_duplicate_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
