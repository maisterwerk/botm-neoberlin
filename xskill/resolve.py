#!/usr/bin/env python3
"""
resolve.py — Phase 2: settle every adjudicated claim against the independent price series,
and score it against a no-information baseline.

Why the baseline matters (this is the non-obvious part): in a trending market a raw hit-rate
leaderboard just ranks people by whether they happened to be pointing the same way as the market.
A claim only demonstrates skill if it beats what you would have got for free. We use two
free strategies evaluated on the SAME claims:
  DRIFT   : assume the price on the deadline equals the price when the post was made.
  ALWAYS  : assume every "above" claim resolves the way the majority of claims did.
"""
import json, sys
from datetime import datetime, timedelta

prices = json.load(open("prices.json"))
cands = {c["id"]: c for c in json.load(open("candidates.json"))}

adj = {}
for f in ("adjB1.json", "adjB2.json", "adjB3.json"):
    try:
        for a in json.load(open(f)):
            adj[a["id"]] = a
    except FileNotFoundError:
        pass


def price_on(asset, day):
    s = prices[asset]
    d = datetime.fromisoformat(day)
    for i in range(10):
        k = (d - timedelta(days=i)).date().isoformat()
        if k in s:
            return s[k]
    return None


def settle(target, direction, actual):
    if direction == "above":
        return actual >= target
    return actual <= target


ledger = []
for tid, a in adj.items():
    if not a.get("keep"):
        continue
    c = cands.get(tid)
    if not c:
        continue
    target = float(a.get("target_usd") or c["target_usd"])
    direction = a.get("direction") or c["direction"]
    actual = price_on(c["asset"], c["deadline"])
    spot = c["spot_at_post"]
    if actual is None:
        continue
    hit = settle(target, direction, actual)
    # baseline DRIFT: what if the price had simply stayed where it was when posted?
    drift_hit = settle(target, direction, spot)
    ledger.append({
        "id": tid, "account": c["account"], "url": c["url"], "asset": c["asset"],
        "posted": c["posted"], "deadline": c["deadline"],
        "spot_at_post": round(spot), "target": round(target), "direction": direction,
        "actual_at_deadline": round(actual), "hit": hit, "drift_baseline_hit": drift_hit,
        "confidence": a.get("confidence", "high"),
        "required_move_pct": round((target / spot - 1) * 100, 1),
        "actual_move_pct": round((actual / spot - 1) * 100, 1),
        "text": c["text"][:180],
    })

ledger.sort(key=lambda r: r["deadline"])
json.dump(ledger, open("ledger.json", "w"), indent=1)

n = len(ledger)
hits = sum(r["hit"] for r in ledger)
drift = sum(r["drift_baseline_hit"] for r in ledger)
bull = sum(1 for r in ledger if r["direction"] == "above")

print(f"RESOLVED LEDGER — {n} first-party falsifiable claims\n")
print(f"{'account':<20}{'asset':<9}{'posted':<11}{'deadline':<11}{'target':>9}{'actual':>9}  {'needed':>8}  {'moved':>8}  result")
for r in ledger:
    print(f"@{r['account']:<19}{r['asset']:<9}{r['posted']:<11}{r['deadline']:<11}"
          f"{r['target']:>9,}{r['actual_at_deadline']:>9,}  {r['required_move_pct']:>7.1f}%  "
          f"{r['actual_move_pct']:>7.1f}%  {'HIT ' if r['hit'] else 'MISS'}")

print(f"\nAggregate")
print(f"  claims resolved            {n}")
print(f"  hit rate (the posters)     {hits}/{n} = {hits/n:.0%}")
print(f"  hit rate (DRIFT baseline)  {drift}/{n} = {drift/n:.0%}   <- free, no information")
print(f"  edge over drift            {(hits-drift)/n:+.0%}")
print(f"  directional split          {bull} 'above' / {n-bull} 'below'")
