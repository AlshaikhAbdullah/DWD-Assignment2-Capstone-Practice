#!/usr/bin/env python3
"""Layer 4 — elv_material_value as a SCENARIO RANGE, never a point estimate.

Formula (approved 2026-07-09):
  value = scrap_share(scenario) x car_deregistrations(year, VERIFIED)
          x curb_weight (modeled) x material_fraction (modeled)
          x price (verified for Al/Cu from the landed World Bank CMO Pink
            Sheet; steel scrap unverified placeholder)

Every factor except the deregistration count comes from
data/reference/material_value_inputs.csv, which carries per-input provenance
and verification_status. Output grain: (year, scrap_share_scenario, material)
with LOW/MID/HIGH bands (low = all-low inputs, high = all-high — a
deliberately wide, honest band). The 2024 disposal-split floor (share 0.0379)
is one anchor scenario INSIDE the band, not the tonnage.

Years: 2023, 2024 — the years with verified prices (the landed Pink Sheet
vintage ends 2024M12) and the Comtrade cross-check window.

Aluminum/copper prices are re-derived from the landed XLSX at build time (no
hand-typed numbers reach the table without the CSV provenance row agreeing —
the check suite enforces CSV == XLSX).
"""

import csv
import os
import re
import statistics
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bq_client as bq

P, D = bq.PROJECT, bq.DATASET
ROOT = bq.ROOT
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def pink_sheet_annual_avg():
    """(material, year) -> annual mean USD/t from the landed Pink Sheet."""
    d = os.path.join(ROOT, "data", "landing", "worldbank_cmo_pink_sheet")
    path = os.path.join(d, sorted(os.listdir(d))[-1])
    z = zipfile.ZipFile(path)
    shared = ["".join(t.text or "" for t in e.iter(f"{NS}t"))
              for e in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{NS}si")]
    root = ET.fromstring(z.read("xl/worksheets/sheet2.xml"))  # "Monthly Prices"

    def val(c):
        v = c.findtext(f"{NS}v")
        if v is None:
            return None
        return shared[int(v)] if c.get("t") == "s" else v

    rows = {}
    for row in root.iter(f"{NS}row"):
        rows[int(row.get("r"))] = {
            re.match(r"([A-Z]+)", c.get("r")).group(1): val(c) for c in row.iter(f"{NS}c")}
    cols = {v: k for k, v in rows[5].items() if v}
    out = {}
    for wb_name, material in (("Aluminum", "aluminium"), ("Copper", "copper")):
        col = cols[wb_name]
        for year in ("2023", "2024"):
            vals = [float(rows[r][col]) for r in rows
                    if (rows[r].get("A") or "").startswith(year + "M")
                    and rows[r].get(col) not in (None, "…")]
            assert len(vals) == 12, f"{wb_name} {year}: {len(vals)} months"
            out[(material, int(year))] = round(statistics.mean(vals), 2)
    return out


def load_inputs():
    with open(os.path.join(ROOT, "data", "reference", "material_value_inputs.csv")) as f:
        return list(csv.DictReader(f))


def main():
    inputs = load_inputs()
    xlsx_prices = pink_sheet_annual_avg()

    # provenance gate: the CSV's verified price rows must equal the landed file
    for row in inputs:
        if row["parameter"] == "price_usd_per_tonne" and row["verification_status"] == "verified":
            key = (row["material"], int(row["year"]))
            assert abs(float(row["mid"]) - xlsx_prices[key]) < 0.01, \
                f"CSV price {row} != landed Pink Sheet {xlsx_prices[key]}"

    dereg = {int(r["y"]): int(r["n"]) for r in bq.query(f"""
        SELECT EXTRACT(YEAR FROM month) AS y, CAST(SUM(deregistrations) AS INT64) AS n
        FROM `{P}.{D}.fact_vehicle_flows`
        WHERE is_car_scope AND EXTRACT(YEAR FROM month) IN (2023, 2024)
        GROUP BY y""")}

    scenarios = [(r["parameter"].replace("scrap_share_", ""), float(r["mid"]), r["verification_status"], r["year"])
                 for r in inputs if r["parameter"].startswith("scrap_share_")]
    weight = next(r for r in inputs if r["parameter"] == "curb_weight_t")
    fractions = {r["material"]: r for r in inputs if r["parameter"] == "material_fraction"}
    prices = {(r["material"], int(r["year"])): r for r in inputs
              if r["parameter"] == "price_usd_per_tonne"}

    values = []
    for year in (2023, 2024):
        for scen_name, share, share_status, scen_year in scenarios:
            if scen_year not in ("all", str(year)):
                continue  # the 2024 floor anchor applies to 2024 only
            for material, frac in fractions.items():
                price = prices[(material, year)]
                def band(k):
                    return round(dereg[year] * share * float(weight[k])
                                 * float(frac[k]) * float(price[k]))
                values.append({
                    "year": year, "scrap_share_scenario": scen_name,
                    "scrap_share": share, "scrap_share_status": share_status,
                    "material": material,
                    "deregistrations_cars_verified": dereg[year],
                    "tonnes_low": round(dereg[year] * share * float(weight["low"]) * float(frac["low"])),
                    "tonnes_mid": round(dereg[year] * share * float(weight["mid"]) * float(frac["mid"])),
                    "tonnes_high": round(dereg[year] * share * float(weight["high"]) * float(frac["high"])),
                    "price_usd_per_tonne_mid": float(price["mid"]),
                    "price_verification": price["verification_status"],
                    "value_usd_low": band("low"),
                    "value_usd_mid": band("mid"),
                    "value_usd_high": band("high"),
                    "weight_verification": weight["verification_status"],
                    "fraction_verification": frac["verification_status"],
                    "confidence_tier": "scenario_range_unverified_inputs",
                })

    schema = [{"name": n, "type": t} for n, t in [
        ("year", "INTEGER"), ("scrap_share_scenario", "STRING"),
        ("scrap_share", "FLOAT"), ("scrap_share_status", "STRING"),
        ("material", "STRING"), ("deregistrations_cars_verified", "INTEGER"),
        ("tonnes_low", "INTEGER"), ("tonnes_mid", "INTEGER"), ("tonnes_high", "INTEGER"),
        ("price_usd_per_tonne_mid", "FLOAT"), ("price_verification", "STRING"),
        ("value_usd_low", "INTEGER"), ("value_usd_mid", "INTEGER"), ("value_usd_high", "INTEGER"),
        ("weight_verification", "STRING"), ("fraction_verification", "STRING"),
        ("confidence_tier", "STRING")]]
    bq.load_ndjson("elv_material_value", schema, values)
    print(f"built {D}.elv_material_value: {len(values)} rows "
          f"(2 years x scenarios x 3 materials; scenario range, no point estimates)")


if __name__ == "__main__":
    main()
