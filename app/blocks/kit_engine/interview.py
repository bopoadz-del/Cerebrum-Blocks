"""The interview — the questions a kit needs answered, in the owner's own words.

``manifest.yaml`` says what the domain TALKS about. ``invariants.yaml`` says what
must hold. Neither says what the platform has to go and ASK, and until the domain
owner supplied their question sheets the kits carried a question derived from the
quantity name — "what is the rate?" — which is one number for a whole domain and
unanswerable in practice. The sheet asks for the rate per package, the lead time
per item, the geometry limit at each of three tiers.

``questions.yaml`` is that sheet, generated from ``docs/kit_questions/<kit>.md``
by ``scripts/import_kit_questions.py``. Two things in it cannot be derived from
anything else the kit holds:

  gate            the owner's own [GATE] / [GAP] split. GATE blocks; GAP is
                  experience the platform is better for having. Before this, the
                  kit treated every unanswered figure as blocking, which would
                  have held a platform hostage to "what a PM new to fit-out most
                  commonly gets wrong in their first year".
  answer_format   the fields an answer must arrive with, per domain. Fit-out wants
                  quality band and market; fire protection wants the code edition;
                  dental wants adult-or-paediatric and the protocol version. The
                  kernel reads this rather than holding its own list, so there is
                  one definition of a complete answer per domain.

UNMARKED counts as GATING. The FM sheet marks nothing, and a question whose class
cannot be read must block rather than pass — the same fail-closed rule as the rest
of the layer. ``Question.marked`` tells them apart for a reader.

NO ANSWERS LIVE HERE. A kit is a signed Store block shared by every customer;
answers are per-platform and belong in the platform's own storage. This module
only ever READS an answer map the caller passes in.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml

QUESTIONS_FILE = "questions.yaml"

#: The one answer-format entry that is the answer itself rather than a field that
#: must accompany it. Everything else in the sheet's format line is required.
VALUE_FIELD = "value"


class InterviewError(ValueError):
    """questions.yaml is not usable. The kit is disabled, which means it refuses.

    A kit whose interview will not parse must not fall back to "no questions":
    that reads as an interview with nothing outstanding, which is the single most
    misleading thing this file could report.
    """


@dataclass(frozen=True)
class Question:
    id: str
    section: str
    section_title: str
    text: str
    #: True = [GATE], False = [GAP], None = the sheet marked neither.
    gate: Optional[bool] = None
    covers: Tuple[str, ...] = ()
    #: The sheet gave no id for this one and the importer assigned a positional
    #: one. Surfaced so nobody cites it back to the owner as their numbering.
    id_assigned: bool = False

    @property
    def gating(self) -> bool:
        """Unmarked gates. Only an explicit [GAP] does not."""
        return self.gate is not False

    @property
    def marked(self) -> str:
        return "GATE" if self.gate is True else ("GAP" if self.gate is False else "unmarked")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "section": self.section,
            "section_title": self.section_title,
            "text": self.text,
            "marked": self.marked,
            "gating": self.gating,
            "covers": list(self.covers),
            "id_assigned": self.id_assigned,
        }


@dataclass(frozen=True)
class Interview:
    kit: str
    title: str
    source_document: str
    answer_format: Tuple[str, ...]
    sections: Dict[str, str] = field(default_factory=dict)
    questions: Tuple[Question, ...] = ()

    # ---- the shape of a complete answer, per domain -----------------------

    def required_fields(self) -> Tuple[str, ...]:
        """The metadata an answer must arrive with, derived from the sheet's own
        'Answer format:' line — every entry but the value itself, as a key.

        Derived rather than declared a second time: 'quality band' becomes
        ``quality_band``, 'confirmed or indicative' becomes
        ``confirmed_or_indicative``. Those are the same names the manifests
        already use for their qualifier fields, which is why the mapping is
        mechanical and not a translation table someone has to maintain.
        """
        return tuple(
            entry.strip().lower().replace(" ", "_")
            for entry in self.answer_format
            if entry.strip().lower() != VALUE_FIELD
        )

    # ---- lookup ----------------------------------------------------------

    def by_id(self, qid: str) -> Optional[Question]:
        for question in self.questions:
            if question.id == qid:
                return question
        return None

    def for_quantity(self, quantity: str) -> Tuple[Question, ...]:
        """The sheet questions that visibly ask about this quantity. Empty is a
        real answer: it means the sheet does not name it, and the kit's derived
        question is all there is."""
        return tuple(q for q in self.questions if quantity in q.covers)

    # ---- state -----------------------------------------------------------

    def outstanding(self, answered: Optional[Mapping[str, Any]] = None) -> Tuple[Question, ...]:
        """Gating questions with no answer, in sheet order.

        Sheet order, not sorted: the owner grouped these into sections that run
        from rates to incidents, and asking them out of that order makes the
        interview read as a random quiz.
        """
        have = set(answered or {})
        return tuple(q for q in self.questions if q.gating and q.id not in have)

    def gaps(self, answered: Optional[Mapping[str, Any]] = None) -> Tuple[Question, ...]:
        """Unanswered [GAP] questions. Worth asking, never blocking."""
        have = set(answered or {})
        return tuple(q for q in self.questions if not q.gating and q.id not in have)

    def ready(self, answered: Optional[Mapping[str, Any]] = None) -> bool:
        return not self.outstanding(answered)

    def status(self, answered: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        have = set(answered or {})
        unknown = sorted(qid for qid in have if self.by_id(qid) is None)
        gating = [q for q in self.questions if q.gating]
        out = self.outstanding(answered)
        return {
            "kit": self.kit,
            "source_document": self.source_document,
            "questions": len(self.questions),
            "gating": len(gating),
            "gaps": len(self.questions) - len(gating),
            "answered": len(have & {q.id for q in self.questions}),
            "outstanding": len(out),
            "ready": not out,
            "required_fields": list(self.required_fields()),
            # An answer against an id the sheet does not have is not a pass and
            # not a silent discard: it is named, because it means somebody
            # answered a question this kit never asked.
            "answers_to_unknown_questions": unknown,
        }


def parse_interview(raw: Any, where: str = "questions.yaml") -> Interview:
    if not isinstance(raw, dict):
        raise InterviewError(f"{where}: not a mapping")
    kit = str(raw.get("kit") or "").strip()
    if not kit:
        raise InterviewError(f"{where}: names no kit")
    answer_format = tuple(str(f) for f in (raw.get("answer_format") or ()))
    if not answer_format:
        raise InterviewError(
            f"{where}: no answer_format — without it nothing knows which fields an "
            f"answer must carry, and every answer would be accepted bare"
        )
    sections = {
        str(sid): str((spec or {}).get("title") or "")
        for sid, spec in (raw.get("sections") or {}).items()
    }
    records = raw.get("questions")
    if not records:
        raise InterviewError(
            f"{where}: kit '{kit}' declares no questions. An interview with nothing "
            f"outstanding reads as a finished one"
        )
    questions: List[Question] = []
    seen: set = set()
    for record in records:
        if not isinstance(record, dict):
            raise InterviewError(f"{where}: each question must be a mapping")
        qid = str(record.get("id") or "").strip()
        if not qid:
            raise InterviewError(f"{where}: a question has no id — an answer could never find it")
        if qid in seen:
            raise InterviewError(f"{where}: duplicate question id {qid}")
        seen.add(qid)
        text = str(record.get("text") or "").strip()
        if not text:
            raise InterviewError(f"{where}: question {qid} has no text")
        gate = record.get("gate")
        if gate not in (True, False, None):
            raise InterviewError(
                f"{where}: question {qid} has gate={gate!r}; expected true ([GATE]), "
                f"false ([GAP]) or null (the sheet marked neither)"
            )
        section = str(record.get("section") or "")
        if section and section not in sections:
            raise InterviewError(
                f"{where}: question {qid} is in section '{section}', which is not declared"
            )
        questions.append(Question(
            id=qid,
            section=section,
            section_title=sections.get(section, ""),
            text=text,
            gate=gate,
            covers=tuple(str(c) for c in (record.get("covers") or ())),
            id_assigned=bool(record.get("id_assigned")),
        ))
    return Interview(
        kit=kit,
        title=str(raw.get("title") or ""),
        source_document=str(raw.get("source_document") or ""),
        answer_format=answer_format,
        sections=sections,
        questions=tuple(questions),
    )


def load_interview(directory: pathlib.Path) -> Optional[Interview]:
    """The kit's interview, or None when the domain owner has supplied no sheet.

    None is not an error and is not emptiness: it means this kit still runs on the
    derived one-per-quantity questions, and every caller that reports interview
    state has to say so rather than showing a kit with no questions as complete.
    """
    path = pathlib.Path(directory) / QUESTIONS_FILE
    if not path.is_file():
        return None
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise InterviewError(f"{path}: unreadable: {exc}") from exc
    return parse_interview(raw, where=str(path))
