# Claim → evidence map (every dashboard number traces here)

> Rule: no number appears on the dashboard unless its row here points to a
> committed check (re-runnable, in `verification/`) or a labeled-unverified /
> cited input (in `data/reference/material_value_inputs.csv`). Confidence
> vocabulary: `verified` · `literature_cited` · `literature_cited_geo_transfer` · `derived_lower_bound` ·
> `assumed` · `unverified` · `unverified context`.

## Act 1 — verified headline

| # | Claim on the page | Number(s) | Source object | Committed evidence | Confidence |
|---|---|---|---|---|---|
| 1.1 | Cars deregistered per year (headline series) | 29,089 (2023) · 36,137 (2024) · 49,550 (2025) | `fact_vehicle_flows` where `is_car_scope` | `part1_analysis_ready_checks.md` (ties to scouting-verified sums); `part1_landing_checks.md` (Σcats=Total, 0 unexplained violations) | verified |
| 1.2 | Series reconciles with LTA's published annual table | 77/77 cells exact, 2015–2025 | `data/reference/lta_mvp05_1_yearly_dereg.csv` + committed PDF | `part1_invariant_reconciliation.md` §Reconciliation | verified |
| 1.3 | Monthly series is internally consistent (stock-flow) | 420/431 months conserve exactly; residual pattern diagnosed | `clean_vehicle_flows` | `part1_invariant_reconciliation.md` T1–T3 (incl. circularity verdict: same-register consistency, invariant demoted to secondary) | verified |
| 1.4 | Deregistration = permanent removal | definitional + empirical | LTA OneMotoring definition; T2 transfer evidence | `layer4_scenario_construction.md` §0; DECISIONS.md | verified |
| 1.5 | Full history depth (1990-05 →) with no gaps | 432/433 months, no missing/doubled | landing files + manifest | `part1_landing_checks.md` continuity | verified |
| 1.6 | Newest month may revise slightly | 1-month COE revalidation grace | LTA MVP05-1 footnote 6 (committed PDF) | `data/reference/README.md` | verified (source note) |

## Act 2 — the honest gap

| # | Claim | Number(s) | Source object | Committed evidence | Confidence |
|---|---|---|---|---|---|
| 2.1 | LTA publishes no export/scrap split anywhere reachable | 3 sources exhausted, 0 hits | — | `checkpoint_b_scouting.md` §2 + §5 (data.gov.sg scan, LTA PDFs, SingStat) | verified (negative result) |
| 2.2 | Export proxy vs deregistrations ratio | 1.309 (2023) · 0.962 (2024) | `elv_disposal_split.export_proxy_ratio` | `part1_analysis_ready_checks.md`; Comtrade landing files (per-year, sha256) | verified computation over an upper-bound proxy |
| 2.3 | The proxy is an UPPER bound (re-export contamination) | 2023 proxy > total car deregs | `elv_disposal_split.export_bound_direction` | `part1_analysis_ready_checks.md` (proxy_exceeds flag); DECISIONS.md bound semantics | verified (the overflow is the proof) |
| 2.4 | Domestic-scrap floor 2024 | 1,368 cars = 3.79% | `elv_disposal_split.scrapped_est_residual` + `scrapped_bound_direction` | `part1_analysis_ready_checks.md` (bound-direction check) | derived_lower_bound |
| 2.5 | 2023 floor does not exist | scrapped NULL + flag | same table | same check (no negative/fabricated count) | verified (honest NULL) |
| 2.6 | No 2022/2025 export count exists | Comtrade qty=0 with 15–19 kt netWgt | `clean_comtrade_exports` flags | `part1_landing_checks.md` Comtrade inventory; `part1_raw_clean_checks.md` flag equality | verified (source defect) |
| 2.7 | Singapore is a used-car export hub | (context prose, no number) | — | none — labeled | unverified context |

## Act 3 — illustrative value band

| # | Claim | Number(s) | Source object | Committed evidence | Confidence |
|---|---|---|---|---|---|
| 3.1 | Conditional value sentence per slider position | value_usd_low/mid/high per (year, scenario, material) | `elv_material_value` (27 rows) | `layer4_material_value_checks.md` (formula reproduces from provenance CSV; strict low<mid<high; no point column) | scenario range |
| 3.2 | Car deregistrations factor | 29,089 / 36,137 | `fact_vehicle_flows` | tie-back check (21/21 years) | verified |
| 3.3 | Al price 2023/2024 | $2,255.74 / $2,419.02 per t | landed World Bank CMO Pink Sheet | re-derived from landed XLSX at build AND check time | verified |
| 3.4 | Cu price 2023/2024 | $8,490.29 / $9,142.14 per t | same | same | verified |
| 3.5 | Steel-scrap price | $300–450 per t | named proxy (HMS 1&2 80:20) | labeled in CSV — deliberately NO citation (unreachable) | unverified |
| 3.6 | Curb weight | 1.2 / 1.44 / 1.6 t | steelonthenet snapshot (committed) | CSV row + committed HTML snapshot | literature_cited_geo_transfer |
| 3.7 | Steel fraction | 0.55 / 0.58 / 0.65 | steelonthenet (830/1440 kg = 58%); high end covers ferrous incl. cast iron | CSV row + snapshot | literature_cited_geo_transfer |
| 3.8 | Aluminium fraction | 0.06 / 0.08 / 0.10 | Aluminum Association grave-to-gate report citing Ducker (251 lbs 1999 → ~397 lbs 2015) | CSV row (URL + accessed date) | literature_cited_geo_transfer |
| 3.9 | Copper fraction | 0.012 / 0.0176 / 0.020 | CAR "Copper in ELV Recycling": 55.7 lbs/vehicle (snapshot committed) | CSV row + committed PDF | literature_cited_geo_transfer |
| 3.10 | Scrap-share slider axis | 5–50% + 3.79% floor anchor | scenario design; anchor from 2.4 | anchor tie-back check | assumed (axis) / derived_lower_bound (anchor) |
| 3.11 | Steel-dominance caveat | steel ≈ 58–70% of mass → unverified steel price dominates the band | — | DECISIONS.md (locked note; must render beside the slider) | verified (structural statement about the model) |
| 3.11b | Geographic-transfer caveat | composition = US/global fleet averages applied to SG (1,440 kg not SG-measured) | `material_value_inputs.csv` | DECISIONS.md (locked note; must render on provenance strip) | verified (structural statement) |
| 3.12 | Why no 2025 | no countable export proxy (qty=0) | `clean_comtrade_exports` | DECISIONS.md 2025-exclusion decision; landing checks | verified |

## Closing panel

| # | Claim | Source | Evidence |
|---|---|---|---|
| 4.1 | Trust table (layer × basis × breaks) | DECISIONS.md | the underlying checks per row above |
| 4.2 | Pipeline provenance chain | `data/landing/manifest.jsonl` (URL + UTC ts + sha256 per file) | `part1_raw_clean_checks.md` content-equality checks |
| 4.3 | Locked clean rules (parent/child era; suppressed cells) | CLAUDE.md decision log | `part1_raw_clean_checks.md` RULE 1 / RULE 2 proofs |
| 4.4 | Generalization note (capstone) | DECISIONS.md capstone section | narrative only, no number |

## Numbers that must NOT appear

- Any unconditional dollar figure from Layer 4 (conditional framing only).
- Any export/scrap **percentage split** presented as measured (only the
  bounded floor + the >100% proxy ratio, each with bound direction).
- Any 2025 value figure; any FOB dollars on a vehicle-count axis.
- Any 2022/2025 export count (qty is broken those years).
