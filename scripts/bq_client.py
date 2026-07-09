#!/usr/bin/env python3
"""Minimal BigQuery REST client (stdlib only) for the sg_elv pipeline.

Auth: decrypts the committed encrypted service-account key
(cloud-credentials.*.enc + CLOUD_CREDENTIALS_KEY) and mints an OAuth token via
verification/gcp_token.py — same bootstrap the Checkpoint A checks use.
"""

import glob
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.environ.get("GCP_PROJECT", "msbai-dwd-aa13072")
DATASET = "sg_elv"

_token_cache = None


def token():
    global _token_cache
    if _token_cache:
        return _token_cache
    if os.environ.get("GCP_ACCESS_TOKEN"):
        _token_cache = os.environ["GCP_ACCESS_TOKEN"]
        return _token_cache
    enc = glob.glob(os.path.join(ROOT, "cloud-credentials.*.enc"))[0]
    key_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    try:
        key_file.close()
        subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-salt",
             "-pass", "env:CLOUD_CREDENTIALS_KEY", "-in", enc, "-out", key_file.name],
            check=True, capture_output=True)
        out = subprocess.run(
            [sys.executable, os.path.join(ROOT, "verification", "gcp_token.py"),
             key_file.name], check=True, capture_output=True, text=True)
        _token_cache = out.stdout.strip()
        return _token_cache
    finally:
        os.unlink(key_file.name)


def _http(method, url, body, content_type="application/json"):
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token()}", "Content-Type": content_type})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def query(sql, timeout_ms=120000):
    """Run a query, return list of row dicts (schema-keyed, values as strings)."""
    res = _http("POST",
                f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}/queries",
                {"query": sql, "useLegacySql": False, "timeoutMs": timeout_ms})
    if not res.get("jobComplete"):
        raise RuntimeError(f"query did not complete: {res}")
    if "errors" in res:
        raise RuntimeError(f"query errors: {res['errors']}")
    fields = [f["name"] for f in res.get("schema", {}).get("fields", [])]
    return [dict(zip(fields, [c["v"] for c in row["f"]]))
            for row in res.get("rows", [])]


def load_ndjson(table, schema_fields, rows):
    """Multipart load job: WRITE_TRUNCATE NDJSON into DATASET.table."""
    config = {"configuration": {"load": {
        "destinationTable": {"projectId": PROJECT, "datasetId": DATASET, "tableId": table},
        "sourceFormat": "NEWLINE_DELIMITED_JSON",
        "writeDisposition": "WRITE_TRUNCATE",
        "schema": {"fields": schema_fields},
    }}}
    ndjson = "\n".join(json.dumps(r) for r in rows)
    boundary = "sg_elv_boundary_7391"
    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(config)}\r\n"
        f"--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n"
        f"{ndjson}\r\n--{boundary}--\r\n"
    ).encode()
    res = _http("POST",
                f"https://bigquery.googleapis.com/upload/bigquery/v2/projects/{PROJECT}/jobs?uploadType=multipart",
                body, content_type=f"multipart/related; boundary={boundary}")
    job_id = res["jobReference"]["jobId"]
    location = res["jobReference"]["location"]
    while True:
        st = _http("GET",
                   f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}/jobs/{job_id}?location={location}",
                   None)
        if st["status"]["state"] == "DONE":
            if "errorResult" in st["status"]:
                raise RuntimeError(f"load job failed: {st['status']}")
            return st
        time.sleep(2)
