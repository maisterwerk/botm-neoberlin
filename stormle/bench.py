import json,math,time
from collections import Counter
from engine import score, entropy_of_guess
W=json.load(open('words.json')); OP=[w for w,h in json.load(open('openers.json'))]
PROBES=OP[:250]
PAT={}
def sc(g,a):
    k=(g,a); v=PAT.get(k)
    if v is None: v=score(g,a); PAT[k]=v
    return v
def best_guess_shipped(c):
    if len(c)==len(W): return "TEARS"
    if len(c)==1: return c[0]
    lst = W if len(c)<=150 else list(set(c)|set(PROBES))
    isc=set(c); n=len(c); bw=None; bh=-1; bc=False
    for g in lst:
        b={}
        for a in c:
            p=sc(g,a); b[p]=b.get(p,0)+1
        h=0.0
        for cnt in b.values():
            p=cnt/n; h-=p*math.log2(p)
        cand=g in isc
        if h>bh+1e-9 or (abs(h-bh)<=1e-9 and cand and not bc):
            bh=h; bw=g; bc=cand
    return bw
def solve(ans):
    c=W[:]
    for i in range(1,7):
        g=best_guess_shipped(c)
        if g==ans: return i
        pat=sc(g,ans); c=[w for w in c if sc(g,w)==pat]
    return 7
t=time.time(); res=[solve(a) for a in W]
d=dict(sorted(Counter(res).items())); ok=sum(1 for x in res if x<=6)
print(f"VOLLER POOL ({time.time()-t:.0f}s): gelöst {ok}/{len(W)} ({100*ok/len(W):.1f}%)  "
      f"Schnitt {sum(res)/len(res):.3f}  max {max(res)}")
print("Verteilung:", d)
json.dump({"dist":{str(k):v for k,v in d.items()},"mean":sum(res)/len(res),
           "solved":ok,"n":len(W),"max":max(res)}, open('benchmark.json','w'),indent=1)
