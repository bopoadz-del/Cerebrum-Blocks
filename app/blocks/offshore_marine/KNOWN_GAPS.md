# Known gaps — offshore marine operations

**all figures — pending interview, domain encoding sheet, Offshore Oil & Gas
Marine Operations.**

No interview has run. Every `value` in `manifest.yaml` is `null` and stays null
until it does. The qualifiers are present and enforced at load time; the values
are not, and this layer refuses rather than supplying a figure it does not have.

Specifically outstanding:

- **All figures per spread type** — s_lay, j_lay, reel_lay, heavy_lift. Nothing
  carries between them, so each needs its own set; a figure filled for one
  spread does not reduce the gap for another.
- **All DP capability plots** — intact and per failure case. Without the plot
  the failure case cannot be named, so INV-4 refuses every DP question.
- **Forecast alpha factor** — no weather window can be stated without it
  (derivation guard: "window without alpha").
- **Weather criteria** — Hs and Tp together, from one source. Hs alone is
  rejected as proof.
- **Cost figures** — not supplied; out of scope beyond what the barge master
  supplies.
- **Incident shapes** — the failure histories that would seed regression tests
  are not recorded.

## Not gaps

The refusals are not gaps. A question this layer refuses before retrieval —
can we start the lift, is the weather OK, can we run on two thrusters, is it
safe to dive, can we get closer — stays refused after the interview. Those are
named-person decisions and no manifest value changes that.
