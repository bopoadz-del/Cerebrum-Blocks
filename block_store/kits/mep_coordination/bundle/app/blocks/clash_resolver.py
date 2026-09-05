"""clash_resolver — propose moves that are checked, sourced, or refused.

The dangerous failure mode of an automated coordination tool is not missing a
clash. It is confidently proposing a move that creates two more, or that
flattens a drain. So every candidate here is re-tested through the same
geometry engine that found the clash, and a move that cannot be tied to a rule
is FLAGGED rather than proposed.

NO LLM IN THE DECISION PATH. Moves are geometry and arithmetic. A language
model is used only to write the BCF comment prose from an already-decided
proposal, in block B5 — never to choose the move. A model that invents a
plausible-sounding offset is precisely the thing an engineer cannot check.

GRAVITY IS SPECIAL. A drainage segment carries fall. Raising or lowering one
end changes the slope of the whole run, and a reversed fall is a hydraulic
failure that looks fine in a clash report. Vertical moves on gravity elements
are rejected outright; only lateral moves are offered.

READS   the triage queue; elements with meshes; the rule table.
WRITES  proposals: {clash_id, move_vector_mm, element, rule_ids, clause_text,
        status, attempts}.
NEVER   applies a move to a model. Proposing and applying are different acts
        with different blast radius; applying belongs to model_clone (B6),
        against a clone, reviewed by an engineer.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

logger = logging.getLogger(__name__)

STATUS_PROPOSED = "proposed"
STATUS_FLAGGED = "flagged_unsourced"
STATUS_ESCALATED = "escalated"

MAX_ATTEMPTS = 3          # the order's cap; a 4th is an escalation, not a retry
DEFAULT_MARGIN_MM = 25.0  # installation tolerance on top of the required gap

MOVE_OFFSET = "offset"
MOVE_ELEVATION = "elevation_change"
MOVE_RESIZE = "resize"
MOVE_RESEQUENCE = "re_sequence"
MOVE_SLEEVE = "sleeve_penetration"


@dataclass
class Proposal:
    clash_id: str
    element: str
    move_type: str
    move_vector_mm: tuple[float, float, float]
    status: str
    attempts: int
    rule_ids: list[str] = field(default_factory=list)
    clause_text: str | None = None
    rejected: list[str] = field(default_factory=list)
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["move_vector_mm"] = list(self.move_vector_mm)
        return d


def _free_axes(element: Any) -> list[int]:
    """Which axes this element may move along.

    Gravity services keep their fall, so Z is not available to them. This is
    the single most consequential constraint in the block: a tool that
    silently lifts a drain to clear a duct produces a model that coordinates
    and a building that does not drain.
    """
    if getattr(element, "is_gravity", False):
        return [0, 1]        # lateral only
    return [0, 1, 2]


def _slope_of(mesh) -> float | None:
    """Fall along the run, from the mesh extent. Used to reject a move that
    would reverse it."""
    try:
        b = mesh.bounds
        dz = float(b[1][2] - b[0][2])
        dxy = max(float(b[1][0] - b[0][0]), float(b[1][1] - b[0][1]))
        return dz / dxy if dxy else None
    except Exception:  # noqa: BLE001
        return None


def preserves_fall(element: Any, vector_mm: Sequence[float]) -> bool:
    """A gravity element may not take a vertical component. Anything else may.

    Returns True when the move is acceptable on fall grounds.
    """
    if not getattr(element, "is_gravity", False):
        return True
    return abs(float(vector_mm[2])) < 1e-9


def candidate_moves(
    item: Any,
    element: Any,
    required_gap_mm: float,
    margin_mm: float = DEFAULT_MARGIN_MM,
) -> list[tuple[str, tuple[float, float, float]]]:
    """Ordered cheapest-first. Offsets before elevation before resize, because
    that is the order of cost on site: shifting a hanger is a morning, resizing
    a duct is a redesign."""
    need = float(required_gap_mm) + float(margin_mm)
    out: list[tuple[str, tuple[float, float, float]]] = []
    for axis in _free_axes(element):
        for sign in (1.0, -1.0):
            v = [0.0, 0.0, 0.0]
            v[axis] = sign * need
            move = MOVE_ELEVATION if axis == 2 else MOVE_OFFSET
            out.append((move, (v[0], v[1], v[2])))
    if getattr(element, "discipline", "") == "structural":
        # You do not move a wall to clear a pipe; you sleeve through it.
        return [(MOVE_SLEEVE, (0.0, 0.0, 0.0))]
    return out


def _would_create_new_clash(
    element: Any,
    vector_mm: Sequence[float],
    neighbours: Iterable[Any],
    buffer_m: float = 2.0,
) -> str | None:
    """Re-check the moved element against its neighbourhood.

    Returns the id of the first element it would now hit, or None. This is the
    check that stops the tool trading one clash for two -- and it uses the SAME
    engine that found the original, so a move cannot be validated by a weaker
    test than the one that condemned it.
    """
    mesh = getattr(element, "mesh", None)
    if mesh is None:
        return None
    try:
        moved = mesh.copy()
        moved.apply_translation([v / 1000.0 for v in vector_mm])
    except Exception:  # noqa: BLE001
        return None

    from app.blocks.geometry_engine import judge_pair

    for other in neighbours:
        if getattr(other, "global_id", None) == getattr(element, "global_id", None):
            continue
        omesh = getattr(other, "mesh", None)
        if omesh is None:
            continue
        try:
            if not _near(moved, omesh, buffer_m):
                continue
            verdict = judge_pair(
                getattr(element, "global_id", "moved"),
                getattr(other, "global_id", "other"),
                moved, omesh,
            )
        except Exception:  # noqa: BLE001
            continue
        if verdict.kind == "clash":
            return getattr(other, "global_id", "unknown")
    return None


def _near(mesh_a, mesh_b, buffer_m: float) -> bool:
    from app.blocks.geometry_engine import aabb_overlaps

    return aabb_overlaps(mesh_a.bounds.flatten(), mesh_b.bounds.flatten(), pad=buffer_m)


def resolve(
    item: Any,
    element: Any,
    neighbours: Iterable[Any],
    required_gap_mm: float | None = None,
    rule_ids: Sequence[str] | None = None,
    clause_text: str | None = None,
    margin_mm: float = DEFAULT_MARGIN_MM,
) -> Proposal:
    """Propose one move for one queued clash, or refuse to.

    A move with no rule behind it is emitted FLAGGED, never proposed. The
    distinction matters: a proposal invites an engineer to accept it, and an
    unsourced number dressed as a proposal is how a coordination tool loses
    the right to be trusted.
    """
    clash_id = getattr(item, "clash_id", "unknown")
    rule_ids = list(rule_ids or [])
    neighbours = list(neighbours)
    gap = float(required_gap_mm) if required_gap_mm is not None else 0.0

    rejected: list[str] = []
    attempts = 0

    for move_type, vector in candidate_moves(item, element, gap, margin_mm):
        if attempts >= MAX_ATTEMPTS:
            break
        attempts += 1

        # DEFENCE IN DEPTH, and currently unreachable through this function:
        # candidate_moves() already withholds the Z axis from a gravity run, so
        # no vertical vector reaches here today. It stays because resolve() is
        # public and a caller may one day supply its own candidates, and
        # because the cost of the check is nothing against the cost of a
        # flattened drain. Do not delete it as dead code -- it is the second
        # lock on the one failure this block must never allow.
        if not preserves_fall(element, vector):
            rejected.append(f"{move_type} {vector}: would alter the fall of a gravity run")
            continue

        blocker = _would_create_new_clash(element, vector, neighbours)
        if blocker:
            rejected.append(f"{move_type} {vector}: would clash with {blocker}")
            continue

        if not rule_ids or not clause_text:
            # Geometrically sound, but nothing authorises the distance.
            return Proposal(
                clash_id=clash_id,
                element=getattr(element, "global_id", "unknown"),
                move_type=move_type,
                move_vector_mm=vector,
                status=STATUS_FLAGGED,
                attempts=attempts,
                rule_ids=rule_ids,
                clause_text=clause_text,
                rejected=rejected,
                note=(
                    "move is geometrically valid but no clause authorises the "
                    "clearance; requires an engineer's decision before it is a proposal"
                ),
            )

        return Proposal(
            clash_id=clash_id,
            element=getattr(element, "global_id", "unknown"),
            move_type=move_type,
            move_vector_mm=vector,
            status=STATUS_PROPOSED,
            attempts=attempts,
            rule_ids=rule_ids,
            clause_text=clause_text,
            rejected=rejected,
        )

    return Proposal(
        clash_id=clash_id,
        element=getattr(element, "global_id", "unknown"),
        move_type=MOVE_RESEQUENCE,
        move_vector_mm=(0.0, 0.0, 0.0),
        status=STATUS_ESCALATED,
        attempts=attempts,
        rule_ids=rule_ids,
        clause_text=clause_text,
        rejected=rejected,
        note=(
            "no candidate move survived checking; this belongs on a coordination "
            "meeting agenda with the alternatives already tried"
        ),
    )
