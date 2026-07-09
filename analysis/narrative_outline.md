# Analysis narrative — outline (Checkpoint C → D gate)

> The story the dashboard tells, in the approved order: **verified headline →
> honest gap → illustrative value band.** Every number below traces to a row
> in `analysis/claim_evidence_map.md`; nothing appears on the page without a
> committed check or a labeled-unverified input behind it.

## Act 1 — The verified headline: Singapore generates a measurable ELV stream

**Claim:** ~29k (2023) → ~36k (2024) → ~50k (2025) cars reached end-of-life
in Singapore — permanently deregistered, disposal legally required.

- Chart 1: **Car deregistrations per year** (Cat A + B, 1990→2025), the
  monthly series aggregated yearly; recent-3-years callout numbers.
- Chart 2: **The COE heartbeat** — monthly deregistrations showing the
  ~10-year cohort cycle (the 2015–2018 peak echoing the 2005–2008
  registration wave; the basis for Part-2 projection, labeled provisional).
- Trust strip under both: "reconciles exactly with LTA's published annual
  table, 77/77 cells (2015–2025)" + link to the committed check.
- Definitional footnote: deregistration = permanent removal (LTA definition;
  lay-up is a different scheme and never enters this series).

## Act 2 — The honest gap: where do they go? Open data cannot say

**Claim:** the exported-vs-scrapped split of that stream is NOT publicly
measurable — and that opacity is itself the finding (the invisible-gap
thesis in miniature).

- Panel: the three places the split should be, all checked, all negative
  (data.gov.sg 80-dataset scan; LTA statistics PDFs; SingStat).
- Chart 3: **Comtrade export proxy vs. car deregistrations** (2023–2024
  only): 2023 proxy = 131% of deregistrations → visually shows the proxy
  breaking; 2024 = 96%.
- The one honest number: **2024 domestic-scrap floor = 1,368 cars (3.8%)** —
  presented as a LOWER bound with the bound direction on the label, never a
  count.
- Context strip (labeled `unverified context`): Singapore as a used-car
  export hub.

## Act 3 — The coda: what's at stake *if* (illustrative value band)

**Claim (conditional only):** "**if** X% of Singapore's ELV stream were
scrapped domestically, the recoverable steel/aluminium/copper would be worth
≈ $low–$high per year (illustrative, modeled)."

- Interactive: **scrap-share slider** (3.79% floor anchor marked, 5–50%
  range). Output text is always the conditional sentence; never an
  unconditional figure.
- Band chart: value_low → value_high per material, 2023 & 2024; mid line
  drawn thin, band emphasized.
- Provenance strip alongside the slider (verified vs cited vs unverified per
  input) + the **steel-dominance caveat**: steel is ~58–70% of vehicle mass,
  so the unverified steel-scrap price dominates the band — the whole layer
  is illustrative-tier regardless of Al/Cu precision.
- No 2025: no countable export proxy exists (Comtrade qty = 0), so there is
  no quantity to value.

## Closing panel — Why trust this / where it stops

- The trust table from DECISIONS.md (layer × trust basis × where it breaks).
- Pipeline provenance: landing manifest (source URL + timestamp + sha256) →
  raw verbatim → clean rules (both locked rules named) → facts; all checks
  committed and re-runnable.
- Capstone note: the failure mode found here (trade data can't isolate
  used-vehicle flows) is expected to be the global norm — quantifying that
  opacity country-by-country is the capstone.

## Page furniture (every page)

- Confidence legend: `verified` / `literature_cited` / `derived_lower_bound`
  / `assumed` / `unverified`.
- Data-vintage line: landing fetch timestamps; LTA 1-month revision-grace
  note for the newest month.
- Repo link (checks are public evidence).
