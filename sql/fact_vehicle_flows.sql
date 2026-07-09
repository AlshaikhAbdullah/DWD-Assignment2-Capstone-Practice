
CREATE OR REPLACE TABLE `msbai-dwd-aa13072.sg_elv.fact_vehicle_flows` AS
SELECT
  month,
  quota_category,
  quota_category IN ('cat_a', 'cat_b', 'weekend_offpeak') AS is_car_scope,
  MAX(IF(series = 'new_registrations', units, NULL)) AS new_registrations,
  MAX(IF(series = 'deregistrations', COALESCE(units, units_derived), NULL)) AS deregistrations,
  MAX(IF(series = 'deregistrations',
         IF(units_derived IS NOT NULL, 'derived_checksum', 'reported'), NULL)) AS deregistrations_source,
  MAX(IF(series = 'vehicle_population', units, NULL)) AS vehicle_population
FROM `msbai-dwd-aa13072.sg_elv.clean_vehicle_flows`
WHERE NOT is_total
GROUP BY month, quota_category
