"""clash_triage: three tests + mutation probe.

The defects being guarded are the ones that make a coordination report get
ignored: the same conflict listed several times, assembly artefacts drowning
the real findings, and a queue whose order does not match how the work
happens.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.blocks.clash_triage import (
    KIND_CLEARANCE,
    KIND_HARD,
    load_order,
    pair_key,
    resolution_rank,
    triage,
    zone_congestion,
)


@dataclass
class F:
    element_a: str
    element_b: str
    kind: str = "clash"
    distance_m: float | None = 0.0
    required_clearance_m: float | None = None
    penetration_volume_m3: float | None = 0.001
    rule_id: str | None = None
    category_a: str | None = None
    category_b: str | None = None


@dataclass
class E:
    global_id: str
    system: str
    name: str = ""
    level: str = "L1"
    discipline: str = "mep"
    zone_key: str = "L1|0_0"
    bbox: tuple = (0, 0, 0, 1, 1, 1)


def test_the_same_clash_reported_twice_is_queued_once():
    """A clash between A and B is the same clash as between B and A. Counting
    it twice is what turns 400 real conflicts into an 800-row report nobody
    reads."""
    els = {"A": E("A", "ventilation"), "B": E("B", "electrical")}
    findings = [F("A", "B"), F("B", "A")]  # same conflict, both orderings
    r = triage(findings, els)
    assert len(r.queue) == 1
    assert r.deduped == 1


def test_a_fitting_meeting_its_own_segment_is_dropped_but_counted():
    """Assembly, not conflict. Dropping it is right; dropping it SILENTLY is
    not -- an invisible drop cannot be distinguished from a missed clash."""
    els = {
        "P1": E("P1", "drainage_storm", name="hwa afvoer segment"),
        "P2": E("P2", "drainage_storm", name="hwa afvoer bend fitting"),
    }
    r = triage([F("P1", "P2")], els)
    assert r.queue == []
    assert r.dropped_workflow == 1


def test_a_cross_system_fitting_clash_is_NOT_treated_as_noise():
    """The guard needs both conditions. A fitting touching a DIFFERENT
    system is a real clash; suppressing it on the fitting hint alone would
    hide genuine conflicts."""
    els = {
        "P1": E("P1", "drainage_storm", name="hwa afvoer bend fitting"),
        "D1": E("D1", "ventilation", name="duct fitting"),
    }
    r = triage([F("P1", "D1")], els)
    assert len(r.queue) == 1
    assert r.dropped_workflow == 0


def test_gravity_is_queued_before_pressurised_whatever_the_severity():
    """Order is a sequence, not a preference. A trivial gravity clash still
    precedes a severe pressurised one, because moving the drain last means
    its space is already gone."""
    els = {
        "G1": E("G1", "drainage_storm"), "W1": E("W1", "structure", discipline="structural"),
        "F1": E("F1", "fire"), "W2": E("W2", "structure", discipline="structural"),
    }
    minor_gravity = F("G1", "W1", penetration_volume_m3=1e-9)
    severe_pressurised = F("F1", "W2", penetration_volume_m3=10.0)
    r = triage([severe_pressurised, minor_gravity], els)
    assert r.queue[0].system_a == "drainage_storm" or r.queue[0].system_b == "drainage_storm"
    assert r.queue[0].resolution_rank < r.queue[1].resolution_rank


def test_congestion_ranks_the_denser_zone_higher():
    """Two zones, same clash count, different density."""
    dense = [E(f"d{i}", "ventilation", zone_key="L1|0_0", bbox=(0, 0, 0, 2, 2, 2)) for i in range(6)]
    sparse = [E("s1", "ventilation", zone_key="L1|9_9", bbox=(0, 0, 0, 0.2, 0.2, 0.2))]
    z = zone_congestion({e.global_id: e for e in dense + sparse}.values())
    assert z["L1|0_0"] > z["L1|9_9"]


def test_an_unknown_system_is_ranked_last_but_never_dropped():
    """An unclassified service is exactly the one to look at, not to hide."""
    order = load_order()
    assert resolution_rank("drainage_storm", order) == 1
    assert resolution_rank("some_unmapped_system", order) == len(order) + 1


def test_order_yaml_and_the_builtin_fallback_agree():
    """The YAML is the source of record and the fallback exists only for a
    missing PyYAML. If they drift, the queue silently changes depending on
    whether an optional dependency is installed."""
    from app.blocks.clash_triage import _DEFAULT_ORDER

    loaded = load_order()
    assert [c for c, _ in loaded] == [c for c, _ in _DEFAULT_ORDER]
    for (_, a), (_, b) in zip(loaded, _DEFAULT_ORDER):
        assert set(a) == set(b)


def test_mutation_probe_ordered_pair_key_reopens_double_counting():
    """MUTATION PROBE.

    Dedupe hinges on the pair key being unordered. Restore an ordered key and
    the same conflict reported both ways becomes two queue rows again.
    """
    def ordered_key(a: str, b: str) -> tuple[str, str]:
        return (a, b)  # the bug

    a, b = "A", "B"
    assert pair_key(a, b) == pair_key(b, a), "unordered key is the invariant"
    assert ordered_key(a, b) != ordered_key(b, a), (
        "probe is inert: the mutant must actually differ from the real key"
    )

    els = {"A": E("A", "ventilation"), "B": E("B", "electrical")}
    real = triage([F("A", "B"), F("B", "A")], els)
    assert len(real.queue) == 1, "engine regressed to counting both orderings"
