# DECISIONS.md — Singapore ELV Data Product

> The narrative record required by the assignment: why this scope, what the
> headline number actually measures, where it can and cannot be trusted, and
> how the pilot generalizes to the capstone. Machine-facing decisions (ids,
> grains, load rules) live in `CLAUDE.md`; evidence lives in `verification/`.

## Why Singapore

The capstone thesis (*The Global ELV Recycling Gap*) is that **vehicles reach
end-of-life where they are used, not where they were produced** — so ELV
material flows are invisible to production-centric accounting. Singapore is the
sharpest single-country pilot for that claim because:

1. **Its data is unusually good.** LTA publishes monthly registrations,
   deregistrations, and vehicle stock back to 1990 (stock to 1962) through one
   API (data.gov.sg), with published annual totals to reconcile against. Few
   countries make the full stock-flow triple public at monthly grain.
2. **The COE system creates a ~10-year cohort clock.** Certificates of
   Entitlement expire, so deregistration timing is unusually predictable —
   ideal for the Part-2 projection.
3. **It stress-tests the thesis.** Singapore deregisters tens of thousands of
   cars a year but scraps only part of them domestically — much of the fleet
   leaves as used-car exports. If the export/scrap boundary is hard to see
   *even here*, with world-class open data, the global invisible-gap argument
   makes itself.

## Why this question

"How many vehicles reach end-of-life in Singapore each year, what happens to
them, and what is the recoverable material value of the domestically scrapped
stream?" — one country, one flow, every layer verifiable or explicitly labeled
where it is not.

## The headline metric — what it measures and its limits

**Layer 1 (verified headline): annual ELV generation = car deregistrations
(COE Categories A + B).**

- *What it measures:* cars permanently removed from Singapore's register —
  the flow that feeds both export and scrap channels. Verified against
  LTA's published annual totals (exact match, total and per-category,
  2023–2025; see `verification/checkpoint_b_scouting.md` §5) and — at
  Part 1 — a stock-flow invariant per COE category.
- *Scope reasoning:* Category E is bidding-only — no flow series carries an E
  row, and Σ(categories) = published Total with 0 violations across 72
  series-months (2023–2025), so E-COE cars are already inside A/B. Weekend/
  Off-Peak cars fold into A/B per LTA's own footnote.
- *Limit:* deregistration ≠ end-of-life in the material sense. An exported
  used car is an ELV for Singapore but not for the world.

## The reframe: the disposal split is a finding, not an input

*Decided 2026-07-08, after triangulation returned an impossible ratio.*

We set out to split deregistrations into exported vs. domestically scrapped.
Public data cannot do this cleanly:

- LTA does not publish the split anywhere reachable (LTA statistics PDFs,
  data.gov.sg — 80-dataset scan, SingStat — all checked, all negative).
- UN Comtrade HS 8703 conflates **new-car re-exports** with used-ELV exports:
  Singapore-reported export units vs. car deregistrations = **1.31 (2023)** —
  more exports than total car deregistrations — and 0.96 (2024).

So the product presents:

- **(a) Layer 1** — ELV generation — as the verified headline.
- **(b) Layer 2** — the disposal split — as a **bounded, low-confidence
  estimate** whose honest finding is: *"open data cannot separate domestic
  scrapping from export."* That is the invisible-gap thesis in miniature, and
  it is reported as such. **No fabricated percentage.**
- **(c) Layer 4** — material value at risk — as a **scenario range keyed to an
  assumed domestic-scrap share** (with the assumption on the axis, not buried),
  never a point estimate.
- Domain context (Singapore as a used-car export hub) appears only as labeled
  `unverified` context.

## Why trustworthy — and where not

| Layer | Trust basis | Where it breaks |
|---|---|---|
| Raw → clean pipeline | Landing files carry source URL + fetch timestamp; Σcategories = embedded Total checksum per period; replayable without re-fetch | Upstream revisions (LTA notes deregistration figures may change within a 1-month grace window) |
| Layer 1 ELV generation | Stock-flow invariant + exact reconciliation to LTA published annual totals | Pre-2005 history not yet reconciled against a published target |
| Layer 2 disposal split | Bounded above by Comtrade net weight/units; bounded below by zero; labeled `triangulated`, low confidence | The bound is loose: re-exports inflate it by an unknown amount; Comtrade 2025 qty field is broken (0 units against ~19kt) — net weight preferred, partial years flagged |
| Layer 4 material value | Scenario range; prices from LME; composition from literature | Composition/curb-weight inputs are `unverified` literature values; scrap-share axis is an assumption by construction |

## Capstone note — how this generalizes

The pipeline shape (landing with provenance → raw-as-is → cleaning view →
analysis-ready facts + invariant checks) transfers to any country with
registration/deregistration statistics; the verification strategy (stock-flow
invariant, reconciliation to published totals, trade-data triangulation)
transfers even where the data is worse — indeed the *failure mode* found here
(trade data cannot isolate used-vehicle flows) is expected to be the norm, and
quantifying that opacity country-by-country **is** the capstone's contribution.
Only the COE cohort clock is Singapore-specific; elsewhere the projection needs
an age-distribution survival model instead.
