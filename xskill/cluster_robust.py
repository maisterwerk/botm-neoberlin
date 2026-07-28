#!/usr/bin/env python3
"""
cluster_robust.py — the answer to the second criticism: "effective n is below 41".

The exact Poisson-binomial test in calibration.py assumes 41 independent trials. The ledger is not
independent: two accounts posted the *identical* Bitcoin claim on the same day, three Ethereum
claims fall within six days of each other, and claims on the same asset in the same month resolve
against overlapping stretches of the same price path. Treating those as separate draws inflates
significance.

So we do three things instead of one:
  1. DEDUPLICATE exact duplicates (same asset, same target, same deadline) — those are one event.
  2. CLUSTER by (asset, calendar month) and report the design effect and effective sample size.
  3. CLUSTER BOOTSTRAP: resample whole clusters with replacement, recompute the shortfall
     (expected hits from our own ex-ante probabilities minus observed hits) in each replicate,
     and read the p-value off the bootstrap distribution. This is the honest version of
     "our engine is miscalibrated" once correlated claims are accounted for.
"""
import json, math, random, statistics
from collections import defaultdict
from datetime import datetime

prices = json.load(open("prices_long.json"))
ledger = json.load(open("ledger_multi.json"))


def base_rate(asset, req_pct, horizon, before):
    s = prices[asset]
    days = sorted(d for d in s if d < before)
    vals = [s[d] for d in days]
    h = max(1, int(horizon)); n = len(vals)
    if h >= n:
        return None, 0
    hits = tot = 0
    for i in range(n - h):
        mv = (vals[i + h] / vals[i] - 1) * 100
        tot += 1
        if (req_pct >= 0 and mv >= req_pct) or (req_pct < 0 and mv <= req_pct):
            hits += 1
    return (hits / tot if tot else None), tot


rows = []
for r in ledger:
    hz = (datetime.fromisoformat(r["deadline"]) - datetime.fromisoformat(r["posted"])).days
    p, w = base_rate(r["asset"], r["required_move_pct"], hz, r["posted"])
    if p is None or w < 30:
        continue
    rows.append({**r, "p": p, "horizon": hz})

# ---------- 1. exact duplicates ----------
seen, dedup, dupes = {}, [], []
for r in rows:
    key = (r["asset"], round(r["target"], 2), r["deadline"])
    if key in seen:
        dupes.append((seen[key]["account"], r["account"], r["asset"], r["deadline"]))
        continue
    seen[key] = r
    dedup.append(r)

print("CLUSTER-ROBUST RE-ANALYSIS\n")
print(f"claims with >=30 prior windows           : {len(rows)}")
print(f"exact duplicates removed                 : {len(rows) - len(dedup)}")
for a, b, asset, dl in dupes:
    print(f"    @{a} and @{b} posted the same {asset} claim due {dl}")
print(f"claims after de-duplication              : {len(dedup)}")

# ---------- 2. clusters and design effect ----------
clusters = defaultdict(list)
for r in dedup:
    clusters[(r["asset"], r["posted"][:7])].append(r)
sizes = [len(v) for v in clusters.values()]
m = len(sizes); nbar = sum(sizes) / m
# intra-cluster correlation of the outcome, estimated crudely from between/within variance
obs = [r["hit"] for r in dedup]
pbar = sum(obs) / len(obs)
between = sum(len(v) * ((sum(x["hit"] for x in v) / len(v)) - pbar) ** 2 for v in clusters.values())
within = pbar * (1 - pbar) * len(obs)
icc = max(0.0, min(1.0, (between / max(within, 1e-9) - 1) / max(nbar - 1, 1e-9))) if nbar > 1 else 0.0
deff = 1 + (nbar - 1) * icc
print(f"\nclusters (asset x calendar month)        : {m}, mean size {nbar:.2f}, max {max(sizes)}")
print(f"estimated intra-cluster correlation      : {icc:.3f}")
print(f"design effect                            : {deff:.2f}")
print(f"EFFECTIVE SAMPLE SIZE                    : {len(dedup)/deff:.1f}  (nominal {len(dedup)})")

# ---------- 3. cluster bootstrap ----------
exp = sum(r["p"] for r in dedup)
hits = sum(r["hit"] for r in dedup)
shortfall = exp - hits
rng = random.Random(42)
keys = list(clusters.keys())
B = 20000
worse = 0
draws = []
for _ in range(B):
    samp = []
    for _ in range(len(keys)):
        samp += clusters[keys[rng.randrange(len(keys))]]
    e = sum(r["p"] for r in samp)
    # null: outcomes really do occur with our stated probabilities
    h = sum(1 for r in samp if rng.random() < r["p"])
    draws.append(e - h)
    if (e - h) >= shortfall * (len(samp) / len(dedup)):
        worse += 1
p_boot = (worse + 1) / (B + 1)
print(f"\nOur engine predicted {exp:.2f} hits; {hits} occurred. Shortfall {shortfall:.2f}.")
print(f"Cluster bootstrap ({B:,} resamples of whole clusters, seed 42):")
print(f"  P(shortfall this large or larger under our own probabilities) = {p_boot:.4f}")
print(f"  bootstrap mean shortfall under the null = {statistics.mean(draws):+.2f} "
      f"(sd {statistics.pstdev(draws):.2f})")
print(f"\nFor comparison, the naive independent Poisson-binomial gave P = 0.0083.")
print("The cluster-robust figure is the one to quote.")
