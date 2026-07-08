# Checkpoint B scouting — series verification & findings (NO DATA LOADED)

**Date:** 2026-07-08 · **Method:** read-only `datastore_search` probes (bounded,
in-memory samples), re-runnable via `python3 verification/scout_checkpoint_b.py`.
Raw probe output: `verification/checkpoint_b_probe_output.md`. All 16 candidate
ids resolved (HTTP 200, `success: true`); first pass hit API rate limits (429) on
8 of 16 — fixed with backoff + 4s pacing, second pass clean.

## 1. The three core series — verified

Two families exist for each series: a **wide "SingStat" format** (one column per
month, `DataSeries` = category rows) that is **current through 2026**, and
long-format snapshots that are **stale** (frozen at 2017/2018/2020). The wide
series are the only ones covering the present.

### Proposed canonical sources (all VERIFIED — resolved + full sample inspected)

| Series | Resource id | Format | Grain | Coverage | Rows |
|---|---|---|---|---|---|
| New registrations | `d_d94cf5d839fc11a144f24ef971705d3e` | wide (432 month cols) | month × COE quota category (A, B, C±ETS, D, Taxis, Exempt, Weekend/Off-Peak) + Total row | **1990-05 → 2026-04** | 10 |
| Deregistrations | `d_d520d6034b5e0c4f883b4e480de28f97` | wide (432 month cols) | month × COE quota category + Total row | **1990-05 → 2026-04** | 8 |
| Vehicle population (stock, VQS) | `d_ede1a559013d10f234d209ac5e9fd9b4` | wide (433 month cols) | month × COE quota category + Total row | **1990-05 → 2026-05** | 8 |
| Vehicle population (stock, by type) | `d_206838bdc92c07ab495af49475563da5` | wide (772 month cols) | month × vehicle type (Cars, Buses, Goods & Other, M/C, Taxis, Private Hire, Public Motor Cars) + Total | **1962-01 → 2026-04** | 8 |

**A monthly stock series exists** (two, in fact) → the stock-flow invariant
`Δpopulation ≈ new_reg − dereg` is testable. Crucially, registrations,
deregistrations, and the VQS population stock all share the **same COE-category
taxonomy and the same 1990-05 start**, so the invariant can be checked
per-category *and* on totals without any taxonomy mapping.

### Stale long-format duplicates (VERIFIED but frozen — cross-check use only)

| Resource id | Series | Coverage |
|---|---|---|
| `d_06c3969c73ac5ba2d059cf39491ce048` | New reg, monthly long | 2014-01 → 2020-04 |
| `d_1332f905376c3848bdcc032423ca5563` | Dereg, monthly long | 2014-01 → 2020-04 |
| `d_529752a3d78beb78bd4f38e3be37f1b6` | New reg, wide (older vintage) | 1990-05 → 2026-01 |
| `d_f52d6995ea85ad8d5088906d7a24d5df` | New reg, annual by COE cat | 2005 → 2017 |
| `d_6e50d957520951abb4083d2b2bd0ae90` | Dereg, annual by COE cat | 2005 → 2017 |
| `d_cc30f50369bcd6b6f848a586bded2290` | Population, annual by COE cat | 2005 → 2017 |
| `d_f8876e8c0959ba5bcfa2c40cf6d25dab` | Population (VQS), monthly long | 2014-01 → 2018-02 |
| `d_2ecb009f1e1ec5a816a454944dec4022` | Population by type, monthly long | 2012-01 → 2018-02 |
| `d_2873f3b1b2a836103f51f696350b98fa` | Population by type+subtype, annual | 2005 → 2024 |
| `d_aa457c0abaacccefd238c31cfed211d9` | Population by type, annual wide | 1961 → 2025 |
| `d_f8408eaf8ecf45adae760a035b8d850d` | New reg, quarterly by type+subtype | 2016-Q1 → 2020-Q4 |
| `d_5a32a72cbc741ecfda152c20677f0f3d` | Dereg, quarterly by type+subtype | 2016-Q1 → 2020-Q4 |

The annual 2005–2017 series and the 1961–2025 annual population series serve as
**reconciliation targets** for the overlap years; recent-year reconciliation
needs the LTA annual statistics publication (PDF — *unverified*, not yet fetched).

## 2. Headline question: export vs. scrap split — **ANSWER: NO SPLIT**

Every deregistration dataset was scanned — column names *and* every distinct
categorical value in a full sample — for export/scrap/disposal/demolish
keywords. **None found.** The actual columns are, exhaustively:

- `d_d520d…` (monthly, canonical): `DataSeries` + one column per month. The 8
  `DataSeries` values are the 7 COE categories + "Total Motor Vehicles
  De-Registered". Nothing else.
- `d_1332f…` / `d_6e50d…` (long): `month`/`year`, `category`, `number`. The
  `category` values are only COE categories.
- `d_5a32a…` (quarterly): `period`, `category`, `type`, `number` — `type` is a
  25-value vehicle-usage taxonomy (Private cars, Company cars, Off peak cars,
  Private Hire…), still **no disposal channel**.

Also: no dataset in the 80-item full-catalog scan has export/scrap/disposal in
its *name*. LTA publishes the disposal split (COE rebate statistics distinguish
exported vs. scrapped-at-ATF) in its annual publication, not on data.gov.sg.

**Consequence — decision for Abdullah:** the exported-vs-scrapped split must
come from outside data.gov.sg. Proposed: **UN Comtrade triangulation** (already
allowlisted), with the LTA annual publication PDF as a reconciliation
spot-check if we can locate the disposal table in it.

**Comtrade viability — VERIFIED live (2026-07-08):**
`GET https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=702&period=2023&cmdCode=8703&flowCode=X`
→ HTTP 200, **80 records** (Singapore-reported 2023 exports of HS 8703 passenger
cars, by partner) on the keyless preview endpoint. Reference files
(`/files/v1/app/reference/Reporters.json`) also 200. Monthly/higher-volume pulls
may need a (free) subscription key — flagged, not yet needed.

## 3. Caveats found while scouting (on the record)

1. **Wide format**: the three canonical series are pivoted (one column per
   month). The clean layer must UNPIVOT; raw layer lands them as-is.
2. **Taxonomy mismatch across families**: flows are by *COE quota category*;
   the deep population stock is by *vehicle type*. Cars ≈ Cat A + Cat B, but
   Taxis/Exempt/Private-Hire complicate mapping. v1 avoids the mapping by
   running the invariant in COE-category space (all three canonical series
   share it).
3. **`na` values** appear in early years of the annual population series
   (pre-1981 columns typed as text) — the clean layer needs explicit
   NULL-handling, and the wide monthly series likely have the same for
   pre-launch months (e.g. Cat C-ETS).
4. **Leading whitespace** in `DataSeries` values encodes hierarchy
   (indent = subcategory) — must be trimmed and the Total rows separated from
   category rows, or sums will double-count.
5. **Duplicate vintages** of the same series exist; pipeline must pin exact
   resource ids (done above), not names.
6. **API rate limiting** (429 under burst) — the loader needs backoff+pacing
   (the scout script already implements it).

## 4. Not yet verified (deliberately)

| Item | Status |
|---|---|
| COE bidding results `d_69b3380ad7e51aff3a7dcc84eba52b8a` | resolves (CP A scan) but columns/grain **not probed** — needed for projection at CP C, not B |
| LTA annual statistics PDF (reconciliation + disposal split) | **unverified** — not fetched |
| Comtrade full extract (monthly, quantity units, partner detail) | preview verified; full pull **not done** (no loading) |
| LME prices, material composition | **unverified** — CP C scope |
