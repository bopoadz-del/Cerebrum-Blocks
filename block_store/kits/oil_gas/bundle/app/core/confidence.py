"""Confidence scoring helpers for extraction blocks.

Mirrors the interface expected by ``construction_v2.py`` and other
TypedBlock extraction pipelines. Keeps scoring deterministic and fast.
"""

from typing import Any, Dict, List, Optional


def assess_extraction_confidence(
    result: Dict[str, Any],
    expected_fields: List[str],
    ocr_quality: Optional[float] = None,
) -> Dict[str, Any]:
    """Score how well an extraction result populated expected fields.

    Args:
        result: The extraction result dict.
        expected_fields: Field names that should be present and non-empty.
        ocr_quality: Optional 0-1 quality score to blend in.

    Returns:
        Dict with ``overall`` confidence (0-1), ``field_scores``,
        and ``ocr_quality``.
    """
    scores: List[float] = []
    field_scores: Dict[str, float] = {}

    for field in expected_fields:
        value = result.get(field)
        if value is None:
            score = 0.0
        elif isinstance(value, list):
            score = min(1.0, len(value) / 5.0)
        elif isinstance(value, dict):
            score = min(1.0, len(value) / 3.0)
        elif isinstance(value, (int, float)):
            score = 1.0 if value else 0.0
        elif isinstance(value, str):
            score = 1.0 if value.strip() else 0.0
        else:
            score = 0.8 if value else 0.0

        scores.append(score)
        field_scores[field] = round(score, 2)

    overall = sum(scores) / len(scores) if scores else 0.0
    if ocr_quality is not None:
        overall = overall * 0.7 + max(0.0, min(1.0, ocr_quality)) * 0.3

    return {
        "overall": round(overall, 2),
        "field_scores": field_scores,
        "ocr_quality": ocr_quality,
    }
