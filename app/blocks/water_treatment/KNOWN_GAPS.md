# Known gaps — water treatment plant operations

all figures — pending interview, domain encoding sheet, Water Treatment Plant
Operations.

No interview has run. Every `value` in `manifest.yaml` is `null` and stays null
until it does. The qualifiers are present and enforced at load time; the values
are not, and this layer refuses rather than supplying a figure it does not
have.

Specifically outstanding:

- **All CT figures, every temperature/pH row** — CT_required and CT_achieved
  are read off the correct row of the CT table for the actual temperature and
  pH, not the nearest row and not an average. Without the table and the
  disinfectant/organism/log-target context, INV-1 refuses every CT question.
- **Contact-time basis per basin** — the clearwell tracer study (T10) and the
  rapid-mix theoretical detention are not interchangeable, and neither is
  supplied yet. Without the tracer study, INV-2 refuses every clearwell
  contact-time question that needs it.
- **Delivered chemical strength, per delivery** — the nameplate/rated strength
  on the drum is not the delivered strength; the delivered strength is
  supplied by the certificate of analysis on EACH delivery and is not
  recorded yet (staleness: "chemical strength — EACH delivery").
- **Regulatory limits with averaging basis, monitoring frequency and named
  regulation** — turbidity and distribution residual limits are not usable
  until all three are attached; a limit without them cannot be checked
  against a reading.
- **Cost figures** — not supplied; out of scope beyond what plant operations
  supplies.
- **Incident shapes** — the failure histories that would seed regression
  tests (analyser calibration lapses, boil-notice triggers) are not recorded.

## Not gaps

The refusals are not gaps. A question this layer refuses before retrieval —
is this water safe to supply, can we skip filter-to-waste, do we need a boil
notice, can I enter the chlorine room — stays refused after the interview.
Those are named-person decisions and no manifest value changes that.

INV-5 (conflicting limits from two sources) is likewise not a gap the
interview closes: a permit stricter than the underlying code is a standing
conflict to be reported, not resolved by picking one source as authoritative.
