"""Singapore ELV — end-of-life vehicle data product (Checkpoint D artifact).

Page order is fixed by narrative_outline.md: Act 1 (verified ELV-generation
headline + 77/77 trust strip) → Act 2 (the honest export/scrap gap) → Act 3
(the illustrative value band, last). Every rendered claim string comes from
dashboard/content.py, whose functions are also exercised by
verification/predeploy_scan.py against the "numbers that must NOT appear" list.
"""

import pandas as pd
import streamlit as st

import content
import data_source

st.set_page_config(page_title="Singapore ELV — where cars go to die",
                   page_icon="🚗", layout="wide")


@st.cache_data(ttl=3600)
def load_data():
    return data_source.load(st)


data = load_data()

st.title("🚗 The Global ELV Recycling Gap — Singapore pilot")
st.caption("Vehicles reach end-of-life where they are *used*, not where they "
           "were produced. Singapore, with world-class open data, still can't "
           "fully see where its end-of-life cars go — which is the point.")

LEGEND = ("**Confidence legend:** ✅ verified · 📚 literature-cited · "
          "🌍 literature-cited (US/global→SG transfer) · "
          "⬇️ derived lower bound · 🎚️ assumed (scenario axis) · ⚠️ unverified")
st.caption(LEGEND)

# ============================================================ ACT 1
a1 = content.act1_headline(data)
st.header(f"1 · {a1['title']}")
st.markdown(a1["lead"], unsafe_allow_html=True)
st.success(a1["trust_strip"])

yf = pd.DataFrame(data["yearly_flows"])
yf["year"] = yf["year"].astype(int)
yf["car_deregistrations"] = pd.to_numeric(yf["car_deregistrations"], errors="coerce")
yf = yf.dropna(subset=["car_deregistrations"])
c1, c2 = st.columns([3, 2])
with c1:
    st.markdown("**Cars reaching end-of-life each year** (deregistrations, "
                "COE Cat A + B, 1990–2025)")
    st.bar_chart(yf.set_index("year")["car_deregistrations"], height=320)
with c2:
    st.markdown("**The COE ~10-year heartbeat** (monthly car deregistrations)")
    md = pd.DataFrame(data["monthly_car_dereg"])
    md["month"] = pd.to_datetime(md["month"])
    md["car_deregistrations"] = pd.to_numeric(md["car_deregistrations"], errors="coerce")
    md = md.dropna(subset=["car_deregistrations"])  # 2026-05: pop exists, dereg not yet
    st.line_chart(md.set_index("month")["car_deregistrations"], height=320)
st.caption("Deregistration = permanent removal (LTA definition; temporary "
           "lay-up is a separate scheme and never enters this series). "
           "Newest month may revise within LTA's 1-month COE revalidation grace.")

st.divider()

# ============================================================ ACT 2
a2 = content.act2_gap(data)
st.header(f"2 · {a2['title']}")
st.markdown(a2["body"], unsafe_allow_html=True)
st.warning(a2["one_honest_number"])

ds = pd.DataFrame([r for r in data["disposal_split"] if r["year"] in ("2023", "2024")])
ds["year"] = ds["year"].astype(int)
plot = pd.DataFrame({
    "year": ds["year"],
    "car deregistrations (removed)": ds["deregistrations_total"].astype(int),
    "Comtrade export proxy (upper bound)": ds["exported_units_comtrade"].astype(int),
}).set_index("year")
st.markdown("**Export proxy vs. cars actually removed** — where the proxy bar "
            "exceeds the deregistration bar (2023), it is provably counting "
            "new-car re-exports, not just used ELVs.")
st.bar_chart(plot, height=300)
st.markdown(a2["context"], unsafe_allow_html=True)

st.divider()

# ============================================================ ACT 3
st.header("3 · What's at stake *if* — the illustrative value band")
st.markdown(content.why_no_2025(), unsafe_allow_html=True)
st.info(content.value_illustrative_caveat(), icon="⚠️")

with st.expander("▶ Open the illustrative value calculator", expanded=False):
    st.markdown(content.value_provenance_strip(data), unsafe_allow_html=True)
    col_y, col_s = st.columns(2)
    with col_y:
        year = st.radio("Year", ["2024", "2023"], horizontal=True)
    with col_s:
        share_pct = st.slider(
            "Assumed domestic-scrap share (%) — this is the unknown, not a "
            "measurement", min_value=5, max_value=50, value=25, step=5)
    anchor = data.get("floor_anchor_share_2024")
    if anchor:
        st.caption(f"For reference, the 2024 **lower-bound floor** sits at "
                   f"≈{anchor:.1%} — far below this slider's range.")

    # A dollar figure renders ONLY after explicit interaction, and only
    # alongside the caveat furniture above.
    reveal = st.checkbox("Show the illustrative $ estimate for this scenario",
                         value=False)
    if reveal:
        st.markdown(content.value_sentence(data, int(year), share_pct / 100.0),
                    unsafe_allow_html=True)
        st.caption("Illustrative, modeled — steel-scrap price is unverified and "
                   "dominates the band; composition is a US/global→SG transfer.")
    else:
        st.caption("_Move the slider and tick the box to reveal a conditional, "
                   "illustrative estimate. No headline dollar figure is shown by "
                   "default — the scrap share is genuinely unknown._")

st.divider()

# ============================================================ CLOSING
st.header("Why trust this — and where it stops")
tt = pd.DataFrame(content.closing_trust_table(),
                  columns=["Layer", "Trust basis", "Where it breaks"])
st.table(tt)
st.markdown(
    "**Pipeline provenance:** landing files carry source URL + UTC timestamp + "
    "sha256 (`data/landing/manifest.jsonl`) → raw tables verbatim → clean views "
    "(parent/child taxonomy era rule; suppressed cells never silently imputed) "
    "→ analysis-ready facts. Every number on this page traces to a committed "
    "check in `verification/` or a labeled input in "
    "`data/reference/material_value_inputs.csv` — see `analysis/"
    "claim_evidence_map.md`.")
st.markdown(
    "**Capstone note:** the failure mode found here — trade data cannot isolate "
    "used-vehicle flows from new-car re-exports — is expected to be the global "
    "norm. Quantifying that opacity country-by-country is the capstone's "
    "contribution. Full reasoning in `DECISIONS.md`.")
st.caption(LEGEND)
