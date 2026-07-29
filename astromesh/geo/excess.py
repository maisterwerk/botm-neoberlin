#!/usr/bin/env python3
"""Local-excess periodicity test.

The previous control asked "does this series have memory beyond 13 days" and answered yes at
EVERY lag band — 60-80, 200-220, even 400-420 — because a block bootstrap destroys all
autocorrelation while geomagnetic activity is broadband-correlated out to a year by the 11-year
solar cycle. An independent audit demonstrated that, including on a surrogate with the 22-33 day
band notched out of the spectrum: it still returned "peak lag 27, PASS". The control certified
claims nobody makes. It was permissive in exactly the direction the whole design is supposed to
guard against.

The right question is not "is there correlation at 27" but "does 27 stand ABOVE the smooth
background". So the statistic is a local excess:

    excess(L) = r(L) - median r over a flanking window around L

and the null is that same statistic at every other lag in a wide band, excluding the candidate
region. No resampling, no surrogate, no assumed model: if lag 27 is not a sharper bump than the
bumps found anywhere else in the profile, it does not pass.
"""
import json, math
import numpy as np

def lag_profile(x, lmax=420):
    x = np.asarray(x, float); x = x - x.mean()
    n = len(x)
    f = np.fft.rfft(x, 2*n)
    ac = np.fft.irfft(f*np.conj(f))[:lmax+1].real
    return ac[1:]/ac[0]                      # r(1..lmax)

def excess(prof, L, inner=3, outer=12):
    lo, hi = L-outer, L+outer
    idx = [i for i in range(max(1,lo), min(len(prof), hi+1)) if abs(i-L) > inner]
    return prof[L-1] - np.median([prof[i-1] for i in idx])

def test(x, target=27, band=(15, 400), exclude=(22, 33), inner=3, outer=12):
    prof = lag_profile(x, band[1]+outer+2)
    obs = excess(prof, target, inner, outer)
    null = [excess(prof, L, inner, outer) for L in range(band[0], band[1]+1)
            if not (exclude[0] <= L <= exclude[1])]
    null = np.array(null)
    p = (np.sum(null >= obs) + 1) / (len(null) + 1)
    return {"target": target, "r_at_target": float(prof[target-1]),
            "local_baseline": float(prof[target-1]-obs), "excess": float(obs),
            "p": float(p), "null_lags": len(null),
            "null_excess_mean": float(null.mean()), "null_excess_max": float(null.max())}

if __name__ == "__main__":
    ap = np.array([r[4] for r in json.load(open("ap_daily.json"))], float)
    print("A) the real series, asking about lag 27")
    r = test(ap, 27); print("  ", {k: (round(v,4) if isinstance(v,float) else v) for k,v in r.items()})
    print(f"   -> {'DETECTED' if r['p']<0.05 else 'not detected'}")

    print("\nB) the auditor's counter-examples: lags where nobody claims a recurrence")
    for L in (80, 108, 205, 409):
        r2 = test(ap, L)
        print(f"   lag {L:>3}: r={r2['r_at_target']:.4f} baseline={r2['local_baseline']:.4f} "
              f"excess={r2['excess']:+.4f} p={r2['p']:.3f} -> "
              f"{'DETECTED (bad)' if r2['p']<0.05 else 'correctly rejected'}")

    print("\nC) surrogate with the 22-33 day band notched out of the spectrum")
    n = len(ap); F = np.fft.rfft(ap - ap.mean()); fr = np.fft.rfftfreq(n, d=1.0)
    per = np.divide(1.0, fr, out=np.full_like(fr, np.inf), where=fr > 0)
    F[(per >= 22) & (per <= 33)] = 0
    notched = np.fft.irfft(F, n) + ap.mean()
    r3 = test(notched, 27)
    print(f"   lag 27 on notched series: r={r3['r_at_target']:.4f} excess={r3['excess']:+.4f} "
          f"p={r3['p']:.3f} -> {'DETECTED (bad)' if r3['p']<0.05 else 'correctly rejected'}")
