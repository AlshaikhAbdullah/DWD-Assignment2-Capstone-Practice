#!/usr/bin/env python3
"""Checkpoint A verification prompts — re-runnable, no fabrication.

Runs the three setup checks from PROJECT_BRIEF.md Part 0:
  1. Run a real BigQuery query in the project.
  2. Create the `sg_elv` dataset and write a one-row test table, then read it back.
  3. Reach data.gov.sg with a real API call.

Prints PASS/FAIL per check with the raw evidence (HTTP status + response
excerpt). Exits non-zero if any check fails. No external dependencies —
stdlib only, so it runs anywhere Python 3 does.

Configuration (environment variables):
  GCP_PROJECT        required for checks 1-2 (BigQuery project id)
  GCP_ACCESS_TOKEN   OAuth token for BigQuery; falls back to
                     CLOUDSDK_AUTH_ACCESS_TOKEN if unset
  BQ_LOCATION        dataset location for check 2 (default: US — open
                     decision, see PR/issue; asia-southeast1 is the
                     Singapore region)
  DATAGOV_RESOURCE_ID  optional CKAN resource id; when set, check 3 also
                     fetches one real record from it (per the brief, we do
                     not assume resource ids — verify one, then set it)
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

RESULTS = []


def record(name, ok, evidence):
    RESULTS.append((name, ok, evidence))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    for line in evidence.splitlines():
        print(f"       {line}")


def http(method, url, token=None, body=None, timeout=60):
    """Return (status_code, response_text). Never raises."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:  # DNS, proxy CONNECT denial, timeout, TLS
        return None, f"{type(e).__name__}: {e}"


def bq_query(project, token, sql):
    status, text = http(
        "POST",
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{project}/queries",
        token=token,
        body={"query": sql, "useLegacySql": False},
    )
    return status, text


def check_1_bigquery_query(project, token):
    sql = "SELECT 1 AS ok, CURRENT_TIMESTAMP() AS ts"
    status, text = bq_query(project, token, sql)
    ok = status == 200 and '"jobComplete": true' in text.replace(": ", ": ")
    record(
        "1. BigQuery query runs in project",
        status == 200,
        f"query: {sql}\nHTTP {status}\n{text[:400]}",
    )
    return status == 200


def check_2_dataset_and_table(project, token, location):
    # Create dataset sg_elv (idempotent: 409 = already exists is fine).
    status, text = http(
        "POST",
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{project}/datasets",
        token=token,
        body={"datasetReference": {"projectId": project, "datasetId": "sg_elv"},
              "location": location},
    )
    if status not in (200, 409):
        record("2. Create dataset sg_elv + one-row test table",
               False, f"dataset create: HTTP {status}\n{text[:400]}")
        return False

    made = f"dataset sg_elv: HTTP {status} ({'created' if status == 200 else 'already existed'})"
    sql = ("CREATE OR REPLACE TABLE sg_elv._setup_check AS "
           "SELECT 1 AS ok, 'checkpoint A' AS note, CURRENT_TIMESTAMP() AS created_at")
    status, text = bq_query(project, token, sql)
    if status != 200:
        record("2. Create dataset sg_elv + one-row test table",
               False, f"{made}\ntable create: HTTP {status}\n{text[:400]}")
        return False

    status, text = bq_query(project, token, "SELECT * FROM sg_elv._setup_check")
    ok = status == 200
    record("2. Create dataset sg_elv + one-row test table",
           ok, f"{made}\nread-back: HTTP {status}\n{text[:400]}")
    return ok


def check_3_datagov_reach(resource_id):
    # Reachability first: the CKAN action endpoint must answer with JSON.
    # Without a resource id it returns a structured CKAN error — that still
    # proves the host is reachable and the API is alive.
    base = "https://data.gov.sg/api/action/datastore_search"
    url = base + (f"?resource_id={urllib.parse.quote(resource_id)}&limit=1"
                  if resource_id else "")
    status, text = http("GET", url)
    reachable = status is not None
    looks_json = reachable and text.lstrip().startswith("{")
    ok = reachable and (status == 200 if resource_id else looks_json)
    record(
        "3. data.gov.sg live API call",
        ok,
        f"GET {url}\nHTTP {status}\n{text[:400]}",
    )
    return ok


def main():
    project = os.environ.get("GCP_PROJECT")
    token = os.environ.get("GCP_ACCESS_TOKEN") or os.environ.get("CLOUDSDK_AUTH_ACCESS_TOKEN")
    location = os.environ.get("BQ_LOCATION", "US")
    resource_id = os.environ.get("DATAGOV_RESOURCE_ID")

    if not project:
        record("1. BigQuery query runs in project", False,
               "GCP_PROJECT not set — project id is an open decision in CLAUDE.md")
        record("2. Create dataset sg_elv + one-row test table", False,
               "GCP_PROJECT not set")
    elif not token:
        record("1. BigQuery query runs in project", False, "no GCP access token in environment")
        record("2. Create dataset sg_elv + one-row test table", False, "no GCP access token")
    else:
        check_1_bigquery_query(project, token)
        check_2_dataset_and_table(project, token, location)

    check_3_datagov_reach(resource_id)

    failed = [n for n, ok, _ in RESULTS if not ok]
    print()
    print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
