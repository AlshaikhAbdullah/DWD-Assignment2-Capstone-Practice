#!/usr/bin/env python3
"""Part 1 analysis-ready checks — fact tables vs clean layer + disposal rules.

Usage: python3 verification/analysis_ready_checks.py > verification/part1_analysis_ready_checks.md
Exit 1 on any failure.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import bq_client as bq

P, D = bq.PROJECT, bq.DATASET
FAILURES = []


def check(name, ok, evidence):
    print(f"- {'PASS' if ok else '**FAIL**'} — {name}: {evidence}")
    if not ok:
        FAILURES.append(name)


def q1(sql):
    rows = bq.query(sql)
    return list(rows[0].values())[0] if rows else None


def main():
    print("# Part 1 — analysis-ready checks (fact tables, live BigQuery)\n")

    print("## fact_vehicle_flows")
    n = int(q1(f"SELECT COUNT(*) FROM `{P}.{D}.fact_vehicle_flows`"))
    expect = int(q1(f"""SELECT COUNT(DISTINCT CONCAT(CAST(month AS STRING), quota_category))
                        FROM `{P}.{D}.clean_vehicle_flows` WHERE NOT is_total"""))
    check("grain completeness: one row per clean (month, quota_category)",
          n == expect, f"{n} rows == {expect} distinct keys (433 months × 7 categories = 3,031)")

    cars = bq.query(f"""SELECT STRING_AGG(DISTINCT quota_category ORDER BY quota_category)
                        AS cats FROM `{P}.{D}.fact_vehicle_flows` WHERE is_car_scope""")[0]["cats"]
    check("car scope filterable and exactly Cat A + Cat B + Weekend/Off-Peak",
          cars == "cat_a,cat_b,weekend_offpeak", f"is_car_scope covers: {cars}")

    other = int(q1(f"""SELECT COUNT(DISTINCT quota_category)
                       FROM `{P}.{D}.fact_vehicle_flows` WHERE NOT is_car_scope"""))
    check("non-car categories retained-but-flagged", other == 4,
          f"{other} non-car categories present (cat_c, cat_d, taxis, exempt)")

    rows = bq.query(f"""SELECT CAST(month AS STRING) m, quota_category, deregistrations
                        FROM `{P}.{D}.fact_vehicle_flows`
                        WHERE deregistrations_source = 'derived_checksum'""")
    check("exactly one derived deregistration cell, labeled",
          len(rows) == 1 and rows[0]["m"] == "2002-09-01"
          and rows[0]["quota_category"] == "cat_d" and rows[0]["deregistrations"] == "1422",
          f"{[(r['m'], r['quota_category'], r['deregistrations']) for r in rows]}")

    mism = int(q1(f"""
      SELECT COUNTIF(f.new_registrations IS DISTINCT FROM c.reg
                  OR f.vehicle_population IS DISTINCT FROM c.pop)
      FROM `{P}.{D}.fact_vehicle_flows` f
      JOIN (SELECT month, quota_category,
                   MAX(IF(series='new_registrations', units, NULL)) reg,
                   MAX(IF(series='vehicle_population', units, NULL)) pop
            FROM `{P}.{D}.clean_vehicle_flows` WHERE NOT is_total
            GROUP BY 1, 2) c USING (month, quota_category)"""))
    check("pivot equality with clean (full table)", mism == 0, f"{mism} mismatching cells")

    yearly = {r["y"]: int(r["n"]) for r in bq.query(f"""
      SELECT CAST(EXTRACT(YEAR FROM month) AS STRING) y, CAST(SUM(deregistrations) AS INT64) n
      FROM `{P}.{D}.fact_vehicle_flows`
      WHERE is_car_scope AND EXTRACT(YEAR FROM month) BETWEEN 2023 AND 2025 GROUP BY y""")}
    check("car-scope yearly deregistrations match scouting-verified numbers",
          yearly == {"2023": 29089, "2024": 36137, "2025": 49550}, f"{yearly}")

    print("\n## fact_population_by_type")
    n = int(q1(f"SELECT COUNT(*) FROM `{P}.{D}.fact_population_by_type`"))
    expect = int(q1(f"SELECT COUNT(*) FROM `{P}.{D}.clean_population_by_type` WHERE NOT is_total"))
    check("row count matches clean (era rule inherited)", n == expect, f"{n} == {expect}")
    coexist = int(q1(f"""SELECT COUNT(*) FROM (
        SELECT month FROM `{P}.{D}.fact_population_by_type`
        WHERE vehicle_type IN ('public_motor_cars','private_hire_cars','taxis')
        GROUP BY month
        HAVING COUNTIF(vehicle_type='public_motor_cars') > 0
           AND COUNTIF(vehicle_type IN ('private_hire_cars','taxis')) > 0)"""))
    check("parent/child never co-exist in the fact", coexist == 0, f"{coexist} months")

    print("\n## elv_disposal_split (locked rules)")
    rows = bq.query(f"""SELECT year, deregistrations_total, exported_units_comtrade,
                               scrapped_est_residual, export_proxy_ratio,
                               proxy_exceeds_deregistrations, method, confidence_tier
                        FROM `{P}.{D}.elv_disposal_split` ORDER BY year""")
    check("one row per year 2005–2025", len(rows) == 21 and rows[0]["year"] == "2005"
          and rows[-1]["year"] == "2025", f"{len(rows)} rows, {rows[0]['year']}→{rows[-1]['year']}")

    with_counts = [r["year"] for r in rows if r["exported_units_comtrade"] is not None]
    check("export COUNTS only for locked qty years (2023, 2024)",
          with_counts == ["2023", "2024"], f"count years: {with_counts}")

    r23 = next(r for r in rows if r["year"] == "2023")
    check("2023: proxy exceeds deregistrations → scrapped NULL + flag, no negative count",
          r23["proxy_exceeds_deregistrations"] == "true" and r23["scrapped_est_residual"] is None
          and r23["exported_units_comtrade"] == "38076" and r23["export_proxy_ratio"] == "1.309",
          f"exported={r23['exported_units_comtrade']}, ratio={r23['export_proxy_ratio']}, "
          f"scrapped={r23['scrapped_est_residual']}, flag={r23['proxy_exceeds_deregistrations']}")

    r24 = next(r for r in rows if r["year"] == "2024")
    check("2024: residual scrapped estimate computed",
          r24["scrapped_est_residual"] == "1368" and r24["export_proxy_ratio"] == "0.962"
          and r24["proxy_exceeds_deregistrations"] == "false",
          f"dereg={r24['deregistrations_total']} − exported={r24['exported_units_comtrade']} "
          f"= scrapped_est {r24['scrapped_est_residual']} (ratio {r24['export_proxy_ratio']})")

    bounds = bq.query(f"""SELECT year, scrapped_bound_direction, export_bound_direction
                          FROM `{P}.{D}.elv_disposal_split`
                          WHERE scrapped_est_residual IS NOT NULL
                             OR exported_units_comtrade IS NOT NULL ORDER BY year""")
    check("bound directions labeled: residual is a lower-bound FLOOR, proxy an upper bound",
          all(r["export_bound_direction"] == "upper_bound" for r in bounds)
          and [r["scrapped_bound_direction"] for r in bounds] == [None, "lower_bound"],
          f"{[(r['year'], r['scrapped_bound_direction'], r['export_bound_direction']) for r in bounds]} "
          "(2023 has no scrap floor — proxy exceeds total; 2024 floor=1,368)")

    ctx = [r for r in rows if r["exported_units_comtrade"] is None]
    check("value-only years are context, not a series",
          all(r["method"] == "no_countable_export_proxy" and r["confidence_tier"] == "context_only"
              and r["scrapped_est_residual"] is None for r in ctx),
          f"{len(ctx)} context years; none emit export counts, scrap estimates, or ratios")

    tiers = {r["confidence_tier"] for r in rows if r["exported_units_comtrade"] is not None}
    check("countable years carry the low/upper-bound confidence tier",
          tiers == {"low_triangulated_upper_bound"}, f"tiers: {tiers}")

    match = int(q1(f"""
      SELECT COUNTIF(s.deregistrations_total = f.n) FROM `{P}.{D}.elv_disposal_split` s
      JOIN (SELECT EXTRACT(YEAR FROM month) y, CAST(SUM(deregistrations) AS INT64) n
            FROM `{P}.{D}.fact_vehicle_flows` WHERE is_car_scope GROUP BY y) f
      ON CAST(s.year AS INT64) = f.y"""))
    check("deregistrations_total ties back to fact_vehicle_flows car scope",
          match == 21, f"{match}/21 years equal")

    print()
    if FAILURES:
        print(f"**RESULT: FAIL** — {FAILURES}")
        sys.exit(1)
    print("**RESULT: all analysis-ready checks PASS**")


if __name__ == "__main__":
    main()
