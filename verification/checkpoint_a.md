# Checkpoint A — Setup verification (status: BLOCKED, 0/3 checks passing)

> Run `python3 verification/checkpoint_a_checks.py` to reproduce. This file records
> the current evidence honestly (rule 6: never fabricate). Nothing below is marked
> done unless it returned real output.

**Session date:** 2026-07-08 · **Environment:** Claude Code remote (managed container, egress via policy-enforcing proxy)

## The three verification prompts

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Run a BigQuery query in the project | **FAIL — blocked** | No project id set (`CLAUDE.md` still reads `<reuse msbai-... or set here>`) and no valid GCP credential in the session (see audit below) |
| 2 | Create dataset + write one-row test table | **FAIL — blocked** | Same blockers as #1 |
| 3 | Live data.gov.sg API call | **FAIL — blocked** | `GET https://data.gov.sg/api/action/datastore_search` → proxy CONNECT denied: `403 Forbidden`. Proxy status log: `"gateway answered 403 to CONNECT (policy denial or upstream failure)", host: "data.gov.sg:443"` |

## Environment audit (what was actually found)

**GCP credentials — not working.**
- `gcloud` / `bq` CLIs are not installed; checks use the BigQuery REST API (stdlib only).
- `CLOUDSDK_AUTH_ACCESS_TOKEN` is set but is a 14-char `proxy-…` placeholder. The session
  proxy is expected to substitute a real credential; a direct call to
  `bigquery.googleapis.com/bigquery/v2/projects` returned a genuine Google
  `401 UNAUTHENTICATED "Invalid Credentials"` — so **no real GCP credential is attached
  to this environment**.
- `CLOUD_CREDENTIALS_KEY` is set but is only **8 characters** — consistent with a
  decryption passphrase for an encrypted service-account key (cloud-bootstrap pattern),
  but **no encrypted key file is committed in this repo**, so there is nothing to decrypt.
- Positive finding: `googleapis.com` **is allowed** by the egress policy (the request
  reached Google and failed on auth, not on policy). Once credentials exist, checks 1–2
  should pass with no network-policy change.

**data.gov.sg — blocked by egress policy, not by the source.**
- The organization/network policy for this session denies `data.gov.sg:443` at the proxy
  (403 on CONNECT). Per proxy guidance, policy denials must be reported, not routed
  around. The source itself was never reached, so its availability is **unverified**.

**Teaching-team access — unverifiable from this session.**
- GitHub: the integration token cannot list collaborators
  (`403 Resource not accessible by integration`), so whether pi1@stern.nyu.edu and
  it2190@stern.nyu.edu are collaborators is **unverified**. Owner must confirm in
  repo Settings → Collaborators.
- BigQuery Data Viewer IAM grant: cannot be verified until GCP access works.

**Budget alert ($10):** cannot be verified without GCP access. **Unverified.**

## What unblocks this (owner actions — Abdullah)

1. **Set the GCP project id** in `CLAUDE.md` (currently `<reuse msbai-... or set here>`).
2. **Attach working GCP credentials** to the Claude Code environment — either connect the
   GCP integration for this environment, or run cloud-bootstrap and commit the encrypted
   service-account key that `CLOUD_CREDENTIALS_KEY` decrypts (key file is currently
   missing from the repo). Minimum roles: BigQuery dataset/table write in the project.
3. **Allow `data.gov.sg` in the environment's network policy** (Claude Code environment
   settings → network access). While there, also allow the other planned sources so
   Checkpoint B doesn't hit the same wall: `comtradeapi.un.org` (UN Comtrade) and the
   LME price source (TBD).
4. **Confirm teaching-team grants** (GitHub collaborators + BigQuery Data Viewer) —
   owner-only actions.
5. Re-run `python3 verification/checkpoint_a_checks.py` with `GCP_PROJECT` set; commit
   the passing output to this file. Checkpoint A is done only when it prints 3/3.

## Raw check output (2026-07-08)

```
[FAIL] 1. BigQuery query runs in project
       GCP_PROJECT not set — project id is an open decision in CLAUDE.md
[FAIL] 2. Create dataset sg_elv + one-row test table
       GCP_PROJECT not set
[FAIL] 3. data.gov.sg live API call
       GET https://data.gov.sg/api/action/datastore_search
       HTTP None
       URLError: <urlopen error Tunnel connection failed: 403 Forbidden>

0/3 checks passed.
exit code: 1
```

## Open questions surfaced by this checkpoint (decisions for the tech lead)

- **GCP project id** — which project? (`msbai-…` reuse vs. fresh.)
- **BigQuery dataset location** — `US` (default) vs. `asia-southeast1` (Singapore).
  The check script defaults to `US` via `BQ_LOCATION`; this should be decided before
  the dataset is created, because location cannot be changed later.
- **data.gov.sg resource ids** — deliberately not assumed (per PROJECT_BRIEF §3). Once
  the host is reachable, verify the exact resource ids for the three LTA series and
  record them in `CLAUDE.md` before any pipeline code.
