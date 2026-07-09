#!/usr/bin/env python3
"""Deploy pre-flight — run before publishing the dashboard URL.

Three gates:
  1. The four analysis-ready tables exist in sg_elv with sane row counts.
  2. The committed dashboard/snapshot.json EQUALS the live tables — so the
     app's no-secrets fallback can never serve stale numbers.
  3. The read-only dashboard SA (sg-elv-dashboard-ro@...) is present in the
     sg_elv dataset ACL with a reader role. (Checked via datasets.get with
     the pipeline SA; requires the owner to have minted + granted it.
     Skipped with a clear message until then — rerun after minting.)

Usage: python3 verification/preflight_deploy.py > verification/checkpoint_d_preflight.md
Exit 1 on any FAIL (a missing dashboard SA is FAIL only with --require-sa).
"""

import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import bq_client as bq

P, D = bq.PROJECT, bq.DATASET
DASHBOARD_SA = f"sg-elv-dashboard-ro@{P}.iam.gserviceaccount.com"
EXPECTED_TABLES = {
    "fact_vehicle_flows": 3031,
    "fact_population_by_type": 4309,
    "elv_disposal_split": 21,
    "elv_material_value": 27,
}
FAILURES = []


def check(name, ok, evidence):
    print(f"- {'PASS' if ok else '**FAIL**'} — {name}: {evidence}")
    if not ok:
        FAILURES.append(name)


def gate1_tables():
    print("## Gate 1 — analysis-ready tables exist")
    for table, expected in EXPECTED_TABLES.items():
        try:
            n = int(bq.query(f"SELECT COUNT(*) FROM `{P}.{D}.{table}`")[0]["f0_"])
        except Exception:
            n = int(list(bq.query(f"SELECT COUNT(*) AS n FROM `{P}.{D}.{table}`")[0].values())[0])
        check(f"{D}.{table}", n == expected, f"{n} rows (expected {expected})")


def gate2_snapshot():
    print("\n## Gate 2 — committed snapshot == live tables (fallback freshness)")
    snap = json.load(open(os.path.join(ROOT, "dashboard", "snapshot.json")))

    live_yearly = bq.query(f"""
        SELECT CAST(EXTRACT(YEAR FROM month) AS STRING) year,
          CAST(SUM(deregistrations) AS INT64) car_deregistrations,
          CAST(SUM(new_registrations) AS INT64) car_new_registrations
        FROM `{P}.{D}.fact_vehicle_flows`
        WHERE is_car_scope AND EXTRACT(YEAR FROM month) <= 2025
        GROUP BY year ORDER BY year""")
    check("yearly_flows", live_yearly == snap["yearly_flows"],
          f"{len(live_yearly)} live years == snapshot" if live_yearly == snap["yearly_flows"]
          else "live differs from snapshot — regenerate scripts/build_dashboard_snapshot")

    live_monthly = bq.query(f"""
        SELECT CAST(month AS STRING) month,
          CAST(SUM(deregistrations) AS INT64) car_deregistrations
        FROM `{P}.{D}.fact_vehicle_flows`
        WHERE is_car_scope GROUP BY month ORDER BY month""")
    check("monthly_car_dereg", live_monthly == snap["monthly_car_dereg"],
          f"{len(live_monthly)} live months == snapshot" if live_monthly == snap["monthly_car_dereg"]
          else "live differs from snapshot")

    live_split = bq.query(f"""
        SELECT CAST(year AS STRING) year, deregistrations_total,
          exported_units_comtrade, scrapped_est_residual, export_proxy_ratio,
          proxy_exceeds_deregistrations, scrapped_bound_direction,
          export_bound_direction, method, confidence_tier
        FROM `{P}.{D}.elv_disposal_split` ORDER BY year""")
    check("disposal_split", live_split == snap["disposal_split"],
          f"{len(live_split)} live years == snapshot" if live_split == snap["disposal_split"]
          else "live differs from snapshot")

    live_mv = bq.query(f"""
        SELECT CAST(year AS STRING) year, scrap_share_scenario,
          CAST(scrap_share AS STRING) scrap_share, material,
          deregistrations_cars_verified, tonnes_low, tonnes_mid, tonnes_high,
          CAST(price_usd_per_tonne_mid AS STRING) price_usd_per_tonne_mid,
          price_verification, value_usd_low, value_usd_mid, value_usd_high,
          weight_verification, fraction_verification, confidence_tier
        FROM `{P}.{D}.elv_material_value` ORDER BY year, scrap_share, material""")
    check("material_value", live_mv == snap["material_value"],
          f"{len(live_mv)} live rows == snapshot" if live_mv == snap["material_value"]
          else "live differs from snapshot")


def gate3_dashboard_sa(require):
    print("\n## Gate 3 — read-only dashboard SA can read sg_elv")
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{P}/datasets/{D}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {bq.token()}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        ds = json.load(r)
    entries = ds.get("access", [])
    hit = [e for e in entries if e.get("userByEmail", "").lower() == DASHBOARD_SA
           or DASHBOARD_SA in json.dumps(e).lower()]
    if hit:
        roles = [e.get("role") for e in hit]
        check("dashboard SA in dataset ACL", any(r in ("READER", "roles/bigquery.dataViewer") for r in roles),
              f"{DASHBOARD_SA} present with role(s) {roles}")
        print("  (jobUser at project level cannot be read from here — owner-confirmed; "
              "the live app will prove it end-to-end on first load)")
    elif require:
        check("dashboard SA in dataset ACL", False,
              f"{DASHBOARD_SA} NOT in sg_elv ACL — mint the SA and grant "
              "roles/bigquery.dataViewer on the dataset (README step 1)")
    else:
        print(f"- SKIPPED — {DASHBOARD_SA} not yet in the dataset ACL. Rerun with "
              "--require-sa after the owner mints and grants it.")


def main():
    require_sa = "--require-sa" in sys.argv
    print("# Checkpoint D deploy pre-flight\n")
    gate1_tables()
    gate2_snapshot()
    gate3_dashboard_sa(require_sa)
    print()
    if FAILURES:
        print(f"**RESULT: PRE-FLIGHT FAIL** — {FAILURES}")
        sys.exit(1)
    print("**RESULT: pre-flight PASS**"
          + ("" if require_sa else " (SA gate pending owner mint — rerun with --require-sa)"))


if __name__ == "__main__":
    main()
