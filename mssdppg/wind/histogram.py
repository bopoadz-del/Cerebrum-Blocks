from __future__ import annotations

import csv
from io import StringIO
from typing import List, Tuple


def parse_histogram(csv_text: str) -> List[Tuple[float, float]]:
    if not csv_text.strip():
        return []
    reader = csv.DictReader(StringIO(csv_text.strip()))
    bins: List[Tuple[float, float]] = []
    for row in reader:
        if not row:
            continue
        speed = float(row.get("speed_mps", 0.0))
        prob = float(row.get("prob", 0.0))
        bins.append((speed, prob))
    return bins
