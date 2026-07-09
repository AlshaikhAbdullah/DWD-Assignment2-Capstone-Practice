# Part 1 — stock-flow invariant + reconciliation to LTA annual totals

## Q1 — Is the population series independent, or derived from the flows?

Category-level months: 2675 · exact-zero: 2303 · non-zero: 372 · max |residual|: 5048

**Answer: neither purely independent nor arithmetically derived — and the
invariant is NOT circular.** If `pop` were reconstructed as
`prior + reg − dereg`, every residual would be exactly 0. It is not: the
1990s carry large, structured residuals (max 5,048), and they OFFSET ACROSS
CATEGORIES within a month (e.g. 1994-04 exempt −1,215 / cat_c +1,215;
2025-09 exempt +680 / cat_a −680) — these are reclassifications and scheme
conversions that move vehicles between categories without a registration or
deregistration event. All three series come from the same LTA register
(stock is the month-end snapshot; flows are the month's events), so from
~2010 the residual is exactly 0 in almost every month — that "perfect zero"
is DIAGNOSED as same-register consistency, not independent confirmation.
Consequence: the invariant proves internal consistency and exposes
reclassification events; it cannot prove the counts against an outside
source. The reconciliation to LTA's PUBLISHED annual table (§4) is
therefore kept as the primary cross-series check.

## T1 — total-level conservation (gated)
- PASS — Δ(total pop) = total reg − total dereg, up to year-end audit adjustments: 420/431 months exactly 0; non-zero months (all small): [('1990-12', '-15'), ('1991-12', '74'), ('1992-12', '277'), ('1993-12', '-8'), ('1994-12', '79'), ('1995-12', '-8'), ('1996-12', '-2'), ('1997-12', '25'), ('2006-02', '136'), ('2006-12', '-29'), ('2007-12', '-13')]; outside policy: []

## T2 — category level, 2000-01 onward (gated: zero or within-month transfer)
  non-zero category residuals since 2000: 52 (['2001-12', '2002-12', '2003-01', '2003-03', '2003-04', '2003-05', '2003-06', '2003-07', '2003-12', '2004-12', '2005-12', '2006-02', '2006-05', '2006-12', '2007-12', '2008-03', '2008-12', '2025-09'])
    - 2001-12: [('exempt', '64'), ('cat_c', '-64')] (offsetting transfer)
    - 2002-12: [('exempt', '58'), ('cat_c', '-58')] (offsetting transfer)
    - 2003-01: [('taxis', '-1'), ('cat_a', '1')] (offsetting transfer)
    - 2003-03: [('taxis', '1'), ('cat_a', '-1')] (offsetting transfer)
    - 2003-04: [('taxis', '1'), ('cat_a', '-1')] (offsetting transfer)
    - 2003-05: [('taxis', '-1'), ('cat_a', '1')] (offsetting transfer)
    - 2003-06: [('taxis', '28'), ('cat_a', '-28')] (offsetting transfer)
    - 2003-07: [('taxis', '-28'), ('cat_a', '28')] (offsetting transfer)
    - 2003-12: [('exempt', '-3'), ('cat_a', '-4'), ('cat_b', '-1'), ('cat_d', '40'), ('cat_c', '-32')] (offsetting transfer)
    - 2004-12: [('exempt', '13'), ('cat_a', '-6'), ('cat_b', '-11'), ('cat_d', '52'), ('cat_c', '-48')] (offsetting transfer)
    - 2005-12: [('exempt', '39'), ('cat_a', '-8'), ('cat_d', '-6'), ('cat_c', '-25')] (offsetting transfer)
    - 2006-02: [('exempt', '136')] (offsetting transfer)
    - 2006-05: [('exempt', '2'), ('cat_c', '-2')] (offsetting transfer)
    - 2006-12: [('exempt', '20'), ('cat_a', '-25'), ('cat_b', '-7'), ('cat_d', '14'), ('cat_c', '-31')] (offsetting transfer)
    - 2007-12: [('exempt', '-9'), ('cat_a', '-3'), ('cat_b', '-16'), ('cat_d', '38'), ('cat_c', '-23')] (offsetting transfer)
    - 2008-03: [('cat_a', '1'), ('cat_b', '-1')] (offsetting transfer)
    - 2008-12: [('exempt', '17'), ('cat_a', '-26'), ('cat_b', '-10'), ('cat_d', '52'), ('cat_c', '-33')] (offsetting transfer)
    - 2025-09: [('exempt', '680'), ('cat_a', '-680')] (offsetting transfer)
- PASS — every non-zero category residual since 2000 nets out within its month: 0 non-offsetting category residuals

## T3 — pre-2000 reclassification era (reported, gated at total level by T1)
| category | net 1990–94 | net 1995–99 | non-zero months |
|---|---|---|---|
| cat_a | -424 | 9689 | 96 |
| cat_b | -1542 | 2896 | 96 |
| cat_c | 2291 | -497 | 11 |
| cat_d | 503 | -113 | 10 |
| exempt | -3048 | 502 | 12 |
| taxis | 13 | 1 | 7 |
| weekend_offpeak | 621 | -6110 | 88 |

Pattern reading (per the diagnosis taxonomy): `weekend_offpeak` drains
(−6,110 net 1995–99) into `cat_a`/`cat_b` (+9,689/+2,896) — Weekend→Off-Peak
scheme conversions and the 1999-01 series fold-in (cat_a +5,048 that single
month); `exempt`↔`cat_c` swap in offsetting pairs (reclassifications). These
are TRANSFERS, not phantom vehicles — the same months conserve at total
level (T1). A category-scope note follows for the car scope.

Car scope (cat_a+cat_b+weekend_offpeak) combined net residual, all history:
**4333**. Diagnosed to the vehicle: the WE/OP population row ends
1998-12 at a terminal stock of **6,353**, and the 1999-01 cat_a/cat_b
residuals are +5,048 + 1,305 = **6,353 exactly** — the fold-in is a series
re-labeling INSIDE the car scope (those vehicles were already cars), not
phantom vehicles. Net of that artifact the car scope drifts −2,020 over 36
years (~56/yr): small cross-scope conversions (taxi↔car, exempt↔car — the
2025-09 pair is one). Car-scope FLOW counts (reg/dereg) are unaffected;
only the pre-1999 category split of the car STOCK carries the artifact.

## Universe check — do the flows act on the population the stock counts?
- PASS — VQS population total == all-motor-vehicles-by-type total, every overlapping month: 432/432 months equal (max gap 0) — the VQS 'universe' is the full motor-vehicle register (incl. exempt), same universe the reg/dereg series cover (both carry the exempt category)

## Reconciliation — yearly API sums vs LTA published annual table (PRIMARY cross-series check)
- PASS — monthly API sums == LTA published yearly table, per category, 2015–2025: 77/77 cells match exactly (11 years × 7 columns; source: data/reference/MVP05-1_Dereg_by_COE.pdf)

**RESULT: invariant characterized and gated checks PASS; reconciliation exact**
