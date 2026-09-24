"""The eight invariant kinds, plus `band`. One implementation each, shared by
every kit. Nothing here knows what a runway or a slab is.

  grounding        does this figure exist in evidence?                    H3
  qualifier        is it accompanied by what makes it actionable?          H3
  unit_discipline  are unit and datum stated, and not mixed?          H2 + H3
  authority        does it come from the class of source that governs?     H1
  provenance       was it carried from another entity or revision?        H3
  currency         has the thing that invalidates it happened?            H3
  scope            is the question answerable from documents at all?      H0
  derivation       do the stated working and the stated result agree?     H3
  band             is the value physically possible?                      H2

Each kind exists because a defect of that shape shipped to a live product and
was caught by counting, not by review. The comments name them.

Two rules hold in every domain and are enforced here, not left to kit authors:

  * **Never refuse the operator's own figure.** If they typed the rate it is
    authoritative input, not a claim to check: the severity is softened to
    `flag` and the finding records what it was softened from.
  * A finding names the invariant AND what is missing. "Blocked" on its own
    teaches the caller nothing and gets the layer switched off.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from app.blocks.kit_engine.figure import Figure, Finding, SEVERITIES
from app.blocks.kit_engine.manifest import Manifest

KINDS = (
    "grounding", "qualifier", "unit_discipline", "authority",
    "provenance", "currency", "scope", "derivation", "band",
)

H0_PRE_RETRIEVAL = "H0"
H1_RANKING = "H1"
H2_TOOL_TIME = "H2"
H3_ANSWER_TIME = "H3"
H4_EXPORT_TIME = "H4"

#: Which hook each kind runs at. unit_discipline runs at TWO hooks on purpose:
#: H2 alone misses figures the model states without a tool; H3 alone lets a
#: corrupted value reach exports and source panels before anyone checks.
HOOKS_BY_KIND: Dict[str, Tuple[str, ...]] = {
    "scope": (H0_PRE_RETRIEVAL,),
    "authority": (H1_RANKING,),
    "unit_discipline": (H2_TOOL_TIME, H3_ANSWER_TIME),
    "band": (H2_TOOL_TIME,),
    "grounding": (H3_ANSWER_TIME,),
    "qualifier": (H3_ANSWER_TIME,),
    "provenance": (H3_ANSWER_TIME,),
    "currency": (H3_ANSWER_TIME,),
    "derivation": (H3_ANSWER_TIME,),
}


class InvariantError(ValueError):
    """An invariant record is not usable. The kit is disabled, and refuses."""


@dataclass
class Invariant:
    id: str
    kind: str
    severity: str
    applies_to: Dict[str, Any] = field(default_factory=dict)
    requires: Tuple[str, ...] = ()
    requires_one_of: Tuple[str, ...] = ()
    forbid: Tuple[str, ...] = ()
    across: Tuple[str, ...] = ()
    band: Dict[str, Any] = field(default_factory=dict)
    window: Dict[str, Any] = field(default_factory=dict)
    governing: Tuple[str, ...] = ()
    evidence: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    #: A repeat-probe question, N runs, a number before and after. An invariant
    #: you cannot count is an opinion, so the loader requires this.
    measurement: str = ""
    _classes: Dict[str, Tuple[str, ...]] = field(default_factory=dict, repr=False)

    def hooks(self) -> Tuple[str, ...]:
        return HOOKS_BY_KIND[self.kind]

    def quantities(self) -> Tuple[str, ...]:
        raw = self.applies_to.get("quantity")
        if raw is None:
            return ()
        return (str(raw),) if isinstance(raw, str) else tuple(str(q) for q in raw)

    def governs(self, quantity: str) -> bool:
        """`any_*` is a CLASS the manifest defines, never a wildcard.

        The first cut treated it as match-all, and INV-UNITS-DATUM then demanded
        a vertical datum for a PCN — a bearing-strength number with neither unit
        nor datum. `any` alone still means every quantity, spelled out.
        """
        wanted = self.quantities()
        if not wanted or wanted == ("any",):
            return True
        for name in wanted:
            if name == quantity:
                return True
            if name.startswith("any_") and quantity in self._classes.get(name, ()):
                return True
        return False


def _text(inv: "Invariant", computed: str) -> str:
    """The kit's declared message is a HEADLINE, not a replacement.

    The first cut used ``inv.message or computed``, so any kit that declared a
    message silently DISCARDED the specifics — which facility the figure came
    from, which equation disagreed with its own result. That is exactly the
    "blocked teaches the caller nothing" failure this layer exists to prevent,
    and it was in the evaluator itself. The declared text leads; the computed
    detail always follows.
    """
    headline = (inv.message or "").strip()
    computed = (computed or "").strip()
    if not headline:
        return computed
    if not computed:
        return headline
    return f"{headline} [{computed}]"


def _render(message: str, missing: Sequence[str], figure: Optional[Figure] = None) -> str:
    text = message.replace("{missing}", ", ".join(missing) if missing else "its qualifiers")
    if figure is not None:
        text = text.replace("{value}", str(figure.value)).replace("{quantity}", figure.quantity)
    return text


def parse_invariant(raw: Any, classes: Dict[str, Tuple[str, ...]], where: str) -> Invariant:
    """Parse one invariant record. Every rejection prevents a silent no-op."""
    if not isinstance(raw, dict):
        raise InvariantError(f"{where}: an invariant must be a mapping")
    inv_id = str(raw.get("id") or "").strip()
    if not inv_id:
        raise InvariantError(f"{where}: an invariant must declare an id")
    kind = str(raw.get("kind") or "").strip()
    if kind not in KINDS:
        raise InvariantError(
            f"{where}: {inv_id} has kind {kind!r}; expected one of {', '.join(KINDS)}"
        )
    severity = str(raw.get("severity") or "").strip()
    if severity not in SEVERITIES:
        raise InvariantError(
            f"{where}: {inv_id} has severity {severity!r}; expected one of "
            f"{', '.join(SEVERITIES)}"
        )
    measurement = str(raw.get("measurement") or "").strip()
    if not measurement:
        raise InvariantError(
            f"{where}: {inv_id} declares no measurement case. An invariant you cannot "
            f"count is an opinion — name the repeat-probe question and the number"
        )

    inv = Invariant(
        id=inv_id,
        kind=kind,
        severity=severity,
        applies_to=dict(raw.get("applies_to") or {}),
        requires=tuple(str(f) for f in (raw.get("requires") or ())),
        requires_one_of=tuple(str(f) for f in (raw.get("requires_one_of") or ())),
        forbid=tuple(str(f) for f in (raw.get("forbid") or ())),
        across=tuple(str(f) for f in (raw.get("across") or ())),
        band=dict(raw.get("band") or {}),
        window=dict(raw.get("window") or {}),
        governing=tuple(str(c) for c in (raw.get("governing") or ())),
        evidence=dict(raw.get("evidence") or {}),
        message=str(raw.get("message") or ""),
        measurement=measurement,
        _classes=classes,
    )

    # A record that could never fire reports green while gating nothing.
    if kind == "qualifier" and not inv.requires:
        raise InvariantError(f"{where}: {inv_id} is a qualifier invariant requiring no fields")
    if kind == "unit_discipline" and not (inv.requires_one_of or inv.forbid):
        raise InvariantError(
            f"{where}: {inv_id} must declare requires_one_of or forbid"
        )
    if kind == "provenance" and not inv.across:
        raise InvariantError(
            f"{where}: {inv_id} must name the dimensions a figure may not cross"
        )
    if kind == "currency" and not inv.window.get("provider"):
        raise InvariantError(f"{where}: {inv_id} must name a state provider in window")
    if kind == "band" and not (inv.band.get("min") is not None or inv.band.get("max") is not None):
        raise InvariantError(f"{where}: {inv_id} declares no band min or max")
    if kind == "authority" and not inv.governing:
        raise InvariantError(
            f"{where}: {inv_id} must name the governing source class(es)"
        )
    for wanted in inv.quantities():
        if wanted.startswith("any_") and wanted not in classes:
            raise InvariantError(
                f"{where}: {inv_id} applies to class '{wanted}', which no quantity "
                f"declares. An invariant that matches nothing is a decoration"
            )
    return inv


def _finding(
    inv: Invariant, figure: Optional[Figure], message: str, missing: Sequence[str] = ()
) -> Finding:
    """Build the finding, applying the never-refuse-the-operator rule."""
    # The kit's declared message is a HEADLINE and the computed detail always
    # follows it. Applied here, once, so no evaluator can drop the specifics.
    # Compose first, THEN render: a declared headline carries {missing} and
    # {value} too, and substituting only the computed half left "{missing}"
    # printed literally in the operator's refusal.
    message = _render(_text(inv, message), missing, figure)
    severity = inv.severity
    softened = None
    if figure is not None and figure.is_operators_own and severity == "refuse":
        severity, softened = "flag", inv.severity
        message = (
            message
            + " — flagged, not refused: this is the operator's own figure, which is "
            "authoritative input rather than a claim to check"
        )
    return Finding(
        invariant_id=inv.id,
        kind=inv.kind,
        severity=severity,
        message=message,
        quantity=figure.quantity if figure else "",
        missing=list(missing),
        span=dict(figure.span) if (figure and figure.span) else None,
        softened_from=softened,
    )


# ---------------------------------------------------------------- grounding --

def eval_grounding(inv: Invariant, figure: Figure, manifest: Manifest) -> Optional[Finding]:
    """A figure the model produced with no source is an invented figure.

    Live: "a rate nobody supplied". ``operator`` origin is exempt by definition —
    the operator IS the source.
    """
    if not inv.governs(figure.quantity):
        return None
    if figure.origin in ("operator",):
        return None
    if figure.origin in ("document", "tool") and figure.source_id:
        return None
    return _finding(
        inv, figure,
        _render((
            "{quantity} = {value} is not grounded: origin is "
            + figure.origin
            + " with no source_id. A figure nobody supplied is invented"
        ), (), figure),
        ["source_id"],
    )


# ---------------------------------------------------------------- qualifier --

def eval_qualifier(inv: Invariant, figure: Figure, manifest: Manifest) -> Optional[Finding]:
    if not inv.governs(figure.quantity):
        return None
    missing = figure.missing(inv.requires)
    if not missing:
        return None
    return _finding(
        inv, figure,
        _render("a {quantity} figure without {missing} cannot be acted on",
                missing, figure),
        missing,
    )


# ---------------------------------------------------------- unit_discipline --

_BARE_NUMBER = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?(?![\w.%])")
_UNIT_NEAR_NUMBER = re.compile(
    r"-?\d[\d,]*(?:\.\d+)?\s*(?:mm|cm|m|km|ft|in|nm|kg|t|kN|kPa|MPa|psi|psig|%|"
    r"days?|hours?|s|deg|°|mg/l|ppm)\b",
    re.IGNORECASE,
)
_UNIT_TOKEN = re.compile(r"-?\d[\d,]*(?:\.\d+)?\s*(mm|m|ft|metres|meters|feet|in|inches)\b",
                         re.IGNORECASE)
_UNIT_NORMAL = {
    "mm": "mm", "m": "m", "metres": "m", "meters": "m",
    "ft": "ft", "feet": "ft", "in": "in", "inches": "in",
}

#: Datum families whose members must never be mixed in one statement.
DATUM_FAMILIES: Dict[str, Tuple[str, ...]] = {
    "vertical": ("AMSL_m", "AMSL_ft", "AOD", "chart datum", "berth datum"),
    "horizontal": ("WGS-84", "WGS84", "local grid", "national grid"),
    "bearing": ("magnetic", "true"),
}

#: A datum whose NAME encodes the unit the figure must be in.
DATUM_UNITS: Dict[str, str] = {"AMSL_m": "m", "AMSL_ft": "ft"}


def _datum_unit_conflict(figure: Figure) -> Optional[str]:
    """The figure's unit disagrees with the unit its datum names.

    This is the well-qualified-but-wrong case: a unit IS present and a datum IS
    present, and they contradict. An elevation in feet against a metre datum
    reads as complete and is not the height it looks like.
    """
    for name, value in figure.qualifiers.items():
        expected = DATUM_UNITS.get(str(value))
        if expected is None:
            continue
        stated = []
        if figure.unit:
            stated.append(_UNIT_NORMAL.get(str(figure.unit).lower(), str(figure.unit).lower()))
        for match in _UNIT_TOKEN.finditer(figure.text or ""):
            stated.append(_UNIT_NORMAL[match.group(1).lower()])
        wrong = sorted({u for u in stated if u in ("m", "ft", "mm", "in") and u != expected})
        if wrong:
            return f"{', '.join(wrong)} quoted against {name}={value}"
    return None


def _mixed_datum(text: str) -> Optional[str]:
    lowered = (text or "").lower()
    for family, members in DATUM_FAMILIES.items():
        present = {m for m in members if m.lower() in lowered}
        if len(present) >= 2:
            return f"{family}: {', '.join(sorted(present))}"
    return None


def eval_unit_discipline(
    inv: Invariant, figure: Figure, manifest: Manifest
) -> Optional[Finding]:
    if not inv.governs(figure.quantity):
        return None

    if "mixed_datum" in inv.forbid:
        conflict = _datum_unit_conflict(figure)
        if conflict:
            return _finding(inv, figure, (
                f"mixed datum: {conflict}. The datum names its own unit, so a figure "
                f"quoted in the other one is not the value it appears to be"
            ))
        mixed = _mixed_datum(figure.text)
        if mixed:
            return _finding(inv, figure, (
                f"two datums in one statement ({mixed}) — a figure carries one datum "
                f"or it cannot be compared to anything"
            ))

    # The unit must be one the kit declares legal for this quantity. Live: a
    # slab calculator bound metres to a millimetre parameter and returned
    # `0.2 mm` with status success.
    spec = manifest.quantities.get(figure.quantity)
    if spec and spec.units and figure.unit and figure.unit not in spec.units:
        return _finding(inv, figure, (
            f"unit {figure.unit!r} is not legal for {figure.quantity} "
            f"(expected one of {', '.join(spec.units)})"
        ), ["unit"])

    if inv.requires_one_of:
        haystack = (figure.text or "").lower()
        values = {str(v).lower() for v in figure.qualifiers.values() if v is not None}
        if not any(t.lower() in haystack or t.lower() in values for t in inv.requires_one_of):
            return _finding(inv, figure, (
                "no datum stated — one of "
                + ", ".join(inv.requires_one_of)
                + " is required, because a figure without a datum is not a measurement"
            ), list(inv.requires_one_of))

    if "bare_number" in inv.forbid and not figure.unit:
        if _BARE_NUMBER.search(figure.text or "") and not _UNIT_NEAR_NUMBER.search(figure.text or ""):
            return _finding(inv, figure, (
                "bare number — every figure carries its unit; a number whose unit the "
                "reader must guess is how metres become millimetres"
            ), ["unit"])
    return None


# ---------------------------------------------------------------- authority --

def eval_authority(inv: Invariant, figure: Figure, manifest: Manifest) -> Optional[Finding]:
    """The figure must come from the class of source that governs the question.

    Live: a site-office mobilisation statement answering a specification
    question. The ladder is in the manifest; `reject_as_proof` says which class
    may not stand in for which.
    """
    if not inv.governs(figure.quantity):
        return None
    if figure.source_class is None:
        return _finding(inv, figure, (
            f"{figure.quantity} carries no source class, so it cannot be ranked against "
            f"the class that governs ({', '.join(inv.governing)})"
        ), ["source_class"])
    if figure.source_class in inv.governing:
        return None
    mine = manifest.source_classes.get(figure.source_class)
    for governing_name in inv.governing:
        governing = manifest.source_classes.get(governing_name)
        if governing is None:
            continue
        if figure.source_class in governing.reject_as_proof:
            return _finding(inv, figure, (
                f"a {figure.source_class} is not proof of {figure.quantity}: "
                f"{governing_name} governs, and {figure.source_class} is explicitly "
                f"rejected as proof of it"
            ))
        if mine is not None and mine.rank > governing.rank:
            return _finding(inv, figure, (
                f"{figure.source_class} (rank {mine.rank}) is outranked by "
                f"{governing_name} (rank {governing.rank}) for {figure.quantity}"
            ))
    return None


# --------------------------------------------------------------- provenance --

_CARRY_VERB = re.compile(
    r"\bsame\b|\bapplies\b|\bapply\b|\bcarry\b|\bcarried\b|\breuse\b|\bas\s+well\b|"
    r"\bequivalent\b|\btransfer\b|\bsimilar\b|\banother\b",
    re.IGNORECASE,
)


def eval_provenance(inv: Invariant, figure: Figure, manifest: Manifest) -> Optional[Finding]:
    """Was the figure carried from another entity or revision?

    The check is NOT "this dimension appears twice". Naming the same runway
    twice is what a CORRECT answer looks like, and a mention-counting regex
    blocks it — that bug was written and fixed by hand in the first kit built
    this way. Carrying means the figure's OWN entity differs from the entity the
    question is about, or two DISTINCT values appear with a carry verb.

    Live: delay damages computed on another contract's amount.
    """
    if not inv.governs(figure.quantity):
        return None

    for dimension in inv.across:
        mine = figure.qualifiers.get(dimension)
        if dimension == "revision":
            mine = figure.revision if figure.revision is not None else mine
        theirs = figure.asked_about.get(dimension)
        if mine is not None and theirs is not None and str(mine) != str(theirs):
            return _finding(inv, figure, (
                f"this figure belongs to {dimension}={mine}; the question is about "
                f"{dimension}={theirs}. A figure does not carry across {dimension}"
            ), [dimension])

    text = figure.text or ""
    if _CARRY_VERB.search(text):
        for dimension in inv.across:
            spec = manifest.qualifier_fields.get(dimension)
            values = _distinct_values(text, spec)
            if len(values) >= 2:
                return _finding(inv, figure, (
                    f"carrying a figure across {dimension} "
                    f"({' -> '.join(values[:2])}) is never allowed"
                ), [dimension])
    return None


def _distinct_values(text: str, spec: Any) -> List[str]:
    if spec is None:
        return []
    found: List[str] = []
    if spec.type == "enum":
        for value in spec.values:
            if re.search(rf"\b{re.escape(str(value))}\b", text, re.IGNORECASE):
                if str(value) not in found:
                    found.append(str(value))
    elif spec.pattern:
        for match in re.finditer(spec.pattern, text):
            if match.group(0) not in found:
                found.append(match.group(0))
    return found


# ----------------------------------------------------------------- currency --

def eval_currency(
    inv: Invariant,
    figure: Figure,
    manifest: Manifest,
    state: Optional[Dict[str, Any]] = None,
    events: Optional[Sequence[str]] = None,
    now: Optional[float] = None,
) -> Optional[Finding]:
    """Has the thing that invalidates this figure happened?

    Currency is usually an EVENT, not a clock: "any valve operation", "any
    approved MOC". A provider that cannot be read yields UNKNOWN — never a
    fallback to the design basis, because a design figure presented as a live
    state is the defect.
    """
    if not inv.governs(figure.quantity):
        return None
    provider_name = str(inv.window.get("provider"))
    provider = manifest.state_providers.get(provider_name)
    if provider is None:
        return _finding(inv, figure, (
            f"state provider '{provider_name}' is not declared by this kit, so "
            f"currency cannot be established"
        ), [provider_name])

    record = (state or {}).get(provider_name)
    if record is None:
        return _finding(inv, figure, (
            f"state UNKNOWN — {provider_name} unavailable. Live state has no "
            f"design-basis fallback: a design figure is not a current state"
        ), [provider_name])

    happened = [e for e in (events or ()) if e in manifest.staleness_triggers.get(figure.quantity, ())]
    if happened:
        return _finding(inv, figure, (
            f"{figure.quantity} is stale: " + ", ".join(happened)
            + " has happened since it was recorded"
        ), happened)

    max_age = inv.window.get("max_age", provider.max_age)
    try:
        seconds = float(max_age)
    except (TypeError, ValueError):
        seconds = None
    if seconds is not None:
        import time as _time

        moment = now if now is not None else _time.time()
        as_of = record.get("as_of") if isinstance(record, dict) else None
        if as_of is None or (moment - float(as_of)) > seconds:
            return _finding(inv, figure, (
                f"{provider_name} record is older than its {seconds:g}s validity"
            ), [provider_name])
    return None


# -------------------------------------------------------------------- scope --

def eval_scope(manifest: Manifest, question: str, severity: str = "refuse") -> Optional[Finding]:
    """Classify the question BEFORE retrieval.

    No document makes an operational-authority question answerable, so
    retrieving at all is wrong: it produces citations that read as though they
    authorised the decision. Live: "can we put the crane here", "will this
    affect the ILS".
    """
    for refusal in manifest.scope_refusals:
        if refusal.matches(question):
            return Finding(
                invariant_id=f"SCOPE:{refusal.label}",
                kind="scope",
                severity=severity,
                message=(
                    f"refused before retrieval ({refusal.label}): this is "
                    f"{refusal.authority}'s decision. No document makes it answerable, "
                    f"so nothing was retrieved"
                ),
            )
    return None


# --------------------------------------------------------------- derivation --

_EQUATION = re.compile(
    r"(-?\d[\d,]*(?:\.\d+)?)\s*([/*x×+-])\s*(-?\d[\d,]*(?:\.\d+)?)\s*=\s*(-?\d[\d,]*(?:\.\d+)?)"
)


def _number(token: str) -> float:
    return float(token.replace(",", ""))


def check_arithmetic(text: str, tolerance: float = 0.01) -> Optional[Tuple[str, float, float]]:
    """Find a stated ``a op b = c`` whose result is wrong.

    Live: "L/20 = 4800/20 = **200 mm**" — the rule right, the span right, the
    result wrong. That is the hardest defect to see by reading, and it is
    trivial to catch by evaluating.
    """
    for match in _EQUATION.finditer(text or ""):
        left, op, right, stated = match.groups()
        try:
            a, b, c = _number(left), _number(right), _number(stated)
        except ValueError:
            continue
        if op == "/":
            if b == 0:
                continue
            expected = a / b
        elif op in ("*", "x", "×"):
            expected = a * b
        elif op == "+":
            expected = a + b
        else:
            expected = a - b
        if expected == 0:
            if abs(c) > tolerance:
                return match.group(0), expected, c
            continue
        if abs(expected - c) / abs(expected) > tolerance:
            return match.group(0), expected, c
    return None


def eval_derivation(
    inv: Invariant, figure: Figure, manifest: Manifest, siblings: Sequence[Figure] = ()
) -> Optional[Finding]:
    """Do the stated working and the stated result agree — and does the answer
    agree with itself?

    Two live defects, one kind: an equation whose arithmetic is wrong, and the
    same quantity stated twice with different values in one answer ("40 days"
    and "400 days").
    """
    if not inv.governs(figure.quantity):
        return None

    wrong = check_arithmetic(figure.text)
    if wrong:
        shown, expected, stated = wrong
        return _finding(inv, figure, (
            f"stated working and stated result disagree: '{shown}' — "
            f"{expected:g}, not {stated:g}"
        ))

    for other in siblings:
        if other is figure or other.quantity != figure.quantity:
            continue
        if other.value is None or figure.value is None:
            continue
        if other.unit == figure.unit and other.value != figure.value:
            return _finding(inv, figure, (
                f"the answer contradicts itself on {figure.quantity}: "
                f"{figure.value} and {other.value} "
                f"{figure.unit or ''}".strip()
            ))
    return None


# --------------------------------------------------------------------- band --

def eval_band(inv: Invariant, figure: Figure, manifest: Manifest) -> Optional[Finding]:
    """Is the value physically possible? Caught where it is born, at H2.

    Live: a slab calculator returned `0.2 mm` with status success, because
    metres were bound to a millimetre parameter. Nothing downstream questioned
    it, and it was narrated to the user as a result.
    """
    if not inv.governs(figure.quantity):
        return None
    if figure.value is None or isinstance(figure.value, bool):
        return None
    try:
        value = float(figure.value)
    except (TypeError, ValueError):
        return None
    low, high = inv.band.get("min"), inv.band.get("max")
    if low is not None and value < float(low):
        return _finding(inv, figure, (
            f"{figure.quantity} = {figure.value}{figure.unit or ''} is below the "
            f"possible minimum {low}{figure.unit or ''} — check the unit it was "
            f"computed in"
        ))
    if high is not None and value > float(high):
        return _finding(inv, figure, (
            f"{figure.quantity} = {figure.value}{figure.unit or ''} is above the "
            f"possible maximum {high}{figure.unit or ''} — check the unit it was "
            f"computed in"
        ))
    return None
