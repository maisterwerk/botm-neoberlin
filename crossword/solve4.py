import json, sys
from collections import defaultdict
src=open('solve_mini.py').read().split('if __name__')[0]
ns={}; exec(src,ns); C=ns['BY_LEN']          # nur geläufige Wörter, nichts anderes
W3,W4,W5=C[3],C[4],C[5]
# Muster:  ...##  /  .....  /  .....  /  .....  /  ##...
# Waagerecht: Z0=3, Z1..Z3=5, Z4=3
# Senkrecht : S0=Z0..Z3 (4), S1=Z0..Z3 (4), S2=Z0..Z4 (5), S3=Z1..Z4 (4), S4=Z1..Z4 (4)
end3=defaultdict(list)   # 4er nach letzten 3 Zeichen
beg3=defaultdict(list)   # 4er nach ersten 3 Zeichen
for w in W4:
    end3[w[1:]].append(w); beg3[w[:3]].append(w)
THEME=["TALLY","SCORE","COUNT","TOTAL","AUDIT","PROOF","TRUTH","CHECK","TRACK","TRUST"]
out=[]
for r1 in THEME:
    for r3 in THEME:
        if r3==r1: continue
        for r2 in sorted(W5):
            if r2 in (r1,r3): continue
            s0=end3[r1[0]+r2[0]+r3[0]]; s1=end3[r1[1]+r2[1]+r3[1]]
            s3=beg3[r1[3]+r2[3]+r3[3]]; s4=beg3[r1[4]+r2[4]+r3[4]]
            if not(s0 and s1 and s3 and s4): continue
            for a in s0:
                for b in s1:
                    for d in s3:
                        for e in s4:
                            # Zeile0 = a[0], b[0], X   |  Zeile4 = Y, d[3], e[3]
                            for col2 in W5:
                                if col2[1]!=r1[2] or col2[2]!=r2[2] or col2[3]!=r3[2]: continue
                                row0=a[0]+b[0]+col2[0]
                                row4=col2[4]+d[3]+e[3]
                                if row0 not in W3 or row4 not in W3: continue
                                acr=[row0,r1,r2,r3,row4]
                                dwn=[a,b,col2,d,e]
                                if set(acr)&set(dwn): continue
                                out.append({"grid":[row0+"##", r1, r2, r3, "##"+row4],
                                            "across":acr, "down":dwn})
seen=set(); uniq=[]
for g in out:
    k=tuple(g['grid'])
    if k not in seen: seen.add(k); uniq.append(g)
json.dump(uniq, open('grids.json','w'), indent=1)
print(f"{len(uniq)} Gitter — ausschließlich geläufige Wörter")
for g in uniq[:12]:
    print(); print("\n".join(g['grid'])); print("  A:",g['across'],"| D:",g['down'])
