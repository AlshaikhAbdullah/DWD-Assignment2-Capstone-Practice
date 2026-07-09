#!/usr/bin/env python3
"""Part 1 raw+clean checks — prove the two locked clean-layer rules, plus
raw-layer fidelity, against LIVE BigQuery and the landed files.

Locked rules (decision log 2026-07-08):
  RULE 1 (parent/child taxonomy): public_motor_cars (parent) and
    private_hire_cars+taxis (children) never co-exist in clean; one
    representation per era, switching at the proven 1988Dec overlap; the
    reconstructed total must have no double-count across the boundary.
  RULE 2 (suppressed cells): '-'/'na' are NULL in units (raw keeps them
    verbatim); checksum-derived values appear ONLY in units_derived with the
    formula in `derivation`; units is never silently imputed.

Usage: python3 verification/raw_clean_checks.py > verification/part1_raw_clean_checks.md
Exit 1 on any failure.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import bq_client as bq

FAILURES = []


def check(name, ok, evidence):
    print(f"- {'PASS' if ok else '**FAIL**'} — {name}: {evidence}")
    if not ok:
        FAILURES.append(name)


def landing_records(slug):
    d = os.path.join(ROOT, "data", "landing", slug)
    name = sorted(os.listdir(d))[-1]
    with open(os.path.join(d, name)) as f:
        return json.load(f)["result"]["records"]


def q1(sql):
    rows = bq.query(sql)
    return list(rows[0].values())[0] if rows else None


def main():
    P, D = bq.PROJECT, bq.DATASET
    print("# Part 1 — raw + clean layer checks (live BigQuery + landed files)\n")

    print("## Raw layer fidelity (raw_* vs landed files)")
    for slug, table in [("new_registrations_monthly", "raw_new_registrations_monthly"),
                        ("deregistrations_monthly", "raw_deregistrations_monthly"),
                        ("population_vqs_monthly", "raw_population_vqs_monthly"),
                        ("population_by_type_monthly", "raw_population_by_type_monthly")]:
        recs = landing_records(slug)
        n = int(q1(f"SELECT COUNT(*) FROM `{P}.{D}.{table}`"))
        check(f"{table} row count", n == len(recs), f"BQ {n} == landed {len(recs)}")
        rows = bq.query(f"SELECT row_index, raw_record FROM `{P}.{D}.{table}` ORDER BY row_index")
        same = all(json.loads(r["raw_record"]) == recs[int(r["row_index"])] for r in rows)
        check(f"{table} content equality", same,
              "every BQ raw_record JSON == landed record (full-table comparison)")

    v = q1(f"""SELECT JSON_VALUE(raw_record, '$.2002Sep')
               FROM `{P}.{D}.raw_deregistrations_monthly`
               WHERE TRIM(JSON_VALUE(raw_record, '$.DataSeries')) = 'Category D: Motorcycles & Scooters'""")
    check("suppressed cell verbatim in raw", v == "-", f"dereg 2002Sep Cat D raw value = {v!r}")

    print("\n## RULE 2 — suppressed cells (clean_vehicle_flows)")
    bad = int(q1(f"""SELECT COUNTIF(units IS NOT NULL AND TRIM(units_raw) IN ('na','-',''))
                     + COUNTIF(units IS NULL AND TRIM(units_raw) NOT IN ('na','-','') AND units_raw IS NOT NULL)
                     FROM `{P}.{D}.clean_vehicle_flows`"""))
    check("units IS NULL exactly when raw is 'na'/'-'/''", bad == 0, f"{bad} mismatching cells")

    rows = bq.query(f"""SELECT series, CAST(month AS STRING) AS month, quota_category,
                               units, units_derived, derivation
                        FROM `{P}.{D}.clean_vehicle_flows`
                        WHERE units_derived IS NOT NULL""")
    ok = (len(rows) == 1 and rows[0]["series"] == "deregistrations"
          and rows[0]["month"] == "2002-09-01" and rows[0]["quota_category"] == "cat_d"
          and rows[0]["units"] is None and rows[0]["units_derived"] == "1422"
          and rows[0]["derivation"] is not None)
    check("derived values: exactly the one diagnosed cell, labeled, units stays NULL",
          ok, f"rows={[(r['series'], r['month'], r['quota_category'], r['units'], r['units_derived']) for r in rows]}; "
              f"derivation={rows[0]['derivation']!r}" if rows else "no derived rows")

    n_na = int(q1(f"SELECT COUNTIF(TRIM(units_raw) IN ('na','-')) FROM `{P}.{D}.clean_vehicle_flows`"))
    print(f"  (context: {n_na:,} na/suppressed cells total are NULL in `units`; only 1 has a derived value)")

    print("\n## RULE 1 — parent/child taxonomy (clean_population_by_type)")
    coexist = int(q1(f"""SELECT COUNT(*) FROM (
        SELECT month FROM `{P}.{D}.clean_population_by_type`
        WHERE vehicle_type IN ('public_motor_cars','private_hire_cars','taxis')
        GROUP BY month
        HAVING COUNTIF(vehicle_type='public_motor_cars') > 0
           AND COUNTIF(vehicle_type IN ('private_hire_cars','taxis')) > 0)"""))
    check("no month carries both parent and child rows", coexist == 0, f"{coexist} months co-exist")

    row = bq.query(f"""SELECT CAST(MAX(IF(vehicle_type='public_motor_cars', month, NULL)) AS STRING) AS last_parent,
                              CAST(MIN(IF(vehicle_type IN ('private_hire_cars','taxis'), month, NULL)) AS STRING) AS first_child
                       FROM `{P}.{D}.clean_population_by_type`""")[0]
    check("era switch at the proven overlap month",
          row["last_parent"] == "1988-11-01" and row["first_child"] == "1988-12-01",
          f"parent rows end {row['last_parent']}, child rows start {row['first_child']}")

    viol = int(q1(f"""SELECT COUNT(*) FROM (
        SELECT month,
               MAX(IF(is_total, units, NULL)) AS total_units,
               SUM(IF(NOT is_total, units, 0)) AS sum_types
        FROM `{P}.{D}.clean_population_by_type`
        GROUP BY month
        HAVING total_units IS NOT NULL AND ABS(sum_types - total_units) > 0)"""))
    months = int(q1(f"SELECT COUNT(DISTINCT month) FROM `{P}.{D}.clean_population_by_type`"))
    check("reconstructed Σ(types) = Total — no double-count across the boundary",
          viol == 0, f"{viol} violations across {months} months (incl. 1988Dec)")

    print("\n## Clean flows invariants")
    viol = int(q1(f"""SELECT COUNT(*) FROM (
        SELECT series, month,
               MAX(IF(is_total, units, NULL)) AS total_units,
               SUM(IF(NOT is_total, COALESCE(units, units_derived), 0)) AS sum_cats
        FROM `{P}.{D}.clean_vehicle_flows`
        GROUP BY series, month
        HAVING total_units IS NOT NULL AND ABS(sum_cats - total_units) > 0)"""))
    sm = int(q1(f"SELECT COUNT(DISTINCT CONCAT(series, CAST(month AS STRING))) FROM `{P}.{D}.clean_vehicle_flows`"))
    check("Σ(categories)=Total in clean (derived value closes 2002Sep)", viol == 0,
          f"{viol} violations across {sm:,} series-months")

    dupes = int(q1(f"""SELECT COUNT(*) FROM (
        SELECT series, month, quota_category, COUNT(*) c
        FROM `{P}.{D}.clean_vehicle_flows` GROUP BY 1,2,3 HAVING c > 1)"""))
    check("no duplicate (series, month, quota_category)", dupes == 0, f"{dupes} duplicate keys")

    unmapped = int(q1(f"SELECT COUNTIF(quota_category IS NULL) FROM `{P}.{D}.clean_vehicle_flows`"))
    check("every source row maps to a canonical category", unmapped == 0, f"{unmapped} unmapped rows")

    neg = int(q1(f"SELECT COUNTIF(units < 0) + COUNTIF(units_derived < 0) FROM `{P}.{D}.clean_vehicle_flows`"))
    check("non-negative counts", neg == 0, f"{neg} negative values")

    spans = bq.query(f"""SELECT series, CAST(MIN(month) AS STRING) lo, CAST(MAX(month) AS STRING) hi,
                                COUNT(DISTINCT month) n,
                                DATE_DIFF(MAX(month), MIN(month), MONTH) + 1 expected
                         FROM `{P}.{D}.clean_vehicle_flows` GROUP BY series ORDER BY series""")
    for s in spans:
        check(f"month continuity: {s['series']}", s["n"] == s["expected"],
              f"{s['lo']} → {s['hi']}, {s['n']} distinct months == span {s['expected']}")

    print("\n## clean_comtrade_exports (load-rule flags)")
    rows = bq.query(f"""SELECT year, qty_usable, netwgt_usable FROM `{P}.{D}.clean_comtrade_exports` ORDER BY year""")
    qty_bad = sorted(r["year"] for r in rows if r["qty_usable"] == "false")
    wgt_bad = sorted(r["year"] for r in rows if r["netwgt_usable"] == "false")
    check("21 years present", len(rows) == 21, f"{len(rows)} years")
    check("qty flagged unusable exactly where landing checks found it",
          qty_bad == ["2022", "2025"], f"qty unusable: {qty_bad}")
    check("netWgt flagged unusable exactly where landing checks found it",
          wgt_bad == ["2007", "2008", "2018", "2024"], f"netWgt unusable: {wgt_bad}")

    print("\n## Hand spot-checks (clean value traced to landed file)")
    for series, slug, label, col, month in [
            ("new_registrations", "new_registrations_monthly", "    Category A: Cars", "2023Dec", "2023-12-01"),
            ("deregistrations", "deregistrations_monthly", "Total Motor Vehicles De-Registered", "1990May", "1990-05-01"),
            ("vehicle_population", "population_vqs_monthly", "    Category B: Cars", "2026May", "2026-05-01")]:
        rec = next(r for r in landing_records(slug) if r["DataSeries"] == label)
        got = q1(f"""SELECT units FROM `{P}.{D}.clean_vehicle_flows`
                     WHERE series='{series}' AND month=DATE '{month}'
                       AND source_label='{label.strip()}'""")
        want = rec[col].replace(",", "")
        check(f"{series} {month} `{label.strip()}`", str(got) == want,
              f"clean={got} == landed {col}={rec[col]!r}")

    print()
    if FAILURES:
        print(f"**RESULT: FAIL** — {FAILURES}")
        sys.exit(1)
    print("**RESULT: all raw+clean checks PASS — both locked rules proven**")


if __name__ == "__main__":
    main()
