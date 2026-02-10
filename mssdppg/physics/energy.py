from __future__ import annotations

from typing import List


def downsample_frames(frames: List[dict], step: int = 5) -> List[dict]:
    if step <= 1:
        return list(frames)
    return frames[::step]
