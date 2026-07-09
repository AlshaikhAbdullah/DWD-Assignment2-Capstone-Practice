#!/usr/bin/env python3
"""Part 1, clean stage — generate + apply the clean views (no tables).

Encodes the two locked clean-layer rules (decision log, 2026-07-08):

1. PARENT/CHILD TAXONOMY (population by type): 'Public Motor Cars' is the
   pre-1988Dec parent aggregate of 'Private Hire Cars' + 'Taxis' (proven at
   the 1988Dec overlap: 13,613 = 3,140 + 10,473). One representation per era:
   parent rows only BEFORE 1988-12, child rows only FROM 1988-12. They can
   never co-exist in a sum.

2. SUPPRESSED CELLS: 'na' / '-' / '' are NULL in `units` (raw_* keeps them
   verbatim). A checksum-derived value is surfaced ONLY for source-suppressed
   cells (raw text '-'), ONLY when it is the single suppressed cell in its
   (series, month) and the Total is present — in the separate `units_derived`
   column with the formula recorded in `derivation`. `units` itself stays
   NULL: never silently imputed.

The month-column lists are read from the landed files (source of truth), so
the generated SQL unpivots exactly the columns that exist. SQL is written to
sql/ for review and applied with CREATE OR REPLACE VIEW.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bq_client as bq

ROOT = bq.ROOT
SQLDIR = os.path.join(ROOT, "sql")
WIDE_COL = re.compile(r"^(\d{4})([A-Z][a-z]{2})$")
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

FLOW_SERIES = [  # (series name, raw table, landing slug)
    ("new_registrations", "raw_new_registrations_monthly", "new_registrations_monthly"),
    ("deregistrations", "raw_deregistrations_monthly", "deregistrations_monthly"),
    ("vehicle_population", "raw_population_vqs_monthly", "population_vqs_monthly"),
]

FLOW_CATEGORY_CASE = """CASE TRIM(JSON_VALUE(raw_record, '$.DataSeries'))
      WHEN 'Category A: Cars' THEN 'cat_a'
      WHEN 'Category B: Cars' THEN 'cat_b'
      WHEN 'Weekend Cars/Off Peak Cars' THEN 'weekend_offpeak'
      WHEN 'Category C: Goods Vehicles & Buses' THEN 'cat_c'
      WHEN 'Category D: Motorcycles & Scooters' THEN 'cat_d'
      WHEN 'Taxis' THEN 'taxis'
      WHEN 'Vehicles Exempted From VQS' THEN 'exempt'
      ELSE IF(STARTS_WITH(JSON_VALUE(raw_record, '$.DataSeries'), 'Total'), 'total', NULL)
    END"""

TYPE_CATEGORY_CASE = """CASE TRIM(JSON_VALUE(raw_record, '$.DataSeries'))
      WHEN 'Cars' THEN 'cars'
      WHEN 'Public Motor Cars' THEN 'public_motor_cars'
      WHEN 'Private Hire Cars' THEN 'private_hire_cars'
      WHEN 'Taxis' THEN 'taxis'
      WHEN 'Buses' THEN 'buses'
      WHEN 'Motorcycles & Scooters' THEN 'motorcycles_scooters'
      WHEN 'Goods & Other Vehicles' THEN 'goods_other'
      WHEN 'Total' THEN 'total'
      ELSE NULL
    END"""


def month_structs(slug):
    d = os.path.join(ROOT, "data", "landing", slug)
    with open(os.path.join(d, sorted(os.listdir(d))[-1])) as f:
        rec = json.load(f)["result"]["records"][0]
    cols = sorted((c for c in rec if WIDE_COL.match(c)),
                  key=lambda c: (int(c[:4]), MONTHS[c[4:]]))
    return ",\n    ".join(
        f"STRUCT(DATE '{c[:4]}-{MONTHS[c[4:]]:02d}-01' AS month, "
        f"JSON_VALUE(raw_record, '$.{c}') AS units_raw)"
        for c in cols)


def unpivot_block(series, table, slug, category_case):
    return f"""  SELECT
    '{series}' AS series,
    m.month,
    {category_case} AS category,
    TRIM(JSON_VALUE(raw_record, '$.DataSeries')) AS source_label,
    m.units_raw,
    SAFE_CAST(REPLACE(m.units_raw, ',', '') AS INT64) AS units
  FROM `{bq.PROJECT}.{bq.DATASET}.{table}`,
  UNNEST([
    {month_structs(slug)}
  ]) AS m
  -- exclude deeper-indented sub-rows (Cat C ETS split) so Cat C is not double-counted
  WHERE NOT STARTS_WITH(JSON_VALUE(raw_record, '$.DataSeries'), '        ')"""


def clean_vehicle_flows():
    unions = "\n  UNION ALL\n".join(
        unpivot_block(s, t, slug, FLOW_CATEGORY_CASE) for s, t, slug in FLOW_SERIES)
    return f"""-- clean_vehicle_flows: unpivoted, typed, taxonomy-mapped monthly flows.
-- Locked rule (2026-07-08): 'na'/'-' -> NULL in `units`; a checksum-derived
-- value appears ONLY in `units_derived` for source-suppressed ('-') cells,
-- single-suppressed-cell months, with the formula in `derivation`.
-- Total rows are kept (is_total) for the checksum; facts must exclude them.
CREATE OR REPLACE VIEW `{bq.PROJECT}.{bq.DATASET}.clean_vehicle_flows` AS
WITH long AS (
{unions}
),
per_month AS (
  SELECT
    series, month,
    MAX(IF(category = 'total', units, NULL)) AS total_units,
    SUM(IF(category != 'total', units, 0)) AS sum_categories,
    COUNTIF(category != 'total' AND TRIM(units_raw) = '-') AS suppressed_cells
  FROM long
  GROUP BY series, month
)
SELECT
  l.series,
  l.month,
  l.category AS quota_category,
  l.category = 'total' AS is_total,
  l.source_label,
  l.units_raw,
  l.units,
  CASE
    WHEN TRIM(l.units_raw) = '-' AND l.category != 'total'
         AND p.suppressed_cells = 1 AND p.total_units IS NOT NULL
    THEN p.total_units - p.sum_categories
  END AS units_derived,
  CASE
    WHEN TRIM(l.units_raw) = '-' AND l.category != 'total'
         AND p.suppressed_cells = 1 AND p.total_units IS NOT NULL
    THEN 'Total - SUM(other categories) for the month; single source-suppressed cell; locked rule 2026-07-08'
  END AS derivation
FROM long l
JOIN per_month p USING (series, month)
"""


def clean_population_by_type():
    block = unpivot_block("population_by_type", "raw_population_by_type_monthly",
                          "population_by_type_monthly", TYPE_CATEGORY_CASE)
    return f"""-- clean_population_by_type: the 1962->present stock by vehicle type.
-- Locked rule (2026-07-08): 'Public Motor Cars' (parent) and
-- 'Private Hire Cars'+'Taxis' (children) never co-exist: parent rows only
-- BEFORE 1988-12, child rows only FROM 1988-12 (proven overlap month).
CREATE OR REPLACE VIEW `{bq.PROJECT}.{bq.DATASET}.clean_population_by_type` AS
WITH long AS (
{block}
)
SELECT
  month,
  category AS vehicle_type,
  category = 'total' AS is_total,
  source_label,
  units_raw,
  units,
  IF(month < DATE '1988-12-01', 'parent_pre1988dec', 'children_from1988dec') AS taxonomy_era
FROM long
WHERE NOT (category = 'public_motor_cars' AND month >= DATE '1988-12-01')
  AND NOT (category IN ('private_hire_cars', 'taxis') AND month < DATE '1988-12-01')
"""


def clean_comtrade():
    return f"""-- clean_comtrade_exports: SG HS 8703 exports, world aggregate, per year.
-- Load rules (2026-07-08): qty unreliable (0 despite weight in 2022, 2025);
-- prefer netWgt for magnitude; FOB is the only field present in all years;
-- usability flags carried per year, partial years must be flagged downstream.
CREATE OR REPLACE VIEW `{bq.PROJECT}.{bq.DATASET}.clean_comtrade_exports` AS
SELECT
  year,
  SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].qty') AS FLOAT64) AS qty_units,
  SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].netWgt') AS FLOAT64) AS net_wgt_kg,
  SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].fobvalue') AS FLOAT64) AS fob_usd,
  COALESCE(SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].qty') AS FLOAT64), 0) > 0 AS qty_usable,
  COALESCE(SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].netWgt') AS FLOAT64), 0) > 0 AS netwgt_usable,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(raw_response, '$.data')) AS record_count
FROM `{bq.PROJECT}.{bq.DATASET}.raw_comtrade_hs8703`
"""


def main():
    os.makedirs(SQLDIR, exist_ok=True)
    for name, sql in [("clean_vehicle_flows", clean_vehicle_flows()),
                      ("clean_population_by_type", clean_population_by_type()),
                      ("clean_comtrade_exports", clean_comtrade())]:
        path = os.path.join(SQLDIR, f"{name}.sql")
        with open(path, "w") as f:
            f.write(sql)
        bq.query(sql)
        print(f"applied view {bq.DATASET}.{name}  (sql/{name}.sql, {len(sql):,} chars)")


if __name__ == "__main__":
    main()
