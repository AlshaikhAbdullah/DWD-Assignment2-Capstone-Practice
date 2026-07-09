#!/usr/bin/env python3
"""Part 1, raw stage — load landed files into BigQuery raw_* tables, as-is.

One row per source record; the record itself is carried VERBATIM as a JSON
string in `raw_record` (BigQuery column names cannot start with a digit, so
the wide month columns like `2026Apr` cannot be literal columns — the JSON
payload keeps the source shape byte-faithful instead; the clean views parse
it). Suppressed cells ('-') and 'na' therefore arrive untouched and only
become NULL downstream in the clean layer (locked rule, 2026-07-08).

Provenance columns per row come from data/landing/manifest.jsonl.
Re-runnable: WRITE_TRUNCATE per table.
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bq_client as bq

ROOT = bq.ROOT
LANDING = os.path.join(ROOT, "data", "landing")

SERIES_TABLES = {
    "new_registrations_monthly": "raw_new_registrations_monthly",
    "deregistrations_monthly": "raw_deregistrations_monthly",
    "population_vqs_monthly": "raw_population_vqs_monthly",
    "population_by_type_monthly": "raw_population_by_type_monthly",
}

PROVENANCE_FIELDS = [
    {"name": "_resource_id", "type": "STRING"},
    {"name": "_source_url", "type": "STRING"},
    {"name": "_source_file", "type": "STRING"},
    {"name": "_fetched_at_utc", "type": "STRING"},
    {"name": "_sha256", "type": "STRING"},
    {"name": "_loaded_at", "type": "TIMESTAMP"},
]


def manifest_latest():
    """Latest manifest entry per landing directory."""
    latest = {}
    with open(os.path.join(LANDING, "manifest.jsonl")) as f:
        for line in f:
            e = json.loads(line)
            slug = os.path.dirname(e["path"]).replace("data/landing/", "")
            if slug not in latest or e["fetched_at_utc"] > latest[slug]["fetched_at_utc"]:
                latest[slug] = e
    return latest


def rid_from_url(url):
    return url.split("resource_id=")[1].split("&")[0] if "resource_id=" in url else None


def main():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    latest = manifest_latest()

    for slug, table in SERIES_TABLES.items():
        e = latest[slug]
        with open(os.path.join(ROOT, e["path"])) as f:
            payload = json.load(f)
        rows = [{
            "row_index": i,
            "raw_record": json.dumps(rec, ensure_ascii=False),
            "_resource_id": rid_from_url(e["source_url"]),
            "_source_url": e["source_url"],
            "_source_file": e["path"],
            "_fetched_at_utc": e["fetched_at_utc"],
            "_sha256": e["sha256"],
            "_loaded_at": now,
        } for i, rec in enumerate(payload["result"]["records"])]
        schema = ([{"name": "row_index", "type": "INTEGER"},
                   {"name": "raw_record", "type": "STRING"}] + PROVENANCE_FIELDS)
        bq.load_ndjson(table, schema, rows)
        print(f"loaded {bq.DATASET}.{table}: {len(rows)} rows from {e['path']}")

    # Comtrade: one row per landed year file, full response body verbatim.
    rows = []
    for slug, e in sorted(latest.items()):
        if not slug.startswith("comtrade_hs8703_exports/"):
            continue
        with open(os.path.join(ROOT, e["path"])) as f:
            body = f.read()
        rows.append({
            "year": int(slug.rsplit("/", 1)[1]),
            "raw_response": body,
            "_resource_id": None,
            "_source_url": e["source_url"],
            "_source_file": e["path"],
            "_fetched_at_utc": e["fetched_at_utc"],
            "_sha256": e["sha256"],
            "_loaded_at": now,
        })
    schema = ([{"name": "year", "type": "INTEGER"},
               {"name": "raw_response", "type": "STRING"}] + PROVENANCE_FIELDS)
    bq.load_ndjson("raw_comtrade_hs8703", schema, rows)
    print(f"loaded {bq.DATASET}.raw_comtrade_hs8703: {len(rows)} rows")


if __name__ == "__main__":
    main()
