#!/usr/bin/env python3
"""Exhaustive census of EVERY legal grid for the pattern
   ...##  /  .....  /  .....  /  .....  /  ##...
over the 3,560-word common lexicon. Enumerates the centre down entry first and prunes the
row triples by which crossings can still be completed, which makes the full count tractable."""
import json
from collections import defaultdict
b={}; exec(open('solve_mini.py').read().split('if __name__')[0], b)
e={}; exec(open('words_extra.py').read(), e)
W5=sorted({w for w in (b['BY_LEN'][5]|set(e['EX5'])) if len(w)==5})
W4={w for w in (b['BY_LEN'][4]|set(e['EX4'])) if len(w)==4}
W3={w for w in (b['BY_LEN'][3]|set(e['EX3'])) if len(w)==3}
end3=defaultdict(list); beg3=defaultdict(list)
for w in W4: end3[w[1:]].append(w); beg3[w[:3]].append(w)
by2=defaultdict(list)
for w in W5: by2[w[2]].append(w)
total=distinct=0; hits=[]
for col2 in W5:
    R1=by2.get(col2[1],()); R2=by2.get(col2[2],()); R3=by2.get(col2[3],())
    if not(R1 and R2 and R3): continue
    for r1 in R1:
        for r2 in R2:
            ax={k[2] for k in end3 if k[0]==r1[0] and k[1]==r2[0]}
            if not ax: continue
            ay={k[2] for k in end3 if k[0]==r1[1] and k[1]==r2[1]}
            if not ay: continue
            dx={k[2] for k in beg3 if k[0]==r1[3] and k[1]==r2[3]}
            if not dx: continue
            ex={k[2] for k in beg3 if k[0]==r1[4] and k[1]==r2[4]}
            if not ex: continue
            for r3 in R3:
                if r3[0] not in ax or r3[1] not in ay: continue
                if r3[3] not in dx or r3[4] not in ex: continue
                A=end3[r1[0]+r2[0]+r3[0]]; B=end3[r1[1]+r2[1]+r3[1]]
                D=beg3[r1[3]+r2[3]+r3[3]]; E=beg3[r1[4]+r2[4]+r3[4]]
                for a in A:
                    for bb in B:
                        r0=a[0]+bb[0]+col2[0]
                        if r0 not in W3: continue
                        for d in D:
                            for ee in E:
                                r4=col2[4]+d[3]+ee[3]
                                if r4 not in W3: continue
                                total+=1
                                acr=[r0,r1,r2,r3,r4]; dwn=[a,bb,col2,d,ee]
                                if set(acr)&set(dwn): continue
                                distinct+=1
                                if {"TEST","OATH","PROOF"} <= set(dwn):
                                    hits.append({"across":acr,"down":dwn})
print(f"legale Gitter insgesamt           : {total}")
print(f"davon mit 10 VERSCHIEDENEN Wörtern: {distinct}")
print(f"davon mit TEST + OATH + PROOF     : {len(hits)}")
for h in hits: print("   ", h["across"], h["down"])
json.dump({"total":total,"distinct":distinct,"themed":hits}, open("census.json","w"), indent=1)
