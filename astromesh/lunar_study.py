#!/usr/bin/env python3
"""
lunar_study.py — the analytical core behind AstroMesh's `test_astro_claim` tool.

"Full moons move markets" is the most repeated astro-finance claim there is. Nobody who repeats it
states a null hypothesis. This does: it buckets real daily returns by real lunar phase and runs a
permutation test that controls for the fact that we are looking at eight buckets at once.

Data: the same CoinGecko daily series used elsewhere in this project (BTC/ETH/SOL, 299 days).
Astronomy: synodic month from a known new moon — deterministic, no API, reproducible offline.

The expected outcome is NO effect. That is the point: a tool that can only ever confirm astrology
is not a tool, it is a horoscope.
"""
import json, math, random, statistics, sys

SYNODIC = 29.530588853          # mean synodic month, days
KNOWN_NEW_MOON_JD = 2451550.1   # 2000-01-06 18:14 UTC
PHASE_NAMES = ["New", "Waxing crescent", "First quarter", "Waxing gibbous",
               "Full", "Waning gibbous", "Last quarter", "Waning crescent"]


def to_jd(y, m, d):
    if m <= 2:
        y -= 1; m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def phase_fraction(datestr):
    """0.0 = new moon, 0.5 = full moon."""
    y, m, d = (int(x) for x in datestr.split("-"))
    days = to_jd(y, m, d) - KNOWN_NEW_MOON_JD
    return (days % SYNODIC) / SYNODIC


def octant(frac):
    return int((frac * 8 + 0.5) % 8)


def daily_returns(series):
    days = sorted(series)
    out = []
    for i in range(1, len(days)):
        p0, p1 = series[days[i - 1]], series[days[i]]
        if p0 > 0:
            out.append((days[i], math.log(p1 / p0) * 100))
    return out


def permutation_test(labels, values, trials=10000, seed=42):
    """Null: labels carry no information. Statistic: the largest absolute bucket mean.
    Taking the MAX across buckets is what makes this honest — testing eight buckets and
    reporting the prettiest one is how astro-finance 'findings' are manufactured."""
    rng = random.Random(seed)
    buckets = {}
    for lab, v in zip(labels, values):
        buckets.setdefault(lab, []).append(v)
    observed = {k: statistics.mean(v) for k, v in buckets.items() if len(v) >= 5}
    obs_stat = max(abs(m) for m in observed.values())
    sizes = [(k, len(v)) for k, v in buckets.items() if len(v) >= 5]
    pool = list(values)
    hits = 0
    for _ in range(trials):
        rng.shuffle(pool)
        i = 0
        stat = 0.0
        for _, n in sizes:
            seg = pool[i:i + n]; i += n
            stat = max(stat, abs(sum(seg) / len(seg)))
        if stat >= obs_stat:
            hits += 1
    return observed, obs_stat, (hits + 1) / (trials + 1), {k: len(v) for k, v in buckets.items()}


def study(asset, series):
    rets = daily_returns(series)
    labels = [octant(phase_fraction(d)) for d, _ in rets]
    values = [r for _, r in rets]
    observed, obs_stat, p, counts = permutation_test(labels, values)
    return {"asset": asset, "n_days": len(values), "by_phase": observed,
            "max_abs_mean_pct": obs_stat, "p_value": p, "counts": counts}


if __name__ == "__main__":
    prices = json.load(open(sys.argv[1] if len(sys.argv) > 1
                            else "/Users/claude/Neo 2.0/projects/botm-artifacts/xskill/prices.json"))
    print("DOES THE MOON MOVE THE MARKET?")
    print("Daily log-returns bucketed by lunar octant; permutation test on the largest bucket mean")
    print("(10,000 shuffles, seed=42), which corrects for looking at eight buckets at once.\n")
    results = {}
    for asset in ("bitcoin", "ethereum", "solana"):
        r = study(asset, prices[asset])
        results[asset] = r
        print(f"{asset.upper()}  ({r['n_days']} daily returns)")
        for oc in range(8):
            if oc in r["by_phase"]:
                bar = "+" if r["by_phase"][oc] >= 0 else "-"
                print(f"   {PHASE_NAMES[oc]:<18} n={r['counts'][oc]:>3}  mean {r['by_phase'][oc]:+6.3f}%  {bar * min(int(abs(r['by_phase'][oc]) * 4), 20)}")
        verdict = "NO DETECTABLE EFFECT" if r["p_value"] > 0.05 else "effect survives the null"
        print(f"   -> largest |bucket mean| = {r['max_abs_mean_pct']:.3f}%   p = {r['p_value']:.3f}   {verdict}\n")
    json.dump({k: {kk: (vv if not isinstance(vv, dict) else {str(a): b for a, b in vv.items()})
                   for kk, vv in v.items()} for k, v in results.items()},
              open("lunar_study.json", "w"), indent=1)
    print("Written: lunar_study.json")
