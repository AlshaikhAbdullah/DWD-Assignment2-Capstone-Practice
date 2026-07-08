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
  GCP_ACCESS_TOKEN   OAuth token for BigQuery. If unset, the script
                     bootstraps one from the encrypted service-account key
                     committed at the repo root (cloud-credentials.*.enc,
                     passphrase in CLOUD_CREDENTIALS_KEY) via gcp_token.py.
  BQ_LOCATION        dataset location for check 2 (default: US —
                     DECIDED 2026-07-08, see verification/checkpoint_a.md)
  DATAGOV_RESOURCE_ID  CKAN resource id for check 3; defaults to the LTA
                     monthly-new-registrations dataset id verified live on
                     2026-07-08 (see checkpoint_a.md). Check 3 fetches one
                     real record from it.
"""

import glob
import json
import os
import subprocess
import sys
import tempfile
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
    # Only declare a JSON body when there is one: CKAN answers a bare GET
    # carrying "Content-Type: application/json" with 422 invalid-JSON.
    headers = {"User-Agent": "sg-elv-checkpoint/1.0"}
    if body is not None:
        headers["Content-Type"] = "application/json"
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


def bootstrap_gcp_token():
    """Mint an OAuth token from the encrypted service-account key committed at
    the repo root. Returns (token_or_None, how) — never raises, never writes
    the decrypted key anywhere but a temp file that is removed afterwards."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    enc_files = glob.glob(os.path.join(repo_root, "cloud-credentials.*.enc"))
    if not enc_files:
        return None, "no cloud-credentials.*.enc at repo root"
    if not os.environ.get("CLOUD_CREDENTIALS_KEY"):
        return None, "CLOUD_CREDENTIALS_KEY not set"
    key_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    try:
        key_file.close()
        dec = subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-salt",
             "-pass", "env:CLOUD_CREDENTIALS_KEY",
             "-in", enc_files[0], "-out", key_file.name],
            capture_output=True, text=True)
        if dec.returncode != 0:
            return None, f"decrypt failed: {dec.stderr.strip()[:200]}"
        mint = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "gcp_token.py"),
             key_file.name],
            capture_output=True, text=True)
        if mint.returncode != 0:
            return None, f"token mint failed: {mint.stderr.strip()[:200]}"
        return mint.stdout.strip(), f"minted from {os.path.basename(enc_files[0])}"
    finally:
        os.unlink(key_file.name)


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


# LTA "New Registration of Motor Vehicles under Vehicle Quota System (VQS)".
# Found by scanning the live api-production.data.gov.sg catalog and verified
# with a real datastore_search call on 2026-07-08 (see checkpoint_a.md).
DEFAULT_RESOURCE_ID = "d_f52d6995ea85ad8d5088906d7a24d5df"


def check_3_datagov_reach(resource_id):
    # A real datastore_search against a verified resource id: must return
    # HTTP 200, CKAN "success": true, and at least one record.
    url = ("https://data.gov.sg/api/action/datastore_search"
           f"?resource_id={urllib.parse.quote(resource_id)}&limit=1")
    status, text = http("GET", url)
    got_record = False
    if status == 200:
        try:
            payload = json.loads(text)
            got_record = (payload.get("success") is True
                          and len(payload["result"]["records"]) >= 1)
        except (ValueError, KeyError, TypeError):
            pass
    record(
        "3. data.gov.sg live API call",
        got_record,
        f"GET {url}\nHTTP {status}\n{text[:400]}",
    )
    return got_record


def main():
    project = os.environ.get("GCP_PROJECT")
    token = os.environ.get("GCP_ACCESS_TOKEN")
    location = os.environ.get("BQ_LOCATION", "US")
    resource_id = os.environ.get("DATAGOV_RESOURCE_ID", DEFAULT_RESOURCE_ID)

    if not token:
        token, how = bootstrap_gcp_token()
        print(f"(gcp auth: {how})")

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
