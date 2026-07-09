"""Data loading for the dashboard.

Primary path (Streamlit Community Cloud): read the analysis-ready tables live
from BigQuery using a READ-ONLY service account supplied via st.secrets
["gcp_service_account"], cached with @st.cache_data. The SA key is never
committed to the repo.

Fallback path (no secrets / offline / the pre-deploy scan): load the committed
dashboard/snapshot.json, which was generated from the same BigQuery tables by
scripts/build_dashboard_snapshot.py. The factor block lets the value band be
computed for any slider position with the committed formula.
"""

import json
import os

SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshot.json")
PROJECT = "msbai-dwd-aa13072"
DATASET = "sg_elv"


def load_snapshot():
    with open(SNAPSHOT) as f:
        return json.load(f)


def _bq_live(secrets):
    """Live read via google-cloud-bigquery from a read-only SA in st.secrets.
    Returns a snapshot-shaped dict so content.py is source-agnostic."""
    from google.cloud import bigquery
    from google.oauth2 import service_account

    info = dict(secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/bigquery.readonly"])
    client = bigquery.Client(project=PROJECT, credentials=creds)

    def q(sql):
        return [dict(r) for r in client.query(sql).result()]

    P, D = PROJECT, DATASET
    data = {}
    data["yearly_flows"] = q(f"""
        SELECT CAST(EXTRACT(YEAR FROM month) AS STRING) year,
          CAST(SUM(deregistrations) AS INT64) car_deregistrations,
          CAST(SUM(new_registrations) AS INT64) car_new_registrations
        FROM `{P}.{D}.fact_vehicle_flows`
        WHERE is_car_scope AND EXTRACT(YEAR FROM month) <= 2025
        GROUP BY year ORDER BY year""")
    data["monthly_car_dereg"] = q(f"""
        SELECT CAST(month AS STRING) month,
          CAST(SUM(deregistrations) AS INT64) car_deregistrations
        FROM `{P}.{D}.fact_vehicle_flows`
        WHERE is_car_scope GROUP BY month ORDER BY month""")
    data["disposal_split"] = q(f"""
        SELECT CAST(year AS STRING) year, deregistrations_total,
          exported_units_comtrade, scrapped_est_residual,
          CAST(export_proxy_ratio AS STRING) export_proxy_ratio,
          proxy_exceeds_deregistrations, scrapped_bound_direction,
          export_bound_direction, method, confidence_tier
        FROM `{P}.{D}.elv_disposal_split` ORDER BY year""")
    # factors + reconciliation are stable inputs — reuse the committed snapshot
    snap = load_snapshot()
    data["factors"] = snap["factors"]
    data["reconciliation"] = snap["reconciliation"]
    data["floor_anchor_share_2024"] = snap["floor_anchor_share_2024"]
    # normalise ints stored as strings for content.py
    for r in data["disposal_split"]:
        for k in ("deregistrations_total", "exported_units_comtrade", "scrapped_est_residual"):
            if r[k] is not None:
                r[k] = int(r[k])
    return data


def load(st=None):
    """Return the dashboard data dict. If Streamlit + secrets are present, read
    BigQuery live (cached); otherwise fall back to the committed snapshot."""
    if st is not None:
        try:
            if "gcp_service_account" in st.secrets:
                return _bq_live(st.secrets)
        except Exception as e:  # missing secrets, network, lib — degrade gracefully
            st.warning(f"Live BigQuery unavailable ({type(e).__name__}); "
                       "showing the committed snapshot.")
    return load_snapshot()
