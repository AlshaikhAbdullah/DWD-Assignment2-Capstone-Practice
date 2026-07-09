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

**Bound semantics of the residual** (*locked 2026-07-09*): because the
Comtrade export proxy is an **upper bound** on used-car exports (new-car
re-export contamination — the same effect that pushes the 2023 proxy above
total car deregistrations), the residual `deregistrations − proxy` is a
**floor**: the 2024 `scrapped_est_residual` of 1,368 is a **low-confidence
LOWER bound on domestic scrapping, not a point estimate** — true scrapped is
likely higher. `elv_disposal_split` carries `scrapped_bound_direction` /
`export_bound_direction` columns (and BigQuery column descriptions) so no
downstream stage can read either as a clean count. In the Layer-4 scenario
band, this floor is **one anchor inside the band, never the tonnage**.

**Comtrade cross-check scope** (*locked 2026-07-08*): the Comtrade
triangulation is a **spot cross-check limited to qty-available years — 2023
and 2024** for the analysis window (`qty` is broken in 2022 and 2025: zero
units against 15–19 kt of net weight; earlier qty years exist but predate the
analysis window and carry the same re-export conflation). FOB value is the
only field spanning all of 2005–2025, and **no stage may compare FOB dollars
to vehicle counts on the same axis** — value-only years are **labeled
context, not a series**.

**Deregistration = permanent removal — confirmed 2026-07-09.** LTA's own
definition (OneMotoring, fetched): deregistration cancels the registration
and REQUIRES disposal — scrapping, export, or EPZ-pending-export — with
proof within 1 month; keeping or using a deregistered vehicle is an offence.
Temporary "Vehicle Lay-Up" is a separate *Owning* scheme in which the car
stays registered and never enters the deregistration series. Empirically:
status/scheme changes appear in our stock-flow residuals as within-month
category transfers, never as dereg+re-reg events. The ELV-generation
headline (deregistrations = permanent removals) stands. Known bounded
revision channel: 1-month COE revalidation grace (MVP05-1 footnote 6).
Evidence: `verification/layer4_scenario_construction.md` §0.

**Layer 4 input citations + steel-dominance caveat — locked 2026-07-09.**
Curb weight (1.44 t typical) and steel share (~58%) cited from
steelonthenet's Automotive Steel Weight Analysis (snapshot committed);
aluminium share (7–10%) from the Aluminum Association grave-to-gate report
citing Ducker Worldwide; copper (55.7 lbs ≈ 1.8%) from the Center for
Automotive Research ELV-copper report (snapshot committed). Steel-scrap
PRICE stays labeled-unverified with a **named proxy** (HMS 1&2 80:20 export
benchmark) — no fabricated citation; lme.com is blocked and steel scrap is
absent from the World Bank CMO. **Steel-dominance caveat (also required on
the dashboard): steel is ~58–70% of vehicle mass, so the unverified
steel-scrap price dominates the value band — the whole value layer stays
illustrative-tier regardless of aluminium/copper price precision.**

**2025 excluded from Layer 4 — decided 2026-07-09.** No 2025 export count
exists (Comtrade qty = 0 despite ~19 kt net weight), so there is no quantity
to value; Layer 4 stays at 2023–2024.

**Dashboard presentation rules — locked 2026-07-09.** Band-plus-slider;
every slider output framed conditionally — "if X% scrapped → ≈ $Y
(illustrative, modeled)" — never an unconditional figure, with
verified-vs-modeled provenance shown alongside. Page order: (1) verified
ELV-generation series (headline), (2) the export/scrap gap (the honest
finding), (3) the value band as the closing "what's at stake if" coda —
never the headline.

**Layer 4 construction — locked 2026-07-09.** Scenario band per
(year, scrap-share scenario, material): assumed share axis (5–50%) with the
2024 disposal-split floor (3.79%) as a lower-bound anchor INSIDE the band;
verified factors: car deregistrations + Al/Cu prices (landed World Bank CMO
Pink Sheet, LME cash); unverified-labeled: curb weight, material fractions,
steel-scrap price (placeholders PENDING CITATION). No point-estimate column
exists; checks enforce strict low<mid<high. Input provenance:
`data/reference/material_value_inputs.csv`.

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
