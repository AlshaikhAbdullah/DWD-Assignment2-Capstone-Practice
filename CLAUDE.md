# CLAUDE.md — Singapore ELV Data Product

> Read this at the start of **every** session. It is the project's memory: the goal, the rules we work by, the decisions already made, the decisions still open, and how you must verify before I merge. The fuller narrative is in `PROJECT_BRIEF.md`.

---

## Project

**DWD Assignment 2 — Build an End-to-End Data Product (individual).** A pilot of my NYU Stern MSBAi capstone *"The Global ELV Recycling Gap,"* scoped to **one country: Singapore.**

- **Repo:** `AlshaikhAbdullah/DWD-Assignment2-Capstone-Practice` (branch `main`)
- **Lead:** Abdullah Alshaikh (tech lead — I Specify/Decompose/Verify/Diagnose/Translate; you implement)
- **GCP project:** `msbai-dwd-aa13072` (reused) · **BigQuery dataset:** `sg_elv` (new)
- **Artifact:** public Streamlit dashboard on Streamlit Community Cloud (NYU blocks public Cloud Run)

**One-liner:** Load Singapore LTA vehicle registration/deregistration/population data into BigQuery; quantify the annual ELV stream; **split it into exported vs. domestically scrapped**; project it forward via the COE ~10-year cohort; estimate the recoverable **material value at risk** of the scrapped stream; ship it as a dashboard a capstone stakeholder could use. Core thesis: *vehicles reach end-of-life where they are used, not where they were produced* — Singapore proves it because much of its deregistered fleet is exported, not scrapped.

---

## How we work (rules)

1. **I am accountable, not you.** A pipeline that runs green can still be wrong; a number that computes can still be meaningless. "The agent said so" is never a defense.
2. **The repo is the memory.** Propose changes as **pull requests**; I review and merge. Do **not** commit to `main` directly. Keep this file's decision log current.
3. **One checkpoint at a time.** Build a stage → prove it → commit the evidence → next. Don't jump ahead.
4. **Verify before merge.** No PR that adds a table or a claim merges without its check committed alongside.
5. **Diagnose before patching.** On a failed check or surprising result: hypothesis → evidence (rows per source per period) → real cause → fix. Most exciting early results are bugs.
6. **Never fabricate.** No invented counts, endpoints, or reconciliation figures. If a source can't be reached or a number can't be verified, say so and label it `unverified`.
7. **Surface open decisions as questions** (in a PR description or issue); don't silently pick. Ask me.

---

## Decision log (Specify) — append every decision with a reason

### Data sources — **verify each is reachable before trusting it**
- **data.gov.sg** (CKAN `datastore_search` API) — LTA monthly new registrations, monthly deregistrations, annual vehicle population by type; COE data. *Primary raw source.*
- **LTA annual stats (PDF, lta.gov.sg)** — published annual totals. *Reconciliation target — VERIFIED 2026-07-08: MVP05-1 yearly dereg PDF matches API sums exactly for 2023–2025. Carries NO scrapped-vs-exported split (checked).*
- **UN Comtrade (HS 8703)** — Singapore car export volumes. *Bounded upper estimate of the export stream (includes new-car re-exports) — VERIFIED reachable, keyless preview.*
- **LME** — steel/aluminium/copper prices. *Material value at risk.*
- **ELV material composition** (literature) — curb weight + material fractions. *Modeled → label `unverified`.*

### Canonical schema & grain (in dataset `sg_elv`) — *approved 2026-07-08 (Abdullah, PR #2)*
- **Layers:** `data/landing/` in the repo (raw untouched CKAN JSON, KB-scale; **source URL + fetch timestamp recorded per file**) → `raw_*` tables (as-is, one per series, wide stays wide) → `clean_vehicle_flows` (view: unpivot wide→long, trim `DataSeries` whitespace, `na`→NULL, taxonomy mapped; **Σcategories = embedded Total rows checked as a per-period checksum before Totals are dropped from facts**) → analysis-ready tables below.
- `fact_vehicle_flows` — **grain (month, quota_category)** — `new_registrations`, `deregistrations`, `vehicle_population` (VQS stock). Native shared grain of the three canonical monthly series; export/scrap split does NOT exist at monthly grain in any source, so it lives in the yearly table below, not here.
- `fact_population_by_type` — **grain (month, vehicle_type)** — the 1962→present stock series; context + type↔category bridge.
- `elv_disposal_split` — **grain (year, scope)** — `deregistrations_total`, `exported_units_comtrade`, `scrapped_est`, `export_share`, `method`, `confidence_tier`. Comtrade-derived → **bounded upper estimate, low confidence tier** (see export-share decision).
- `elv_material_value` — **grain (year, material)** — `tonnes_recovered`, `price_per_tonne_usd`, `value_usd`, `confidence_tier`.
- **Why layers:** land raw so we can replay/re-clean without re-fetching; clean in a view so a parse bug costs a query, not a reload.

### Clean-layer rules — locked 2026-07-08 (Abdullah), proven in `verification/part1_raw_clean_checks.md`
- **Parent/child taxonomy:** `Public Motor Cars` (pre-1988Dec parent) and `Private Hire Cars`+`Taxis` (children) must **never enter the same sum**. One representation per era — parent rows only before 1988-12, child rows only from 1988-12 (the proven overlap month: 13,613 = 3,140 + 10,473). Committed check: reconstructed Σ(types) = Total, 0 violations across all 772 months including the boundary.
- **Suppressed cells:** `'-'`/`na` are carried **verbatim in `raw_*`** and become **NULL in clean `units`**. A checksum-derived value may surface **only** in the separate `units_derived` column, only for source-suppressed (`'-'`) cells that are the single suppressed cell of their (series, month) with Total present, with the formula recorded in `derivation`. **Never silently imputed.** (Exactly one such cell exists: dereg 2002Sep cat_d = 1,422.)
- **Raw format note:** BigQuery column names cannot start with a digit, so the wide month columns (`2026Apr`, …) cannot be literal columns; `raw_*` carries each source record verbatim as a JSON string (`raw_record`) plus provenance (`_resource_id`, `_source_url`, `_source_file`, `_fetched_at_utc`, `_sha256`, `_loaded_at`). Content-equality with the landed files is checked per load.

### Canonical source resource ids (verified live 2026-07-08; see `verification/checkpoint_b_scouting.md`)
- New registrations (monthly, wide, 1990-05→): `d_d94cf5d839fc11a144f24ef971705d3e`
- Deregistrations (monthly, wide, 1990-05→): `d_d520d6034b5e0c4f883b4e480de28f97`
- Population VQS stock (monthly, wide, 1990-05→): `d_ede1a559013d10f234d209ac5e9fd9b4`
- Population by vehicle type (monthly, wide, 1962-01→): `d_206838bdc92c07ab495af49475563da5`

### Infrastructure decisions
- **GCP project: `msbai-dwd-aa13072`** — reuse existing project; new dataset `sg_elv`. *Decided 2026-07-08 (Abdullah).*
- **BigQuery dataset location: `US` (multi-region)** — immutable once created; chosen for cross-dataset join compatibility; no data-residency requirement since all data is public and aggregate. *Decided 2026-07-08 (Abdullah).*

### Scope decisions
- **Vehicle scope v1: cars = Category A + Category B** (+ the historical `Weekend Cars/Off Peak Cars` row for months where it is populated). *Decided 2026-07-08.* Reason: Category E is a **bidding-only** category — no flow series carries an E row, and Σ(7 categories) = published Total with **0 violations across 72 series-months (2023–2025)**, so there is no hidden E bucket; E-COE cars are already recorded inside A/B. LTA's own yearly table footnote confirms WE/OP cars are folded into the category columns (the API's WE/OP row is `na` from the 2000s on). Cars are 58–70% of deregistrations 2023–2025.
- **Export-share method: Comtrade HS 8703 as a bounded UPPER estimate, low confidence tier.** *Decided 2026-07-08.* The LTA scrapped-vs-exported split is **not published in any reachable machine-readable or statistical-PDF source** — exhaustively checked: 80-dataset data.gov.sg scan (names + columns + category values), LTA yearly/monthly/quarterly dereg PDFs (MVP05-1, M05, M06B: COE categories only), SingStat table search (`scrapped`/`deregistered`/`vehicles exported` → 0 relevant tables). Raw HS 8703 includes **re-exported new cars** and therefore overstates used-ELV exports: Comtrade export units vs. car (A+B) deregistrations = **1.31 (2023), 0.96 (2024)** — exceeding total car deregistrations in 2023. 2025 Comtrade qty field is 0 with ~19kt net weight (unusable; flag). Every derived split labeled `triangulated`, never presented as LTA-reported.
- **Projection horizon: provisional 2035; model deferred to Part 2.** *Decided 2026-07-08.*
- **Analytical framing (reframe): the disposal split is itself a finding, not an input.** *Decided 2026-07-08 (Abdullah), after the Comtrade/deregistration ratio hit 1.31 (2023).* The export/scrap split is **not cleanly measurable from public data** — Comtrade HS 8703 conflates new-car re-exports with used-ELV exports. Therefore: **(a)** Layer 1 (annual ELV generation = car deregistrations) is the verified headline; **(b)** Layer 2 (disposal split) is presented as a bounded, low-confidence estimate whose honest finding is *"open data can't separate domestic scrapping from export"* — the invisible-gap thesis in miniature; **no fabricated percentage**; **(c)** Layer 4 (material value at risk) is a **scenario range keyed to an assumed domestic-scrap share**, not a point estimate. Domain context (Singapore as a used-car export hub) appears only as labeled `unverified` context.
- **Comtrade load rules.** *Decided 2026-07-08.* Pull `qty` + `netWgt` + FOB value together; treat `qty` as **unreliable** (2025: qty=0 despite ~19kt net weight); prefer **net weight** for magnitude statements; **flag partial/incomplete years** explicitly.

---

## Verify strategy (no answer key — produce evidence a skeptic accepts)

- **Reconcile** monthly registration/deregistration sums to LTA annual published totals.
- **Stock-flow invariant (strong):** `population(t) − population(t−1) ≈ new_registrations(t) − deregistrations(t)`. Should hold if the LTA series are internally consistent.
- **Triangulate export:** LTA "exported" vs UN Comtrade HS 8703 export quantity (same order of magnitude; explain gaps).
- **Invariants:** no duplicate `(month, vehicle_type)`; plausible ranges; **no missing/doubled months**; totals add up.
- **Spot-check** records back to the raw API response by hand.
- **Prediction:** hold out a recent window the model never saw; report **out-of-sample** error + prediction intervals, not in-sample fit.
- Commit checks + results (e.g., `verification/` + `reconciliation.md`). A check you can't show is a check you didn't do.

---

## Checkpoints (leave evidence in the repo)

| CP | Milestone | Proof |
|----|-----------|-------|
| A | Setup done | 3 verification prompts pass; teaching team (pi1@stern.nyu.edu, it2190@stern.nyu.edu) have repo + BigQuery Data Viewer |
| B | Data loaded & verified | raw + clean + analysis-ready layers; verification evidence committed (stock-flow + reconciliation) |
| C | Analysis answers the question | analysis runs, results checked not just produced, findings written down |
| D | Artifact shipped | public dashboard live (URL in README), reaches audience, every claim supported |

When stuck: open a GitHub **issue** — checkpoint + symptom in the title, exact error, the prompt used, what's ruled out; @-mention the instructor and Ilias.

---

## Guardrails

- **$10 GCP budget alert stays on.** Stop and flag if a job loops.
- Respect data.gov.sg / LTA / Comtrade / LME **terms & licenses**; aggregate public data only; no sensitive personal data.
- Deployment breaks on **environment & identity** (who runs it, who's allowed, which port) — ask the sharper question before rerunning the error.

---

## Deliverables (submission)

Repo with pipeline + analysis + artifact link, this `CLAUDE.md`, committed verification evidence, and `DECISIONS.md` (why Singapore, why this question, what the headline metric measures + its limits, why trustworthy + where not, and — capstone note — how the pipeline/analysis generalize to other countries). Project ID + layer names. Public dashboard URL.
