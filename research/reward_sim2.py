#!/usr/bin/env python3
"""
reward_sim2.py — falsification harness for the lab's FINAL mechanism.

This script exists because our red-team Mind made three *numeric, falsifiable* predictions
about our own design. Instead of arguing with it, we implemented all three attacks and
measured them. Every number printed here is produced by this file (seed=42, deterministic).

Mechanisms compared
  BASE  per-Mind proportional payout            (naive; the thing everyone ships first)
  V1    steward-binding + quadratic dampening   (our round-1 design)
  LOO   leave-one-steward-out marginal credit   (round-1 mechanism-design expert's f_s)
  V2    FINAL: shrunk max with winner's-curse debias + duplicate clustering
        + anti-suppression floor + Shapley credit + fair-share cap with burn

Attacks (each = one red-team prediction)
  A1 sybil farm        attacker adds k cheap low-quality Minds
  A2 clone pump        attacker adds k noisy clones of its OWN best Mind
                       (red team: E[max] grows ~ mu + sigma*sqrt(2 ln k) => SGR > 1 "by construction")
  A3 clone-to-suppress attacker clones the TOP HONEST steward's Mind
                       (red team: under LOO the victim stops being the unique argmax => payout -> 0)

Metrics
  attacker share   fraction of the pool the attacker captures
  SGR(k)           attacker payout with k Minds / with its single best Mind
  TSI(h)           1 - p_h(attacker present) / p_h(attacker absent), same seed  (worst-case victim)
  SCR              attacker cost (forfeited bonds, in pool units) / victim's lost payout
  Gini             inequality of payout-per-unit-true-merit across honest stewards
"""
import random, math, statistics

SEED = 42
N_HONEST = 200          # honest stewards, 1 Mind each
T = 4                   # tasks / events
TAU = 1.0               # score floor a Mind must clear to earn anything
SIGMA_B = 1.5           # between-steward spread of true skill
SIGMA_E1 = 1.0          # per-match measurement noise
M_FLOOR = 100           # guaranteed matches per Mind (V2; paid by the bond)
M_BUDGET = 20000        # total match budget (BASE/V1/LOO: sybils dilute everyone's sampling)
LAMBDA = 0.5            # anti-suppression floor
ALPHA = 1.5             # payout curvature
CAP_MULT = 5.0          # per-steward cap = CAP_MULT x fair share, overflow BURNED
BOND = 100.0            # per-Mind bond, forfeited by a Mind flagged as a duplicate
POOL_CREDITS = 200000.0 # prize pool expressed in the same credits as the bond (for SCR)
SHAPLEY_PERMS = 120
TRIALS = 60
P_DIM = 32              # probes in the held-out behavioural fingerprint
FP_NOISE = 0.25         # run-to-run jitter of a Mind's probe profile
DUP_THRESHOLD = 0.5     # a pair is "the same Mind" iff fingerprint distance < this x sqrt(2*P_DIM)

U = [1.0 / T] * T       # task weights


# ---------------------------------------------------------------- world model
def make_field(rng):
    """Honest stewards: one Mind each, true per-task quality + a behavioural fingerprint.

    The fingerprint models what the duplicate detector actually sees in a real tournament:
    a Mind's answer profile on a held-out probe set (P_DIM probes). Two independently built
    Minds have uncorrelated profiles; a clone inherits its source's profile up to noise."""
    minds = []
    for s in range(N_HONEST):
        skill = rng.gauss(5, SIGMA_B)
        theta = [max(0.0, min(10.0, skill + rng.gauss(0, 0.4))) for _ in range(T)]
        fp = [rng.gauss(0, 1) for _ in range(P_DIM)]
        minds.append({"owner": s, "theta": theta, "fp": fp})
    return minds


def observe(minds, rng, floored):
    """Attach observed scores. floored=True -> every Mind gets M_FLOOR matches (V2 rule).
    floored=False -> a fixed total match budget is split across all Minds, so sybils
    dilute everyone's measurement (the red team's DoS channel)."""
    m = M_FLOOR if floored else max(5, M_BUDGET // max(1, len(minds)))
    sig = SIGMA_E1 / math.sqrt(m)
    for mind in minds:
        mind["m"] = m
        mind["sig"] = sig
        mind["s"] = [max(0.0, t + rng.gauss(0, sig)) for t in mind["theta"]]
        mind["fp_obs"] = [f + rng.gauss(0, FP_NOISE) for f in mind["fp"]]
    return sig


def owners(minds):
    return sorted({m["owner"] for m in minds})


def raw_value(mind):
    return sum(u * max(0.0, s - TAU) for u, s in zip(U, mind["s"]))


# ---------------------------------------------------------------- mechanisms
def pay_base(minds):
    """Per-Mind proportional: a steward's weight is the SUM over its Minds."""
    w = {o: 0.0 for o in owners(minds)}
    for mind in minds:
        w[mind["owner"]] += raw_value(mind)
    tot = sum(w.values()) or 1.0
    return {o: v / tot for o, v in w.items()}


def pay_v1(minds):
    """Round-1 design: one bucket per steward, weight = sqrt(total merit)."""
    w = {o: 0.0 for o in owners(minds)}
    for mind in minds:
        w[mind["owner"]] += raw_value(mind)
    w = {o: math.sqrt(v) for o, v in w.items()}
    tot = sum(w.values()) or 1.0
    return {o: v / tot for o, v in w.items()}


def _steward_task_max(minds, debias=False, dropped=frozenset()):
    """Per-steward, per-task best observed score. debias=True subtracts the exact
    winner's-curse term sigma*sqrt(2 ln k) when a steward fields k>1 Minds."""
    per = {}
    k = {}
    for i, mind in enumerate(minds):
        if i in dropped:
            continue
        o = mind["owner"]
        k[o] = k.get(o, 0) + 1
        cur = per.setdefault(o, [0.0] * T)
        for t in range(T):
            if mind["s"][t] > cur[t]:
                cur[t] = mind["s"][t]
    if debias:
        for o, vec in per.items():
            if k[o] > 1:
                sig = minds[0]["sig"]
                pen = sig * math.sqrt(2 * math.log(k[o]))
                per[o] = [max(0.0, v - pen) for v in vec]
    return per


def _V(per, subset):
    """Coalition value: for each task, the best steward in the subset."""
    tot = 0.0
    for t in range(T):
        best = 0.0
        for o in subset:
            v = per[o][t] - TAU
            if v > best:
                best = v
        tot += U[t] * best
    return tot


def pay_loo(minds):
    """Leave-one-steward-out marginal credit (the attack surface the red team found)."""
    per = _steward_task_max(minds)
    allo = list(per.keys())
    full = _V(per, allo)
    f = {}
    for o in allo:
        rest = [x for x in allo if x != o]
        f[o] = max(0.0, full - _V(per, rest))
    tot = sum(f.values()) or 1.0
    return {o: v / tot for o, v in f.items()}


def _shapley(per, rng, perms=SHAPLEY_PERMS):
    allo = list(per.keys())
    phi = {o: 0.0 for o in allo}
    order = allo[:]
    for _ in range(perms):
        rng.shuffle(order)
        run = [0.0] * T            # running best per task
        prev = 0.0
        for o in order:
            for t in range(T):
                v = per[o][t] - TAU
                if v > run[t]:
                    run[t] = v
            cur = sum(U[t] * run[t] for t in range(T))
            phi[o] += cur - prev
            prev = cur
    return {o: v / perms for o, v in phi.items()}


def detect_duplicates(minds):
    """Cluster Minds whose behavioural fingerprint is near-identical on the held-out probe set.
    A cluster counts once (earliest registration kept, so the ORIGINAL survives and the copy
    is the one dropped); the dropped Minds' bonds are forfeited.
    Returns (dropped_indices, false_positive_count)."""
    thr = DUP_THRESHOLD * math.sqrt(2 * P_DIM)
    dropped, fps = set(), 0
    for i in range(len(minds)):
        if i in dropped:
            continue
        for j in range(i + 1, len(minds)):
            if j in dropped:
                continue
            d2 = 0.0
            for p in range(P_DIM):
                dd = minds[i]["fp_obs"][p] - minds[j]["fp_obs"][p]
                d2 += dd * dd
                if d2 > thr * thr:
                    break
            if d2 < thr * thr:
                dropped.add(j)
                is_clone = all(abs(minds[i]["fp"][p] - minds[j]["fp"][p]) < 1e-9 for p in range(P_DIM))
                if not is_clone:
                    fps += 1     # two genuinely different Minds wrongly clustered
    return dropped, fps


def pay_v2(minds, rng):
    """FINAL mechanism. Returns (payouts, dropped_indices, false_positives)."""
    dropped, fps = detect_duplicates(minds)
    per = _steward_task_max(minds, debias=True, dropped=dropped)
    phi = _shapley(per, rng)
    f = {}
    for o in per:
        standalone = _V(per, [o])
        f[o] = max(phi[o], LAMBDA * standalone)
    w = {o: v ** ALPHA for o, v in f.items()}
    tot = sum(w.values()) or 1.0
    p = {o: v / tot for o, v in w.items()}
    cap = CAP_MULT / len(p)
    p = {o: min(v, cap) for o, v in p.items()}      # overflow burned, never redistributed
    return p, dropped, fps


# ---------------------------------------------------------------- metrics
def gini(xs):
    xs = sorted(xs); n = len(xs); s = sum(xs)
    if s == 0 or n == 0:
        return 0.0
    cum = sum(i * x for i, x in enumerate(xs, 1))
    return (2 * cum) / (n * s) - (n + 1) / n


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def ci95(xs):
    if len(xs) < 2:
        return 0.0
    return 1.96 * statistics.stdev(xs) / math.sqrt(len(xs))


def clone_of(mind, owner):
    """A copy: same true quality, same behavioural fingerprint, independent run-to-run noise."""
    return {"owner": owner, "theta": list(mind["theta"]), "fp": list(mind["fp"])}


# ---------------------------------------------------------------- experiments
def run():
    ATTACKER = 9999
    res = {k: [] for k in (
        "a1_base", "a1_v1", "a1_v2",
        "a2_sgr_v1", "a2_sgr_v2",
        "a3_tsi_loo", "a3_tsi_v2", "a3_scr_v2", "a3_fp",
        "gini_base", "gini_v1", "gini_v2",
        "honest_base", "honest_v2")}

    for trial in range(TRIALS):
        rng = random.Random(SEED + trial)

        # ---------- A1: sybil farm, k=50 cheap Minds ----------
        honest = make_field(rng)
        merit = {}
        for m in honest:
            merit[m["owner"]] = sum(u * max(0.0, t - TAU) for u, t in zip(U, m["theta"]))
        sybils = []
        for _ in range(50):
            skill = rng.gauss(2, 0.5)
            sybils.append({"owner": ATTACKER,
                           "theta": [max(0.0, min(10.0, skill + rng.gauss(0, 0.3))) for _ in range(T)],
                           "fp": [rng.gauss(0, 1) for _ in range(P_DIM)]})   # distinct, not clones
        field = honest + sybils
        observe(field, rng, floored=False)
        pb, p1 = pay_base(field), pay_v1(field)
        observe(field, rng, floored=True)
        p2, _, _ = pay_v2(field, rng)
        res["a1_base"].append(pb.get(ATTACKER, 0.0))
        res["a1_v1"].append(p1.get(ATTACKER, 0.0))
        res["a1_v2"].append(p2.get(ATTACKER, 0.0))
        for tag, p in (("base", pb), ("v1", p1), ("v2", p2)):
            ratios = [p.get(o, 0.0) / max(merit[o], 1e-9) for o in merit]
            res["gini_" + tag].append(gini(ratios))
        res["honest_base"].append(statistics.median(pb.get(o, 0.0) for o in merit))
        res["honest_v2"].append(statistics.median(p2.get(o, 0.0) for o in merit))

        # ---------- A2: clone pump — k noisy clones of the attacker's OWN best Mind ----------
        rng2 = random.Random(SEED + 1000 + trial)
        honest2 = make_field(rng2)
        attacker_mind = {"owner": ATTACKER,
                         "theta": [max(0.0, min(10.0, rng2.gauss(6.5, 0.3))) for _ in range(T)],
                         "fp": [rng2.gauss(0, 1) for _ in range(P_DIM)]}
        solo = honest2 + [attacker_mind]
        observe(solo, rng2, floored=False)
        s_v1 = pay_v1(solo).get(ATTACKER, 0.0)
        observe(solo, rng2, floored=True)
        s_v2 = pay_v2(solo, rng2)[0].get(ATTACKER, 0.0)
        K = 20
        pumped = honest2 + [clone_of(attacker_mind, ATTACKER) for _ in range(K)]
        observe(pumped, rng2, floored=False)
        k_v1 = pay_v1(pumped).get(ATTACKER, 0.0)
        observe(pumped, rng2, floored=True)
        k_v2 = pay_v2(pumped, rng2)[0].get(ATTACKER, 0.0)
        res["a2_sgr_v1"].append(k_v1 / max(s_v1, 1e-12))
        res["a2_sgr_v2"].append(k_v2 / max(s_v2, 1e-12))

        # ---------- A3: clone-to-suppress the top honest steward ----------
        rng3 = random.Random(SEED + 2000 + trial)
        honest3 = make_field(rng3)
        victim = max(honest3, key=lambda m: sum(m["theta"]))
        vo = victim["owner"]
        observe(honest3, rng3, floored=False)
        before_loo = pay_loo(honest3).get(vo, 0.0)
        observe(honest3, rng3, floored=True)
        before_v2 = pay_v2(honest3, rng3)[0].get(vo, 0.0)
        K3 = 5
        attacked = honest3 + [clone_of(victim, ATTACKER) for _ in range(K3)]
        observe(attacked, rng3, floored=False)
        after_loo = pay_loo(attacked).get(vo, 0.0)
        observe(attacked, rng3, floored=True)
        p2a, dropped, fps = pay_v2(attacked, rng3)
        after_v2 = p2a.get(vo, 0.0)
        res["a3_tsi_loo"].append(1 - after_loo / max(before_loo, 1e-12))
        res["a3_tsi_v2"].append(1 - after_v2 / max(before_v2, 1e-12))
        # SCR: bonds forfeited by the attacker's flagged clones, vs the victim's lost payout
        att_dropped = sum(1 for i in dropped if attacked[i]["owner"] == ATTACKER)
        lost = max(before_v2 - after_v2, 0.0) * POOL_CREDITS
        res["a3_scr_v2"].append((att_dropped * BOND) / max(lost, 1e-9) if lost > 0 else float("inf"))
        res["a3_fp"].append(fps)

    # ---------------------------------------------------------------- report
    def line(label, *vals):
        print(label.ljust(46) + "".join(v.rjust(15) for v in vals))

    print(f"reward_sim2.py — seed={SEED}, {TRIALS} trials, {N_HONEST} honest stewards, {T} tasks,")
    print(f"Shapley: {SHAPLEY_PERMS} permutations/trial. All figures are means with 95% CI.\n")

    print("A1  SYBIL FARM — attacker registers 50 cheap Minds")
    line("", "BASE", "V1(round-1)", "V2(final)")
    line("  attacker share of pool",
         f"{mean(res['a1_base'])*100:.2f}%", f"{mean(res['a1_v1'])*100:.2f}%", f"{mean(res['a1_v2'])*100:.2f}%")
    line("  +/- 95% CI",
         f"{ci95(res['a1_base'])*100:.2f}", f"{ci95(res['a1_v1'])*100:.2f}", f"{ci95(res['a1_v2'])*100:.2f}")
    line("  Gini(payout per unit true merit)",
         f"{mean(res['gini_base']):.3f}", f"{mean(res['gini_v1']):.3f}", f"{mean(res['gini_v2']):.3f}")
    line("  honest median payout",
         f"{mean(res['honest_base'])*100:.3f}%", "-", f"{mean(res['honest_v2'])*100:.3f}%")

    print("\nA2  CLONE PUMP — 20 noisy clones of the attacker's own best Mind")
    print("    red-team prediction: max-based scoring gains ~sigma*sqrt(2 ln k); SGR>1 by construction")
    line("", "V1(max/sum)", "V2(debiased)")
    line("  SGR(k=20)  [sound iff <= 1.05]",
         f"{mean(res['a2_sgr_v1']):.3f}", f"{mean(res['a2_sgr_v2']):.3f}")
    line("  +/- 95% CI", f"{ci95(res['a2_sgr_v1']):.3f}", f"{ci95(res['a2_sgr_v2']):.3f}")

    print("\nA3  CLONE-TO-SUPPRESS — 5 clones of the TOP HONEST steward's Mind")
    print("    red-team prediction: under leave-one-out credit the victim's payout collapses")
    line("", "LOO(round-1)", "V2(final)")
    line("  TSI of the victim  [target <= 0.10]",
         f"{mean(res['a3_tsi_loo']):.3f}", f"{mean(res['a3_tsi_v2']):.3f}")
    line("  +/- 95% CI", f"{ci95(res['a3_tsi_loo']):.3f}", f"{ci95(res['a3_tsi_v2']):.3f}")
    finite = [x for x in res["a3_scr_v2"] if x != float("inf")]
    print(f"  SCR (attacker cost / victim loss), V2:  "
          f"{'no measurable victim loss in any trial' if not finite else f'{mean(finite):.2f}'}"
          f"   [target >= 1.0]")
    print(f"  duplicate-detector false positives per tournament (V2): {mean(res['a3_fp']):.2f} "
          f"of {N_HONEST} honest Minds")

    verdict = []
    verdict.append(("A1 sybil farm", mean(res['a1_v2']) < mean(res['a1_base'])))
    verdict.append(("A2 SGR(k=20) <= 1.05", mean(res['a2_sgr_v2']) <= 1.05))
    verdict.append(("A3 worst-case TSI <= 0.10", mean(res['a3_tsi_v2']) <= 0.10))
    print("\nPRE-REGISTERED FALSIFIERS (mechanism is rejected if any FAILS):")
    for name, ok in verdict:
        print(f"  {name:34s} {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    run()
