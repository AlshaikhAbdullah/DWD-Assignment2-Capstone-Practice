#!/usr/bin/env python3
"""Mint a GCP OAuth2 access token from a service-account key file.

Stdlib + the `openssl` binary only (no google-auth dependency), so it runs in
any container. Used by checkpoint checks:

    export GCP_ACCESS_TOKEN=$(python3 verification/gcp_token.py /path/to/sa-key.json)

The key file itself is never committed — only the encrypted blob at the repo
root (`cloud-credentials.<email>.enc`, AES-256-CBC/PBKDF2, passphrase in the
CLOUD_CREDENTIALS_KEY env var):

    openssl enc -d -aes-256-cbc -pbkdf2 -salt -pass env:CLOUD_CREDENTIALS_KEY \
        -in cloud-credentials.<email>.enc -out /tmp/sa-key.json
"""

import base64
import json
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import time


def b64url(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def main(key_path: str) -> None:
    with open(key_path) as f:
        key = json.load(f)

    now = int(time.time())
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = b64url(json.dumps({
        "iss": key["client_email"],
        "scope": "https://www.googleapis.com/auth/bigquery https://www.googleapis.com/auth/cloud-platform",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }).encode())
    signing_input = header + b"." + claims

    with tempfile.NamedTemporaryFile("w", suffix=".pem") as pem:
        pem.write(key["private_key"])
        pem.flush()
        sig = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", pem.name],
            input=signing_input, capture_output=True, check=True,
        ).stdout

    jwt = (signing_input + b"." + b64url(sig)).decode()
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt,
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        token = json.loads(resp.read())["access_token"]
    print(token)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: gcp_token.py <service-account-key.json>")
    main(sys.argv[1])
