#!/usr/bin/env python3
"""calibration.py — the test that turns a ledger into evidence about the ENGINE, not the posters.

For every claim we compute the ex-ante base rate strictly from history that existed on the posting
date, then ask: does the average predicted probability match the observed hit rate? A scoreboard
tells you who was wrong. A calibrated predictor tells you the tool works.
"""
import json, math
from datetime import datetime, timedelta
prices=json.load(open("prices_long.json")); ledger=json.load(open("ledger_multi.json"))

def series(asset, before):
    s=prices[asset]; return sorted(d for d in s if d<before)

def base_rate(asset, req_pct, horizon, before):
    days=series(asset,before); s=prices[asset]
    vals=[s[d] for d in days]; h=max(1,int(horizon)); n=len(vals)
    if h>=n: return None,0
    hits=tot=0
    for i in range(n-h):
        mv=(vals[i+h]/vals[i]-1)*100; tot+=1
        if (req_pct>=0 and mv>=req_pct) or (req_pct<0 and mv<=req_pct): hits+=1
    return (hits/tot if tot else None), tot

def wilson(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-m), min(1,c+m))

rows=[]
for r in ledger:
    hz=(datetime.fromisoformat(r["deadline"])-datetime.fromisoformat(r["posted"])).days
    br,w=base_rate(r["asset"], r["required_move_pct"], hz, r["posted"])
    if br is None or w<30: continue
    rows.append({**r,"base_rate":br,"windows":w,"horizon":hz})

n=len(rows); hits=sum(r["hit"] for r in rows)
pred=sum(r["base_rate"] for r in rows)
lo,hi=wilson(hits,n)
print(f"CALIBRATION — {n} claims with >=30 prior windows of history\n")
print(f"{'posted':<11}{'regime':<7}{'account':<18}{'needed':>8}{'days':>5}{'ex-ante p':>11}  outcome")
for r in sorted(rows,key=lambda x:x['base_rate']):
    print(f"{r['posted']:<11}{r['regime']:<7}@{r['account']:<17}{r['required_move_pct']:>7.1f}%{r['horizon']:>5}"
          f"{r['base_rate']*100:>10.1f}%  {'HIT' if r['hit'] else 'MISS'}")
print(f"\nExpected hits from our own ex-ante base rates : {pred:.2f}")
print(f"Actually observed                             : {hits}")
print(f"Observed rate {hits}/{n} = {hits/n:.1%}   95% CI [{lo:.1%}, {hi:.1%}]")
print(f"Mean predicted probability                    : {pred/n:.1%}")
inside = lo <= pred/n <= hi
print(f"\nPredicted mean lies inside the observed CI: {'YES — the engine is calibrated' if inside else 'NO'}")
# decile-style buckets
print("\nRELIABILITY (predicted vs observed, by band)")
for lo_b,hi_b in ((0,.05),(.05,.15),(.15,1.01)):
    b=[r for r in rows if lo_b<=r["base_rate"]<hi_b]
    if b:
        print(f"  p in [{lo_b:.0%},{hi_b:.0%})  n={len(b):<3} mean predicted {sum(x['base_rate'] for x in b)/len(b):.1%}  observed {sum(x['hit'] for x in b)/len(b):.1%}")
