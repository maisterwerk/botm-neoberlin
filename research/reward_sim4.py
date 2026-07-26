#!/usr/bin/env python3
"""
reward_sim4.py — final harness. Supersedes reward_sim3.py.

Round-6 review found a design bug that reward_sim3.py hid rather than caused:
the anti-suppression floor f_s = max(phi_s, lambda * standalone_s) mixed UNNORMALISED
Shapley credit (mean 0.0398) with UNNORMALISED standalone value (mean 2.025), so the floor
bound for 200/200 stewards, the Shapley term was computed and discarded, and V2 silently
degenerated to payout ~ (own standalone)^alpha. That makes TSI ~ 0 a tautology: a payout rule
that cannot see rivals cannot be suppressed by them.

Fixed here: the floor is applied in SHARE space, which is what it always meant --
    f_s = max( phi_s / sum(phi), lambda * standalone_s / sum(standalone) )
and the binding rate is printed, so the reader can see whether it is doing anything.

Also added, all because a reviewer asked for it:
  * James-Stein shrinkage actually implemented (it was prose-only before)
  * floor / Shapley ablation on the suppression test
  * alpha x floor sweep -> the F4 (Gini) frontier, i.e. we try to FIX the criterion we fail
  * duplicate-threshold sweep with the false-positive rate (the defender adapts too, not just
    the attacker), and a registration-order swap (what if the attacker registers FIRST?)
  * a dilution regime with enough power to actually test the per-Mind match floor

Run: python3 reward_sim4.py    (seed=42, deterministic, stdlib only, ~5 min)
"""
import random, math, statistics

SEED = 42
N_HONEST = 200
T = 4
TAU = 1.0
SIGMA_B = 1.5
SIGMA_E1 = 1.0
M_FLOOR = 100
M_BUDGET = 2000          # deliberately tight: 250 Minds -> 8 matches each, so dilution BITES
LAMBDA = 0.5
ALPHA = 1.5
CAP_MULT = 5.0
BOND = 100.0
POOL_CREDITS = 200000.0
SHAPLEY_PERMS = 80
TRIALS = 25
P_DIM = 32
FP_NOISE = 0.25
DUP_MULT = 0.5           # cutoff = DUP_MULT * sqrt(2*P_DIM) = 4.0
U = [1.0 / T] * T
ATT = 9999


# ---------------------------------------------------------------- world
def make_field(rng, n=N_HONEST):
    out = []
    for s in range(n):
        skill = rng.gauss(5, SIGMA_B)
        out.append({"owner": s,
                    "theta": [max(0.0, min(10.0, skill + rng.gauss(0, 0.4))) for _ in range(T)],
                    "fp": [rng.gauss(0, 1) for _ in range(P_DIM)]})
    return out


def observe(minds, rng, floored=True):
    m = M_FLOOR if floored else max(2, M_BUDGET // max(1, len(minds)))
    sig = SIGMA_E1 / math.sqrt(m)
    for mind in minds:
        mind["m"] = m; mind["sig"] = sig
        mind["s_raw"] = [max(0.0, t + rng.gauss(0, sig)) for t in mind["theta"]]
        mind["fp_obs"] = [f + rng.gauss(0, FP_NOISE) for f in mind["fp"]]
    shrink(minds, sig)
    return sig


def shrink(minds, sig):
    """James-Stein / empirical-Bayes shrinkage toward the field mean, per task.
    B = sigma_b^2 / (sigma_b^2 + sigma_e^2/m). Previously claimed but never implemented."""
    for t in range(T):
        vals = [m["s_raw"][t] for m in minds]
        mu = sum(vals) / len(vals)
        var = statistics.pvariance(vals) if len(vals) > 1 else 1.0
        between = max(1e-9, var - sig * sig)
        B = between / (between + sig * sig)
        for m in minds:
            m.setdefault("s", [0.0] * T)
            m["s"][t] = mu + B * (m["s_raw"][t] - mu)


def clone_of(mind, owner, rng=None, eps=0.0):
    fp = list(mind["fp"])
    if eps > 0 and rng is not None:
        fp = [f + rng.gauss(0, eps) for f in fp]
    return {"owner": owner, "theta": list(mind["theta"]), "fp": fp}


def owners(minds):
    return sorted({m["owner"] for m in minds})


def raw_value(mind):
    return sum(u * max(0.0, s - TAU) for u, s in zip(U, mind["s"]))


# ---------------------------------------------------------------- mechanisms
def pay_base(minds):
    w = {o: 0.0 for o in owners(minds)}
    for m in minds:
        w[m["owner"]] += raw_value(m)
    tot = sum(w.values()) or 1.0
    return {o: v / tot for o, v in w.items()}


def pay_v1_sum(minds):
    w = {o: 0.0 for o in owners(minds)}
    for m in minds:
        w[m["owner"]] += raw_value(m)
    w = {o: math.sqrt(v) for o, v in w.items()}
    tot = sum(w.values()) or 1.0
    return {o: v / tot for o, v in w.items()}


def _per_steward(minds, debias=False, dropped=frozenset()):
    per, k = {}, {}
    for i, mind in enumerate(minds):
        if i in dropped:
            continue
        o = mind["owner"]; k[o] = k.get(o, 0) + 1
        cur = per.setdefault(o, [0.0] * T)
        for t in range(T):
            if mind["s"][t] > cur[t]:
                cur[t] = mind["s"][t]
    if debias:
        sig = minds[0]["sig"]
        for o in per:
            if k[o] > 1:
                pen = sig * math.sqrt(2 * math.log(k[o]))
                per[o] = [max(0.0, v - pen) for v in per[o]]
    return per


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


def pay_loo(minds, cap_mult=None):
    """cap_mult=None reproduces the round-1 rule (uncapped). Pass a cap to compare LOO against
    the Shapley arms LIKE FOR LIKE — a reviewer showed our headline compared uncapped LOO with
    capped Shapley, attributing the cap's effect to Shapley."""
    per = _per_steward(minds)
    allo = list(per.keys())
    full = _V(per, allo)
    f = {o: max(0.0, full - _V(per, [x for x in allo if x != o])) for o in allo}
    tot = sum(f.values()) or 1.0
    p = {o: v / tot for o, v in f.items()}
    if cap_mult is not None:
        cap = cap_mult / len(p)
        p = {o: min(v, cap) for o, v in p.items()}
    return p


def _shapley(per, rng, perms=SHAPLEY_PERMS):
    allo = list(per.keys()); phi = {o: 0.0 for o in allo}; order = allo[:]
    for _ in range(perms):
        rng.shuffle(order)
        run = [0.0] * T; prev = 0.0
        for o in order:
            for t in range(T):
                v = per[o][t] - TAU
                if v > run[t]:
                    run[t] = v
            cur = sum(U[t] * run[t] for t in range(T))
            phi[o] += cur - prev; prev = cur
    return {o: v / perms for o, v in phi.items()}


def detect_duplicates(minds, mult=DUP_MULT, attacker_first=False):
    """Cluster near-identical fingerprints; the LATER registration is dropped.
    attacker_first=True reverses scan order, i.e. the attacker registered before the victim."""
    thr2 = (mult * math.sqrt(2 * P_DIM)) ** 2
    idx = list(range(len(minds)))
    if attacker_first:
        idx = sorted(idx, key=lambda i: 0 if minds[i]["owner"] == ATT else 1)
    dropped, fps, caught = set(), 0, 0
    for a in range(len(idx)):
        i = idx[a]
        if i in dropped:
            continue
        for b in range(a + 1, len(idx)):
            j = idx[b]
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


def pay_v2(minds, rng, debias=True, dedup=True, floor=True, alpha=ALPHA, lam=LAMBDA,
           cap_mult=CAP_MULT, dup_mult=DUP_MULT, attacker_first=False):
    """Returns (payouts, dropped, fps, caught, diag)."""
    dropped, fps, caught = (detect_duplicates(minds, dup_mult, attacker_first)
                            if dedup else (set(), 0, 0))
    per = _per_steward(minds, debias=debias, dropped=dropped)
    phi = _shapley(per, rng)
    std = {o: _V(per, [o]) for o in per}
    sphi = sum(phi.values()) or 1.0
    sstd = sum(std.values()) or 1.0
    f, bound = {}, 0
    for o in per:
        a = phi[o] / sphi
        b = lam * std[o] / sstd
        if floor and b > a:
            f[o] = b; bound += 1
        else:
            f[o] = a
    w = {o: max(v, 0.0) ** alpha for o, v in f.items()}
    tot = sum(w.values()) or 1.0
    p = {o: v / tot for o, v in w.items()}
    cap = cap_mult / len(p)
    capped = sum(1 for v in p.values() if v > cap)
    p = {o: min(v, cap) for o, v in p.items()}
    return p, dropped, fps, caught, {"floor_bound": bound, "n": len(per), "capped": capped}


# ---------------------------------------------------------------- stats
def gini(xs):
    xs = sorted(xs); n = len(xs); s = sum(xs)
    if s == 0 or n == 0:
        return 0.0
    return (2 * sum(i * x for i, x in enumerate(xs, 1))) / (n * s) - (n + 1) / n


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def ci95(xs):
    return 1.96 * statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0


def cell(*v, w=15):
    return "".join(str(x).rjust(w) for x in v)


# ---------------------------------------------------------------- experiments
def exp_dilution():
    """Does the per-Mind match floor actually buy anything? reward_sim3 had no power to say."""
    res = {"diluted": [], "floored": [], "dil_hon": [], "flo_hon": []}
    for trial in range(TRIALS):
        rng = random.Random(SEED + trial)
        honest = make_field(rng)
        syb = [{"owner": ATT, "theta": [max(0.0, min(10.0, rng.gauss(2, .5) + rng.gauss(0, .3))) for _ in range(T)],
                "fp": [rng.gauss(0, 1) for _ in range(P_DIM)]} for _ in range(50)]
        field = honest + syb
        for reg in ("diluted", "floored"):
            observe(field, rng, floored=(reg == "floored"))
            p = pay_v2(field, rng)[0]
            res[reg].append(p.get(ATT, 0.0))
            res[("dil_hon" if reg == "diluted" else "flo_hon")].append(
                statistics.median(p.get(m["owner"], 0.0) for m in honest))
    return res


def exp_suppression_ablation(victim_rank=0):
    """Clone-to-suppress: which component actually protects the victim?

    victim_rank=0 attacks the BEST honest steward -- but that steward sits at the payout cap, so
    TSI ~ 0 there is partly the cap arithmetic (cap = 5/N, and N grows when the attacker registers).
    victim_rank=9 attacks the 10th-best steward, who is BELOW the cap, which is the honest test.

    All four arms are paired on identical seeds and the cap is matched across arms.
    """
    modes = [("LOO, no cap", ("loo", None)), ("LOO, 5x cap", ("loo", CAP_MULT)),
             ("shapley_only, 5x cap", ("v2", dict(floor=False))),
             ("shapley+floor, 5x cap", ("v2", dict(floor=True))),
             ("shapley+floor, no cap", ("v2", dict(floor=True, cap_mult=1e9)))]
    out = {k: [] for k, _ in modes}
    diag = {k: [] for k, _ in modes}
    capped_both = {k: 0 for k, _ in modes}
    for trial in range(TRIALS):
        rng = random.Random(SEED + 2000 + trial)
        honest = make_field(rng)
        ranked = sorted(honest, key=lambda m: -sum(m["theta"]))
        victim = ranked[min(victim_rank, len(ranked) - 1)]
        vo = victim["owner"]
        clones = [clone_of(victim, ATT, rng, 1.0) for _ in range(5)]   # EVASIVE: dedup is off the table
        for c in clones:
            c["is_clone"] = True
        attacked = honest + clones
        for name, (kind, kw) in modes:
            r_before = random.Random(SEED + 7000 + trial)   # paired seeds across arms
            r_after = random.Random(SEED + 8000 + trial)
            observe(honest, r_before, floored=True)
            if kind == "loo":
                before = pay_loo(honest, kw).get(vo, 0.0)
            else:
                before = pay_v2(honest, r_before, **kw)[0].get(vo, 0.0)
            observe(attacked, r_after, floored=True)
            if kind == "loo":
                after = pay_loo(attacked, kw).get(vo, 0.0)
                capref = (kw / len(honest)) if kw else None
            else:
                p, _, _, _, d = pay_v2(attacked, r_after, **kw)
                after = p.get(vo, 0.0)
                diag[name].append(d["floor_bound"] / d["n"])
                cm = kw.get("cap_mult", CAP_MULT)
                capref = cm / (len(honest) + 1)
            if capref is not None and after >= capref * 0.999 and before > 0:
                capped_both[name] += 1
            out[name].append(1 - after / max(before, 1e-12))
    return out, diag, capped_both


def exp_alpha_frontier():
    """F4 said our alpha=1.5 curvature degrades honest merit-proportionality.
    Instead of confessing it, sweep it: is there a config that passes ALL FOUR?"""
    rows = []
    for alpha, floor in ((1.0, True), (1.25, True), (1.5, True), (1.0, False), (1.5, False)):
        att, gin, hon, bound = [], [], [], []
        for trial in range(TRIALS):
            rng = random.Random(SEED + trial)
            honest = make_field(rng)
            merit = {m["owner"]: sum(u * max(0.0, t - TAU) for u, t in zip(U, m["theta"])) for m in honest}
            syb = [{"owner": ATT, "theta": [max(0.0, min(10.0, rng.gauss(2, .5))) for _ in range(T)],
                    "fp": [rng.gauss(0, 1) for _ in range(P_DIM)]} for _ in range(50)]
            field = honest + syb
            observe(field, rng, floored=True)
            p, _, _, _, d = pay_v2(field, rng, alpha=alpha, floor=floor)
            att.append(p.get(ATT, 0.0))
            gin.append(gini([p.get(o, 0.0) / max(merit[o], 1e-9) for o in merit]))
            hon.append(statistics.median(p.get(o, 0.0) for o in merit))
            bound.append(d["floor_bound"] / d["n"])
        rows.append({"alpha": alpha, "floor": floor, "att": mean(att), "gini": mean(gin),
                     "hon": mean(hon), "bound": mean(bound)})
    # baseline Gini for reference
    gb = []
    for trial in range(TRIALS):
        rng = random.Random(SEED + trial)
        honest = make_field(rng)
        merit = {m["owner"]: sum(u * max(0.0, t - TAU) for u, t in zip(U, m["theta"])) for m in honest}
        syb = [{"owner": ATT, "theta": [max(0.0, min(10.0, rng.gauss(2, .5))) for _ in range(T)],
                "fp": [rng.gauss(0, 1) for _ in range(P_DIM)]} for _ in range(50)]
        field = honest + syb
        observe(field, rng, floored=True)
        pb = pay_base(field)
        gb.append(gini([pb.get(o, 0.0) / max(merit[o], 1e-9) for o in merit]))
    return rows, mean(gb)


def exp_detector_arms_race():
    """The attacker adapts (eps) AND the defender adapts (threshold). Report both, plus the
    false-positive cost the defender pays, and what happens if the ATTACKER registers first."""
    rows = []
    for eps in (0.0, 0.5, 1.0, 1.5, 2.0):
        for mult in (0.5, 0.75, 1.0):
            caught, fp, caught_af = [], [], []
            for trial in range(TRIALS):
                rng = random.Random(SEED + 3000 + trial)
                honest = make_field(rng)
                victim = max(honest, key=lambda m: sum(m["theta"]))
                clones = [clone_of(victim, ATT, rng, eps) for _ in range(5)]
                for c in clones:
                    c["is_clone"] = True
                field = honest + clones
                observe(field, rng, floored=True)
                _, f1, c1 = detect_duplicates(field, mult)
                _, f2, c2 = detect_duplicates(field, mult, attacker_first=True)
                caught.append(c1 / 5); fp.append(f1); caught_af.append(c2 / 5)
            rows.append({"eps": eps, "mult": mult, "cut": mult * math.sqrt(2 * P_DIM),
                         "caught": mean(caught), "fp": mean(fp), "caught_attacker_first": mean(caught_af)})
    return rows


def main():
    print(f"reward_sim4.py — seed={SEED}, {TRIALS} trials, {N_HONEST} honest stewards, {T} tasks,")
    print(f"Shapley {SHAPLEY_PERMS} perms, James-Stein shrinkage ON. Supersedes reward_sim3.py.\n")

    d = exp_dilution()
    print("D  DOES THE PER-MIND MATCH FLOOR DO ANYTHING? (reward_sim3 had no power to test this)")
    print(f"   diluted regime = {M_BUDGET} matches split across 250 Minds = 8 each; floored = {M_FLOOR} each")
    print(cell("", "attacker share", "honest median", w=20))
    print(cell("diluted", f"{mean(d['diluted'])*100:.2f}%", f"{mean(d['dil_hon'])*100:.3f}%", w=20))
    print(cell("floored", f"{mean(d['floored'])*100:.2f}%", f"{mean(d['flo_hon'])*100:.3f}%", w=20))
    print(f"   -> the floor changes the attacker's take by "
          f"{(mean(d['diluted'])-mean(d['floored']))*100:+.2f} percentage points.")

    for rank, label in ((0, "TOP steward (sits AT the payout cap)"),
                        (9, "10th-best steward (BELOW the cap — the honest test)")):
        sup, diag, capped = exp_suppression_ablation(rank)
        print(f"\nS{rank}  CLONE-TO-SUPPRESS, victim = {label}")
        print("    Evasive clones (eps=1.0, duplicate detector already beaten). Arms paired on identical")
        print("    seeds, cap matched across arms. TSI = fraction of the victim's payout destroyed (<=0.10).")
        for k, _ in (("LOO, no cap", 0), ("LOO, 5x cap", 0), ("shapley_only, 5x cap", 0),
                     ("shapley+floor, 5x cap", 0), ("shapley+floor, no cap", 0)):
            extra = f"   floor binds {mean(diag[k])*100:.0f}%" if diag.get(k) else ""
            pin = f"   victim pinned at cap in {capped[k]}/{TRIALS} trials" if capped[k] else ""
            print(f"    {k:24s} TSI = {mean(sup[k]):+.3f} +/- {ci95(sup[k]):.3f}{extra}{pin}")
    print("\n    (In reward_sim3 the floor bound for 100% of stewards, which made this test vacuous;")
    print("     and the headline compared UNCAPPED LOO against CAPPED Shapley, crediting Shapley")
    print("     with the cap's effect. Both are corrected above.)")

    rows, g_base = exp_alpha_frontier()
    print(f"\nF  THE F4 FRONTIER — can we fix the criterion we failed? (BASE Gini = {g_base:.3f})")
    print(cell("alpha", "floor", "attacker share", "Gini(pay/merit)", "floor binds", w=17))
    for r in rows:
        print(cell(f"{r['alpha']:.2f}", "on" if r["floor"] else "off", f"{r['att']*100:.2f}%",
                   f"{r['gini']:.3f}", f"{r['bound']*100:.0f}%", w=17))
    ok = [r for r in rows if r["gini"] <= g_base]
    print("   -> configurations that satisfy F4 (Gini <= BASE): "
          + (", ".join(f"alpha={r['alpha']}, floor={'on' if r['floor'] else 'off'}" for r in ok) if ok
             else "NONE — F4 is not reachable by tuning alpha or the floor."))

    arms = exp_detector_arms_race()
    print("\nA  DUPLICATE DETECTOR ARMS RACE — attacker perturbs (eps), defender raises the cutoff.")
    print(cell("eps", "cutoff", "clones caught", "honest wrongly", "caught if attacker", w=17))
    print(cell("", "", "", "clustered", "registered FIRST", w=17))
    for r in arms:
        print(cell(f"{r['eps']:.1f}", f"{r['cut']:.1f}", f"{r['caught']*100:.0f}%",
                   f"{r['fp']:.2f}", f"{r['caught_attacker_first']*100:.0f}%", w=17))
    print("   'honest wrongly clustered' is the false-positive cost of a higher cutoff:")
    print("   it is the number the defender pays to keep catching evasive clones.")


if __name__ == "__main__":
    main()
