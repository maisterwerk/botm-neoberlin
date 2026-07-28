import json, sys
from collections import defaultdict
src=open('solve_mini.py').read().split('if __name__')[0]
ns={}; exec(src, ns); COMMON=ns['BY_LEN']
big=[l.strip().upper() for l in open('/usr/share/dict/words')]
BIG={n:{w for w in big if len(w)==n and w.isalpha()} for n in (3,5)}
for n in (3,5): BIG[n]|=COMMON[n]
# Index: 5-Buchstaben-Wörter nach ihren mittleren drei Zeichen (Positionen 1,2,3)
mid=defaultdict(list)
for w in BIG[5]: mid[w[1:4]].append(w)
print("Lexikon 5er:", len(BIG[5]), "| Mittelmuster:", len(mid), file=sys.stderr)

def commonness(ents):
    return sum(1 for e in ents if e in COMMON.get(len(e), ())) / len(ents)

THEME=["TALLY","SCORE","COUNT","TOTAL","AUDIT","PROOF","TRUTH","CHECK","LEDGE"]
out=[]
mids=sorted(COMMON[5])            # mittlere Zeilen aus dem geläufigen Wortschatz
for r1 in THEME:
    for r3 in THEME:
        if r3==r1: continue
        for r2 in mids:
            col2 = r1[2]+r2[2]+r3[2]
            if col2 not in BIG[3]: continue
            cols=[]
            ok=True
            for c in (0,1,3,4):
                pat=r1[c]+r2[c]+r3[c]
                cand=mid.get(pat)
                if not cand: ok=False; break
                cols.append((c,cand))
            if not ok: continue
            # nimm für jede Spalte das geläufigste Wort
            pick=[]
            for c,cand in cols:
                cc=[w for w in cand if w in COMMON[5]] or cand
                pick.append((c,sorted(cc)[0]))
            downs=[w for _,w in pick]+[col2]
            acr=[r1,r2,r3]
            if set(acr)&set(downs): continue
            g=["#"]*5
            row0=[""]*5; row4=[""]*5
            for c,w in pick: row0[c]=w[0]; row4[c]=w[4]
            row0[2]="#"; row4[2]="#"
            grid=["".join(row0), r1, r2, r3, "".join(row4)]
            sc=commonness(acr+downs)
            out.append({"grid":grid,"across":acr,"down":downs,"common":round(sc,2)})
out.sort(key=lambda x:-x['common'])
seen=set(); uniq=[]
for g in out:
    k=tuple(g['grid'])
    if k in seen: continue
    seen.add(k); uniq.append(g)
json.dump(uniq[:60], open('grids.json','w'), indent=1)
print(f"{len(uniq)} Gitter gefunden")
for g in uniq[:10]:
    print(); print("\n".join(g['grid'])); print(f"  A: {g['across']}  D: {g['down']}  geläufig={g['common']:.0%}")
