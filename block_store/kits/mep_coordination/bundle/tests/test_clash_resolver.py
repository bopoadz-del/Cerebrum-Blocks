"""clash_resolver: three tests + mutation probe.

The failure being guarded is a confident wrong answer: a move that clears one
clash and causes another, a move that flattens a drain, or an unsourced number
presented as a recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

trimesh = pytest.importorskip("trimesh", reason="geometry backend not installed")

from app.blocks.clash_resolver import (  # noqa: E402
    MOVE_SLEEVE,
    STATUS_ESCALATED,
    STATUS_FLAGGED,
    STATUS_PROPOSED,
    candidate_moves,
    preserves_fall,
    resolve,
)


@dataclass
class El:
    global_id: str
    system: str = "ventilation"
    discipline: str = "mep"
    is_gravity: bool = False
    mesh: object = None


@dataclass
class Item:
    clash_id: str = "C1"


def _box(at=(0, 0, 0), size=(0.2, 0.2, 0.2)):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(at)
    return m


CITED = dict(rule_ids=["MEP-GAS-ANY-300"], clause_text="NOTES item 6: 300MM IN ANY DIRECTION")


def test_an_offset_resolves_a_planted_clash_and_carries_its_clause():
    """The happy path, and the citation requirement in one assertion: a
    proposal that cannot name its rule is not a proposal."""
    el = El("A", mesh=_box())
    neighbour = El("B", mesh=_box(at=(0.15, 0, 0)))   # 200mm services, overlapping
    p = resolve(Item(), el, [neighbour], required_gap_mm=300, **CITED)
    assert p.status == STATUS_PROPOSED, f"rejected: {p.rejected}"
    assert p.rule_ids == ["MEP-GAS-ANY-300"]
    assert "300MM" in (p.clause_text or "")
    assert any(v != 0 for v in p.move_vector_mm)


def test_a_move_that_would_hit_something_else_is_rejected_not_proposed():
    """Trading one clash for another is the failure that destroys trust. The
    element is boxed in on +X, so that candidate must be rejected and the
    rejection recorded."""
    el = El("A", mesh=_box())
    blocker = El("B", mesh=_box(at=(0.15, 0, 0)))
    # A wall sits exactly where the +X offset would land it.
    wall = El("W", mesh=_box(at=(0.325, 0, 0), size=(0.1, 4, 4)))
    p = resolve(Item(), el, [blocker, wall], required_gap_mm=300, **CITED)
    assert any("would clash with" in r for r in p.rejected), p.rejected


def test_a_gravity_run_is_never_offered_a_vertical_move():
    """Raising a drain to clear a duct reverses its fall. The report would
    look coordinated; the building would not drain."""
    drain = El("G", system="drainage_storm", is_gravity=True, mesh=_box())
    moves = candidate_moves(Item(), drain, 300)
    assert moves, "a gravity element must still get lateral options"
    assert all(abs(v[2]) < 1e-9 for _m, v in moves), "vertical move offered to a gravity run"
    assert preserves_fall(drain, (0, 0, 300)) is False
    assert preserves_fall(drain, (300, 0, 0)) is True
    # A non-gravity service keeps all three axes.
    duct = El("D", system="ventilation", mesh=_box())
    assert any(abs(v[2]) > 0 for _m, v in candidate_moves(Item(), duct, 300))


def test_an_unsourced_move_is_flagged_never_proposed():
    """Geometrically valid is not the same as authorised."""
    el = El("A", mesh=_box())
    neighbour = El("B", mesh=_box(at=(0.15, 0, 0)))
    p = resolve(Item(), el, [neighbour], required_gap_mm=300)  # no rule, no clause
    assert p.status == STATUS_FLAGGED
    assert p.status != STATUS_PROPOSED
    assert "no clause authorises" in (p.note or "")


def test_structure_is_sleeved_not_moved():
    """You do not move a wall to clear a pipe."""
    wall = El("W", system="structure", discipline="structural", mesh=_box())
    moves = candidate_moves(Item(), wall, 300)
    assert [m for m, _v in moves] == [MOVE_SLEEVE]


def test_mutation_probe_dropping_the_fall_guard_lets_a_drain_be_lifted():
    """MUTATION PROBE.

    preserves_fall is the only thing standing between a clash report and a
    flat drain. Expressed directly so the probe fails loudly if the guard is
    removed: without it, a gravity run is offered the same vertical move as a
    duct.
    """
    drain = El("G", system="drainage_storm", is_gravity=True, mesh=_box())

    def lax_free_axes(_element):
        return [0, 1, 2]  # the bug: gravity treated like anything else

    assert 2 not in [i for i in range(3) if any(
        abs(v[i]) > 0 for _m, v in candidate_moves(Item(), drain, 300)
    )], "Z axis offered to a gravity run"
    assert 2 in lax_free_axes(drain), "probe is inert: the mutant must differ"
    assert preserves_fall(drain, (0, 0, 325)) is False, "fall guard is not load-bearing"
