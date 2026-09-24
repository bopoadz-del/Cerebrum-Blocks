"""The interview: the domain owner's own question sheets, as the kits carry them.

The sheets in ``docs/kit_questions/`` are the record of what was asked for, in the
owner's words. ``app/blocks/<kit>/questions.yaml`` is a GENERATED view of them. The
first test here is therefore the important one: it regenerates every file from its
sheet and fails if what is committed differs. Without it the YAML is a second copy
of the same fact, free to drift, and a hand-edit that quietly reworded a [GATE]
question into a [GAP] would never be caught.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re

import pytest
import yaml

from app.blocks.kit_engine import (
    DisabledKit,
    Interview,
    InterviewError,
    load_kit,
    parse_interview,
)
from app.blocks.kit_engine.engine import KitLoadError

ROOT = pathlib.Path(__file__).resolve().parents[2]
BLOCKS = ROOT / "app" / "blocks"
SHEETS = ROOT / "docs" / "kit_questions"

#: The two kits with no sheet, named so that adding an eighteenth kit without one
#: fails here instead of shipping a domain nobody interviewed.
WITHOUT_SHEET = {"datacentre", "offshore_marine"}


def _importer():
    spec = importlib.util.spec_from_file_location(
        "kit_question_importer", ROOT / "scripts" / "import_kit_questions.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def kit_dirs():
    return sorted(
        p.parent for p in BLOCKS.glob("*/manifest.yaml")
        if (p.parent / "invariants.yaml").is_file()
    )


def sheet_kits():
    """One entry per kit sheet. A sheet is named for its kit, so anything in the
    directory that is not a kit directory is documentation about the sheets rather
    than one of them."""
    return sorted(
        p.stem for p in SHEETS.glob("*.md")
        if (BLOCKS / p.stem / "manifest.yaml").is_file()
    )


# --------------------------------------------------------------------------
# the drift guard
# --------------------------------------------------------------------------

@pytest.mark.parametrize("kit", sheet_kits())
def test_committed_questions_match_the_sheet_exactly(kit):
    """Regenerate from the markdown and compare. A hand-edit fails here."""
    imp = _importer()
    sheet = SHEETS / f"{kit}.md"
    manifest = yaml.safe_load((BLOCKS / kit / "manifest.yaml").read_text(encoding="utf-8")) or {}
    title, answer_format, sections, questions = imp.parse_sheet(sheet)
    for question in questions:
        question["covers"] = imp._covers(question["text"], manifest.get("quantities") or {})
    expected = imp.render(kit, sheet, title, answer_format, sections, questions)
    committed = (BLOCKS / kit / "questions.yaml").read_text(encoding="utf-8")
    assert committed == expected, (
        f"{kit}/questions.yaml has drifted from docs/kit_questions/{kit}.md. "
        f"Edit the sheet and re-run scripts/import_kit_questions.py; never hand-edit the YAML."
    )


@pytest.mark.parametrize("kit", sheet_kits())
def test_every_question_text_is_verbatim_from_the_sheet(kit):
    """The wording is the owner's. A paraphrase is a different question."""
    sheet_text = (SHEETS / f"{kit}.md").read_text(encoding="utf-8")
    normalised = " ".join(sheet_text.split())
    interview = load_kit(BLOCKS / kit).interview
    for question in interview.questions:
        assert " ".join(question.text.split()) in normalised, (
            f"{kit} {question.id}: text is not in the sheet verbatim: {question.text[:70]}"
        )


@pytest.mark.parametrize("kit", sheet_kits())
def test_gate_and_gap_counts_match_the_sheets_own_marks(kit):
    sheet_text = (SHEETS / f"{kit}.md").read_text(encoding="utf-8")
    interview = load_kit(BLOCKS / kit).interview
    assert sum(1 for q in interview.questions if q.gate is True) == len(
        re.findall(r"\[GATE\]", sheet_text))
    assert sum(1 for q in interview.questions if q.gate is False) == len(
        re.findall(r"\[GAP\]", sheet_text))


def test_all_fifteen_sheets_are_installed_and_the_other_two_are_named():
    installed = {d.name for d in kit_dirs() if (d / "questions.yaml").is_file()}
    missing = {d.name for d in kit_dirs()} - installed
    assert installed == set(sheet_kits())
    assert missing == WITHOUT_SHEET, (
        f"kits with no owner question sheet: {sorted(missing)}. Add the sheet, or add "
        f"the kit to WITHOUT_SHEET so it is a stated gap and not an oversight."
    )


# --------------------------------------------------------------------------
# answers never live in the kit
# --------------------------------------------------------------------------

@pytest.mark.parametrize("kit", sheet_kits())
def test_no_questions_file_holds_an_answer(kit):
    """The kit is a signed Store block shared by every customer. One client's
    figures arriving inside another's kit is the provenance failure this whole
    layer exists to prevent, and it would arrive signed."""
    raw = yaml.safe_load((BLOCKS / kit / "questions.yaml").read_text(encoding="utf-8"))
    for question in raw["questions"]:
        for forbidden in ("answer", "value", "answered_by", "answered_at"):
            assert forbidden not in question, (
                f"{kit} {question['id']} has an '{forbidden}' slot in the kit"
            )


# --------------------------------------------------------------------------
# gating
# --------------------------------------------------------------------------

def test_unmarked_questions_gate_because_an_unreadable_class_must_block():
    interview = load_kit(BLOCKS / "fm").interview
    unmarked = [q for q in interview.questions if q.gate is None]
    assert unmarked, "the FM sheet marks nothing; it is the case this rule exists for"
    assert all(q.gating for q in unmarked)
    assert all(q.marked == "unmarked" for q in unmarked), (
        "an unmarked question must still be distinguishable from one the owner marked GATE"
    )


def test_a_gap_question_never_blocks_readiness():
    interview = load_kit(BLOCKS / "fitout").interview
    gaps = [q for q in interview.questions if q.gate is False]
    assert gaps
    # Answer every gating question and nothing else: ready, with GAPs outstanding.
    answers = {q.id: "x" for q in interview.questions if q.gating}
    assert interview.ready(answers)
    assert interview.gaps(answers) == tuple(gaps)


def test_one_outstanding_gate_question_is_enough_to_block():
    interview = load_kit(BLOCKS / "fitout").interview
    gating = [q for q in interview.questions if q.gating]
    answers = {q.id: "x" for q in gating[1:]}
    assert not interview.ready(answers)
    assert interview.outstanding(answers) == (gating[0],)


def test_outstanding_is_in_sheet_order_not_sorted():
    """The owner grouped these from rates to incidents. Asked out of order the
    interview reads as a random quiz."""
    interview = load_kit(BLOCKS / "rail").interview
    out = [q.id for q in interview.outstanding({})]
    assert out != sorted(out)
    order = [q.id for q in interview.questions]
    assert out == [qid for qid in order if qid in set(out)]


def test_an_answer_to_a_question_the_sheet_never_asked_is_named():
    interview = load_kit(BLOCKS / "fitout").interview
    status = interview.status({"B.1": "x", "NOT.A.QUESTION": "x"})
    assert status["answers_to_unknown_questions"] == ["NOT.A.QUESTION"]
    assert status["answered"] == 1, "an unknown id must not count toward answered"


# --------------------------------------------------------------------------
# the shape of a complete answer, per domain
# --------------------------------------------------------------------------

def test_required_fields_come_from_the_sheets_answer_format_line():
    fitout = load_kit(BLOCKS / "fitout").interview
    assert fitout.required_fields() == (
        "unit", "quality_band", "market", "source", "date", "confirmed_or_indicative")
    # "value" is the answer itself, not a field that must accompany it.
    assert "value" not in fitout.required_fields()


def test_each_domain_demands_its_own_fields_not_a_shared_list():
    dental = load_kit(BLOCKS / "dental").interview.required_fields()
    fire = load_kit(BLOCKS / "fire_protection").interview.required_fields()
    assert "adult_or_paediatric" in dental and "protocol_version" in dental
    assert "code_edition" in fire
    assert set(dental) != set(fire), (
        "if every domain demanded the same fields there would be no reason to read "
        "the sheet's answer-format line at all"
    )


def test_required_fields_are_names_the_manifest_already_uses_where_they_overlap():
    """The mapping from the sheet's prose to a field key is mechanical, which only
    holds because the manifests already spell them the same way."""
    kit = load_kit(BLOCKS / "fitout")
    assert "confirmed_or_indicative" in kit.manifest.qualifier_fields
    assert "quality_band" in kit.manifest.qualifier_fields
    assert "market" in kit.manifest.qualifier_fields


# --------------------------------------------------------------------------
# fail closed
# --------------------------------------------------------------------------

def test_a_sheet_that_will_not_parse_disables_the_kit(tmp_path):
    src = BLOCKS / "fitout"
    for name in ("manifest.yaml", "invariants.yaml"):
        (tmp_path / name).write_text((src / name).read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "questions.yaml").write_text("kit: fitout\nquestions: []\n", encoding="utf-8")
    with pytest.raises(KitLoadError) as exc:
        load_kit(tmp_path)
    assert "questions" in str(exc.value).lower()


def test_an_interview_belonging_to_another_kit_disables_rather_than_asks(tmp_path):
    """Asking one domain's questions while gating another's figures is worse than
    not loading."""
    src = BLOCKS / "fitout"
    for name in ("manifest.yaml", "invariants.yaml"):
        (tmp_path / name).write_text((src / name).read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "questions.yaml").write_text(
        (BLOCKS / "rail" / "questions.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(KitLoadError) as exc:
        load_kit(tmp_path)
    assert "rail" in str(exc.value) and "fitout" in str(exc.value)


def test_an_interview_with_no_answer_format_is_refused():
    with pytest.raises(InterviewError) as exc:
        parse_interview({
            "kit": "x",
            "questions": [{"id": "1.1", "text": "?", "gate": True}],
        })
    assert "answer_format" in str(exc.value)


def test_a_bad_gate_value_is_refused_rather_than_read_as_false():
    with pytest.raises(InterviewError):
        parse_interview({
            "kit": "x", "answer_format": ["value", "source"],
            "questions": [{"id": "1.1", "text": "?", "gate": "yes"}],
        })


# --------------------------------------------------------------------------
# what a caller sees
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_a_kit_without_a_sheet_never_reports_as_interviewed():
    """The whole point of questions_source. A kit with no sheet and a kit whose
    sheet is fully answered both have nothing outstanding in the block itself;
    reporting them alike would call an un-interviewed domain ready."""
    from app.blocks.datacentre_kit import DatacentreKitBlock
    out = await DatacentreKitBlock().process(
        {"figures": [{"quantity": "power_capacity", "value": 1, "unit": "kW"}]}, {})
    state = out["result"]["interview"]
    assert state["questions_source"] == "derived"
    assert state["sheet_supplied"] is False
    assert state["ready"] is False
    assert "not the domain owner's own" in state["note"]


@pytest.mark.asyncio
async def test_a_kit_with_a_sheet_reports_the_owners_questions_and_what_is_next():
    from app.blocks.fitout_kit import FitoutKitBlock
    out = await FitoutKitBlock().process(
        {"figures": [{"quantity": "rate", "value": 1, "unit": "currency_per_m2"}]}, {})
    state = out["result"]["interview"]
    assert state["questions_source"] == "owner_sheet"
    assert state["sheet_supplied"] is True
    assert state["questions"] == 62
    assert state["ready"] is False
    first = state["next"][0]
    assert first["id"] == "B.1" and first["marked"] == "GATE"
    assert "quality band" in first["text"]


def test_covers_links_a_question_to_a_quantity_only_on_an_exact_naming():
    """A fuzzy link would report a figure as asked when nothing asks it."""
    interview = load_kit(BLOCKS / "rail").interview
    covered = {c for q in interview.questions for c in q.covers}
    quantities = set(load_kit(BLOCKS / "rail").manifest.quantities)
    assert covered <= quantities
    assert interview.for_quantity("face_pressure"), "the rail sheet names face pressure"
    assert not interview.for_quantity("no_such_quantity")
