# Checkpoint D deploy pre-flight

## Gate 1 — analysis-ready tables exist
- PASS — sg_elv.fact_vehicle_flows: 3031 rows (expected 3031)
- PASS — sg_elv.fact_population_by_type: 4309 rows (expected 4309)
- PASS — sg_elv.elv_disposal_split: 21 rows (expected 21)
- PASS — sg_elv.elv_material_value: 27 rows (expected 27)

## Gate 2 — committed snapshot == live tables (fallback freshness)
- PASS — yearly_flows: 36 live years == snapshot
- PASS — monthly_car_dereg: 433 live months == snapshot
- PASS — disposal_split: 21 live years == snapshot
- PASS — material_value: 27 live rows == snapshot

## Gate 3 — read-only dashboard SA can read sg_elv
- SKIPPED — sg-elv-dashboard-ro@msbai-dwd-aa13072.iam.gserviceaccount.com not yet in the dataset ACL. Rerun with --require-sa after the owner mints and grants it.

**RESULT: pre-flight PASS** (SA gate pending owner mint — rerun with --require-sa)
