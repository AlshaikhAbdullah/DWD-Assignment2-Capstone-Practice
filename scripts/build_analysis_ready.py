#!/usr/bin/env python3
"""Part 1, analysis-ready stage — materialize the fact tables (approved schema).

- fact_vehicle_flows (month, quota_category): pivoted from clean, Total rows
  excluded, cars = cat_a + cat_b + weekend_offpeak cleanly filterable via
  is_car_scope, other categories retained-but-flagged. The single
  checksum-derived deregistration cell is labeled via deregistrations_source.
- fact_population_by_type (month, vehicle_type): from clean (era rule already
  applied there), Total rows excluded.
- elv_disposal_split (year, scope): scrapped only as a residual where the
  export proxy is COUNTABLE (2023, 2024 — locked Comtrade cross-check scope);
  per-year availability + confidence-tier columns; NO export count emitted
  for value-only years (they are context rows). FOB dollars never share an
  axis with vehicle counts (DECISIONS.md).

Tables are CREATE OR REPLACE — re-runnable, sourced entirely from the clean
views. Run after build_clean_views.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bq_client as bq

P, D = bq.PROJECT, bq.DATASET

FACT_VEHICLE_FLOWS = f"""
CREATE OR REPLACE TABLE `{P}.{D}.fact_vehicle_flows` AS
SELECT
  month,
  quota_category,
  quota_category IN ('cat_a', 'cat_b', 'weekend_offpeak') AS is_car_scope,
  MAX(IF(series = 'new_registrations', units, NULL)) AS new_registrations,
  MAX(IF(series = 'deregistrations', COALESCE(units, units_derived), NULL)) AS deregistrations,
  MAX(IF(series = 'deregistrations',
         IF(units_derived IS NOT NULL, 'derived_checksum', 'reported'), NULL)) AS deregistrations_source,
  MAX(IF(series = 'vehicle_population', units, NULL)) AS vehicle_population
FROM `{P}.{D}.clean_vehicle_flows`
WHERE NOT is_total
GROUP BY month, quota_category
"""

FACT_POPULATION_BY_TYPE = f"""
CREATE OR REPLACE TABLE `{P}.{D}.fact_population_by_type` AS
SELECT month, vehicle_type, units, taxonomy_era
FROM `{P}.{D}.clean_population_by_type`
WHERE NOT is_total
"""

ELV_DISPOSAL_SPLIT = f"""
CREATE OR REPLACE TABLE `{P}.{D}.elv_disposal_split` AS
WITH car_dereg AS (
  SELECT EXTRACT(YEAR FROM month) AS year,
         SUM(deregistrations) AS deregistrations_cars
  FROM `{P}.{D}.fact_vehicle_flows`
  WHERE is_car_scope
    AND EXTRACT(YEAR FROM month) BETWEEN 2005 AND 2025
  GROUP BY year),
comtrade AS (
  SELECT year, qty_units, net_wgt_kg, fob_usd, qty_usable, netwgt_usable
  FROM `{P}.{D}.clean_comtrade_exports`),
joined AS (
  SELECT
    d.year,
    'cars_cat_a_b_weop' AS scope,
    d.deregistrations_cars AS deregistrations_total,
    -- Locked Comtrade cross-check scope (DECISIONS.md 2026-07-08): export
    -- COUNTS only for qty-available years in the analysis window (2023, 2024).
    IF(d.year IN (2023, 2024) AND c.qty_usable, CAST(c.qty_units AS INT64), NULL) AS exported_units_comtrade,
    c.net_wgt_kg AS export_net_wgt_kg_context,
    c.fob_usd AS export_fob_usd_context,
    c.qty_usable AS qty_available,
    c.netwgt_usable AS netwgt_available,
    c.fob_usd IS NOT NULL AS fob_available
  FROM car_dereg d LEFT JOIN comtrade c USING (year))
SELECT
  year, scope, deregistrations_total, exported_units_comtrade,
  -- residual only where countable AND non-negative; 2023's proxy EXCEEDS
  -- total car deregistrations (ratio 1.31) — the honest output there is
  -- NULL + flag, not a negative scrap count (reframe: no fabricated numbers).
  IF(exported_units_comtrade IS NOT NULL
     AND deregistrations_total - exported_units_comtrade >= 0,
     deregistrations_total - exported_units_comtrade, NULL) AS scrapped_est_residual,
  IF(exported_units_comtrade IS NOT NULL,
     ROUND(exported_units_comtrade / deregistrations_total, 3), NULL) AS export_proxy_ratio,
  exported_units_comtrade IS NOT NULL
    AND exported_units_comtrade > deregistrations_total AS proxy_exceeds_deregistrations,
  export_net_wgt_kg_context, export_fob_usd_context,
  qty_available, netwgt_available, fob_available,
  CASE
    WHEN exported_units_comtrade IS NOT NULL THEN 'comtrade_hs8703_world_export_upper_bound'
    ELSE 'no_countable_export_proxy'
  END AS method,
  CASE
    WHEN exported_units_comtrade IS NOT NULL THEN 'low_triangulated_upper_bound'
    ELSE 'context_only'
  END AS confidence_tier
FROM joined
"""


def main():
    for name, sql in [("fact_vehicle_flows", FACT_VEHICLE_FLOWS),
                      ("fact_population_by_type", FACT_POPULATION_BY_TYPE),
                      ("elv_disposal_split", ELV_DISPOSAL_SPLIT)]:
        path = os.path.join(bq.ROOT, "sql", f"{name}.sql")
        with open(path, "w") as f:
            f.write(sql)
        bq.query(sql)
        n = bq.query(f"SELECT COUNT(*) AS n FROM `{P}.{D}.{name}`")[0]["n"]
        print(f"built {D}.{name}: {n} rows  (sql/{name}.sql)")


if __name__ == "__main__":
    main()
