# CLAUDE.md — Singapore ELV Data Product

> Read this at the start of **every** session. It is the project's memory: the goal, the rules we work by, the decisions already made, the decisions still open, and how you must verify before I merge. The fuller narrative is in `PROJECT_BRIEF.md`.

---

## Project

**DWD Assignment 2 — Build an End-to-End Data Product (individual).** A pilot of my NYU Stern MSBAi capstone *"The Global ELV Recycling Gap,"* scoped to **one country: Singapore.**

- **Repo:** `AlshaikhAbdullah/DWD-Assignment2-Capstone-Practice` (branch `main`)
- **Lead:** Abdullah Alshaikh (tech lead — I Specify/Decompose/Verify/Diagnose/Translate; you implement)
- **GCP project:** `<reuse msbai-... or set here>` · **BigQuery dataset:** `sg_elv`
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
- **LTA "Statistics in Brief" / annual stats (PDF)** — published annual totals. *Reconciliation target.*
- **UN Comtrade (HS 8703)** — Singapore used-vehicle export volumes. *Triangulate the export stream.*
- **LME** — steel/aluminium/copper prices. *Material value at risk.*
- **ELV material composition** (literature) — curb weight + material fractions. *Modeled → label `unverified`.*

### Canonical schema & grain (in dataset `sg_elv`)
- **Layers:** `landing/` (raw untouched, timestamped) → `raw_*` tables (as-is, one per series) → `clean_vehicle_flows` (view: parsed, typed, taxonomy reconciled, months aligned) → analysis-ready tables below.
- `fact_vehicle_flows` — **grain (month, vehicle_type)** — `new_registrations`, `deregistrations`, `deregistrations_exported`, `deregistrations_scrapped`, `vehicle_population`.
- `elv_material_value` — **grain (year, material)** — `tonnes_recovered`, `price_per_tonne_usd`, `value_usd`, `confidence_tier`.
- **Why layers:** land raw so we can replay/re-clean without re-fetching; clean in a view so a parse bug costs a query, not a reload.

### Scope decisions (fill in as we make them)
- Vehicle scope for v1: **[OPEN]** cars/passenger only vs. include motorcycles/goods.
- Export-share method: **[OPEN]** native LTA field vs. Comtrade triangulation.
- Projection horizon + model: **[OPEN]** 2030/2035; cohort-survival vs. gradient-boosting.

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
