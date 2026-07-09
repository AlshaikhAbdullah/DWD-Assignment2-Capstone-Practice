#!/usr/bin/env python3
"""Layer 4 checks — scenario range integrity + input provenance enforcement.

Usage: python3 verification/material_value_checks.py > verification/layer4_material_value_checks.md
Exit 1 on any failure.
"""

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import bq_client as bq
from build_material_value import pink_sheet_annual_avg

P, D = bq.PROJECT, bq.DATASET
FAILURES = []


def check(name, ok, evidence):
    print(f"- {'PASS' if ok else '**FAIL**'} — {name}: {evidence}")
    if not ok:
        FAILURES.append(name)


def main():
    print("# Layer 4 — material-value scenario checks (live BigQuery + landed sources)\n")
    rows = bq.query(f"SELECT * FROM `{P}.{D}.elv_material_value` ORDER BY year, scrap_share, material")
    f = lambda r, k: float(r[k])

    check("row inventory: 2 years × scenarios × 3 materials, floor anchor 2024-only",
          len(rows) == 27
          and len([r for r in rows if r["year"] == "2023"]) == 12
          and len([r for r in rows if r["scrap_share_scenario"] == "floor_anchor_2024"]) == 3,
          f"{len(rows)} rows; 2023: {len([r for r in rows if r['year'] == '2023'])}; "
          f"floor-anchor rows: {[(r['year'], r['material']) for r in rows if r['scrap_share_scenario'] == 'floor_anchor_2024']}")

    # verified prices == landed Pink Sheet, re-derived independently right now
    xlsx = pink_sheet_annual_avg()
    bad = [r for r in rows if r["price_verification"] == "verified"
           and abs(f(r, "price_usd_per_tonne_mid") - xlsx[(r["material"], int(r["year"]))]) > 0.01]
    n_verified = sum(r["price_verification"] == "verified" for r in rows)
    check("every 'verified' price equals the landed World Bank Pink Sheet annual mean",
          not bad and n_verified == 18,
          f"{n_verified} verified price cells (Al/Cu × 2 years × scenarios); mismatches: {len(bad)}; "
          f"Pink Sheet: {[(k, v) for k, v in sorted(xlsx.items())]}")

    steel = {r["price_verification"] for r in rows if r["material"] == "steel"}
    check("steel price labeled unverified (no reachable source)", steel == {"unverified"}, f"{steel}")

    unv = [r for r in rows if r["weight_verification"] != "literature_cited_geo_transfer"
           or r["fraction_verification"] != "literature_cited_geo_transfer"]
    check("curb weight and material fractions labeled literature_cited_geo_transfer everywhere",
          not unv, "US/global auto averages transferred to SG fleet (modeled geographic "
          f"transfer; sources: steelonthenet, Aluminum Association/Ducker, CAR); {len(unv)} rows missing the label")

    bad = [r for r in rows if not (f(r, "value_usd_low") < f(r, "value_usd_mid") < f(r, "value_usd_high"))]
    check("strict band ordering low < mid < high in every row (no point estimates)",
          not bad, f"{len(bad)} degenerate bands")

    tiers = {r["confidence_tier"] for r in rows}
    check("single confidence tier: scenario_range_unverified_inputs",
          tiers == {"scenario_range_unverified_inputs"}, f"{tiers}")

    # formula reproduction from the provenance CSV, independent of the builder
    with open(os.path.join(ROOT, "data", "reference", "material_value_inputs.csv")) as fh:
        inputs = list(csv.DictReader(fh))
    weight = next(r for r in inputs if r["parameter"] == "curb_weight_t")
    frac = {r["material"]: r for r in inputs if r["parameter"] == "material_fraction"}
    price = {(r["material"], r["year"]): r for r in inputs if r["parameter"] == "price_usd_per_tonne"}
    mism = 0
    for r in rows:
        want = round(f(r, "deregistrations_cars_verified") * f(r, "scrap_share")
                     * float(weight["mid"]) * float(frac[r["material"]]["mid"])
                     * float(price[(r["material"], r["year"])]["mid"]))
        if want != int(r["value_usd_mid"]):
            mism += 1
    check("value_usd_mid reproduces from the provenance CSV for all 27 rows",
          mism == 0, f"{mism} mismatches (formula: dereg × share × weight × fraction × price)")

    anchor = next(r for r in rows if r["scrap_share_scenario"] == "floor_anchor_2024"
                  and r["material"] == "steel")
    floor = bq.query(f"""SELECT ROUND(scrapped_est_residual / deregistrations_total, 4) AS s
                         FROM `{P}.{D}.elv_disposal_split` WHERE year = 2024""")[0]["s"]
    check("floor anchor share ties to elv_disposal_split 2024 lower bound",
          abs(f(anchor, "scrap_share") - float(floor)) < 0.0001,
          f"anchor {anchor['scrap_share']} == split residual share {floor} "
          "(a LOWER-bound anchor inside the band, not the tonnage)")

    dereg = {r["y"]: r["n"] for r in bq.query(f"""
        SELECT CAST(year AS STRING) y, CAST(deregistrations_total AS STRING) n
        FROM `{P}.{D}.elv_disposal_split` WHERE year IN (2023, 2024)""")}
    bad = [r for r in rows if r["deregistrations_cars_verified"] != dereg[r["year"]]]
    check("the one verified factor (car deregistrations) ties to the fact layer",
          not bad, f"2023={dereg['2023']}, 2024={dereg['2024']}; mismatching rows: {len(bad)}")

    print()
    if FAILURES:
        print(f"**RESULT: FAIL** — {FAILURES}")
        sys.exit(1)
    print("**RESULT: all Layer 4 scenario checks PASS**")


if __name__ == "__main__":
    main()
