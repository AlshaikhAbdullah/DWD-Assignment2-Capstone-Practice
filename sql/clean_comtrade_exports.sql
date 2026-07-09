-- clean_comtrade_exports: SG HS 8703 exports, world aggregate, per year.
-- Load rules (2026-07-08): qty unreliable (0 despite weight in 2022, 2025);
-- prefer netWgt for magnitude; FOB is the only field present in all years;
-- usability flags carried per year, partial years must be flagged downstream.
CREATE OR REPLACE VIEW `msbai-dwd-aa13072.sg_elv.clean_comtrade_exports` AS
SELECT
  year,
  SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].qty') AS FLOAT64) AS qty_units,
  SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].netWgt') AS FLOAT64) AS net_wgt_kg,
  SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].fobvalue') AS FLOAT64) AS fob_usd,
  COALESCE(SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].qty') AS FLOAT64), 0) > 0 AS qty_usable,
  COALESCE(SAFE_CAST(JSON_VALUE(raw_response, '$.data[0].netWgt') AS FLOAT64), 0) > 0 AS netwgt_usable,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(raw_response, '$.data')) AS record_count
FROM `msbai-dwd-aa13072.sg_elv.raw_comtrade_hs8703`
