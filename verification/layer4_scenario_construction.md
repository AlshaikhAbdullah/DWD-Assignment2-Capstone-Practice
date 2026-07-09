# Layer 4 — scenario construction & input provenance (pre-dashboard gate)

> Deliverable requested 2026-07-09: the scenario construction and the
> input-provenance table, BEFORE any dashboard number is wired. Checks:
> `verification/layer4_material_value_checks.md` (9/9 PASS, re-runnable via
> `verification/material_value_checks.py`).

## 0. Prerequisite confirmed: "deregistration" = permanent removal

The ELV-generation headline depends on deregistration meaning permanent
removal, not temporary lay-up. Evidence, both definitional and empirical:

1. **LTA's own definition** (onemotoring.lta.gov.sg → Selling/Deregistering →
   Deregister a Vehicle, fetched 2026-07-09): *"Deregistration is to cancel
   the registration for your vehicle and stop using it in Singapore. When you
   deregister your vehicle, you must dispose of it by scrapping it, exporting
   it or storing it temporarily in an Export Processing Zone (EPZ) pending
   export. … It is an offence if you fail to submit proof of disposal of your
   deregistered vehicle to LTA on time. It is also an offence to keep or use
   a deregistered vehicle."* Disposal documents (ATF scrapping, or export
   Cargo Clearance Permit + Bill of Lading / foreign re-registration) are
   mandatory within 1 month.
2. **Temporary lay-up is a different scheme entirely** — "Vehicle Lay-Up"
   sits under *Owning → Ongoing Car Costs* on LTA's own site: a laid-up
   vehicle stays registered (road tax suspended, can later renew road tax
   after inspection). Laid-up vehicles never enter the deregistration series.
3. **Empirical corroboration in our data**: status/scheme changes
   (taxi↔car, exempt↔car, Off-Peak conversions) appear in the stock-flow
   residuals as within-month category TRANSFERS — never as
   deregistration+re-registration events (T2, 0 non-offsetting residuals
   since 2000). If temporary status changes were counted as deregistrations,
   they would appear in the flows; they do not.
4. **Known revision channel, bounded**: MVP05-1 footnote 6 — owners get a
   1-month grace to *revalidate* a COE upon deregistration, so the latest
   month's figures can be revised slightly downward. This is a revision
   window, not a lay-up channel.

**Conclusion: car deregistrations are a valid measure of annual ELV
generation for Singapore** (with the export-vs-scrap destination being
Layer 2's separately-stated problem).

## 1. Scenario construction

```
value_usd(year, scenario, material) =
    scrap_share(scenario)                -- ASSUMED axis (see below)
  × car_deregistrations(year)            -- VERIFIED (fact_vehicle_flows,
                                            reconciled 77/77 to LTA PDF)
  × curb_weight_t                        -- MODELED, unverified
  × material_fraction(material)          -- MODELED, unverified
  × price_usd_per_tonne(material, year)  -- VERIFIED for Al/Cu (landed World
                                            Bank CMO Pink Sheet, LME cash);
                                            UNVERIFIED for steel scrap
```

- **Output = band per (year, scenario, material)**: `value_usd_low/mid/high`
  where low multiplies all low inputs and high all high inputs — a
  deliberately wide, honest band. **No point-estimate column exists**;
  the check suite enforces strict `low < mid < high` in every row.
- **Scenario axis** (`scrap_share`): 5% / 10% / 25% / 50% assumed scenarios,
  plus the **2024 floor anchor at 3.79%** = the disposal split's
  `scrapped_est_residual` (1,368) ÷ car deregistrations (36,137). Per the
  locked bound semantics, this anchor is a LOWER bound — **one anchor inside
  the band, never the tonnage** — and exists only for 2024.
- **Years**: 2023 and 2024 — the verified-price years (the landed Pink Sheet
  vintage, updated 2025-01-03, ends 2024M12) and the Comtrade cross-check
  window. 2025 is excluded until a newer price vintage is landed.
- **Confidence**: every row carries per-input verification columns
  (`price_verification`, `weight_verification`, `fraction_verification`,
  `scrap_share_status`) + overall `confidence_tier =
  'scenario_range_unverified_inputs'`.

## 2. Input-provenance table

Canonical copy: `data/reference/material_value_inputs.csv` (machine-read by
the builder; the check suite re-derives verified prices from the landed XLSX
and fails on any drift).

| Input | Value(s) | Status | Source |
|---|---|---|---|
| Car deregistrations 2023 / 2024 | 29,089 / 36,137 | **verified** | fact_vehicle_flows (API, reconciled exactly to LTA MVP05-1 PDF) |
| Scrap-share scenarios | 5%, 10%, 25%, 50% | assumed (axis) | scenario design — the honest unknown |
| Scrap-share floor anchor (2024 only) | 3.79% | derived **lower bound** | elv_disposal_split residual (Comtrade proxy = upper bound on exports) |
| Curb weight | 1.2 / 1.4 / 1.6 t | **unverified** | ELV-literature placeholder, PENDING CITATION |
| Steel fraction | 0.65 / 0.68 / 0.70 | **unverified** | ELV-composition literature placeholder, PENDING CITATION |
| Aluminium fraction | 0.06 / 0.08 / 0.10 | **unverified** | ELV-composition literature placeholder, PENDING CITATION |
| Copper fraction | 0.010 / 0.015 / 0.020 | **unverified** | ELV-composition literature placeholder, PENDING CITATION |
| Aluminium price 2023 / 2024 | $2,255.74 / $2,419.02 per t | **verified** | World Bank CMO Pink Sheet (LME cash), landed with sha256 in manifest, annual mean of 12 months |
| Copper price 2023 / 2024 | $8,490.29 / $9,142.14 per t | **verified** | same landed Pink Sheet |
| Steel-scrap price | $300 / $380 / $450 per t | **unverified** | HMS benchmark placeholder — lme.com blocked by egress policy; steel scrap absent from the Pink Sheet |

## 3. What the band says (illustrative read, mid inputs)

At the 25% scenario for 2024 (36,137 car deregistrations): ≈ 12.6 kt of
material, of which steel ≈ 8.6 kt → ≈ **$3.3M** steel + ≈ $2.4M aluminium +
≈ $1.7M copper ≈ **$7M/yr mid-band** — versus ≈ **$1.1M** at the 3.79%
floor anchor and ≈ **$14M** at the 50% scenario. The spread IS the finding:
the value at risk is bounded by what open data cannot pin down — the
domestic-scrap share.

## 4. Open items before the dashboard wires any of this

1. Replace the three PENDING CITATION placeholders (curb weight, fractions,
   steel-scrap price) with cited literature values — or keep them and label
   the axis accordingly on the dashboard.
2. Land a newer Pink Sheet vintage to extend prices to 2025.
3. Dashboard presentation: band + scenario slider, floor anchor marked, no
   point estimate anywhere.
