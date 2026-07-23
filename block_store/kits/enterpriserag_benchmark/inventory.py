import json
import hashlib
import zipfile
import os
from pathlib import Path
from collections import Counter

kit_dir = Path.home() / "Cerebrum-Blocks/block_store/kits/enterpriserag_benchmark"
zip_path = kit_dir / "all_documents.zip"

# Inventory external/top-level files
external_files = ["LICENSE", "README.md", "questions.jsonl", "extra_questions.jsonl", "all_documents.zip"]
external_inventory = []
for name in external_files:
    p = kit_dir / name
    if p.exists():
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        external_inventory.append({
            "path": str(name),
            "size": p.stat().st_size,
            "extension": p.suffix.lower(),
            "sha256": h.hexdigest()
        })

with open(kit_dir / "external_inventory.json", "w") as f:
    json.dump(external_inventory, f, indent=2)

# Inventory zip contents
print("Starting zip inventory...")
inventory_path = kit_dir / "file_inventory.jsonl"
stats = {"total": 0, "bytes": 0, "extensions": Counter(), "malformed": 0}

with zipfile.ZipFile(zip_path, "r") as zf:
    with open(inventory_path, "w") as out:
        for info in zf.infolist():
            if info.is_dir():
                continue
            stats["total"] += 1
            stats["bytes"] += info.file_size
            ext = os.path.splitext(info.filename)[1].lower()
            stats["extensions"][ext] += 1
            h = hashlib.sha256()
            try:
                with zf.open(info) as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
                sha = h.hexdigest()
            except Exception as e:
                sha = None
                stats["malformed"] += 1
                print(f"ERROR reading {info.filename}: {e}")
            record = {
                "path": info.filename,
                "size": info.file_size,
                "extension": ext,
                "sha256": sha
            }
            out.write(json.dumps(record) + "\n")
            if stats["total"] % 10000 == 0:
                print(f"  processed {stats['total']} files...")

stats["extensions"] = dict(stats["extensions"].most_common())
with open(kit_dir / "inventory_stats.json", "w") as f:
    json.dump(stats, f, indent=2)

print("Done.")
print(json.dumps(stats, indent=2))
