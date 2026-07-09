#!/usr/bin/env python3
"""Part 1 landing checks — run against the LANDED FILES, not the API.

Checks (CLAUDE.md verify strategy, landing stage):
  1. Sigma-categories = embedded Total row, per month column, full history,
     for the three COE-category series (new reg, dereg, VQS population).
     Category rows = 4-space indent; deeper indents (Cat C ETS sub-splits)
     are excluded so C is not double-counted; `na` -> skipped.
  2. Same checksum for population-by-type (reported separately -- the type
     taxonomy may contain overlapping rows; a systematic failure here is a
     taxonomy fact to record, not a load error).
  3. Month-column continuity: no missing/duplicated month between the first
     and last column of each wide series.
  4. Comtrade per-year inventory: qty / netWgt / FOB presence, with flags for
     qty=0-despite-weight (known 2025 defect) and empty years.

Exit code 1 if any COE-series checksum or continuity check fails.
Usage: python3 verification/landing_checks.py > verification/part1_landing_checks.md
"""

import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(ROOT, "data", "landing")
WIDE_COL = re.compile(r"^(\d{4})([A-Z][a-z]{2})$")
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

FAILURES = []

# Diagnosed source defects (rule 5: diagnose before patching). These months
# still get REPORTED below, but do not fail the run — the cause is understood
# and recorded here, not hidden.
KNOWN_SOURCE_DEFECTS = {
    ("deregistrations_monthly", "2002Sep"):
        "source prints '-' for Category D; implied value = Total − Σothers "
        "= 1,422 (neighbors: 1,262 / 1,148). Clean layer leaves it NULL.",
}

# population_by_type taxonomy: 'Public Motor Cars' is the pre-1988Dec PARENT
# aggregate of 'Private Hire Cars' + 'Taxis' (verified: 1988Dec carries both,
# 13,613 = 3,140 + 10,473 exactly). When the split rows are populated, the
# parent must be excluded from the checksum or it double-counts.
PBT_PARENT = "Public Motor Cars"
PBT_CHILDREN = ("Private Hire Cars", "Taxis")


def latest(slug):
    d = os.path.join(LANDING, slug)
    name = sorted(os.listdir(d))[-1]
    with open(os.path.join(d, name)) as f:
        return os.path.join("data/landing", slug, name), json.load(f)


def num(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if s.lower() in ("na", "-", ""):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def month_key(col):
    m = WIDE_COL.match(col)
    return int(m.group(1)) * 12 + MONTHS[m.group(2)] - 1


def check_wide_series(slug, strict):
    path, payload = latest(slug)
    recs = payload["result"]["records"]
    total_row = next(r for r in recs if not r["DataSeries"].startswith(" "))
    cats = [r for r in recs
            if r["DataSeries"].startswith("    ")
            and not r["DataSeries"].startswith("        ")]
    cols = sorted((c for c in total_row if WIDE_COL.match(c)), key=month_key)

    print(f"\n### `{slug}`  ({path})")
    print(f"- Total row: `{total_row['DataSeries'].strip()}` · "
          f"{len(cats)} category rows · {len(cols)} month columns "
          f"({cols[0]} → {cols[-1]})")

    keys = [month_key(c) for c in cols]
    gaps = [cols[i] for i in range(1, len(cols)) if keys[i] != keys[i-1] + 1]
    dupes = [c for c, n in Counter(cols).items() if n > 1]
    ok_cont = not gaps and not dupes
    print(f"- continuity: {'PASS — no missing/doubled months' if ok_cont else f'FAIL — gaps after {gaps}, dupes {dupes}'}")
    if not ok_cont:
        FAILURES.append(f"{slug}: continuity")

    violations, known, total_na, partial_na = [], [], 0, 0
    for c in cols:
        t = num(total_row.get(c))
        if t is None:
            total_na += 1
            continue
        use = cats
        # taxonomy rule: drop the parent aggregate when its split is populated
        children_live = all(
            num(r.get(c)) is not None for r in cats
            if r["DataSeries"].strip() in PBT_CHILDREN
        ) and any(r["DataSeries"].strip() in PBT_CHILDREN for r in cats)
        if children_live:
            use = [r for r in cats if r["DataSeries"].strip() != PBT_PARENT]
        vals = [num(r.get(c)) for r in use]
        if any(v is None for v in vals):
            partial_na += 1
        s = sum(v for v in vals if v is not None)
        if abs(s - t) > 0.5:
            if (slug, c) in KNOWN_SOURCE_DEFECTS:
                known.append((c, int(t), int(s)))
            else:
                violations.append((c, int(t), int(s)))
    print(f"- checksum Σ(categories)=Total: **{len(violations)} unexplained "
          f"violations** across {len(cols) - total_na} checkable months "
          f"({total_na} months Total=na; {partial_na} months with ≥1 na category)")
    for c, t, s in known:
        print(f"    - {c}: Total={t:,} Σcats={s:,} (Δ={s-t:+,}) — KNOWN source "
              f"defect: {KNOWN_SOURCE_DEFECTS[(slug, c)]}")
    for c, t, s in violations[:12]:
        print(f"    - {c}: Total={t:,} Σcats={s:,} (Δ={s-t:+,})")
    if len(violations) > 12:
        print(f"    - … and {len(violations) - 12} more")
    if violations and strict:
        FAILURES.append(f"{slug}: {len(violations)} checksum violations")
    return violations


def check_comtrade():
    print("\n### `comtrade_hs8703_exports` (per-year world aggregates)")
    print("| year | records | qty (units) | netWgt (kg) | FOB (USD) | flags |")
    print("|---|---|---|---|---|---|")
    base = os.path.join(LANDING, "comtrade_hs8703_exports")
    for year in sorted(os.listdir(base)):
        _, payload = latest(f"comtrade_hs8703_exports/{year}")
        data = payload.get("data") or []
        if not data:
            print(f"| {year} | 0 | — | — | — | **EMPTY — not published/partial** |")
            continue
        r = data[0]
        qty, wgt, fob = r.get("qty"), r.get("netWgt"), r.get("fobvalue")
        flags = []
        if (not qty) and wgt:
            flags.append("**qty missing despite net weight — qty unusable**")
        if not wgt:
            flags.append("**netWgt missing/zero — magnitude must fall back to qty/value**")
        if len(data) > 1:
            flags.append(f"{len(data)} rows (expected 1 world-aggregate)")
        print(f"| {year} | {len(data)} | {qty} | {wgt} | {fob} | {'; '.join(flags) or 'ok'} |")


def main():
    print("# Part 1 — landing-stage checks (run on landed repo files)")
    manifest = os.path.join(LANDING, "manifest.jsonl")
    n = sum(1 for _ in open(manifest))
    print(f"\nManifest: {n} landed files, each with source URL + UTC fetch "
          "timestamp + sha256 (`data/landing/manifest.jsonl`).")

    print("\n## COE-category series (canonical — strict)")
    for slug in ("new_registrations_monthly", "deregistrations_monthly",
                 "population_vqs_monthly"):
        check_wide_series(slug, strict=True)

    print("\n## Population by vehicle type (taxonomy check — informational)")
    check_wide_series("population_by_type_monthly", strict=False)

    print("\n## Comtrade")
    check_comtrade()

    print()
    if FAILURES:
        print(f"**RESULT: FAIL** — {FAILURES}")
        sys.exit(1)
    print("**RESULT: all strict landing checks PASS**")


if __name__ == "__main__":
    main()
