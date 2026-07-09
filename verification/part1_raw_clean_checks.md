# Part 1 — raw + clean layer checks (live BigQuery + landed files)

## Raw layer fidelity (raw_* vs landed files)
- PASS — raw_new_registrations_monthly row count: BQ 10 == landed 10
- PASS — raw_new_registrations_monthly content equality: every BQ raw_record JSON == landed record (full-table comparison)
- PASS — raw_deregistrations_monthly row count: BQ 8 == landed 8
- PASS — raw_deregistrations_monthly content equality: every BQ raw_record JSON == landed record (full-table comparison)
- PASS — raw_population_vqs_monthly row count: BQ 8 == landed 8
- PASS — raw_population_vqs_monthly content equality: every BQ raw_record JSON == landed record (full-table comparison)
- PASS — raw_population_by_type_monthly row count: BQ 8 == landed 8
- PASS — raw_population_by_type_monthly content equality: every BQ raw_record JSON == landed record (full-table comparison)
- PASS — suppressed cell verbatim in raw: dereg 2002Sep Cat D raw value = '-'

## RULE 2 — suppressed cells (clean_vehicle_flows)
- PASS — units IS NULL exactly when raw is 'na'/'-'/'': 0 mismatching cells
- PASS — derived values: exactly the one diagnosed cell, labeled, units stays NULL: rows=[('deregistrations', '2002-09-01', 'cat_d', None, '1422')]; derivation='Total - SUM(other categories) for the month; single source-suppressed cell; locked rule 2026-07-08'
  (context: 1,025 na/suppressed cells total are NULL in `units`; only 1 has a derived value)

## RULE 1 — parent/child taxonomy (clean_population_by_type)
- PASS — no month carries both parent and child rows: 0 months co-exist
- PASS — era switch at the proven overlap month: parent rows end 1988-11-01, child rows start 1988-12-01
- PASS — reconstructed Σ(types) = Total — no double-count across the boundary: 0 violations across 772 months (incl. 1988Dec)

## Clean flows invariants
- PASS — Σ(categories)=Total in clean (derived value closes 2002Sep): 0 violations across 1,297 series-months
- PASS — no duplicate (series, month, quota_category): 0 duplicate keys
- PASS — every source row maps to a canonical category: 0 unmapped rows
- PASS — non-negative counts: 0 negative values
- PASS — month continuity: deregistrations: 1990-05-01 → 2026-04-01, 432 distinct months == span 432
- PASS — month continuity: new_registrations: 1990-05-01 → 2026-04-01, 432 distinct months == span 432
- PASS — month continuity: vehicle_population: 1990-05-01 → 2026-05-01, 433 distinct months == span 433

## clean_comtrade_exports (load-rule flags)
- PASS — 21 years present: 21 years
- PASS — qty flagged unusable exactly where landing checks found it: qty unusable: ['2022', '2025']
- PASS — netWgt flagged unusable exactly where landing checks found it: netWgt unusable: ['2007', '2008', '2018', '2024']

## Hand spot-checks (clean value traced to landed file)
- PASS — new_registrations 2023-12-01 `Category A: Cars`: clean=2593 == landed 2023Dec='2593'
- PASS — deregistrations 1990-05-01 `Total Motor Vehicles De-Registered`: clean=2621 == landed 1990May='2621'
- PASS — vehicle_population 2026-05-01 `Category B: Cars`: clean=334874 == landed 2026May='334874'

**RESULT: all raw+clean checks PASS — both locked rules proven**
