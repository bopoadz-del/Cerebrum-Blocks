"""clearance_rules: the three required tests + mutation probe.

No mocks: every test builds real Rule/Finding-shaped data and calls the real
load_rules()/evaluate() functions. The thing under test IS data validation
and a precedence comparison, so a mock would just be testing the mock.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.blocks.clearance_rules import (
    RuleWithoutCitation,
    evaluate,
    load_rules,
)

SEED_RULES_PATH = Path(__file__).resolve().parent.parent / "app" / "blocks" / "seed_rules.json"


def _finding(category_a="electrical", category_b="plumbing", distance_m=0.1, kind="clearance", axis=None):
    """A minimal stand-in for geometry_engine.Finding. A real Finding works
    identically here since evaluate() only reads attributes via getattr --
    this avoids the test depending on block 1's exact constructor shape."""
    ns = SimpleNamespace(
        element_a="A1",
        element_b="B1",
        category_a=category_a,
        category_b=category_b,
        distance_m=distance_m,
        kind=kind,
    )
    if axis is not None:
        ns.axis = axis
    return ns


def _code_rule(min_gap_mm=150.0, rule_id="CODE-1"):
    return {
        "rule_id": rule_id,
        "system_a": "electrical",
        "system_b": "plumbing",
        "min_gap_mm": min_gap_mm,
        "axis": "any",
        "source": {"doc": "SBC-501", "clause": "5.4.2", "text_hash": "abc123"},
        "precedence": "code",
    }


def _project_rule(min_gap_mm, rule_id="PROJ-1"):
    return {
        "rule_id": rule_id,
        "system_a": "electrical",
        "system_b": "plumbing",
        "min_gap_mm": min_gap_mm,
        "axis": "any",
        "source": {"doc": "Project Spec 26 05 00", "clause": "3.2.1", "text_hash": "def456"},
        "precedence": "project_spec",
    }


def test_a_stricter_project_spec_rule_overrides_a_code_rule_for_the_same_pair():
    """A project is free to demand MORE than the code minimum. If it does,
    its number is what a finding must be judged against."""
    rules = load_rules([_code_rule(min_gap_mm=150.0), _project_rule(min_gap_mm=300.0)])

    # 200mm gap: passes the 150mm code minimum, fails the stricter 300mm
    # project rule. If the project rule is genuinely governing, this must
    # come back as a violation citing PROJ-1.
    finding = _finding(distance_m=0.2)
    violations = evaluate([finding], rules)

    assert len(violations) == 1
    assert violations[0].rule_id == "PROJ-1"
    assert violations[0].required_min_gap_mm == 300.0
    assert violations[0].source_clause == "3.2.1"


def test_a_looser_project_spec_rule_does_not_override_the_code_minimum():
    """THE ASYMMETRY. A project spec cannot relax a code minimum -- it has
    no authority to. A 50mm project rule must lose to a 150mm code rule for
    the same pair, not win because it is 'more specific' or 'newer'."""
    rules = load_rules([_code_rule(min_gap_mm=150.0), _project_rule(min_gap_mm=50.0)])

    # 100mm gap: fails the 150mm code minimum, would PASS the looser 50mm
    # project rule. If the (wrong) override happened, no violation would be
    # reported -- which is precisely the undercut this rule must prevent.
    finding = _finding(distance_m=0.1)
    violations = evaluate([finding], rules)

    assert len(violations) == 1
    assert violations[0].rule_id == "CODE-1"
    assert violations[0].required_min_gap_mm == 150.0

    # And the same geometry judged against ONLY the looser project rule
    # would correctly be clear -- proving the violation above really did
    # come from the code minimum standing its ground, not from some other
    # effect (like the project rule being unparsable).
    project_only = load_rules([_project_rule(min_gap_mm=50.0)])
    assert evaluate([finding], project_only) == []


def test_a_rule_missing_source_clause_is_refused_at_load_and_names_the_rule_id():
    """THE CORE INVARIANT: a rule without a clause is not a rule. load_rules
    must refuse it outright -- not warn, not skip, not load everything else
    and drop this one silently."""
    bad_rule = _code_rule(rule_id="UNCITED-99")
    del bad_rule["source"]["clause"]

    with pytest.raises(RuleWithoutCitation) as exc_info:
        load_rules([bad_rule])

    assert "UNCITED-99" in str(exc_info.value)
    assert exc_info.value.rule_id == "UNCITED-99"


def test_a_rule_missing_source_text_hash_is_also_refused_at_load():
    """The same guard must cover text_hash, not just clause -- a clause
    number with no hash of the actual text it points to still cannot be
    checked for drift if the source document changes."""
    bad_rule = _code_rule(rule_id="UNCITED-HASH")
    del bad_rule["source"]["text_hash"]

    with pytest.raises(RuleWithoutCitation) as exc_info:
        load_rules([bad_rule])

    assert "UNCITED-HASH" in str(exc_info.value)


def test_mutation_probe_a_lax_loader_would_let_an_uncited_rule_through():
    """MUTATION PROBE for the citation guard.

    This reimplements, inline, the lax behaviour the real load_rules() must
    NOT have: a loader that accepts a rule regardless of whether it has a
    clause or text_hash. It proves two things: (1) the uncited rule used
    above is genuinely uncited -- the lax loader accepts it without error,
    so the real loader's refusal in the test above is not an accident of
    some unrelated validation failure; and (2) if load_rules() were ever
    mutated to behave like this lax version, the citation test would stop
    raising and would fail. The probe itself must PASS (it is testing the
    lax stand-in, not the real function) -- what it demonstrates is that the
    guard in the real code is load-bearing, not decorative.
    """

    def lax_load_rules(raw_rules):
        """The forbidden shape: no citation check at all."""
        loaded = []
        for raw in raw_rules:
            loaded.append(raw)  # accepted, clause or no clause
        return loaded

    bad_rule = _code_rule(rule_id="UNCITED-99")
    del bad_rule["source"]["clause"]

    # The lax loader lets it straight through -- no exception.
    lax_result = lax_load_rules([bad_rule])
    assert len(lax_result) == 1
    assert lax_result[0]["rule_id"] == "UNCITED-99"

    # Which is exactly why the real loader must NOT behave this way: this
    # assertion mirrors test_a_rule_missing_source_clause_..., and if
    # load_rules() were ever mutated into the lax shape demonstrated above,
    # pytest.raises would find no exception and fail right here with
    # "DID NOT RAISE" -- proof the guard, not the probe, is what is load-bearing.
    with pytest.raises(RuleWithoutCitation):
        load_rules([bad_rule])


def test_wildcard_rule_applies_when_no_exact_pair_rule_exists():
    """A wildcard rule is the fallback, not the override -- covered here so
    the exact-vs-wildcard specificity logic that the precedence tests lean
    on is itself exercised directly."""
    rules = load_rules(
        [
            {
                "rule_id": "GENERIC-ANY",
                "system_a": "*",
                "system_b": "*",
                "min_gap_mm": 100.0,
                "axis": "any",
                "source": {"doc": "SBC-501", "clause": "1.1", "text_hash": "zzz"},
                "precedence": "code",
            }
        ]
    )
    finding = _finding(category_a="fire", category_b="data", distance_m=0.05)
    violations = evaluate([finding], rules)
    assert len(violations) == 1
    assert violations[0].rule_id == "GENERIC-ANY"


def test_an_exact_pair_rule_is_preferred_over_a_wildcard_even_if_the_wildcard_is_stricter():
    """Specificity is decided before precedence is even consulted -- a
    generic wildcard rule must not out-rank a rule written for this exact
    pair just because it happens to demand a bigger number."""
    rules = load_rules(
        [
            _code_rule(min_gap_mm=150.0, rule_id="EXACT-CODE"),
            {
                "rule_id": "GENERIC-STRICT",
                "system_a": "*",
                "system_b": "*",
                "min_gap_mm": 9000.0,
                "axis": "any",
                "source": {"doc": "SBC-501", "clause": "1.1", "text_hash": "zzz"},
                "precedence": "code",
            },
        ]
    )
    finding = _finding(distance_m=0.2)  # 200mm: fails 9000mm wildcard, passes 150mm exact
    violations = evaluate([finding], rules)
    assert violations == []


def test_a_vertical_only_rule_does_not_fire_on_a_horizontal_separation():
    """axis must be respected -- a vertical clearance requirement (e.g.
    below a structural beam) has nothing to say about two services running
    side by side."""
    rules = load_rules(
        [
            {
                "rule_id": "VERT-ONLY",
                "system_a": "electrical",
                "system_b": "plumbing",
                "min_gap_mm": 500.0,
                "axis": "vertical",
                "source": {"doc": "SBC-501", "clause": "6.1", "text_hash": "vvv"},
                "precedence": "code",
            }
        ]
    )
    horizontal_finding = _finding(distance_m=0.05, axis="horizontal")
    assert evaluate([horizontal_finding], rules) == []

    vertical_finding = _finding(distance_m=0.05, axis="vertical")
    violations = evaluate([vertical_finding], rules)
    assert len(violations) == 1
    assert violations[0].rule_id == "VERT-ONLY"


def test_clash_kind_findings_are_never_judged_by_this_block():
    """A clash already has its verdict from geometry_engine and cites no
    rule -- this block must not second-guess it or attach a rule_id to it."""
    rules = load_rules([_code_rule(min_gap_mm=150.0)])
    clash = _finding(distance_m=0.0, kind="clash")
    assert evaluate([clash], rules) == []


def test_seed_rules_load_cleanly_and_are_all_citable():
    """seed_rules.json ships three real, retrieval-sourced rules (gas main
    vs. low-voltage electrical / any utility / building, off drawing
    IP-INF-053-0000-JCB-DWG-LP-600-0000002 A). load_rules() must accept the
    file as-is -- if this ever raises, the seed file itself has drifted out
    of the citation invariant it is supposed to demonstrate."""
    rules = load_rules(SEED_RULES_PATH)
    assert {r.rule_id for r in rules} == {
        "MEP-GAS-LV-400",
        "MEP-GAS-ANY-300",
        "MEP-GAS-BLDG-5000",
    }
    assert all(r.precedence == "project_spec" for r in rules)
    assert all(r.source.text_hash for r in rules)


def test_the_specific_gas_lv_seed_rule_beats_the_wildcard_gas_seed_rule():
    """Ordering proof for the two overlapping seed rules: NOTES item 5
    (gas_main vs. electrical_lv, 400mm) is more specific than NOTES item 6
    (gas_main vs. '*', 300mm). A gas-main-to-LV finding must be judged
    against 400mm, not 300mm -- getting this backwards would silently let a
    350mm gap pass when the drawing actually requires 400mm."""
    rules = load_rules(SEED_RULES_PATH)

    gas_lv_finding = _finding(category_a="gas_main", category_b="electrical_lv", distance_m=0.35)
    violations = evaluate([gas_lv_finding], rules)
    assert len(violations) == 1
    assert violations[0].rule_id == "MEP-GAS-LV-400"
    assert violations[0].required_min_gap_mm == 400

    # And a gas-main-to-something-else pair (no exact rule) correctly falls
    # through to the item-6 wildcard at 300mm -- 250mm fails that 300mm
    # minimum (it would also fail 400mm, but no rule here demands 400mm for
    # this pair, so a violation here can only be the wildcard doing its job).
    gas_other_finding = _finding(category_a="gas_main", category_b="telecom_duct", distance_m=0.25)
    other_violations = evaluate([gas_other_finding], rules)
    assert len(other_violations) == 1
    assert other_violations[0].rule_id == "MEP-GAS-ANY-300"
