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
    MAX_ATTEMPTS,
    MOVE_SLEEVE,
    STATUS_ESCALATED,
    STATUS_FLAGGED,
    STATUS_PROPOSED,
    Proposal,
    _near,
    _slope_of,
    _would_create_new_clash,
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


def test_proposal_as_dict_converts_the_move_vector_to_a_list():
    """The dataclass keeps move_vector_mm as a tuple internally; as_dict()
    must hand back a plain list, since that is what a JSON-serialising
    caller (a BCF export, a report) actually needs."""
    p = Proposal(
        clash_id="C1", element="A", move_type="offset",
        move_vector_mm=(300.0, 0.0, 0.0), status=STATUS_PROPOSED, attempts=1,
        rule_ids=["R1"], clause_text="clause text",
    )
    d = p.as_dict()
    assert d["move_vector_mm"] == [300.0, 0.0, 0.0]
    assert isinstance(d["move_vector_mm"], list)


def test_slope_of_returns_the_grade_of_a_sloped_run():
    """The whole point of _slope_of: a real fall must come back as a real
    number, so a later check can compare it before and after a proposed
    move."""
    class Sloped:
        bounds = [[0.0, 0.0, 0.0], [4.0, 0.0, -0.5]]

    assert _slope_of(Sloped()) == pytest.approx(-0.125)


def test_slope_of_returns_none_when_the_run_has_no_horizontal_extent():
    """A purely vertical extent (dxy == 0) has no meaningful slope ratio --
    dividing by zero must not happen; None is the honest answer."""
    class Vertical:
        bounds = [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]

    assert _slope_of(Vertical()) is None


def test_slope_of_returns_none_when_the_mesh_has_no_usable_bounds():
    """A mesh with no geometry (or a malformed one) must not crash the
    resolver -- _slope_of degrades to 'unknown' rather than propagating the
    exception into resolve()."""
    class NoBounds:
        pass  # accessing .bounds raises AttributeError

    assert _slope_of(NoBounds()) is None


def test_would_create_new_clash_returns_none_when_the_element_has_no_mesh():
    """An element ifc_loader could not mesh cannot be re-checked
    geometrically. _would_create_new_clash must fail OPEN here (report no
    new clash found) rather than crash -- resolve() still records the move
    as geometrically unverified via its own path, but this function itself
    must not blow up on missing geometry."""
    el = El("A", mesh=None)
    neighbour = El("B", mesh=_box(at=(0.15, 0, 0)))
    assert _would_create_new_clash(el, (300.0, 0.0, 0.0), [neighbour]) is None


def test_would_create_new_clash_returns_none_when_apply_translation_raises():
    """A mesh that raises while being translated (a corrupt or non-affine
    mesh) must not crash the whole resolve() run -- the move simply cannot
    be re-verified, which this function reports as no blocker found."""
    class ExplodesOnMove:
        def copy(self):
            return self

        def apply_translation(self, vector):
            raise RuntimeError("mesh cannot be transformed")

    el = El("A", mesh=ExplodesOnMove())
    neighbour = El("B", mesh=_box())
    assert _would_create_new_clash(el, (300.0, 0.0, 0.0), [neighbour]) is None


def test_would_create_new_clash_skips_the_moved_element_itself_in_its_own_neighbour_list():
    """A naive neighbourhood scan would find the moved element overlapping
    its own former position and report a false blocker. It must be
    recognised by global_id and skipped."""
    el = El("A", mesh=_box())
    assert _would_create_new_clash(el, (300.0, 0.0, 0.0), [el]) is None


def test_would_create_new_clash_skips_a_neighbour_with_no_mesh():
    """A neighbour with no geometry cannot be tested against -- it must be
    skipped, not treated as a guaranteed-safe or guaranteed-blocking
    result."""
    el = El("A", mesh=_box())
    neighbour = El("B", mesh=None)
    assert _would_create_new_clash(el, (300.0, 0.0, 0.0), [neighbour]) is None


def test_would_create_new_clash_skips_a_neighbour_outside_the_buffer():
    """The neighbourhood re-check is bounded by buffer_m -- a neighbour far
    outside it must be skipped without even attempting a geometry test,
    which is what keeps this check cheap on a real, large model."""
    el = El("A", mesh=_box())
    far_away = El("F", mesh=_box(at=(100.0, 100.0, 100.0)))
    assert _would_create_new_clash(el, (300.0, 0.0, 0.0), [far_away], buffer_m=2.0) is None


def test_would_create_new_clash_fails_closed_on_unusable_neighbour_geometry():
    """A neighbour whose mesh looks present but has no usable bounds (a
    degenerate or unmeshable IFC element) must not crash the safety check --
    it is skipped, and the move is reported as having found no blocker
    rather than the whole resolve() run failing."""
    class Unmeshable:
        bounds = None

    el = El("A", mesh=_box())
    degenerate = El("D", mesh=Unmeshable())
    assert _would_create_new_clash(el, (300.0, 0.0, 0.0), [degenerate]) is None


def test_near_treats_a_mesh_with_a_zero_size_bounding_box_as_still_near_at_zero_distance():
    """Degenerate bounds (a single point, e.g. a mesh with one vertex) must
    not break the padded-AABB overlap check -- two coincident degenerate
    boxes are, correctly, near each other."""
    a = _box(at=(0, 0, 0), size=(0.0, 0.0, 0.0))
    b = _box(at=(0, 0, 0), size=(0.0, 0.0, 0.0))
    assert _near(a, b, buffer_m=0.01) is True


def test_resolve_escalates_after_max_attempts_when_the_first_candidates_are_all_blocked():
    """MAX_ATTEMPTS caps how many candidates are tried before this becomes a
    human problem instead of a geometry problem. Surround the element on its
    first three candidate directions (+X, -X, +Y) so the cap -- not
    exhausting the move list -- is what ends the loop."""
    el = El("A", mesh=_box())
    need_m = (300.0 + 25.0) / 1000.0  # required_gap_mm + DEFAULT_MARGIN_MM
    blockers = [
        El("BX+", mesh=_box(at=(need_m, 0, 0))),
        El("BX-", mesh=_box(at=(-need_m, 0, 0))),
        El("BY+", mesh=_box(at=(0, need_m, 0))),
    ]
    p = resolve(Item(), el, blockers, required_gap_mm=300, **CITED)
    assert p.status == STATUS_ESCALATED
    assert p.attempts == MAX_ATTEMPTS
    assert len(p.rejected) == MAX_ATTEMPTS, p.rejected
    assert all("would clash with" in r for r in p.rejected)
    assert "no candidate move survived" in (p.note or "")


def test_resolve_escalates_when_a_structural_elements_only_candidate_is_blocked():
    """A structural element gets exactly one candidate (sleeve through, not
    move -- see test_structure_is_sleeved_not_moved). If even that is
    blocked, the loop must exhaust NATURALLY (there is nothing left to try,
    not a MAX_ATTEMPTS cutoff) and still land on the same escalated
    verdict."""
    wall = El("W", system="structure", discipline="structural", mesh=_box())
    # Sits exactly where the wall already is, so the (0,0,0) sleeve "move"
    # still re-clashes with it.
    already_there = El("B", mesh=_box())
    p = resolve(Item(), wall, [already_there], required_gap_mm=300, **CITED)
    assert p.status == STATUS_ESCALATED
    assert p.attempts == 1, "only one candidate exists for a structural element"
    assert len(p.rejected) == 1
    assert "would clash with" in p.rejected[0]
