
CREATE OR REPLACE TABLE `msbai-dwd-aa13072.sg_elv.fact_population_by_type` AS
SELECT month, vehicle_type, units, taxonomy_era
FROM `msbai-dwd-aa13072.sg_elv.clean_population_by_type`
WHERE NOT is_total
