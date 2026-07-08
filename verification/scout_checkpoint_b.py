#!/usr/bin/env python3
"""Checkpoint B scouting — read-only probes of candidate data.gov.sg series.

Loads NOTHING anywhere. For each candidate resource id this fetches a bounded
sample via CKAN `datastore_search` (in memory only) and reports:
  - resolves? (HTTP 200 + success:true)
  - columns (name + CKAN type)
  - total row count (CKAN `result.total`)
  - time coverage (min/max of the detected time field)
  - distinct values of low-cardinality text fields (the grain, in practice)
  - whether anything in columns or values mentions export / scrap / disposal
    (the headline question: does LTA publish the ELV disposal split?)

Sample is capped at SAMPLE_LIMIT rows per series; when total > cap the
coverage line says so. Re-run: python3 verification/scout_checkpoint_b.py
"""

import json
import re
import time
import urllib.parse
import urllib.request

SAMPLE_LIMIT = 5000
PACE_SECONDS = 4          # rest between datasets — the API 429s under bursts
WIDE_COL = re.compile(r"^\d{4}[A-Z][a-z]{2}$")  # SingStat wide format: 2026Jan
SPLIT_WORDS = ("export", "scrap", "disposal", "dispose", "demolish")

# (id, name) — the registration / deregistration / population candidates from
# verification/datagov_vehicle_datasets.txt (full-catalog scan, 2026-07-08).
CANDIDATES = [
    ("d_529752a3d78beb78bd4f38e3be37f1b6", "New Registration Of Motor Vehicles Under VQS, Monthly"),
    ("d_d94cf5d839fc11a144f24ef971705d3e", "New Registration Of Motor Vehicles Under VQS , Monthly (dup?)"),
    ("d_06c3969c73ac5ba2d059cf39491ce048", "New Registration of Motor Vehicles Under VQS"),
    ("d_f52d6995ea85ad8d5088906d7a24d5df", "New Registration of Motor Vehicles under VQS (verified CP A)"),
    ("d_f8408eaf8ecf45adae760a035b8d850d", "Quarterly New Registration of Vehicle Population"),
    ("d_d520d6034b5e0c4f883b4e480de28f97", "Motor Vehicles De-Registered Under VQS, Monthly"),
    ("d_1332f905376c3848bdcc032423ca5563", "Motor Vehicles De-registered under VQS"),
    ("d_6e50d957520951abb4083d2b2bd0ae90", "Motor Vehicle De-registration under VQS"),
    ("d_5a32a72cbc741ecfda152c20677f0f3d", "Quarterly Deregistration of Vehicle Population"),
    ("d_2ecb009f1e1ec5a816a454944dec4022", "Monthly Motor Vehicle Population by Vehicle Type"),
    ("d_206838bdc92c07ab495af49475563da5", "Motor Vehicle Population By Type Of Vehicle (End Of Period), Monthly"),
    ("d_aa457c0abaacccefd238c31cfed211d9", "Motor Vehicle Population By Type Of Vehicle (End Of Period), Annual"),
    ("d_2873f3b1b2a836103f51f696350b98fa", "Annual Motor Vehicle Population by Vehicle Type"),
    ("d_ede1a559013d10f234d209ac5e9fd9b4", "Motor Vehicle Population Under VQS (End Of Period), Monthly"),
    ("d_cc30f50369bcd6b6f848a586bded2290", "Annual Motor Vehicle Population by Vehicle Quota Categories"),
    ("d_f8876e8c0959ba5bcfa2c40cf6d25dab", "Motor Vehicle Population under VQS"),
]

TIME_FIELD_HINTS = ("month", "year", "quarter", "date", "period")


def fetch(resource_id, limit, tries=5):
    url = ("https://data.gov.sg/api/action/datastore_search?"
           + urllib.parse.urlencode({"resource_id": resource_id, "limit": limit}))
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": "sg-elv-checkpoint/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, json.load(r)
        except Exception as e:
            err = {"error": f"{type(e).__name__}: {e}"}
            if attempt < tries - 1:
                time.sleep(5 * (attempt + 1))   # 429s clear within seconds
    return None, err


def probe(rid, name):
    print(f"\n### {name}\n`{rid}`")
    status, payload = fetch(rid, SAMPLE_LIMIT)
    if status != 200 or not payload.get("success"):
        print(f"- **UNRESOLVED** — HTTP {status}: {str(payload)[:200]}")
        return
    res = payload["result"]
    fields = [(f["id"], f["type"]) for f in res["fields"] if f["id"] != "_id"]
    records = res["records"]
    total = res.get("total", "n/a")
    print(f"- resolves: yes · total rows: **{total}** · sampled: {len(records)}"
          + (" (FULL)" if isinstance(total, int) and total <= len(records) else " (partial sample)"))

    months = {m: i for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
    wide_cols = sorted((n for n, _ in fields if WIDE_COL.match(n)),
                       key=lambda c: (int(c[:4]), months[c[4:]]))
    if wide_cols:
        narrow = [(n, t) for n, t in fields if n not in wide_cols]
        print(f"- **WIDE format**: {len(wide_cols)} month columns "
              f"{wide_cols[0]} → {wide_cols[-1]}; other columns: "
              + ", ".join(f"`{n}` ({t})" for n, t in narrow))
        fields = narrow
    else:
        print(f"- columns: {', '.join(f'`{n}` ({t})' for n, t in fields)}")

    time_fields = [n for n, _ in fields if any(h in n.lower() for h in TIME_FIELD_HINTS)]
    for tf in time_fields:
        vals = sorted({r[tf] for r in records if r.get(tf) is not None})
        if vals:
            print(f"- `{tf}` coverage in sample: {vals[0]} → {vals[-1]} ({len(vals)} distinct)")

    hits = []
    for n, t in fields:
        if any(w in n.lower() for w in SPLIT_WORDS):
            hits.append(f"column `{n}`")
        vals = {str(r.get(n)) for r in records}
        if t == "text" and len(vals) <= 40 and n not in time_fields:
            print(f"- distinct `{n}` values ({len(vals)}): {sorted(vals)}")
        for v in vals:
            if any(w in v.lower() for w in SPLIT_WORDS):
                hits.append(f"value {v!r} in `{n}`")
    uniq = sorted(set(hits))
    print(f"- export/scrap/disposal signal: {uniq if uniq else '**NONE found**'}")


def main():
    print("# Checkpoint B scouting probe output (read-only, nothing loaded)")
    for rid, name in CANDIDATES:
        probe(rid, name)
        time.sleep(PACE_SECONDS)


if __name__ == "__main__":
    main()
