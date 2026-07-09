#!/usr/bin/env python3
"""Part 1, landing stage — fetch raw sources to repo files, untouched.

Writes each HTTP response body EXACTLY as received to
    data/landing/<slug>/<UTC-timestamp>.json
and appends one provenance line per file to data/landing/manifest.jsonl:
    {"path", "source_url", "fetched_at_utc", "http_status", "sha256", "bytes"}

Nothing is parsed, filtered, or re-keyed here — cleaning happens downstream in
BigQuery so a parse bug costs a query, not a re-fetch (CLAUDE.md layer rules).

Sources (decision log, verified 2026-07-08):
  - 4 canonical LTA series from data.gov.sg (CKAN datastore_search, full table)
  - UN Comtrade HS 8703 exports, Singapore (702), annual, world aggregate
    (partnerCode=0), 2005-2025, qty + netWgt + FOB together (Comtrade load
    rules: qty unreliable, prefer net weight, flag partial years downstream)

Re-run: python3 scripts/fetch_landing.py   (adds new timestamped files; never
overwrites earlier fetches)
"""

import datetime
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "data", "landing")
MANIFEST = os.path.join(LANDING, "manifest.jsonl")
UA = {"User-Agent": "sg-elv-pipeline/1.0"}
PACE_SECONDS = 4

CKAN = "https://data.gov.sg/api/action/datastore_search"
SERIES = {  # slug -> resource id (CLAUDE.md canonical source ids)
    "new_registrations_monthly": "d_d94cf5d839fc11a144f24ef971705d3e",
    "deregistrations_monthly": "d_d520d6034b5e0c4f883b4e480de28f97",
    "population_vqs_monthly": "d_ede1a559013d10f234d209ac5e9fd9b4",
    "population_by_type_monthly": "d_206838bdc92c07ab495af49475563da5",
}

COMTRADE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
# The keyless preview endpoint rejects comma-joined periods (400) — one call
# per year. 2005+ matches the annual-API overlap span in the decision log.
COMTRADE_YEARS = [str(y) for y in range(2005, 2026)]


def fetch(url, tries=6):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, r.read()
        except Exception as e:
            err = e
            time.sleep(6 * (attempt + 1))  # data.gov.sg & Comtrade both 429 under burst
    raise RuntimeError(f"{url} failed after {tries} tries: {err}")


def land(slug, url, ext="json"):
    status, body = fetch(url)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    d = os.path.join(LANDING, slug)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{ts}.{ext}")
    with open(path, "wb") as f:
        f.write(body)
    rel = os.path.relpath(path, ROOT)
    entry = {
        "path": rel,
        "source_url": url,
        "fetched_at_utc": ts,
        "http_status": status,
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
    }
    with open(MANIFEST, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"landed {rel}  ({len(body):,} bytes, HTTP {status})")
    return path


def main(which="all"):
    os.makedirs(LANDING, exist_ok=True)
    if which in ("all", "ckan"):
        for slug, rid in SERIES.items():
            url = f"{CKAN}?{urllib.parse.urlencode({'resource_id': rid, 'limit': 10000})}"
            land(slug, url)
            time.sleep(PACE_SECONDS)
    if which not in ("all", "comtrade"):
        return
    for year in COMTRADE_YEARS:
        q = urllib.parse.urlencode({
            "reporterCode": 702, "period": year,
            "cmdCode": 8703, "flowCode": "X", "partnerCode": 0,
        })
        land(f"comtrade_hs8703_exports/{year}", f"{COMTRADE}?{q}")
        time.sleep(PACE_SECONDS)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
