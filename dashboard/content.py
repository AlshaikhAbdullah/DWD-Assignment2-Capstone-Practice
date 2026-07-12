"""Pure content/render functions for the SG-ELV dashboard.

No Streamlit import here on purpose: app.py renders these strings, and
verification/predeploy_scan.py imports the SAME functions to generate every
text state the app can show (all years, all slider positions) and scans them
against the "numbers that must NOT appear" list. What the scan checks is
exactly what the user sees.

Claim→evidence mapping: each render function carries its
claim_evidence_map.md row ids as PYTHON comments (never inside displayed
strings — Streamlit markdown does not strip HTML comments, so anything in
the string reaches the page as visible text; the pre-deploy scan now forbids
stray markup in any rendered state).
"""

MODELED_TAG = "illustrative, modeled"


def _fmt_usd(n):
    return f"${n:,.0f}"


# ---------------------------------------------------------------- Act 1
def act1_headline(data):
    yf = {r["year"]: r for r in data["yearly_flows"]}
    d23, d24, d25 = (int(yf[y]["car_deregistrations"]) for y in ("2023", "2024", "2025"))
    rec = data["reconciliation"]
    return {
        "title": "Singapore generates a measurable end-of-life vehicle stream",
        "lead": (
            f"In 2025, **{d25:,} cars** (COE Categories A + B) were permanently "
            f"deregistered in Singapore — up from {d23:,} in 2023 and {d24:,} in "
            "2024. Deregistration is permanent removal: LTA requires proof of "
            "disposal (scrapping or export) within one month, and it is an "
            "offence to keep or use a deregistered vehicle."),  # claim 1.1, 1.4
        "trust_strip": (
            f"✓ Verified — this series reconciles **exactly** with LTA's "
            f"published annual statistics: {rec['cells_matched']}/"
            f"{rec['cells_total']} cells match (total + 6 categories, "
            f"{rec['years']}). Monthly stock-flow conservation holds in 420/431 "
            "months."),  # claim 1.2, 1.3
    }


# ---------------------------------------------------------------- Act 2
def act2_gap(data):
    ds = {r["year"]: r for r in data["disposal_split"]}
    r23, r24 = ds["2023"], ds["2024"]
    ratio23 = float(r23["export_proxy_ratio"])
    ratio24 = float(r24["export_proxy_ratio"])
    floor24 = int(r24["scrapped_est_residual"])
    floor_pct = 100 * floor24 / int(r24["deregistrations_total"])
    return {
        "title": "Where do they go? Open data cannot cleanly say — and that is the finding",
        "body": (
            "The split between cars **exported** and cars **scrapped "
            "domestically** is not published in any reachable open source — "
            "checked exhaustively across data.gov.sg (80-dataset scan), LTA's "
            "statistics PDFs, and SingStat. The only proxy, UN "  # claim 2.1
            "Comtrade HS 8703 car exports, over-counts because it includes "
            "**new-car re-exports**: in 2023 it reports "
            f"{ratio23:.0%} of total car deregistrations — more exports than "
            "cars removed, which is impossible for used vehicles alone. "
            f"In 2024 it is {ratio24:.0%}. So the proxy is an **upper bound**, "
            "not a split."),  # claim 2.2, 2.3
        "one_honest_number": (
            f"The one defensible number: in 2024 at least **{floor24:,} cars "
            f"(≈{floor_pct:.1f}%)** were scrapped domestically — a "
            "**low-confidence lower bound** (the true figure is likely higher, "
            "because the export proxy is an upper bound). For 2023 no floor "
            "exists at all: the proxy exceeds total deregistrations, so we "
            "report no number."),  # claim 2.4, 2.5
        "context": (
            "_Context (unverified): Singapore is widely described as a used-car "
            "export hub, which is consistent with a low domestic-scrap share — "
            "but open data cannot confirm the magnitude._"),  # claim 2.7
    }


# ---------------------------------------------------------------- Act 3
def value_band(data, year, share):
    """Return (low, mid, high) total USD across the 3 materials for a given
    scrap share, computed from the committed provenance factors — identical to
    the formula verified in layer4_material_value_checks.md."""
    f = data["factors"]
    dereg = f["dereg"][str(year)]
    totals = {"low": 0.0, "mid": 0.0, "high": 0.0}
    for material in ("steel", "aluminium", "copper"):
        for agg in ("low", "mid", "high"):
            tonnes = dereg * share * f["weight"][agg] * f["fraction"][material][agg]
            totals[agg] += tonnes * f["price"][material][str(year)][agg]
    return round(totals["low"]), round(totals["mid"]), round(totals["high"])


def value_sentence(data, year, share):
    """The ONLY way a dollar figure is allowed to appear: conditional +
    illustrative-tier tag. share is a fraction (0.05..0.50)."""
    lo, mid, hi = value_band(data, year, share)
    return (
        f"**If {share:.0%}** of {year}'s end-of-life cars were scrapped in "
        f"Singapore → the recoverable steel + aluminium + copper would be worth "
        f"roughly **{_fmt_usd(lo)} – {_fmt_usd(hi)} per year** "
        f"({MODELED_TAG}; midpoint {_fmt_usd(mid)}).")  # claim 3.1


def value_provenance_strip(data):
    f = data["factors"]
    return (
        "**How this is built** (every factor but one is external/assumed): "
        "car deregistrations — _verified_ (reconciled to LTA); "
        "aluminium & copper prices — _verified_ (World Bank CMO / LME cash); "
        "**steel-scrap price — _unverified_** (named proxy: HMS 1&2 80:20, no "
        "reachable source); curb weight & material fractions — "
        "_literature-cited, US/global fleet averages transferred to Singapore_ "
        f"(e.g. {f['weight']['mid']} t curb weight is a US/global figure, not "
        "SG-measured).")  # claim 3.3-3.9, 3.11b


def value_illustrative_caveat():
    return (
        "⚠️ **Illustrative tier only.** Steel is ~58–70% of vehicle mass, so the "
        "**unverified** steel-scrap price dominates the band — and the whole "
        "composition is a modeled US/global→Singapore transfer. Read the range "
        "as an order-of-magnitude 'what's at stake if', never a measurement. "
        )  # claim 3.11, 3.11b


def why_no_2025():
    return (
        "_2025 is not shown here: no countable export proxy exists for 2025 "
        "(Comtrade reports zero units against ~19 kt of net weight), so there "
        "is no quantity to value._")  # claim 3.12


# ---------------------------------------------------------------- closing
def closing_trust_table():
    return [
        ("Raw → clean pipeline", "Landing files carry source URL + UTC timestamp "
         "+ sha256; Σcategories = embedded Total checksum; replayable without "
         "re-fetch", "Upstream revisions (LTA 1-month COE revalidation grace)"),
        ("Layer 1 — ELV generation", "Stock-flow invariant + exact reconciliation "
         "to LTA published annual totals (77/77)", "Pre-2005 not yet reconciled "
         "to a published target"),
        ("Layer 2 — disposal split", "Bounded: proxy is an upper bound, floor is "
         "a lower bound; both labeled", "The gap between them is wide and "
         "open data cannot close it"),
        ("Layer 4 — material value", "Scenario band; verified prices for Al/Cu; "
         "cited composition", "Steel price unverified; composition is a "
         "US/global→SG transfer; scrap share is an assumption"),
    ]


def scenario_labels():
    """Slider tick semantics for the UI (share fraction -> label)."""
    return {
        "floor_anchor": "3.8% — 2024 domestic-scrap floor (lower bound)",
        "min": "5%", "max": "50%",
    }
