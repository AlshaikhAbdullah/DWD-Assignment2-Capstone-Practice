# Layer 4 — material-value scenario checks (live BigQuery + landed sources)

- PASS — row inventory: 2 years × scenarios × 3 materials, floor anchor 2024-only: 27 rows; 2023: 12; floor-anchor rows: [('2024', 'aluminium'), ('2024', 'copper'), ('2024', 'steel')]
- PASS — every 'verified' price equals the landed World Bank Pink Sheet annual mean: 18 verified price cells (Al/Cu × 2 years × scenarios); mismatches: 0; Pink Sheet: [(('aluminium', 2023), 2255.74), (('aluminium', 2024), 2419.02), (('copper', 2023), 8490.29), (('copper', 2024), 9142.14)]
- PASS — steel price labeled unverified (no reachable source): {'unverified'}
- PASS — curb weight and material fractions labeled literature_cited_geo_transfer everywhere: US/global auto averages transferred to SG fleet (modeled geographic transfer; sources: steelonthenet, Aluminum Association/Ducker, CAR); 0 rows missing the label
- PASS — strict band ordering low < mid < high in every row (no point estimates): 0 degenerate bands
- PASS — single confidence tier: scenario_range_unverified_inputs: {'scenario_range_unverified_inputs'}
- PASS — value_usd_mid reproduces from the provenance CSV for all 27 rows: 0 mismatches (formula: dereg × share × weight × fraction × price)
- PASS — floor anchor share ties to elv_disposal_split 2024 lower bound: anchor 0.0379 == split residual share 0.0379 (a LOWER-bound anchor inside the band, not the tonnage)
- PASS — the one verified factor (car deregistrations) ties to the fact layer: 2023=29089, 2024=36137; mismatching rows: 0

**RESULT: all Layer 4 scenario checks PASS**
