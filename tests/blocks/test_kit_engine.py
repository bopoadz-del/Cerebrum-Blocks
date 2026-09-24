"""The shared reasoning-layer evaluator: the properties every kit depends on.

Written against the portable spec. The tests that matter most are not the eight
kinds — they are the four properties that decide whether the layer can be
trusted at all:

  * a kit that does not parse REFUSES; it does not load with no invariants
  * an invariant that could never fire is a load failure, not a silent no-op
  * the budget cap SKIPS AND SAYS SO; a skipped check is not a pass
  * the operator's own figure is never refused
"""
from __future__ import annotations

import pathlib
import time

import pytest
import yaml

from app.blocks.kit_engine import (
    DisabledKit,
    Figure,
    KitLoadError,
    KitRegistry,
    check_arithmetic,
    kill_switch_off,
    load_kit,
)

DATACENTRE = pathlib.Path("app/blocks/datacentre")


@pytest.fixture
def kit():
    return load_kit(DATACENTRE)


def _grounded(**kw) -> Figure:
    """A figure with nothing wrong with it, for tests about one thing."""
    base = dict(
        quantity="it_load_mw",
        value=0.7,
        unit="MW",
        origin="document",
        source_id="doc-1",
        source_class="live_measurement",
        qualifiers={"facility": "facility_01"},
        text="the IT load is 0.7 MW",
    )
    base.update(kw)
    return Figure(**base)


def _fresh_state():
    now = time.time()
    # All THREE providers the kit declares. A fixture that supplies two of three
    # makes every currency test look like an UNKNOWN-state test.
    return {
        "bms": {"as_of": now},
        "manual_log": {"as_of": now},
        "ist_register": {"as_of": now},
    }


# ── fail closed ────────────────────────────────────────────────────────────

def test_a_kit_that_does_not_parse_is_disabled_and_refuses(tmp_path):
    """The whole safety property. A typo must not become "no invariants"."""
    (tmp_path / "manifest.yaml").write_text("kit: broken\nquantities: {}\n", encoding="utf-8")
    (tmp_path / "invariants.yaml").write_text("invariants: []\n", encoding="utf-8")

    registry = KitRegistry(tmp_path.parent)
    loaded = registry.load_one(tmp_path)

    assert isinstance(loaded, DisabledKit)
    outcome = loaded.answer_time([_grounded()])
    assert outcome.verdict == "refused"
    assert "DISABLED" in outcome.blocked_reason
    assert "does not pass statements through" in outcome.blocked_reason


def test_an_unknown_kit_refuses_rather_than_returning_none():
    """Absent is refusal too — a None here becomes an ungated answer path."""
    stand_in = KitRegistry(DATACENTRE.parent).get("no_such_kit")
    assert stand_in.answer_time([_grounded()]).verdict == "refused"


def test_a_kit_with_no_invariants_does_not_load(tmp_path):
    (tmp_path / "manifest.yaml").write_text(
        yaml.safe_dump({"kit": "empty", "quantities": {"x": {}}}), encoding="utf-8"
    )
    (tmp_path / "invariants.yaml").write_text("invariants: []\n", encoding="utf-8")

    with pytest.raises(KitLoadError, match="no invariants"):
        load_kit(tmp_path)


def test_the_kill_switch_disables_one_kit_without_a_deploy(tmp_path):
    assert kill_switch_off("datacentre", {"CEREBRUM_KIT_DATACENTRE": "off"}) is True
    assert kill_switch_off("datacentre", {}) is False

    with pytest.raises(KitLoadError, match="switched off"):
        load_kit(DATACENTRE, env={"CEREBRUM_KIT_DATACENTRE": "off"})


# ── an invariant that cannot fire is a load failure ───────────────────────

def _kit_with(tmp_path, record, quantities=None):
    (tmp_path / "manifest.yaml").write_text(
        yaml.safe_dump({
            "kit": "probe",
            "quantities": quantities or {"thing": {"classes": ["any_thing"]}},
        }),
        encoding="utf-8",
    )
    (tmp_path / "invariants.yaml").write_text(
        yaml.safe_dump({"invariants": [record]}), encoding="utf-8"
    )
    return tmp_path


@pytest.mark.parametrize(
    "record,expected",
    [
        ({"id": "A", "kind": "qualifier", "severity": "refuse", "measurement": "m",
          "applies_to": {"quantity": "thing"}}, "requiring no fields"),
        ({"id": "B", "kind": "provenance", "severity": "refuse", "measurement": "m",
          "applies_to": {"quantity": "thing"}}, "must name the dimensions"),
        ({"id": "C", "kind": "band", "severity": "refuse", "measurement": "m",
          "applies_to": {"quantity": "thing"}}, "no band min or max"),
        ({"id": "D", "kind": "authority", "severity": "refuse", "measurement": "m",
          "applies_to": {"quantity": "thing"}}, "governing source class"),
        ({"id": "E", "kind": "currency", "severity": "refuse", "measurement": "m",
          "applies_to": {"quantity": "thing"}}, "state provider"),
        ({"id": "F", "kind": "qualifier", "severity": "refuse", "requires": ["x"],
          "applies_to": {"quantity": "not_declared"}}, "no measurement case"),
        ({"id": "G", "kind": "qualifier", "severity": "refuse", "requires": ["x"],
          "measurement": "m", "applies_to": {"quantity": "not_declared"}},
         "manifest does not declare"),
        ({"id": "H", "kind": "qualifier", "severity": "refuse", "requires": ["x"],
          "measurement": "m", "applies_to": {"quantity": "any_undefined"}},
         "decoration"),
    ],
    ids=["no-requires", "no-across", "no-band", "no-governing", "no-provider",
         "no-measurement", "undeclared-quantity", "undefined-class"],
)
def test_a_record_that_could_never_fire_refuses_to_load(tmp_path, record, expected):
    with pytest.raises(KitLoadError, match=expected):
        load_kit(_kit_with(tmp_path, record))


def test_any_star_is_a_class_not_a_wildcard(kit):
    """The bug this caught: units-and-datum demanded a vertical datum for a PCN.

    `any_measured` must govern the measured quantities and NOT the claim-shaped
    ones, or one loose invariant governs everything.
    """
    units = next(inv for inv in kit.invariants if inv.id == "INV-DC-UNITS")
    assert units.governs("pue") is True
    assert units.governs("resilience_level") is False


# ── the budget ────────────────────────────────────────────────────────────

def test_the_budget_skips_and_says_so_rather_than_running_unbounded(kit):
    """An unbounded set in this position consumed 2 GB and killed a live
    instance twice in one day. A skipped check is NOT a pass."""
    kit.budget = 3
    figures = [_grounded() for _ in range(50)]

    outcome = kit.answer_time(figures, state=_fresh_state())

    assert outcome.incomplete is True
    assert outcome.skipped > 0
    assert outcome.as_dict()["incomplete"] is True


def test_within_budget_nothing_is_marked_incomplete(kit):
    outcome = kit.answer_time([_grounded()], state=_fresh_state())
    assert outcome.incomplete is False and outcome.skipped == 0


# ── never refuse the operator's own figure ────────────────────────────────

def test_the_operators_own_figure_is_flagged_never_refused(kit):
    """If they typed the rate it is authoritative input, not a claim to check."""
    theirs = _grounded(origin="operator", source_id=None, source_class=None,
                       quantity="available_capacity", value=300, unit="kW",
                       text="available capacity is 300 kW")

    outcome = kit.answer_time([theirs], state=_fresh_state())

    assert outcome.verdict == "flagged"
    assert outcome.blocked_reason == ""
    assert any(f.softened_from == "refuse" for f in outcome.findings)
    assert any("operator's own figure" in f.message for f in outcome.findings)


def test_the_same_defect_in_a_model_figure_is_refused(kit):
    """The softening is about WHOSE figure it is, not about the defect."""
    mine = _grounded(origin="model", source_id=None, source_class=None,
                     quantity="available_capacity", value=300, unit="kW",
                     text="available capacity is 300 kW")

    assert kit.answer_time([mine], state=_fresh_state()).verdict == "refused"


# ── the five hooks ────────────────────────────────────────────────────────

def test_h0_refuses_before_retrieval(kit):
    outcome = kit.pre_retrieval("is the facility ready for IT load?")
    assert outcome.verdict == "refused"
    assert outcome.hook == "H0"
    assert "nothing was retrieved" in outcome.blocked_reason
    assert "authorised person" in outcome.blocked_reason


def test_h0_lets_an_answerable_question_through_to_retrieval(kit):
    assert kit.pre_retrieval("what is the design PUE?").verdict == "pass"


def test_h1_demotes_a_class_that_is_rejected_as_proof(kit):
    """The tier trap, as a ladder rather than a bespoke branch."""
    tier = _grounded(quantity="resilience_level", value="N+1", unit=None,
                     source_class="tier_design_certificate",
                     qualifiers={"facility": "facility_01", "basis": "as_built"},
                     text="the facility is N+1")

    outcome = kit.ranking([tier])

    assert outcome.verdict == "refused"
    assert outcome.hook == "H1"
    assert "test or a live measurement" in outcome.blocked_reason


def test_h2_catches_an_impossible_value_where_it_is_born(kit):
    outcome = kit.tool_time([_grounded(quantity="pue", value=0.4, unit=None,
                                       text="PUE 0.4", origin="tool")])
    assert outcome.verdict == "refused"
    assert outcome.hook == "H2"
    assert "thermodynamically impossible" in outcome.blocked_reason


def test_h4_reruns_the_answer_time_checks_on_the_deliverable(kit):
    """H3 alone lets a corrupted value reach exports and source panels."""
    bad = _grounded(quantity="resilience_level", value="N+1", unit=None,
                    source_class="live_measurement",
                    qualifiers={"facility": "facility_01"},
                    text="the facility is N+1")

    at_answer = kit.answer_time([bad], state=_fresh_state())
    at_export = kit.export_time([bad], state=_fresh_state())

    assert at_answer.verdict == at_export.verdict == "refused"
    assert at_export.hook == "H4"
    assert {f.invariant_id for f in at_answer.findings} == {f.invariant_id for f in at_export.findings}


# ── the kinds whose absence was the reason for the rewrite ───────────────

def test_currency_reports_unknown_and_never_falls_back_to_the_design_basis(kit):
    claim = _grounded(quantity="resilience_level", value="N+1", unit=None,
                      source_class="live_measurement",
                      qualifiers={"facility": "facility_01", "basis": "as_currently_operating"},
                      text="the facility is N+1")

    outcome = kit.answer_time([claim], state={})

    assert outcome.verdict == "refused"
    assert "UNKNOWN" in outcome.blocked_reason
    assert "no design-basis fallback" in outcome.blocked_reason
    assert "N+1" not in outcome.blocked_reason


def test_currency_is_an_event_not_only_a_clock(kit):
    """An IST result is stale the moment the tested systems change, however
    recent the test was — the live chiller incident."""
    claim = _grounded(quantity="tested_result", value=None, unit=None,
                      source_class="integrated_systems_test",
                      qualifiers={"facility": "facility_01", "commissioning_level": "L5",
                                  "load_pct": 100, "failure_scenario": "chiller loss"},
                      text="tested at L5, 100% load, chiller loss")

    fresh = kit.answer_time([claim], state=_fresh_state())
    after = kit.answer_time([claim], state=_fresh_state(),
                            events=["control_sequence_modified"])

    assert fresh.verdict == "pass", fresh.blocked_reason
    assert after.verdict == "refused"
    assert "control_sequence_modified" in after.blocked_reason


def test_provenance_does_not_fire_when_one_entity_is_named_twice(kit):
    """The bug written and fixed by hand in the first kit: a mention-counting
    guard blocks what a CORRECT answer looks like."""
    ok = _grounded(quantity="available_capacity", value=300, unit="kW",
                   qualifiers={"facility": "facility_01",
                               "redundancy_basis": "available_after_redundancy"},
                   text="facility_01 has 300 kW available after redundancy in facility_01")
    ok.asked_about = {"facility": "facility_01"}

    assert kit.answer_time([ok], state=_fresh_state()).verdict == "pass"


def test_provenance_fires_when_the_figure_belongs_to_another_entity(kit):
    borrowed = _grounded(quantity="available_capacity", value=300, unit="kW",
                         qualifiers={"facility": "facility_02",
                                     "redundancy_basis": "available_after_redundancy"},
                         text="300 kW available after redundancy")
    borrowed.asked_about = {"facility": "facility_01"}

    outcome = kit.answer_time([borrowed], state=_fresh_state())

    assert outcome.verdict == "refused"
    assert "facility_02" in outcome.blocked_reason and "facility_01" in outcome.blocked_reason


@pytest.mark.parametrize(
    "text,expected",
    [
        ("L/20 = 4800/20 = 200 mm", True),
        ("L/20 = 4800/20 = 240 mm", False),
        ("total is 12 * 4 = 48 units", False),
        ("total is 12 * 4 = 50 units", True),
        ("no arithmetic here at all", False),
    ],
)
def test_derivation_evaluates_the_arithmetic_a_reader_would_skim(text, expected):
    """Rule right, inputs right, result wrong — the hardest defect to see by
    reading and trivial to catch by evaluating."""
    assert (check_arithmetic(text) is not None) is expected


def test_derivation_catches_an_answer_contradicting_itself(kit):
    """Live: "40 days" and "400 days" in one answer."""
    first = _grounded(quantity="ups_autonomy_minutes", value=30, unit="minutes",
                      text="UPS autonomy is 30 minutes")
    second = _grounded(quantity="ups_autonomy_minutes", value=300, unit="minutes",
                       text="UPS autonomy is 300 minutes")

    outcome = kit.answer_time([first, second], state=_fresh_state())

    assert outcome.verdict == "refused"
    assert "contradicts itself" in outcome.blocked_reason


def test_grounding_refuses_a_figure_nobody_supplied(kit):
    invented = _grounded(origin="model", source_id=None, source_class=None)

    outcome = kit.answer_time([invented], state=_fresh_state())

    assert outcome.verdict == "refused"
    assert "not grounded" in outcome.blocked_reason


def test_a_qualifier_the_kit_does_not_declare_is_refused_before_any_invariant(kit):
    """An invariant reading a field it cannot trust is worse than no invariant."""
    outcome = kit.answer_time(
        [_grounded(qualifiers={"facility": "facility_01", "made_up_field": "x"})],
        state=_fresh_state(),
    )

    assert outcome.verdict == "refused"
    assert any(f.invariant_id == "SCHEMA" for f in outcome.findings)
    assert "not a declared qualifier field" in outcome.blocked_reason


def test_a_finding_carries_the_span_so_one_figure_can_be_repaired(kit):
    """Surgical repair: a long answer with one bad number need not be binned."""
    figure = _grounded(quantity="pue", value=0.4, unit=None, origin="tool",
                       text="PUE 0.4", span={"start": 412, "end": 419})

    finding = kit.tool_time([figure]).findings[0]

    assert finding.span == {"start": 412, "end": 419}


# ── every invariant declares how it will be counted ──────────────────────

def test_every_shipped_invariant_names_its_measurement_case(kit):
    """An invariant you cannot count is an opinion."""
    for inv in kit.invariants:
        assert inv.measurement, f"{inv.id} ships without a measurement case"
        assert any(ch.isdigit() for ch in inv.measurement), (
            f"{inv.id}'s measurement names no number of runs: {inv.measurement}"
        )


def test_the_rewritten_datacentre_kit_covers_all_eight_kinds(kit):
    """The reason for the rewrite: four of the eight kinds were absent from the
    hand-written gate — authority, band, derivation and grounding."""
    kinds = {inv.kind for inv in kit.invariants}
    assert kinds >= {
        "qualifier", "scope", "authority", "provenance",
        "currency", "band", "derivation", "grounding", "unit_discipline",
    }
