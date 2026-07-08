# Part 1 — landing-stage checks (run on landed repo files)

Manifest: 25 landed files, each with source URL + UTC fetch timestamp + sha256 (`data/landing/manifest.jsonl`).

## COE-category series (canonical — strict)

### `new_registrations_monthly`  (data/landing/new_registrations_monthly/20260708T220438Z.json)
- Total row: `Total New Motor Vehicles Registered` · 7 category rows · 432 month columns (1990May → 2026Apr)
- continuity: PASS — no missing/doubled months
- checksum Σ(categories)=Total: **0 unexplained violations** across 432 checkable months (0 months Total=na; 340 months with ≥1 na category)

### `deregistrations_monthly`  (data/landing/deregistrations_monthly/20260708T220444Z.json)
- Total row: `Total Motor Vehicles De-Registered` · 7 category rows · 432 month columns (1990May → 2026Apr)
- continuity: PASS — no missing/doubled months
- checksum Σ(categories)=Total: **0 unexplained violations** across 432 checkable months (0 months Total=na; 343 months with ≥1 na category)
    - 2002Sep: Total=7,658 Σcats=6,236 (Δ=-1,422) — KNOWN source defect: source prints '-' for Category D; implied value = Total − Σothers = 1,422 (neighbors: 1,262 / 1,148). Clean layer leaves it NULL.

### `population_vqs_monthly`  (data/landing/population_vqs_monthly/20260708T220450Z.json)
- Total row: `Total Motor Vehicles` · 7 category rows · 433 month columns (1990May → 2026May)
- continuity: PASS — no missing/doubled months
- checksum Σ(categories)=Total: **0 unexplained violations** across 433 checkable months (0 months Total=na; 341 months with ≥1 na category)

## Population by vehicle type (taxonomy check — informational)

### `population_by_type_monthly`  (data/landing/population_by_type_monthly/20260708T220456Z.json)
- Total row: `Total` · 7 category rows · 772 month columns (1962Jan → 2026Apr)
- continuity: PASS — no missing/doubled months
- checksum Σ(categories)=Total: **0 unexplained violations** across 772 checkable months (0 months Total=na; 323 months with ≥1 na category)

## Comtrade

### `comtrade_hs8703_exports` (per-year world aggregates)
| year | records | qty (units) | netWgt (kg) | FOB (USD) | flags |
|---|---|---|---|---|---|
| 2005 | 1 | 81966.0 | 36482337.0 | 358436547.0 | ok |
| 2006 | 1 | 78802.0 | 45091292.0 | 443002047.0 | ok |
| 2007 | 1 | 63570.0 | None | 437786748.0 | **netWgt missing/zero — magnitude must fall back to qty/value** |
| 2008 | 1 | 66052.0 | None | 409537872.0 | **netWgt missing/zero — magnitude must fall back to qty/value** |
| 2009 | 1 | 38084.0 | 20019650.0 | 253226532.0 | ok |
| 2010 | 1 | 21657.0 | 16058507.465 | 243579908.287 | ok |
| 2011 | 1 | 18336.0 | 16719003.123 | 291896458.998 | ok |
| 2012 | 1 | 15125.0 | 18705512.027 | 334221389.583 | ok |
| 2013 | 1 | 17371.154 | 18304184.2 | 338291939.239 | ok |
| 2014 | 1 | 20069.0 | 17436834.218 | 333966408.295 | ok |
| 2015 | 1 | 23463.301 | 15238727.568 | 259727541.56 | ok |
| 2016 | 1 | 32055.77 | 15328334.836 | 279196372.427 | ok |
| 2017 | 1 | 67901.741 | 14966440.458 | 245469583.905 | ok |
| 2018 | 1 | 60192.68 | 0.0 | 336175045.362 | **netWgt missing/zero — magnitude must fall back to qty/value** |
| 2019 | 1 | 56116.866 | 19624587.937 | 375466105.421 | ok |
| 2020 | 1 | 41722.104 | 21849699.884 | 400676635.706 | ok |
| 2021 | 1 | 37314.412 | 17721715.75 | 321355834.433 | ok |
| 2022 | 1 | 0.0 | 15770391.495 | 307123151.289 | **qty missing despite net weight — qty unusable** |
| 2023 | 1 | 38076.392 | 19051226.87 | 392135475.015 | ok |
| 2024 | 1 | 34769.49 | None | 395609917.537 | **netWgt missing/zero — magnitude must fall back to qty/value** |
| 2025 | 1 | 0.0 | 19066301.617 | 412214247.385 | **qty missing despite net weight — qty unusable** |

**RESULT: all strict landing checks PASS**
