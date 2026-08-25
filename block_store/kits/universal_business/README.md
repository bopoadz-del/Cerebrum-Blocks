# Universal Business Formulas

The baseline every business shares, before any domain is chosen. A new domain
kit starts here and adds what makes that domain different, rather than
re-deriving gross margin for the twentieth time.

29 formulas across nine categories: margin, pricing, break-even, tax,
receivables, billing, assets, liquidity, cash cycle, growth and finance.

## Why this file has no rates

Not one formula encodes a tax rate, an interest rate, a fee percentage or a
statutory threshold. Every such value is a named **input**.

That is not a gap; it is the whole design. A VAT rate written into a universal
set would be wrong for most businesses that load it, and it would be a figure
nobody could check — exactly the problem
`scripts/audit_kit_composition.py` exists to catch. A definitional identity
has no such problem: `gross_margin = (revenue - cogs) / revenue` is true in
every jurisdiction and every currency, and there is nothing in it to source.

Real rates belong to a real business. They enter through
`scripts/intake_formulas.py --kit <kit> --file <rates.json> --kind regulator
--reference "<where it came from>"`, into that business's own kit, where the
source is recorded next to the number.

The file's provenance record is therefore `internal_protocol` pointing at this
README: the set is Cerebrum's own documented definitions, not a claim about
anybody's published rates.

## The one exception, declared

`conventions[].receivables_aging_buckets` — 0-30 / 31-60 / 61-90 / 91+. This is
the only place carrying numbers rather than an identity. It is a widespread
reporting convention rather than a rule, it is marked `default_convention`, and
it is expected to be overridden per client. It sits in the manifest-declared
data file instead of hiding inside a report so that overriding it is a visible
act rather than a discovered one.

## Two traps the set encodes deliberately

**Margin is not markup.** `gross_margin_ratio` divides by revenue;
`markup_on_cost` divides by cost. A 25% margin requires a 33.3% markup. Both
`price_from_margin` and `price_from_markup` are provided so the choice is
explicit at the call site.

**Extracting tax is division.** `net_from_gross` is `gross / (1 + rate)`.
Multiplying a tax-inclusive price by the rate overstates the tax on every
invoice it touches.

## Composition

`"flow": "independent"` — declared, not inferred. `formula_executor_v2`
evaluates the set; `chat` asks questions of it. Neither feeds the other and
either is a valid entry point. The kit ships no domain container, so there is
no resolution order to state.

## Using it

The kit installs one artifact, `app/data/universal_formulas.json`, into the
target platform, where `formula_executor_v2` evaluates entries by `id`. Each
formula carries its `expression`, its named `inputs`, an `output` unit, and
where relevant a `guards` list naming the domain conditions
(`revenue != 0`, `unit_price > unit_variable_cost`) that the caller must
satisfy for the result to mean anything.
