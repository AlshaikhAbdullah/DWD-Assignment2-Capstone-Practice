# Project Brief — Singapore End-of-Life Vehicle (ELV) Data Product

> **This file is the seed brief for Claude Code on the Web.** Drop it into the repo (as `PROJECT_BRIEF.md`, and seed `CLAUDE.md` from the decisions below). Read it at the start of every session. It defines the goal, the decisions the tech lead has already made, the decisions still open, and how we work together.

---

## 0. Who I am and how we work

- I am **Abdullah Alshaikh**, programming/modeling lead on the NYU Stern MSBAi 2027 Capstone: **"The Global ELV Recycling Gap."** This individual assignment is a pilot of that capstone, scoped to **one country: Singapore.**
- **My role is tech lead, not coder.** I **Specify, Decompose, Verify, Diagnose, Translate**; you implement. I am accountable for the outcome, not you. A pipeline that runs green can still be wrong; a number that computes can still be meaningless; "the agent said so" is never a defense.
- **The repo is the memory.** All work lives in this repo. You propose changes as **pull requests**; I review and merge. Do **not** edit `main` directly. Keep `CLAUDE.md` current with every data/analysis decision and its reason.
- **Work one checkpoint at a time.** Build a stage, prove it, commit the evidence, then move on. When a check fails, **diagnose the real cause before changing anything** — form a hypothesis, gather evidence (rows per source per period), then fix.

---

## 1. The project in one paragraph

Singapore is the ideal ELV pilot: the Land Transport Authority (LTA) publishes **actual vehicle deregistration** data (unlike most countries, which have no clean scrappage registry), and because of the **Certificate of Entitlement (COE)** system most cars are deregistered at ~10 years. Crucially, a large share of deregistered vehicles are **exported, not scrapped** — a clean, real-world instance of the capstone's core thesis that *vehicles reach end-of-life where they are used, not where they were produced*. We will load LTA registration/deregistration/population data into BigQuery, quantify Singapore's annual ELV volume, **split it into exported vs. domestically-scrapped**, **project it forward** using the COE cohort cycle, estimate the **recoverable material value at risk** of the scrapped stream, and ship it as a **public interactive dashboard** a capstone stakeholder could use.

---

## 2. Country scope & why Singapore is a strong pick (Specify)

- **Real deregistration data exists** — a direct ELV signal, rare globally.
- **COE ~10-year lifecycle** gives a predictable registration→deregistration cohort relationship (great for the predictive layer and for a stock-flow verification).
- **Export vs. scrap is measurable** — proves the capstone thesis in miniature and forces a genuine data-joining problem (LTA + UN Comtrade).
- **Friction warranting a database:** multiple sources, monthly files over many years, schema/category drift, and a cross-source join. Not a single clean CSV.

---

## 3. Candidate data sources — **verify availability at Checkpoint 0/B before trusting any**

> Do not assume any endpoint or dataset id. At Checkpoint 0 do a real reach test (HTTP HEAD / one API call) to each; at Checkpoint B confirm schema and coverage. Record exact resource ids and URLs in `CLAUDE.md`.

| Source | What it gives | Use |
|--------|---------------|-----|
| **data.gov.sg** (CKAN `datastore_search` API) | LTA series: monthly **new registrations**, monthly **deregistrations**, annual **motor vehicle population** by vehicle type; COE quota/bidding | Primary raw source (API pulled over time) |
| **LTA "Statistics in Brief" / annual road-transport stats (PDF)** | Published annual totals | **Reconciliation** target |
| **UN Comtrade** (HS 8703, used passenger vehicles) | Singapore used-vehicle **export** volumes by destination | **Triangulate** the export stream + destination countries |
| **LME (London Metal Exchange)** | Steel, aluminium, copper prices | Material-value-at-risk (Layer 4) |
| **ELV material composition** (literature / EU ELV stats) | Avg curb weight + material fractions (steel/Al/Cu/plastics) | Modeled input for material tonnage — **mark as modeled/unverified** |

If the deregistration data does **not** natively split export vs. scrap, treat that split as an analysis problem: reconcile LTA "deregistered" against Comtrade export quantity to estimate the exported share, and label the residual (domestically scrapped) with an explicit confidence tier.

---

## 4. Part 0 — Setup (reuse existing accounts)

Reuse the accounts from the Citibike build; **only the repo is new** (`msbai-capstone-<net-id>`, already created, private, with README + empty `CLAUDE.md`).

- [ ] Google Cloud project (reuse `msbai-...` or a fresh `msbai-capstone-<net-id>`), **billing on, $10 budget alert** (non-negotiable — agents can loop).
- [ ] Repo connected to Claude Code; `GITHUB_TOKEN` set; **cloud-bootstrap** skill (github.com/ipeirotis/cloud-bootstrap) run to create a restricted service account; `CLOUD_CREDENTIALS_KEY` in session; encrypted key committed.
  - Minimum permissions to request: **read** from the external sources, **write** BigQuery tables in my project, **serve** the final artifact.
- [ ] Grant teaching team access — **pi1@stern.nyu.edu** and **it2190@stern.nyu.edu**: GitHub repo collaborators, and Google Cloud **BigQuery Data Viewer** (IAM).
- [ ] **Three verification prompts** returning real results: (1) run a BigQuery query in my project, (2) create a dataset + write a one-row test table, (3) reach the Singapore data source (a real data.gov.sg API call).

**Done =** all boxes checked; the three verifications return real output including a live hit on data.gov.sg.

---

## 5. Part 1 — Load (the ETL pipeline)

### Specify (write these in `CLAUDE.md`, each with a reason)
- Exactly which datasets/endpoints, and how we handle each source's quirks: **pagination** (CKAN `limit`/`offset`), **format/category drift** across years, **missing months**, encoding, vehicle-type taxonomy changes.
- **Canonical schema & grain.** Proposed:
  - `fact_vehicle_flows` — **grain: (month, vehicle_type)** — columns: `new_registrations`, `deregistrations`, `deregistrations_exported`, `deregistrations_scrapped`, `vehicle_population` (stock).
  - `elv_material_value` — **grain: (year, material)** — `tonnes_recovered`, `price_per_tonne_usd`, `value_usd`, `confidence_tier`.
- What we deliberately **keep vs. drop** (e.g., focus on cars/passenger vehicles first; note if motorcycles/goods vehicles are excluded and why).

### Decompose (the staircase — adapt to the source)
```
data.gov.sg API + Comtrade + LME
  -> landing/ (raw JSON/CSV, untouched, timestamped)
  -> raw tables (loaded as-is, one per source/series)
  -> clean unified view (parsed, typed, taxonomy reconciled, months aligned)
  -> analysis-ready tables (fact_vehicle_flows, elv_material_value)
```
Be able to say **why each layer exists**: land raw so we can replay/re-clean without re-fetching; clean in a **view** so a parse bug costs a query, not a reload.

### Verify (hard — usually no answer key)
Decide what would convince a skeptic, then produce exactly that evidence and **commit it**:
- **Reconcile** monthly deregistration/registration sums to LTA annual published totals (Statistics in Brief).
- **Stock-flow invariant** (the strong one): `population(t) − population(t−1) ≈ new_registrations(t) − deregistrations(t)`. If the three LTA series are internally consistent, this holds — a source-native check needing no external key.
- **Triangulate the export stream:** LTA "exported" count vs UN Comtrade HS 8703 export quantity from Singapore (expect same order of magnitude; explain gaps).
- **Invariants:** no duplicate `(month, vehicle_type)` keys; values in plausible ranges; **no missing or doubled months**; totals add up.
- **Spot-check** a handful of records by hand back to the raw API response.
- **Label as `unverified`** anything modeled (material composition, curb weight) — never imply confidence you don't have.

### Diagnose
On a failed check: hypothesis → evidence (which rows/periods actually loaded) → real cause → fix. You investigate; I steer and own the conclusion.

**Done =** raw layer + clean unified view + analysis-ready tables in BigQuery; `CLAUDE.md` records every decision with a reason; verification checks + results committed, with unverifiables labeled.

---

## 6. Part 2 — Analyze (four layers, the capstone's four-stage arc)

State each question sharply and write down what a credible answer looks like **before** computing. Guard against a confident-wrong conclusion: sanity-check magnitudes, test against an obvious alternative, keep correlation ≠ causation, state uncertainty, and **hold out data for anything predicted**.

1. **Descriptive — how big is Singapore's ELV stream?**
   Annual + monthly deregistrations by vehicle type, with trend. Reconciled to LTA totals.
2. **Export vs. scrap split (the thesis in miniature).**
   Of deregistered vehicles, what share is **exported** vs **domestically scrapped**? This is the "die where used, not produced" signal. Report the split with its confidence tier and how it was derived (LTA category if available, else Comtrade triangulation).
3. **Predictive — project ELV generation forward (e.g., to 2030/2035).**
   Use the **COE ~10-year cohort**: registrations ~10 years ago drive deregistrations now. Fit on earlier years, **test on a held-out recent window**, report out-of-sample error (e.g., MAPE) and prediction intervals — not in-sample fit.
4. **Material value at risk — the prescriptive/ROI angle (scrapped stream only).**
   Estimate recoverable material tonnage (curb weight × material fractions × scrapped count) × LME prices → **value at risk**. Give ranges/confidence tiers; composition + weight are modeled → **unverified**. Exported vehicles are *not* counted as domestic material loss (they continue their life abroad — the thesis again).

### Diagnose
A surprising result is a fork — finding or bug, not your choice. Trace surprises back to data + code. Most exciting early results are bugs.

**Done =** analysis runs from the analysis-ready tables; decisions + verification checks documented; each finding written as a **plain claim with magnitude and uncertainty**, causal language earned not assumed.

---

## 7. Part 3 — Present (the artifact)

**Primary artifact (graded): a public, interactive Streamlit dashboard**, deployed on **Streamlit Community Cloud** (reason: NYU's GCP org policy blocks public Cloud Run — `host_not_allowed` — and Streamlit reads straight from BigQuery so every number provably ties to the analysis-ready table). Reuse the Citibike deployment pattern: repo `main` + `dashboard/app.py`, service-account key in `st.secrets`, **pin Python 3.12**, cache the BQ read with `@st.cache_data`.

**Audience:** my capstone teammates + a capstone stakeholder (recycler / ESG investor / policymaker). Build for them, not for a data analyst.

**Views (each view's title = its claim):**
- ELV volume over time (deregistrations), reconciled figure shown.
- **Export vs. scrap split** (the headline) with the thesis stated plainly.
- Projection to 2030/2035 with prediction interval and a note that it's out-of-sample-tested.
- Material value at risk of the scrapped stream, with a clear "modeled / confidence-tier" caveat.
- A methods/verification panel linking each number to its check.

**Optional stretch — a static landing page** (Vercel or GitHub Pages) as a front door: one page summarizing the headline finding + a link to the live dashboard. Keep it static (no separate data layer) so it can't drift from the numbers. *The Streamlit app remains the graded artifact.*

### Verify (concrete targets, then check)
- Numbers in the artifact **match the analysis-ready table** exactly.
- Public URL **loads in < a few seconds**, **no login**, in the README.
- **Every claim is visible** in what the reader sees — if a chart doesn't show the claim, it's decoration.

### Diagnose
Deployment breaks on **environment and identity**, not code: who runs the app, who's allowed in, which port. Ask the sharper question before rerunning the error.

**Done =** shareable artifact delivering the finding to the stated audience; public URL (in README) loads within the speed target; every claim supported and numbers reconcile.

---

## 8. Translate — `DECISIONS.md` (defend the choices in plain business terms)

Commit a short `DECISIONS.md` covering: **why Singapore**, **why this question**, what the **headline metric (ELV volume / export share)** really measures and where it falls short, **why the answer is trustworthy and where it isn't**, and — since this is aimed at the capstone — **what it advances and how the team reuses the pipeline/analysis/artifact** (e.g., Singapore as the template pipeline other countries plug into; the export/scrap split as the method to generalize; confidence-tiering carried across).

---

## 9. Checkpoints (prove each, leave evidence in the repo)

| CP | Milestone | Proof |
|----|-----------|-------|
| A | Setup done | Verification prompts pass; teaching team has repo + BQ access |
| B | Data loaded & verified | Raw + clean layers built; verification evidence committed (incl. stock-flow + reconciliation) |
| C | Analysis answers the question | Analysis runs, results **checked not just produced**, findings written down |
| D | Artifact shipped | Public dashboard live, reaches audience, every claim supported |

When stuck: open a GitHub **issue** titled with the checkpoint + symptom; paste the exact error, the prompt given, and what's already ruled out; @-mention the instructor and Ilias. "It doesn't work" isn't debuggable; "data.gov.sg returns 429 after ~200 requests and I've added backoff" is.

---

## 10. Guardrails

- **Budget:** keep the $10 GCP alert; stop and flag if a job loops.
- **Licensing/ToS:** respect data.gov.sg, LTA, Comtrade, LME terms; no scraping against ToS; no sensitive personal data. Vehicle data here is aggregate/public — fine.
- **No fabrication:** never invent counts, endpoints, or reconciliation figures. If a source can't be reached or a number can't be verified, say so and label it `unverified`.
- **Verification before merge:** no PR that adds a table or a claim merges without its check.

---

## 11. Open decisions for the tech lead (Abdullah) — surface these, don't silently pick

1. Vehicle scope for v1 — cars/passenger only, or include motorcycles/goods vehicles?
2. Export-share method if LTA doesn't split it natively — Comtrade triangulation vs. an LTA scheme field.
3. Projection horizon (2030 vs 2035) and model family (cohort-survival vs. gradient-boosting on registrations+calendar).
4. Material composition source + the confidence tiers to attach.
5. Whether to ship the optional Vercel/GitHub Pages landing page.

Bring these to me as questions in a PR description or an issue; I'll decide.
