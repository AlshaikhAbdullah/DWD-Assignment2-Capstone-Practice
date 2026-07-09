# Part 1 — analysis-ready checks (fact tables, live BigQuery)

## fact_vehicle_flows
- PASS — grain completeness: one row per clean (month, quota_category): 3031 rows == 3031 distinct keys (433 months × 7 categories = 3,031)
- PASS — car scope filterable and exactly Cat A + Cat B + Weekend/Off-Peak: is_car_scope covers: cat_a,cat_b,weekend_offpeak
- PASS — non-car categories retained-but-flagged: 4 non-car categories present (cat_c, cat_d, taxis, exempt)
- PASS — exactly one derived deregistration cell, labeled: [('2002-09-01', 'cat_d', '1422')]
- PASS — pivot equality with clean (full table): 0 mismatching cells
- PASS — car-scope yearly deregistrations match scouting-verified numbers: {'2023': 29089, '2024': 36137, '2025': 49550}

## fact_population_by_type
- PASS — row count matches clean (era rule inherited): 4309 == 4309
- PASS — parent/child never co-exist in the fact: 0 months

## elv_disposal_split (locked rules)
- PASS — one row per year 2005–2025: 21 rows, 2005→2025
- PASS — export COUNTS only for locked qty years (2023, 2024): count years: ['2023', '2024']
- PASS — 2023: proxy exceeds deregistrations → scrapped NULL + flag, no negative count: exported=38076, ratio=1.309, scrapped=None, flag=true
- PASS — 2024: residual scrapped estimate computed: dereg=36137 − exported=34769 = scrapped_est 1368 (ratio 0.962)
- PASS — bound directions labeled: residual is a lower-bound FLOOR, proxy an upper bound: [('2023', None, 'upper_bound'), ('2024', 'lower_bound', 'upper_bound')] (2023 has no scrap floor — proxy exceeds total; 2024 floor=1,368)
- PASS — value-only years are context, not a series: 19 context years; none emit export counts, scrap estimates, or ratios
- PASS — countable years carry the low/upper-bound confidence tier: tiers: {'low_triangulated_upper_bound'}
- PASS — deregistrations_total ties back to fact_vehicle_flows car scope: 21/21 years equal

**RESULT: all analysis-ready checks PASS**
