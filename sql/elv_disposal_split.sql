
CREATE OR REPLACE TABLE `msbai-dwd-aa13072.sg_elv.elv_disposal_split` AS
WITH car_dereg AS (
  SELECT EXTRACT(YEAR FROM month) AS year,
         SUM(deregistrations) AS deregistrations_cars
  FROM `msbai-dwd-aa13072.sg_elv.fact_vehicle_flows`
  WHERE is_car_scope
    AND EXTRACT(YEAR FROM month) BETWEEN 2005 AND 2025
  GROUP BY year),
comtrade AS (
  SELECT year, qty_units, net_wgt_kg, fob_usd, qty_usable, netwgt_usable
  FROM `msbai-dwd-aa13072.sg_elv.clean_comtrade_exports`),
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
