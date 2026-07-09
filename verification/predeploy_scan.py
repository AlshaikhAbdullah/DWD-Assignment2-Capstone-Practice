#!/usr/bin/env python3
"""Pre-deploy gate — scan the dashboard's rendered text against the
"numbers that must NOT appear" list (analysis/claim_evidence_map.md).

It imports dashboard/content.py (the same functions app.py renders) and
generates EVERY user-reachable text state: both years, every slider step, the
revealed and hidden value states, and all static blocks. Then it applies the
forbidden-pattern rules. It also statically scans app.py for chart wiring
(no FOB axis, value calculator gated behind interaction) and confirms the
continuous value band reproduces the committed material_value table.

Exit 1 (fail the build) if anything forbidden appears. Run before publishing:
    python3 verification/predeploy_scan.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "dashboard"))
import content  # noqa: E402
import data_source  # noqa: E402

FAILURES = []
DOLLAR = re.compile(r"\$\s?\d[\d,]*")


def fail(rule, detail):
    FAILURES.append(rule)
    print(f"- **FAIL** [{rule}] {detail}")


def ok(rule, detail):
    print(f"- PASS [{rule}] {detail}")


def collect_rendered_states(data):
    """Every (state_id, text) the app can display."""
    states = []
    a1 = content.act1_headline(data)
    states += [("act1.lead", a1["lead"]), ("act1.trust", a1["trust_strip"])]
    a2 = content.act2_gap(data)
    states += [("act2.body", a2["body"]), ("act2.floor", a2["one_honest_number"]),
               ("act2.context", a2["context"])]
    states += [("act3.no2025", content.why_no_2025()),
               ("act3.caveat", content.value_illustrative_caveat()),
               ("act3.provenance", content.value_provenance_strip(data))]
    # value sentences: both years × every slider step the UI allows
    for year in (2023, 2024):
        for pct in range(5, 55, 5):
            states.append((f"value.{year}.{pct}pct",
                           content.value_sentence(data, year, pct / 100.0)))
    for row in content.closing_trust_table():
        states.append(("closing.trust_row", " | ".join(row)))
    return states


def rule_conditional_dollars(states):
    """Any dollar figure must sit in a conditional, illustrative-tagged
    sentence — never unconditional."""
    bad = []
    for sid, text in states:
        if DOLLAR.search(text):
            low = text.lower()
            if not (("if " in low) and (content.MODELED_TAG in low)):
                bad.append(sid)
    if bad:
        fail("unconditional-dollar", f"dollar without 'if…{content.MODELED_TAG}': {bad}")
    else:
        n = sum(bool(DOLLAR.search(t)) for _, t in states)
        ok("unconditional-dollar", f"all {n} dollar-bearing states are conditional + '{content.MODELED_TAG}'")


def rule_no_measured_split(states):
    """No export/scrap DISPOSAL-SPLIT percentage presented as measured. A split
    percentage modifies how the ELV *stream* divides (exported vs scrapped).
    Percentages that carry a bound/conditional word are allowed; and
    composition/price statements ('% of vehicle mass', 'steel-scrap price')
    are not disposal splits at all."""
    bound = ("lower bound", "upper bound", "at least", "floor", "proxy",
             "impossible", "more exports", "cannot", "can't", "if ")
    # a percentage in one of these contexts is NOT a disposal split
    not_a_split = ("mass", "price", "curb weight", "fraction", "of vehicle")
    bad = []
    for sid, text in states:
        low = text.lower()
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s?%", low):
            window = low[max(0, m.start() - 60): m.end() + 60]
            near_disposal = ("export" in window or "scrapped" in window
                             or "domestic-scrap" in window or "deregistrat" in window)
            if near_disposal and not any(c in window for c in not_a_split):
                if not any(b in window for b in bound):
                    bad.append((sid, m.group(0)))
    if bad:
        fail("measured-split-pct", f"disposal-split percentage without a bound word: {bad}")
    else:
        ok("measured-split-pct", "every disposal-split percentage carries a bound/conditional "
           "word; composition/price percentages correctly excluded")


def rule_no_2025_value(data, states):
    """No 2025 value figure. The value formula must have no 2025 factors and
    no value state may mention 2025 alongside a dollar."""
    if "2025" in data["factors"]["dereg"]:
        fail("no-2025-value", "factors carry a 2025 dereg — a 2025 value is computable")
        return
    bad = [sid for sid, t in states if sid.startswith("value.") and "2025" in t]
    if bad:
        fail("no-2025-value", f"value state mentions 2025: {bad}")
    else:
        ok("no-2025-value", "no 2025 factors and no 2025 value sentence (only the "
           "'why no 2025' explanatory note references it)")


def rule_no_fob(states, app_src):
    """FOB dollars must never appear on a vehicle-count axis (or anywhere in
    rendered text / chart wiring)."""
    hits = [sid for sid, t in states if re.search(r"\bfob\b", t.lower())]
    src_hits = re.findall(r"fob\w*", app_src.lower())
    if hits or src_hits:
        fail("no-fob", f"FOB referenced in states={hits} / app.py={set(src_hits)}")
    else:
        ok("no-fob", "no FOB field in any rendered text or chart wiring")


def rule_no_broken_export_counts(data, states, app_src):
    """No export COUNT for the qty-broken years (2022, 2025)."""
    for r in data["disposal_split"]:
        if r["year"] in ("2022", "2025") and r["exported_units_comtrade"] not in (None, "None"):
            fail("no-broken-export-count", f"{r['year']} carries an export count")
            return
    # the Act-2 chart only wires 2023/2024
    if re.search(r'2022|2025', re.search(r'ds = pd\.DataFrame.*?\n', app_src).group(0)):
        fail("no-broken-export-count", "Act-2 chart references 2022/2025")
        return
    ok("no-broken-export-count", "no export count for 2022/2025; Act-2 chart uses 2023/2024 only")


def rule_value_band_ties_to_table(data):
    """The continuous slider band must reproduce the committed material_value
    table at its fixed scenarios (the numbers users see == the checked table)."""
    tbl = {(r["year"], r["scrap_share"], r["material"]): r for r in data["material_value"]}
    mism = 0
    for (year, share, material), r in tbl.items():
        if material != "steel":
            continue  # check one material's total contribution via full band below
    # compare full 3-material band at each scenario
    scen_shares = sorted({(r["year"], r["scrap_share"]) for r in data["material_value"]})
    checked = 0
    for year, share in scen_shares:
        rows = [r for r in data["material_value"] if r["year"] == year and r["scrap_share"] == share]
        tbl_low = sum(int(r["value_usd_low"]) for r in rows)
        tbl_high = sum(int(r["value_usd_high"]) for r in rows)
        lo, mid, hi = content.value_band(data, int(year), float(share))
        if abs(lo - tbl_low) > 2 or abs(hi - tbl_high) > 2:
            mism += 1
        checked += 1
    if mism:
        fail("band-ties-to-table", f"{mism}/{checked} scenarios diverge from material_value")
    else:
        ok("band-ties-to-table", f"continuous band reproduces material_value at all {checked} committed scenarios")


def rule_value_gated(app_src):
    """The dollar sentence must be behind an explicit interaction and inside
    the collapsed expander (no headline dollar on landing)."""
    checks = [
        ('expander collapsed', 'expanded=False' in app_src),
        ('reveal checkbox default off', re.search(r'st\.checkbox\([^)]*value=False', app_src) is not None),
        ('value_sentence only under reveal',
         app_src.index("if reveal:") < app_src.index("content.value_sentence")),
    ]
    bad = [name for name, passed in checks if not passed]
    if bad:
        fail("value-gated", f"value calculator not properly gated: {bad}")
    else:
        ok("value-gated", "value $ is inside a collapsed expander behind an off-by-default checkbox")


def main():
    print("# Pre-deploy scan — dashboard rendered text vs. forbidden list\n")
    data = data_source.load_snapshot()
    states = collect_rendered_states(data)
    app_src = open(os.path.join(ROOT, "dashboard", "app.py")).read()
    print(f"Exercised {len(states)} rendered states "
          "(2 years × 10 slider steps + all static blocks).\n")

    rule_conditional_dollars(states)
    rule_no_measured_split(states)
    rule_no_2025_value(data, states)
    rule_no_fob(states, app_src)
    rule_no_broken_export_counts(data, states, app_src)
    rule_value_band_ties_to_table(data)
    rule_value_gated(app_src)

    print()
    if FAILURES:
        print(f"**RESULT: BUILD FAILED** — {FAILURES}")
        sys.exit(1)
    print("**RESULT: pre-deploy scan PASS — safe to publish**")


if __name__ == "__main__":
    main()
