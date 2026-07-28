#!/usr/bin/env python3
"""One permutation harness, applied to a claim that is TRUE and to claims that are not.

The null is a circular shift of the series, not an i.i.d. shuffle. Geomagnetic activity is
strongly serially correlated; destroying that correlation would manufacture significance out of
nothing. A max-T statistic over every lag/bin examined supplies the multiple-comparison
correction, so a cherry-picked peak has to beat the best peak the null can produce.
"""
import json, math
import numpy as np

AP = json.load(open('ap_daily.json'))               # [year, month, day, bartels_day, Ap]
ap = np.array([r[4] for r in AP], dtype=float)
dates = [(r[0], r[1], r[2]) for r in AP]

def lag_corr_matrix(x, lags):
    out = np.empty(len(lags))
    for i, L in enumerate(lags):
        a, b = x[:-L], x[L:]
        out[i] = np.corrcoef(a, b)[0, 1]
    return out

def periodicity_test(x, lags, iters=2000, seed=7, block=13):
    """A circular shift is the WRONG null for a periodicity question: shifting a periodic series
    leaves the period intact, so the null contains the very effect being tested. The first version
    of this harness did exactly that and failed to detect the 27-day solar rotation — a textbook
    real effect. The null here is a BLOCK BOOTSTRAP with blocks of `block` days: short enough to
    break a ~27-day recurrence, long enough to keep the day-to-day autocorrelation that is the
    actual confound."""
    obs = lag_corr_matrix(x, lags)
    peak_i = int(np.argmax(obs)); peak = obs[peak_i]
    rng = np.random.default_rng(seed)
    n = len(x); nb = n // block
    hits = 0
    for _ in range(iters):
        starts = rng.integers(0, n - block, size=nb)
        s = np.concatenate([x[k:k+block] for k in starts])
        if lag_corr_matrix(s, lags).max() >= peak: hits += 1
    return lags[peak_i], peak, (hits + 1) / (iters + 1), dict(zip(lags, obs))

def jd(y, m, d):
    if m <= 2: y -= 1; m += 12
    A = y // 100; B = 2 - A + A // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5

def moon_bin(y, m, d, nbins=8):
    frac = ((jd(y, m, d) - 2451550.1) / 29.530588853) % 1.0
    return int(frac * nbins) % nbins

def binned_test(x, bins, nbins, iters=2000, seed=7):
    bins = np.asarray(bins)
    onehot = np.zeros((nbins, len(x)))
    for b in range(nbins): onehot[b] = (bins == b)
    cnt = onehot.sum(axis=1)
    def stat(v):
        means = onehot @ v / cnt
        return np.abs(means - v.mean()).max(), means
    obs, means = stat(x)
    rng = np.random.default_rng(seed)
    hits = 0
    for k in rng.integers(60, len(x) - 60, size=iters):
        s = np.concatenate([x[k:], x[:k]])
        if stat(s)[0] >= obs: hits += 1
    return obs, means, (hits + 1) / (iters + 1)

if __name__ == "__main__":
    lags = list(range(20, 41))
    print("=" * 76)
    print("POSITIVE CONTROL — can the harness detect an effect that is REAL?")
    print("Claim: geomagnetic activity recurs with the Sun's ~27-day rotation (Bartels, 1934).")
    pl, pk, p1, prof = periodicity_test(ap, lags, iters=1000)
    print(f"  peak lag {pl} d, r = {pk:.4f},  p = {p1:.4f}   (max-T over lags 20-40, 1000 block bootstraps)")
    print("  profile: " + "  ".join(f"{L}:{prof[L]:.3f}" for L in (22, 25, 26, 27, 28, 29, 33, 40)))
    print(f"  VERDICT: {'DETECTED' if p1 < 0.05 else 'not detected'}")

    print()
    print("=" * 76)
    print("CLAIM — 'the moon drives geomagnetic storms'  (8 lunar-phase bins, same harness)")
    bins = [moon_bin(*d) for d in dates]
    obs, means, p2 = binned_test(ap, bins, 8, iters=20000)
    hi = int(np.argmax(means))
    print(f"  cherry-picked headline a believer would quote: phase bin {hi} averages "
          f"Ap {means[hi]:.2f} against an overall {ap.mean():.2f}")
    print(f"  max-T over 8 bins, 20000 circular shifts:  p = {p2:.4f}")
    print(f"  VERDICT: {'DETECTED' if p2 < 0.05 else 'NOT DETECTED'}")
    json.dump({"n_days": len(ap), "span": [dates[0], dates[-1]],
               "control": {"lag": pl, "r": float(pk), "p": p1,
                           "profile": {str(k): float(v) for k, v in prof.items()}},
               "moon": {"p": p2, "means": [float(m) for m in means],
                        "overall": float(ap.mean())}},
              open("harness_out.json", "w"), indent=1)
