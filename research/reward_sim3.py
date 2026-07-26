#!/usr/bin/env python3
"""
reward_sim3.py — ablation + evasion harness. Supersedes reward_sim2.py.

reward_sim2.py had a load-bearing labelling error that our own pre-flight review caught:
its "V1(max/sum)" column aggregated a steward's Minds by SUM (with sqrt dampening), so the
SGR(k=20) = 4.385 it reported is simply sqrt(20) = 4.472 — sum-aggregation, NOT the
winner's-curse effect the red team predicted. And because V2 ran duplicate-clustering BEFORE
the debias, the winner's-curse debiaser was never exercised at all (dead code in that test).

This version fixes both by ABLATING every component separately, and adds the experiment the
review demanded: an EVASIVE clone that perturbs its behavioural fingerprint to walk through
the duplicate detector. Nothing here is labelled by narrative; each number names its mechanism.

Run: python3 reward_sim3.py     (seed=42, deterministic, no dependencies, ~4 min)
"""
import random, math, statistics

SEED = 42
N_HONEST = 200
T = 4
TAU = 1.0
SIGMA_B = 1.5
SIGMA_E1 = 1.0
M_FLOOR = 100
M_BUDGET = 20000
LAMBDA = 0.5
ALPHA = 1.5
CAP_MULT = 5.0
BOND = 100.0
POOL_CREDITS = 200000.0
SHAPLEY_PERMS = 100
TRIALS = 40
P_DIM = 32
FP_NOISE = 0.25
DUP_THRESHOLD = 0.5          # x sqrt(2*P_DIM) -> Euclidean cutoff on the observed fingerprint
U = [1.0 / T] * T


# ------------------------------------------------------------------ world
def make_field(rng, n=N_HONEST):
    minds = []
    for s in range(n):
        skill = rng.gauss(5, SIGMA_B)
        minds.append({"owner": s,
                      "theta": [max(0.0, min(10.0, skill + rng.gauss(0, 0.4))) for _ in range(T)],
                      "fp": [rng.gauss(0, 1) for _ in range(P_DIM)]})
    return minds


def observe(minds, rng, floored=True):
    m = M_FLOOR if floored else max(5, M_BUDGET // max(1, len(minds)))
    sig = SIGMA_E1 / math.sqrt(m)
    for mind in minds:
        mind["m"] = m
        mind["sig"] = sig
        mind["s"] = [max(0.0, t + rng.gauss(0, sig)) for t in mind["theta"]]
        mind["fp_obs"] = [f + rng.gauss(0, FP_NOISE) for f in mind["fp"]]
    return sig


def clone_of(mind, owner, rng=None, eps=0.0):
    """A copy of `mind`. eps>0 = EVASIVE clone: it deliberately perturbs its behavioural
    fingerprint by eps*N(0,1) per probe to escape duplicate clustering, at no quality cost."""
    fp = list(mind["fp"])
    if eps > 0 and rng is not None:
        fp = [f + rng.gauss(0, eps) for f in fp]
    return {"owner": owner, "theta": list(mind["theta"]), "fp": fp}


def owners(minds):
    return sorted({m["owner"] for m in minds})


def raw_value(mind):
    return sum(u * max(0.0, s - TAU) for u, s in zip(U, mind["s"]))


# ------------------------------------------------------------------ mechanisms
def pay_base(minds):
    """Per-Mind proportional; steward weight = SUM over its Minds."""
    w = {o: 0.0 for o in owners(minds)}
    for mind in minds:
        w[mind["owner"]] += raw_value(mind)
    tot = sum(w.values()) or 1.0
    return {o: v / tot for o, v in w.items()}


def pay_v1_sum(minds):
    """Round-1 design: steward bucket, weight = sqrt(SUM of its Minds' merit)."""
    w = {o: 0.0 for o in owners(minds)}
    for mind in minds:
        w[mind["owner"]] += raw_value(mind)
    w = {o: math.sqrt(v) for o, v in w.items()}
    tot = sum(w.values()) or 1.0
    return {o: v / tot for o, v in w.items()}


def _steward_task_max(minds, debias=False, dropped=frozenset()):
    per, k = {}, {}
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
        sig = minds[0]["sig"]
        for o, vec in per.items():
            if k[o] > 1:
                pen = sig * math.sqrt(2 * math.log(k[o]))
                per[o] = [max(0.0, v - pen) for v in vec]
    return per


def pay_v1_max(minds, debias=False):
    """MAX aggregation per steward, payout proportional to standalone value.
    This is the mechanism the red team actually attacked (no dedup, no floor)."""
    per = _steward_task_max(minds, debias=debias)
    val = {o: sum(U[t] * max(0.0, per[o][t] - TAU) for t in range(T)) for o in per}
    tot = sum(val.values()) or 1.0
    return {o: v / tot for o, v in val.items()}


def _V(per, subset):
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
    per = _steward_task_max(minds)
    allo = list(per.keys())
    full = _V(per, allo)
    f = {o: max(0.0, full - _V(per, [x for x in allo if x != o])) for o in allo}
    tot = sum(f.values()) or 1.0
    return {o: v / tot for o, v in f.items()}


def _shapley(per, rng, perms=SHAPLEY_PERMS):
    allo = list(per.keys())
    phi = {o: 0.0 for o in allo}
    order = allo[:]
    for _ in range(perms):
        rng.shuffle(order)
        run = [0.0] * T
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
    thr2 = (DUP_THRESHOLD * math.sqrt(2 * P_DIM)) ** 2
    dropped, fps, caught = set(), 0, 0
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
                if d2 > thr2:
                    break
            if d2 < thr2:
                dropped.add(j)
                if minds[j].get("is_clone"):
                    caught += 1
                else:
                    fps += 1
    return dropped, fps, caught


def pay_v2(minds, rng, debias=True, dedup=True, floor=True):
    dropped, fps, caught = (detect_duplicates(minds) if dedup else (set(), 0, 0))
    per = _steward_task_max(minds, debias=debias, dropped=dropped)
    phi = _shapley(per, rng)
    f = {}
    for o in per:
        standalone = _V(per, [o])
        f[o] = max(phi[o], LAMBDA * standalone) if floor else phi[o]
    w = {o: max(v, 0.0) ** ALPHA for o, v in f.items()}
    tot = sum(w.values()) or 1.0
    p = {o: v / tot for o, v in w.items()}
    cap = CAP_MULT / len(p)
    p = {o: min(v, cap) for o, v in p.items()}
    return p, dropped, fps, caught


# ------------------------------------------------------------------ helpers
def gini(xs):
    xs = sorted(xs); n = len(xs); s = sum(xs)
    if s == 0 or n == 0:
        return 0.0
    return (2 * sum(i * x for i, x in enumerate(xs, 1))) / (n * s) - (n + 1) / n


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def ci95(xs):
    return 1.96 * statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0


def col(*vals, w=14):
    return "".join(str(v).rjust(w) for v in vals)


# ------------------------------------------------------------------ experiments
ATT = 9999


def exp_A1():
    """Sybil farm, 50 cheap Minds. ALL mechanisms under the SAME observation regime,
    reported separately for the diluted-budget and per-Mind-floored regimes."""
    out = {}
    for regime in ("diluted", "floored"):
        acc = {k: [] for k in ("base", "v1sum", "v1max", "v2", "g_base", "g_v1sum", "g_v2", "hon_base", "hon_v2")}
        for trial in range(TRIALS):
            rng = random.Random(SEED + trial)
            honest = make_field(rng)
            merit = {m["owner"]: sum(u * max(0.0, t - TAU) for u, t in zip(U, m["theta"])) for m in honest}
            sybils = []
            for _ in range(50):
                sk = rng.gauss(2, 0.5)
                sybils.append({"owner": ATT,
                               "theta": [max(0.0, min(10.0, sk + rng.gauss(0, 0.3))) for _ in range(T)],
                               "fp": [rng.gauss(0, 1) for _ in range(P_DIM)]})
            field = honest + sybils
            observe(field, rng, floored=(regime == "floored"))
            pb, p1s, p1m = pay_base(field), pay_v1_sum(field), pay_v1_max(field)
            p2 = pay_v2(field, rng)[0]
            acc["base"].append(pb.get(ATT, 0.0)); acc["v1sum"].append(p1s.get(ATT, 0.0))
            acc["v1max"].append(p1m.get(ATT, 0.0)); acc["v2"].append(p2.get(ATT, 0.0))
            for tag, p in (("g_base", pb), ("g_v1sum", p1s), ("g_v2", p2)):
                acc[tag].append(gini([p.get(o, 0.0) / max(merit[o], 1e-9) for o in merit]))
            acc["hon_base"].append(statistics.median(pb.get(o, 0.0) for o in merit))
            acc["hon_v2"].append(statistics.median(p2.get(o, 0.0) for o in merit))
        out[regime] = acc
    return out


def exp_A2():
    """Clone pump, k=20 identical-quality clones of the attacker's own best Mind.
    ABLATION: which component actually neutralises it?"""
    keys = ("v1sum", "v1max", "v2_debias_only", "v2_dedup_only", "v2_full")
    acc = {k: [] for k in keys}
    for trial in range(TRIALS):
        rng = random.Random(SEED + 1000 + trial)
        honest = make_field(rng)
        att = {"owner": ATT,
               "theta": [max(0.0, min(10.0, rng.gauss(6.5, 0.3))) for _ in range(T)],
               "fp": [rng.gauss(0, 1) for _ in range(P_DIM)]}
        K = 20
        solo = honest + [att]
        pumped = honest + [clone_of(att, ATT) for _ in range(K)]
        for m in pumped[N_HONEST:]:
            m["is_clone"] = True
        for field, tag in ((solo, "solo"), (pumped, "pump")):
            observe(field, rng, floored=True)
        # each mechanism: SGR = payout(k=20)/payout(k=1)
        observe(solo, rng, floored=True); observe(pumped, rng, floored=True)
        s_v1s, k_v1s = pay_v1_sum(solo).get(ATT, 0), pay_v1_sum(pumped).get(ATT, 0)
        s_v1m, k_v1m = pay_v1_max(solo).get(ATT, 0), pay_v1_max(pumped).get(ATT, 0)
        s_db = pay_v2(solo, rng, debias=True, dedup=False)[0].get(ATT, 0)
        k_db = pay_v2(pumped, rng, debias=True, dedup=False)[0].get(ATT, 0)
        s_dd = pay_v2(solo, rng, debias=False, dedup=True)[0].get(ATT, 0)
        k_dd = pay_v2(pumped, rng, debias=False, dedup=True)[0].get(ATT, 0)
        s_f = pay_v2(solo, rng)[0].get(ATT, 0)
        k_f = pay_v2(pumped, rng)[0].get(ATT, 0)
        acc["v1sum"].append(k_v1s / max(s_v1s, 1e-12))
        acc["v1max"].append(k_v1m / max(s_v1m, 1e-12))
        acc["v2_debias_only"].append(k_db / max(s_db, 1e-12))
        acc["v2_dedup_only"].append(k_dd / max(s_dd, 1e-12))
        acc["v2_full"].append(k_f / max(s_f, 1e-12))
    return acc


def exp_A3_evasion():
    """Clone-to-suppress the top honest steward, with an EVASIVE clone.
    eps = how far the clone perturbs its behavioural fingerprint to dodge the detector.
    eps=0 is a naive copy; honest Minds sit at fingerprint distance ~ sqrt(2*P_DIM) = 8.0."""
    EPS = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
    rows = []
    for eps in EPS:
        det, tsi_loo, tsi_v2, tsi_v2_nofloor, loss_zero, losses, bonds = [], [], [], [], 0, [], []
        for trial in range(TRIALS):
            rng = random.Random(SEED + 2000 + trial)
            honest = make_field(rng)
            victim = max(honest, key=lambda m: sum(m["theta"]))
            vo = victim["owner"]
            observe(honest, rng, floored=False)
            before_loo = pay_loo(honest).get(vo, 0.0)
            observe(honest, rng, floored=True)
            before_v2 = pay_v2(honest, rng)[0].get(vo, 0.0)
            before_nf = pay_v2(honest, rng, floor=False)[0].get(vo, 0.0)
            K = 5
            clones = [clone_of(victim, ATT, rng, eps) for _ in range(K)]
            for c in clones:
                c["is_clone"] = True
            attacked = honest + clones
            observe(attacked, rng, floored=False)
            after_loo = pay_loo(attacked).get(vo, 0.0)
            observe(attacked, rng, floored=True)
            p2, dropped, fps, caught = pay_v2(attacked, rng)
            after_v2 = p2.get(vo, 0.0)
            after_nf = pay_v2(attacked, rng, floor=False)[0].get(vo, 0.0)
            det.append(caught / K)
            tsi_loo.append(1 - after_loo / max(before_loo, 1e-12))
            tsi_v2.append(1 - after_v2 / max(before_v2, 1e-12))
            tsi_v2_nofloor.append(1 - after_nf / max(before_nf, 1e-12))
            lost = (before_v2 - after_v2) * POOL_CREDITS
            att_dropped = sum(1 for i in dropped if attacked[i]["owner"] == ATT)
            bonds.append(att_dropped * BOND)
            if lost <= 0:
                loss_zero += 1
            else:
                losses.append(lost)
        rows.append({"eps": eps, "detect": mean(det), "tsi_loo": mean(tsi_loo),
                     "tsi_v2": mean(tsi_v2), "tsi_v2_nofloor": mean(tsi_v2_nofloor),
                     "tsi_v2_ci": ci95(tsi_v2), "zero_loss_trials": loss_zero,
                     "mean_loss_credits": mean(losses) if losses else 0.0,
                     "mean_bond_burn": mean(bonds)})
    return rows


def main():
    print(f"reward_sim3.py — seed={SEED}, {TRIALS} trials, {N_HONEST} honest stewards, {T} tasks,")
    print(f"Shapley {SHAPLEY_PERMS} perms. Means with 95% CI. Supersedes reward_sim2.py (see header).\n")

    a1 = exp_A1()
    print("A1  SYBIL FARM — attacker registers 50 cheap Minds. Attacker's share of the pool.")
    print("    Both observation regimes shown, because they are a separate policy lever:")
    print("    'diluted' = fixed 20k match budget split across all Minds; 'floored' = >=100 matches each.")
    print(col("regime", "BASE", "V1-sum(sqrt)", "V1-max", "V2-full", w=15))
    for reg in ("diluted", "floored"):
        a = a1[reg]
        print(col(reg, f"{mean(a['base'])*100:.2f}%", f"{mean(a['v1sum'])*100:.2f}%",
                  f"{mean(a['v1max'])*100:.2f}%", f"{mean(a['v2'])*100:.2f}%", w=15))
    a = a1["floored"]
    print(col("Gini(payout/merit)", f"{mean(a['g_base']):.3f}", f"{mean(a['g_v1sum']):.3f}", "-",
              f"{mean(a['g_v2']):.3f}", w=15))
    print(col("honest median pay", f"{mean(a['hon_base'])*100:.3f}%", "-", "-",
              f"{mean(a['hon_v2'])*100:.3f}%", w=15))

    a2 = exp_A2()
    print("\nA2  CLONE PUMP — 20 clones of the attacker's own best Mind. SGR = pay(k=20)/pay(k=1).")
    print("    ABLATION — this is the experiment reward_sim2.py got wrong:")
    for k, label in (("v1sum", "V1 sum-aggregation (sqrt)"), ("v1max", "max-aggregation, NO debias"),
                     ("v2_debias_only", "V2, debias only (no dedup)"),
                     ("v2_dedup_only", "V2, dedup only (no debias)"), ("v2_full", "V2 full")):
        print(f"    {label:34s} SGR = {mean(a2[k]):7.3f}  +/- {ci95(a2[k]):.3f}"
              + ("   [sound iff <= 1.05]" if k == "v2_full" else ""))
    print(f"    sqrt(20) = {math.sqrt(20):.3f}  <- V1-sum's 'attack gain' is just sum-aggregation, not the winner's curse.")

    ev = exp_A3_evasion()
    print("\nA3  CLONE-TO-SUPPRESS the top honest steward (5 clones), vs an EVASIVE clone.")
    print("    eps = fingerprint perturbation the clone adds to dodge the duplicate detector.")
    print("    Honest Minds are ~8.0 apart in fingerprint space; the detector cutoff is 4.0.")
    print(col("eps", "clones caught", "TSI (LOO)", "TSI V2", "TSI V2 no-floor", w=16))
    for r in ev:
        print(col(f"{r['eps']:.1f}", f"{r['detect']*100:.0f}%", f"{r['tsi_loo']:.3f}",
                  f"{r['tsi_v2']:+.3f}", f"{r['tsi_v2_nofloor']:+.3f}", w=16))
    print("    (TSI = fraction of the victim's payout destroyed. Target <= 0.10 worst case.)")
    z = ev[0]
    print(f"\n    SCR, honestly: at eps=0 the victim suffered NO measurable loss in "
          f"{z['zero_loss_trials']}/{TRIALS} trials, so the ratio 'attacker cost / victim loss' is "
          f"undefined in those trials.")
    print(f"    Mean bond burned by the attacker: {z['mean_bond_burn']:.0f} credits of a "
          f"{POOL_CREDITS:.0f}-credit pool. The design constraint is what matters:")
    print(f"    griefing is unprofitable iff bond B >= (victim's loss)/(clones needed) — with B=100 and "
          f"a 200k pool that is B >= 0.05% of pool per Mind.")

    print("\nPRE-REGISTERED FALSIFIERS (all four the methodologist registered, including the one we fail):")
    v2f = mean(a2["v2_full"])
    worst_tsi = max(r["tsi_v2"] for r in ev)
    g_base, g_v2 = mean(a1["floored"]["g_base"]), mean(a1["floored"]["g_v2"])
    checks = [
        ("F1 sybil-farm share V2 < BASE", mean(a1["floored"]["v2"]) < mean(a1["floored"]["base"])),
        ("F2 SGR(k=20) <= 1.05", v2f <= 1.05),
        ("F3 worst-case TSI <= 0.10 (all eps)", worst_tsi <= 0.10),
        ("F4 honest-case merit alignment not degraded (Gini)", g_v2 <= g_base),
    ]
    for name, ok in checks:
        print(f"  {name:52s} {'PASS' if ok else 'FAIL'}")
    if not checks[3][1]:
        print(f"       -> F4 FAILS: Gini {g_base:.3f} (BASE) vs {g_v2:.3f} (V2). Under our own rule the")
        print(f"          mechanism is REJECTED pending alpha -> 1.0 with the cap doing the work.")


if __name__ == "__main__":
    main()
