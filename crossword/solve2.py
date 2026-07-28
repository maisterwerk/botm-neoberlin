import json, sys
from collections import defaultdict
src=open('solve_mini.py').read().split('if __name__')[0]
ns={}; exec(src, ns)
COMMON=ns['BY_LEN']                      # kuratiert = "geläufig"
big=[l.strip().upper() for l in open('/usr/share/dict/words')]
BIG={n:{w for w in big if len(w)==n and w.isalpha()} for n in (3,4,5)}
for n in (3,4,5): BIG[n] |= COMMON[n]
def pref(ws):
    p=defaultdict(set)
    for w in ws:
        for i in range(len(w)+1): p[w[:i]].add(w)
    return p
PRE={n:pref(BIG[n]) for n in (3,4,5)}
print("Lexikon:", {n:len(BIG[n]) for n in (3,4,5)}, file=sys.stderr)

def solve(theme, limit=4000):
    res=[]; rows=[None]*5
    def ok(rf):
        for c in (0,1,3,4):
            if "".join(rows[r][c] for r in range(rf)) not in PRE[5]: return False
        hi=min(rf,4)
        if hi>1 and "".join(rows[r][2] for r in range(1,hi)) not in PRE[3]: return False
        return True
    def rec(r):
        if len(res)>=limit: return
        if r==5:
            downs=["".join(rows[i][c] for i in range(5)) for c in (0,1,3,4)]
            downs.append("".join(rows[i][2] for i in range(1,4)))
            acr=[rows[1],rows[2],rows[3]]
            acr=["".join(a) for a in acr]
            if all(d in BIG[len(d)] for d in downs) and not(set(acr)&set(downs)):
                res.append({"grid":["".join(x) for x in rows],"across":acr,"down":downs})
            return
        cands=[theme[r]] if r in theme else sorted(BIG[5])
        for w in cands:
            rows[r]=list(w)
            if r in (0,4): rows[r][2]="#"
            if ok(r+1): rec(r+1)
        rows[r]=None
    rec(0); return res

def commonness(g):
    ents=g['across']+g['down']
    return sum(1 for e in ents if e in COMMON[len(e)])/len(ents)

allg=[]
for th in ({1:"TALLY",3:"SCORE"},{1:"SCORE",3:"TALLY"},{1:"COUNT",3:"TALLY"},{1:"AUDIT",3:"SCORE"},{2:"TALLY"},{2:"SCORE"},{2:"COUNT"}):
    r=solve(th)
    r.sort(key=commonness, reverse=True)
    good=[x for x in r if commonness(x)>=0.85]
    print(f"Thema {list(th.values())}: {len(r)} Gitter, davon {len(good)} sehr geläufig", file=sys.stderr)
    allg+=good[:6]
allg.sort(key=commonness, reverse=True)
json.dump(allg, open('grids.json','w'), indent=1)
print(f"\n{len(allg)} hochwertige Gitter")
for g in allg[:8]:
    print(); print("\n".join(g['grid'])); print(f"  A: {g['across']}  D: {g['down']}  geläufig={commonness(g):.0%}")
