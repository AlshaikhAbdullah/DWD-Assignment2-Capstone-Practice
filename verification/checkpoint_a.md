# Checkpoint A — Setup verification (status: **DONE, 3/3 checks passing**)

> Run `GCP_PROJECT=msbai-dwd-aa13072 python3 verification/checkpoint_a_checks.py` to
> reproduce. This file records the evidence honestly (rule 6: never fabricate).
> Nothing below is marked done unless it returned real output.

**Session date:** 2026-07-08 · **Environment:** Claude Code remote (managed container, egress via policy-enforcing proxy)

## The three verification prompts

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Run a BigQuery query in the project | **PASS** | `SELECT 1, CURRENT_TIMESTAMP()` → HTTP 200, `jobComplete`, job `location: US`, project `msbai-dwd-aa13072` |
| 2 | Create dataset + write one-row test table | **PASS** | `sg_elv` created (HTTP 200) with `location: US`; `sg_elv._setup_check` written and read back (HTTP 200) |
| 3 | Live data.gov.sg API call | **PASS** | `datastore_search` on verified resource `d_f52d6995ea85ad8d5088906d7a24d5df` → HTTP 200, `"success": true`, 1 real record returned |

## What unblocked it (diagnosis, not just a rerun)

1. **Egress policy** now allows `data.gov.sg`, `api-production.data.gov.sg`,
   `comtradeapi.un.org` (owner action, confirmed live this session).
2. **GCP credentials**: the encrypted service-account key
   `cloud-credentials.aa13072@stern.nyu.edu.enc` is committed at the repo root
   (AES-256-CBC/PBKDF2; passphrase in the `CLOUD_CREDENTIALS_KEY` env var).
   The check script now bootstraps itself: decrypt → mint an OAuth token via
   `verification/gcp_token.py` (stdlib + openssl, no SDK). The decrypted key
   only ever touches a temp file that is deleted afterwards. Service account:
   `claude-agent@msbai-dwd-aa13072.iam.gserviceaccount.com`.
3. **Two real bugs found in the first passing attempt** (rule 5 — diagnose
   before patching):
   - The script sent `Content-Type: application/json` on GET requests; CKAN
     answers that with **HTTP 422** "invalid JSON". Header is now only sent
     when there is a body.
   - The no-`resource_id` fallback for check 3 is no longer valid — the bare
     endpoint returns a plain-text 404, not a structured CKAN JSON error. The
     check now requires a real record from a **verified** resource id.
   - (Also removed: the fallback to `CLOUDSDK_AUTH_ACCESS_TOKEN`, which in this
     environment is a proxy placeholder that Google rejects with 401.)

## Verified data.gov.sg resource id (per brief: never assume, verify one)

The live catalog (`api-production.data.gov.sg/v2/public/api/datasets`, 4,422
datasets) has **no server-side search**; it was scanned page-by-page and
filtered for vehicle/LTA series. Verified with a real one-record fetch:

- `d_f52d6995ea85ad8d5088906d7a24d5df` — **New Registration of Motor Vehicles
  under Vehicle Quota System (VQS)** — fields `(year, category, number)`,
  first record `{year: 2005, category: "Category A", number: 68468}`.
  Note: this series is **annual by COE category** — the monthly, by-type
  series for `fact_vehicle_flows` still need grain checks at Checkpoint B.

Candidate series found in the same scan (**ids recorded, not yet verified** —
confirm grain + fetch a record before building on them at Checkpoint B):

| datasetId | Name |
|---|---|
| `d_d520d6034b5e0c4f883b4e480de28f97` | Motor Vehicles De-Registered Under Vehicle Quota System, Monthly |
| `d_206838bdc92c07ab495af49475563da5` | Motor Vehicle Population By Type Of Vehicle (End Of Period), Monthly |
| `d_2873f3b1b2a836103f51f696350b98fa` | Annual Motor Vehicle Population by Vehicle Type |
| `d_1332f905376c3848bdcc032423ca5563` | Motor Vehicles De-registered under Vehicle Quota System (VQS) |
| `d_69b3380ad7e51aff3a7dcc84eba52b8a` | COE Bidding Results / Prices |
| `d_2620d9f92656afc0f0a0f0ab2f320406` | Age Distribution of Motor Vehicles |
| `d_529752a3d78beb78bd4f38e3be37f1b6` | New Registration Of Motor Vehicles Under Vehicle Quota System, Monthly |
| `d_2ecb009f1e1ec5a816a454944dec4022` | Monthly Motor Vehicle Population by Vehicle Type |
| `d_5a32a72cbc741ecfda152c20677f0f3d` | Quarterly Deregistration of Vehicle Population |

Full scan output (80 vehicle/COE-related datasets, 0 failed pages out of 443):
`verification/datagov_vehicle_datasets.txt`.

## Teaching-team access & guardrails (as of 2026-07-08)

- **GitHub collaborators (verified via API):** `AlshaikhAbdullah` (admin),
  `it2190` (write — Ilias, it2190@stern.nyu.edu). **`pi1` is not yet in the
  collaborator list** — if the invite was sent, it is pending acceptance.
  Owner should confirm pi1@stern.nyu.edu accepts.
- **BigQuery Data Viewer grant:** owner confirms it is set. Cannot be verified
  from this session (Cloud Resource Manager API is disabled in the project, so
  `getIamPolicy` returns 403) — recorded as **owner-confirmed, unverified**.
- **$10 budget alert:** owner confirms it is on for `msbai-dwd-aa13072`.
  Billing API not accessible from this session — **owner-confirmed, unverified**.

## Raw check output (2026-07-08, exit code 0)

```
(gcp auth: minted from cloud-credentials.aa13072@stern.nyu.edu.enc)
[PASS] 1. BigQuery query runs in project
       query: SELECT 1 AS ok, CURRENT_TIMESTAMP() AS ts
       HTTP 200
       ... "jobReference": {"projectId": "msbai-dwd-aa13072",
                            "jobId": "job_puOzkqPyzv_BgcyEjeEetOCeuuwt",
                            "location": "US"} ...
[PASS] 2. Create dataset sg_elv + one-row test table
       dataset sg_elv: HTTP 200 (created)
       read-back: HTTP 200  (columns: ok INTEGER, note STRING, created_at TIMESTAMP)
[PASS] 3. data.gov.sg live API call
       GET https://data.gov.sg/api/action/datastore_search?resource_id=d_f52d6995ea85ad8d5088906d7a24d5df&limit=1
       HTTP 200
       {"success":true,"result":{...,"records":[{"_id":1,"year":"2005",
        "category":"Category A","number":"68468"}],...}}

3/3 checks passed.
exit code: 0
```

## Decisions recorded at this checkpoint

- **GCP project id** — DECIDED 2026-07-08: `msbai-dwd-aa13072` (reuse; new dataset `sg_elv`).
- **BigQuery dataset location** — DECIDED 2026-07-08: `US` (multi-region), confirmed
  at creation time (`"location": "US"` in both the dataset and the query jobs).
- **GCP auth pattern** — DECIDED 2026-07-08: encrypted SA key committed at repo
  root + `CLOUD_CREDENTIALS_KEY` passphrase in the environment; checks
  self-bootstrap. No plaintext key ever committed.
- **data.gov.sg resource ids** — one verified (above); remaining LTA series ids
  are recorded as *candidates* and must be verified (grain + record fetch)
  before Checkpoint B pipeline code.

## Next (blocked on owner)

Checkpoint A's done-condition is met. **No data loading until PR #1 is merged**
(rule 3: one checkpoint at a time). At Checkpoint B: verify the monthly series
resource ids, then land raw → clean → analysis-ready layers with stock-flow and
reconciliation evidence.
