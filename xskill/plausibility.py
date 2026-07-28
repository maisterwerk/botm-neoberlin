#!/usr/bin/env python3
"""
plausibility.py — the forward-looking half of the Skill.

The ledger told us WHY X predictions fail: not direction, magnitude. So the useful product is
not a retrospective scoreboard, it is an ex-ante base rate:

    "This post needs +16.2% in 28 days. In 299 days of history, BTC moved that far up over a
     28-day window in 11% of windows. Prior odds ~1 in 9."

That number is computable the moment a prediction is posted, months before it resolves, and it
is what nobody on X ever states. Run it on the ledger and every one of the 11 failed claims was
a long shot at the time it was made — which is the validation that the base rate is the right
instrument.
"""
import json, sys
from datetime import datetime

import os
# Use the long series when it is present — the short 299-day file was the prototype-era input
# and a reviewer correctly noted it no longer reproduces the figures this project quotes.
_PF = "prices_long.json" if os.path.exists("prices_long.json") else "prices.json"
prices = json.load(open(_PF))


def series(asset, before=None):
    """Price history. before=YYYY-MM-DD restricts to windows that CLOSED strictly before that
    date — i.e. only what a user could actually have known when the post was made.
    Without this cutoff the base rate silently uses the future, including the claim's own window."""
    s = prices[asset]
    days = sorted(d for d in s if before is None or d < before)
    return days, [s[d] for d in days]


def base_rate(asset, required_pct, horizon_days, before=None):
    """Fraction of PRIOR windows of this length that moved at least this far, same direction.
    `before` makes the estimate strictly causal."""
    days, vals = series(asset, before)
    n = len(vals)
    h = max(1, int(horizon_days))
    if h >= n:
        return None, 0
    hits = 0
    total = 0
    for i in range(0, n - h):
        move = (vals[i + h] / vals[i] - 1) * 100
        total += 1
        if required_pct >= 0:
            if move >= required_pct:
                hits += 1
        else:
            if move <= required_pct:
                hits += 1
    return (hits / total if total else None), total


def assess(asset, spot, target, posted, deadline):
    req = (target / spot - 1) * 100
    horizon = (datetime.fromisoformat(deadline) - datetime.fromisoformat(posted)).days
    rate, windows = base_rate(asset, req, horizon, before=posted)
    return {
        "asset": asset, "required_move_pct": round(req, 1), "horizon_days": horizon,
        "historical_base_rate": None if rate is None else round(rate, 4),
        "causal": True,
        "windows_examined": windows,
        "odds": None if not rate else f"~1 in {round(1/rate)}",
        "verdict": ("NO PRIOR DATA" if rate is None or windows < 5 else
                    "IMPOSSIBLE in sample" if rate == 0 else
                    "LONG SHOT" if rate and rate < 0.15 else
                    "PLAUSIBLE" if rate and rate < 0.5 else "LIKELY" if rate else "n/a"),
    }


if __name__ == "__main__":
    ledger = json.load(open("ledger.json"))
    print("EX-ANTE PLAUSIBILITY — computed only from data available on the posting date\n")
    print(f"{'account':<20}{'needed':>9}{'days':>6}{'base rate':>11}{'odds':>11}  verdict        actual")
    longshots = 0
    for r in ledger:
        a = assess(r["asset"], r["spot_at_post"], r["target"], r["posted"], r["deadline"])
        br = "n/a" if a["historical_base_rate"] is None else f"{a['historical_base_rate']*100:.1f}%"
        odds = a["odds"] or "—"
        if a["windows_examined"] >= 5 and a["historical_base_rate"] is not None and a["historical_base_rate"] < 0.15:
            longshots += 1
        print(f"@{r['account']:<19}{a['required_move_pct']:>8.1f}%{a['horizon_days']:>6}"
              f"{br:>11}{odds:>11}  {a['verdict']:<15}{'HIT' if r['hit'] else 'MISS'}")
    scoreable = sum(1 for r in ledger
                    if assess(r["asset"], r["spot_at_post"], r["target"], r["posted"], r["deadline"])["windows_examined"] >= 5)
    print(f"\nSCOREABLE ex-ante (>=5 prior windows existed): {scoreable}/{len(ledger)}")
    print(f"Of those, {longshots} were LONG SHOT or never-observed at the moment of posting.")
    print("NOTE: this is the strictly causal version. Earlier drafts scanned the whole series,")
    print("which leaked the future into the base rate; two claims turn out to be unscoreable")
    print("because no prior history existed for them in our window.")

    print("\nWhat a typical X price claim asks for, versus what the market actually does:")
    for asset in ("bitcoin", "ethereum", "solana"):
        days, vals = series(asset)
        for h in (30,):
            moves = sorted(abs((vals[i + h] / vals[i] - 1) * 100) for i in range(len(vals) - h))
            med = moves[len(moves) // 2]
            p90 = moves[int(len(moves) * 0.9)]
            print(f"  {asset:9s} median |30d move| = {med:5.1f}%   90th pct = {p90:5.1f}%")
    reqs = sorted(abs(r["required_move_pct"]) for r in ledger)
    print(f"  ledger    median |required move| = {reqs[len(reqs)//2]:5.1f}%   "
          f"max = {reqs[-1]:5.1f}%")
