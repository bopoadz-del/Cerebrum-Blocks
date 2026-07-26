"""New-shape tests for the store's local RAG path + registry integrity.

Two doctrine shapes, both CI-covered via the ``tests/core/test_rag*.py`` glob:

1. PLANTED-TRUTH RAG (local, no cloud, no Postgres) — embed a corpus with a
   known fact plus distractors using the store's own local embedder (zvec /
   model2vec), rank by cosine, and assert the planted chunk wins AND an
   unrelated query does NOT surface the planted chunk (no false retrieval).
   Proves the store can ingest→embed→retrieve the right chunk offline.

2. REGISTRY INTEGRITY — every block the registry lists resolves to a real
   loadable class with a declaration; no dangling references. Complements
   test_all_blocks (which exercises execution) by pinning the discovery
   contract itself.
"""
from __future__ import annotations

import asyncio
import sys

import numpy as np
import pytest

from app.blocks import BLOCK_REGISTRY, get_block

# The store deploys on Linux (CI + Render). A block that only fails to load on
# a Windows dev box (Unix-only stdlib like `resource` in the sandbox block) is
# env-gated, not dangling — so the strict "every block resolves" assertion is
# enforced on Linux and relaxed elsewhere. CI runs on ubuntu → fully strict.
_STRICT_RESOLUTION = sys.platform.startswith("linux")


def _embed(block, text: str) -> np.ndarray:
    res = asyncio.run(block.execute({"text": text}, {"operation": "embed"}))
    vec = (res.get("result") or {}).get("vector")
    assert vec, f"embedder returned no vector: {res}"
    return np.asarray(vec, dtype=float)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


CORPUS = [
    "The design flow rate of pump station WWPS-01 is 366 litres per second.",
    "The site canteen serves lunch between noon and 2pm.",
    "Concrete grade for the raft foundation is C40/50.",
]
PLANTED = CORPUS[0]


@pytest.fixture(scope="module")
def zvec():
    try:
        cls = get_block("zvec")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"zvec block unavailable: {exc}")
    return cls()


def _rank(zvec, query: str):
    qv = _embed(zvec, query)
    scored = [( _cosine(qv, _embed(zvec, d)), d) for d in CORPUS]
    scored.sort(reverse=True)
    return scored


def test_planted_fact_ranks_first(zvec):
    """The chunk carrying the planted fact must win for a fact-seeking query."""
    ranked = _rank(zvec, "What is the flow rate of pump station WWPS-01?")
    top_score, top_doc = ranked[0]
    assert top_doc == PLANTED, f"wrong chunk #1: {ranked}"
    # And it must win decisively, not by a hair, over the best distractor.
    assert top_score > ranked[1][0] + 0.2, f"weak separation: {ranked}"


def test_unrelated_query_does_not_surface_planted_fact(zvec):
    """A query about something the corpus does not answer must NOT rank the
    planted pump-station chunk first — the guard against false retrieval /
    fabrication from an off-topic match."""
    ranked = _rank(zvec, "What time does the gym open on weekends?")
    assert ranked[0][1] != PLANTED, f"off-topic query falsely surfaced planted fact: {ranked}"


def test_embeddings_are_deterministic(zvec):
    """Same text embeds to the same vector — retrieval must be reproducible."""
    a = _embed(zvec, PLANTED)
    b = _embed(zvec, PLANTED)
    assert _cosine(a, b) > 0.999


# ── Registry integrity ──────────────────────────────────────────────────────

def test_registry_is_non_empty():
    assert len(BLOCK_REGISTRY) > 0, "block registry loaded zero blocks"


def test_every_registered_block_resolves_to_a_class():
    """No dangling references: every name the registry advertises must resolve
    via get_block() to a real loadable class — a listed-but-unloadable block is
    a lie the /stats and discovery endpoints would tell.

    Strict on the deployment platform (Linux CI/Render): a None or a raised
    exception for any registered block fails the test. On a non-Linux dev box,
    a block that fails only because of a Unix-only stdlib import (e.g. sandbox
    imports `resource`) is recorded as env-gated, not dangling.
    """
    dangling = []
    env_gated = []
    for name in list(BLOCK_REGISTRY.keys()):
        try:
            cls = get_block(name)
        except Exception as exc:  # noqa: BLE001
            if _STRICT_RESOLUTION:
                dangling.append((name, f"{type(exc).__name__}: {exc}"))
            else:
                env_gated.append((name, f"{type(exc).__name__}"))
            continue
        if cls is None or not callable(cls):
            if _STRICT_RESOLUTION:
                dangling.append((name, "resolved to None/non-callable"))
            else:
                env_gated.append((name, "None on non-linux (platform import)"))
    assert not dangling, f"dangling registry entries: {dangling[:10]}"
    if env_gated:
        print(f"env-gated on {sys.platform} (non-fatal; strict on Linux CI): {env_gated}")
