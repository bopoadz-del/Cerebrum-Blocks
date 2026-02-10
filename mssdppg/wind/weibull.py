from __future__ import annotations

from math import exp
from typing import Iterable, List, Tuple


def bin_probabilities(speeds: Iterable[float], k: float, c: float) -> List[Tuple[float, float]]:
    speeds_list = [float(v) for v in speeds]
    if not speeds_list:
        return []
    pdfs = []
    for v in speeds_list:
        if v <= 0:
            pdfs.append(0.0)
            continue
        pdf = (k / c) * (v / c) ** (k - 1) * exp(-((v / c) ** k))
        pdfs.append(pdf)
    total = sum(pdfs) or 1.0
    return [(v, pdf / total) for v, pdf in zip(speeds_list, pdfs)]
