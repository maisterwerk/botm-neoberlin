# Monte Carlo for the "Quadratic-Merit + Steward Binding" reward mechanism vs a naive baseline.
# Deterministic (seeded) so the numbers are reproducible.
import random, statistics
random.seed(42)

def gini(xs):
    xs=sorted(xs); n=len(xs); s=sum(xs)
    if s==0: return 0.0
    cum=0
    for i,x in enumerate(xs,1): cum+=i*x
    return (2*cum)/(n*s) - (n+1)/n

TRIALS=2000
EVENTS=4
HONEST=100
SYBIL_MINDS=50

base_share=[]; base_gini=[]; base_hon=[]
quad_share=[]; quad_gini=[]; quad_hon=[]
for _ in range(TRIALS):
    # honest stewards: 1 mind each, merit = sum over events ~ N(5,2) clipped 0..10
    honest_merit=[]
    for _ in range(HONEST):
        m=sum(min(10,max(0,random.gauss(5,2))) for _ in range(EVENTS))
        honest_merit.append(m)
    # attacker: SYBIL_MINDS low-quality minds, each merit ~ N(2,1)
    sybil_merit_total=sum(min(10,max(0,random.gauss(2,1))) for _ in range(SYBIL_MINDS*EVENTS))

    # BASELINE: reward proportional to raw summed score, top-N by mind; attacker floods many minds
    # model: pool split proportional to each *mind's* merit; attacker has many minds
    base_weights=honest_merit+[min(10,max(0,random.gauss(2,1)))*EVENTS for _ in range(SYBIL_MINDS)]
    tot=sum(base_weights)
    attacker_base=sum(base_weights[HONEST:])/tot
    # per-steward reward for gini: honest each get their mind's share; attacker gets sum
    steward_base=[w/tot for w in honest_merit]+[attacker_base]
    steward_merit=honest_merit+[sybil_merit_total]
    base_share.append(attacker_base)
    base_gini.append(gini([s/max(m,1e-9) for s,m in zip(steward_base,steward_merit)]))
    base_hon.append(statistics.median(honest_merit)/tot)

    # QUADRATIC + STEWARD BINDING: one bucket per steward, weight=sqrt(total merit)
    import math
    q_weights=[math.sqrt(m) for m in honest_merit]+[math.sqrt(sybil_merit_total)]
    qtot=sum(q_weights)
    attacker_q=q_weights[-1]/qtot
    quad_share.append(attacker_q)
    steward_q=[w/qtot for w in q_weights]
    quad_gini.append(gini([s/max(m,1e-9) for s,m in zip(steward_q,steward_merit)]))
    quad_hon.append(statistics.median([w/qtot for w in q_weights[:HONEST]]))

def mean(x): return sum(x)/len(x)
print("Reproducible Monte Carlo (seed=42, %d trials, %d honest stewards, 1 attacker x %d sybil minds, %d events):"%(TRIALS,HONEST,SYBIL_MINDS,EVENTS))
print()
print("                                 BASELINE   QUADRATIC+BINDING")
print("Attacker reward share:            %5.1f%%      %5.1f%%" % (mean(base_share)*100, mean(quad_share)*100))
print("Gini (reward per unit merit):     %5.2f       %5.2f" % (mean(base_gini), mean(quad_gini)))
print("Honest-steward median share:      %5.3f%%     %5.3f%%" % (mean(base_hon)*100, mean(quad_hon)*100))
print()
print("Honest median payout multiplier (quad/base): %.2fx" % (mean(quad_hon)/mean(base_hon)))
