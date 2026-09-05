"""geometry_engine: the three tests + mutation probe required per block.

These use constructed solids rather than an IFC file on purpose. The defect
being guarded against is a GEOMETRIC one -- bounding boxes calling two
non-touching services a clash -- and a box-vs-mesh disagreement is provable
without any model. A model-level test cannot isolate it, because a real model
mixes the geometry question with parser questions.
"""
from __future__ import annotations

import pytest

trimesh = pytest.importorskip("trimesh", reason="geometry backend not installed")

from app.blocks.geometry_engine import (  # noqa: E402
    KIND_CLASH,
    KIND_CLEAR,
    KIND_CLEARANCE,
    KIND_UNJUDGED,
    METHOD_EXACT,
    aabb_overlaps,
    exact_backend_available,
    judge_pair,
)


def _box(size=(1, 1, 1), at=(0, 0, 0)):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(at)
    return m


def test_interpenetrating_solids_are_a_clash_and_cite_no_rule():
    """A hard clash is a clash under every rule, so it must not depend on
    one being supplied -- and must not invent a citation."""
    a, b = _box(), _box(at=(0.5, 0, 0))
    f = judge_pair("A", "B", a, b)
    assert f.kind == KIND_CLASH
    assert f.rule_id is None
    if exact_backend_available():
        assert f.method == METHOD_EXACT
        assert f.penetration_volume_m3 == pytest.approx(0.5, abs=1e-3)


def test_close_but_not_touching_is_a_clearance_violation_not_a_clash():
    """The distinction the whole kit turns on. 300mm apart, 500mm required:
    nothing touches, but it cannot be built, maintained or insulated."""
    a, b = _box(), _box(at=(1.3, 0, 0))  # 0.3 m gap
    f = judge_pair("A", "B", a, b, required_clearance_m=0.5, rule_id="SBC-501-X")
    assert f.kind == KIND_CLEARANCE
    assert f.distance_m == pytest.approx(0.3, abs=1e-3)
    assert f.rule_id == "SBC-501-X"          # a clearance finding MUST cite
    assert f.required_clearance_m == 0.5


def test_far_apart_is_clear_and_the_same_pair_flips_when_the_rule_tightens():
    """Same geometry, different rule -> different verdict. Proves the rule is
    doing the judging, not a hardcoded threshold hiding in the engine."""
    a, b = _box(), _box(at=(3, 0, 0))  # 2.0 m gap
    assert judge_pair("A", "B", a, b, required_clearance_m=0.5).kind == KIND_CLEAR
    tightened = judge_pair("A", "B", a, b, required_clearance_m=2.5, rule_id="R")
    assert tightened.kind == KIND_CLEARANCE


def test_the_aabb_prefilter_must_pad_by_the_clearance_or_it_hides_violations():
    """The pre-filter's own failure mode. Two boxes 0.3 m apart do NOT
    overlap, so an unpadded filter discards the pair -- and the clearance
    violation in the test above would never be measured. Padding by the
    largest rule is what keeps the filter honest."""
    a = (0, 0, 0, 1, 1, 1)
    b = (1.3, 0, 0, 2.3, 1, 1)
    assert aabb_overlaps(a, b) is False           # unpadded: pair dropped
    assert aabb_overlaps(a, b, pad=0.5) is True   # padded: pair survives


def test_no_geometry_is_reported_unjudged_never_clean():
    """Silence is not a pass. An element the parser could not mesh must be
    visibly unjudged, or a coordination report claims a clean zone it never
    actually looked at."""
    class Unmeshable:
        bounds = None
        vertices = None
        is_watertight = False

        def intersection(self, other):
            raise RuntimeError("no geometry")

        def contains(self, pts):
            raise RuntimeError("no geometry")

    f = judge_pair("A", "B", Unmeshable(), Unmeshable())
    assert f.kind == KIND_UNJUDGED
    assert f.kind != KIND_CLEAR


def test_mutation_probe_bounding_box_verdict_reopens_the_false_positives():
    """MUTATION PROBE.

    The replaced behaviour was "boxes overlap => clash". Expressed directly so
    the probe fails loudly if anyone restores it: two diagonal services whose
    BOXES overlap while the SOLIDS are metres apart. Under the old rule this
    pair is a clash; under this engine it is clear. If those two answers ever
    agree, the engine has regressed to a bounding-box test.
    """
    import numpy as np

    def _diagonal_bar(offset=(0, 0, 0)):
        """A 4 m service running at 45 deg -- the shape an AABB describes worst."""
        m = trimesh.creation.box(extents=(4, 0.2, 0.2))
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 4, (0, 0, 1)))
        m.apply_translation(offset)
        return m

    # Two parallel diagonal services running side by side, 507 mm apart. This
    # is not a contrived shape: it is a cable tray beside a pipe on the same
    # rack. Their upright boxes overlap heavily; the solids never touch.
    mesh_a = _diagonal_bar()
    mesh_b = _diagonal_bar((-0.5, 0.5, 0))

    old_rule_says_clash = aabb_overlaps(mesh_a.bounds.flatten(), mesh_b.bounds.flatten())
    new_verdict = judge_pair("A", "B", mesh_a, mesh_b, required_clearance_m=0.1)

    assert old_rule_says_clash is True, (
        "fixture no longer exercises the defect: the boxes must overlap for "
        "this probe to mean anything"
    )
    assert new_verdict.kind == KIND_CLEAR, (
        "engine agreed with the bounding-box verdict -- the false positive is back"
    )
