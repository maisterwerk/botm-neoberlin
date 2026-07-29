import json, math, numpy as np
data = json.load(open("geo/ap_daily.json"))
SYN=29.530588853; NEWMOON_JD=2451550.1
def jd(y,m,d):
    if m<=2: y-=1; m+=12
    A=y//100; B=2-A+A//4
    return int(365.25*(y+4716))+int(30.6001*(m+1))+d+B-1524.5
ap=[]; lab=[]
for row in data:
    y,mo,dd=row[0],row[1],row[2]; a=row[-1]
    if a is None: continue
    frac=((jd(y,mo,dd)-NEWMOON_JD)%SYN)/SYN
    ap.append(float(a)); lab.append(int((frac*8+0.5)%8))
ap=np.array(ap); lab=np.array(lab); N=len(ap)
overall=ap.mean(); sd=ap.std()
names=["New","WaxCres","FirstQ","WaxGib","Full","WanGib","LastQ","WanCres"]
sums=np.bincount(lab,weights=ap,minlength=8); cnts=np.bincount(lab,minlength=8)
means=sums/cnts
obs=np.max(np.abs(means-overall))
maxd=np.max(np.abs(means-overall)/sd)
print(f"N={N} overall={overall:.4f} sd={sd:.4f}")
for b in range(8):
    print(f"{names[b]:<8} n={cnts[b]:<6} mean={means[b]:.4f} d={(means[b]-overall)/sd:+.4f}")
# exact circular-rotation null, vectorized: roll ap against fixed labels
trials=6000; step=max(1,N//trials)
shifts=list(range(0,N,step)); ge=0; mx=0.0
for sh in shifts:
    apr=np.roll(ap,sh)
    s=np.bincount(lab,weights=apr,minlength=8)
    m=s/cnts
    stat=np.max(np.abs(m-overall))
    if stat>=obs: ge+=1
    if stat>mx: mx=stat
p=(ge+1)/(len(shifts)+1)
print(f"\nobserved largest |bucket-overall|={obs:.4f} Ap  max_d={maxd:.4f}")
print(f"exact circular-rotation: {len(shifts)} rotations, p={p:.4f}, null_max={mx:.4f}")
json.dump({"N":int(N),"overall_ap":round(float(overall),4),
           "bucket_means":{names[b]:round(float(means[b]),4) for b in range(8)},
           "largest_excess_ap":round(float(obs),4),"max_cohens_d":round(float(maxd),4),
           "p_value":round(float(p),4),"rotations":len(shifts),
           "method":"full 94-yr GFZ Ap daily series (1932-), lunar octant buckets, exact circular-rotation null on largest |bucket mean - overall|"},
          open("lunar_ap_full.json","w"),indent=1)
print("saved lunar_ap_full.json")
