# The Global ELV Recycling Gap — Singapore pilot

**DWD Assignment 2 — an end-to-end data product.** Singapore Land Transport
Authority vehicle registration / deregistration / population data → BigQuery
(`sg_elv`) → a public Streamlit dashboard quantifying Singapore's annual
end-of-life-vehicle (ELV) stream and the recoverable material value at risk.

**Live dashboard:** _pending deploy — URL added here once published to
Streamlit Community Cloud_ (NYU blocks public Cloud Run).

## What the headline measures — and its limits

The headline is **annual ELV generation = car deregistrations (COE Categories
A + B)**: cars permanently removed from Singapore's register (LTA requires
proof of disposal within one month; keeping a deregistered vehicle is an
offence — so this is genuine end-of-life, not temporary lay-up). ~29k (2023) →
36k (2024) → 50k (2025). This series is **verified**: it reconciles *exactly*
with LTA's published annual statistics (77/77 cells, 2015–2025) and satisfies a
monthly stock-flow invariant.

**Its limit — and the project's real finding:** what happens to those cars
(exported vs. scrapped domestically) is **not measurable from open data**. The
only proxy (UN Comtrade HS 8703) conflates new-car re-exports with used-ELV
exports — in 2023 it exceeds total car deregistrations. So the disposal split
is presented as a bounded, low-confidence estimate, and the material-value
layer is an **illustrative scenario band keyed to an assumed domestic-scrap
share**, never a point estimate. That opacity — invisible ELV flows even where
open data is world-class — *is* the capstone thesis in miniature. Full
reasoning, trust boundaries, and capstone generalization: **[`DECISIONS.md`](DECISIONS.md)**.

## Dashboard (Checkpoint D)

- App: [`dashboard/app.py`](dashboard/app.py). Page order is fixed: verified
  ELV-generation headline → the honest export/scrap gap → the illustrative
  value band (last). Every rendered number traces to
  [`analysis/claim_evidence_map.md`](analysis/claim_evidence_map.md).
- The value calculator shows **no dollar figure by default**: it sits in a
  collapsed panel behind an off-by-default toggle, and every dollar reads
  "*if X% scrapped → ≈ $Y (illustrative, modeled)*" with provenance and the
  steel-dominance / geographic-transfer caveats always visible.
- **Pre-deploy gate:** [`verification/predeploy_scan.py`](verification/predeploy_scan.py)
  drives every user-reachable text state and fails the build if any forbidden
  number appears (unconditional dollars, measured-looking split %, 2025
  values, FOB on count axes, broken-year export counts). Result committed at
  [`verification/checkpoint_d_predeploy_scan.md`](verification/checkpoint_d_predeploy_scan.md).

### Deploy steps (owner)

1. **Create a read-only service account** on the GCP project:
   ```
   gcloud iam service-accounts create sg-elv-dashboard-ro \
     --project=msbai-dwd-aa13072 --display-name="SG-ELV dashboard read-only"
   # dataset-scoped read + ability to run query jobs, nothing else:
   bq add-iam-policy-binding --member="serviceAccount:sg-elv-dashboard-ro@msbai-dwd-aa13072.iam.gserviceaccount.com" \
     --role="roles/bigquery.dataViewer" msbai-dwd-aa13072:sg_elv
   gcloud projects add-iam-policy-binding msbai-dwd-aa13072 \
     --member="serviceAccount:sg-elv-dashboard-ro@msbai-dwd-aa13072.iam.gserviceaccount.com" \
     --role="roles/bigquery.jobUser"
   gcloud iam service-accounts keys create key.json \
     --iam-account=sg-elv-dashboard-ro@msbai-dwd-aa13072.iam.gserviceaccount.com
   ```
2. On [share.streamlit.io](https://share.streamlit.io): New app → this repo →
   main file `dashboard/app.py` → **advanced settings: Python 3.12**.
3. Paste `key.json` into the app's **Secrets** as `[gcp_service_account]`
   (format in [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)).
   **Never commit the key** — `.gitignore` blocks it.
4. Add the resulting URL to the top of this README.

The app reads BigQuery live (cached with `@st.cache_data`); if secrets are
absent it falls back to the committed `dashboard/snapshot.json` so it always
renders.

## Pipeline layers (`sg_elv` on `msbai-dwd-aa13072`, BigQuery US)

`data/landing/` (raw untouched JSON/XLSX + `manifest.jsonl` provenance) →
`raw_*` tables (verbatim) → `clean_*` views (unpivot, taxonomy era rule,
suppressed-cells rule) → analysis-ready: `fact_vehicle_flows`,
`fact_population_by_type`, `elv_disposal_split`, `elv_material_value`. Every
stage has committed checks in [`verification/`](verification/). Project memory
and decision log: [`CLAUDE.md`](CLAUDE.md).
