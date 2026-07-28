// ---------------------------------------------------------------------------
// The adjudication half of AstroMesh.
//
// Five judgments called the crypto+astrology fusion "themed/entertainment rather
// than deeply analytical" and crypto "one of the more obvious choices". So the
// product here is not another blended horoscope: it is a service that TESTS
// astrological claims against 94 years of daily geomagnetic measurements and
// grades them — with a positive control that proves the instrument can say yes.
//
// Dataset: GFZ Potsdam planetary Ap index, one value per UT day since 1932-01-01
// (CC BY 4.0), embedded so every number below is reproducible offline.
// ---------------------------------------------------------------------------
import { AP_START, AP_N, AP_B64 } from "./ap_embed.js";

let _ap = null;
export function apSeries() {
  if (_ap) return _ap;
  const bin = Uint8Array.from(atob(AP_B64), c => c.charCodeAt(0));
  const dv = new DataView(bin.buffer);
  const out = new Float64Array(AP_N);
  for (let i = 0; i < AP_N; i++) out[i] = dv.getUint16(i * 2, true);
  _ap = out; return out;
}

// --- date helpers -----------------------------------------------------------
function jdn(y, m, d) {
  if (m <= 2) { y -= 1; m += 12; }
  const A = Math.floor(y / 100), B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + B - 1524.5;
}
const JD0 = jdn(AP_START[0], AP_START[1], AP_START[2]);
export function moonBin(i, nbins) {          // i = day index into the series
  const frac = (((JD0 + i) - 2451550.1) / 29.530588853) % 1;
  return Math.floor(((frac % 1) + 1) % 1 * nbins) % nbins;
}

// --- statistics -------------------------------------------------------------
function corr(a, b, off, len) {
  let ma = 0, mb = 0;
  for (let i = 0; i < len; i++) { ma += a[i]; mb += b[i + off]; }
  ma /= len; mb /= len;
  let sa = 0, sb = 0, sab = 0;
  for (let i = 0; i < len; i++) {
    const x = a[i] - ma, y = b[i + off] - mb;
    sa += x * x; sb += y * y; sab += x * y;
  }
  return sab / (Math.sqrt(sa) * Math.sqrt(sb) || 1e-9);
}
function lagPeak(x, lags) {
  let best = -2, bestLag = 0; const prof = {};
  for (const L of lags) { const r = corr(x, x, L, x.length - L); prof[L] = r;
                          if (r > best) { best = r; bestLag = L; } }
  return { peak: best, lag: bestLag, profile: prof };
}
function mulberry(seed) { return function () {
  seed |= 0; seed = seed + 0x6D2B79F5 | 0;
  let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
  t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
  return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

/* PERIODICITY. A circular shift is the WRONG null here: shifting a periodic series leaves the
   period intact, so the null would contain the very effect under test. The first build of this
   harness did exactly that and failed to detect the 27-day solar rotation — a textbook real
   effect — which is how the bug was caught. The null is a BLOCK BOOTSTRAP with 13-day blocks:
   short enough to break a ~27-day recurrence, long enough to keep the day-to-day autocorrelation
   that is the actual confound. */
export function periodicityTest(x, lags, iters = 300, block = 13, seed = 7) {
  const { peak, lag, profile } = lagPeak(x, lags);
  const rnd = mulberry(seed), n = x.length, nb = Math.floor(n / block);
  let hits = 0;
  const buf = new Float64Array(nb * block);
  for (let it = 0; it < iters; it++) {
    for (let b = 0; b < nb; b++) {
      const k = Math.floor(rnd() * (n - block));
      for (let j = 0; j < block; j++) buf[b * block + j] = x[k + j];
    }
    if (lagPeak(buf, lags).peak >= peak) hits++;
  }
  return { peak_lag: lag, peak_r: peak, p: (hits + 1) / (iters + 1),
           profile, iterations: iters, null_model: `block bootstrap, ${block}-day blocks` };
}

/* BINNED CLAIM. Here a circular shift IS the right null: it decouples the calendar-derived bin
   labels from the data while preserving the series' own autocorrelation. The statistic is the
   largest absolute bin deviation (max-T), which is the multiple-comparison correction — a
   cherry-picked bin must beat the best bin the null can produce. */
export function binnedTest(x, binOf, nbins, iters = 2000, seed = 7) {
  const n = x.length, bins = new Int32Array(n);
  for (let i = 0; i < n; i++) bins[i] = binOf(i, nbins);
  const cnt = new Float64Array(nbins);
  for (let i = 0; i < n; i++) cnt[bins[i]]++;
  const stat = (get) => {
    const s = new Float64Array(nbins); let tot = 0;
    for (let i = 0; i < n; i++) { const v = get(i); s[bins[i]] += v; tot += v; }
    const gm = tot / n; let mx = 0; const means = [];
    for (let b = 0; b < nbins; b++) { const m = s[b] / cnt[b]; means.push(m);
                                      mx = Math.max(mx, Math.abs(m - gm)); }
    return { mx, means, gm };
  };
  const obs = stat(i => x[i]);
  const rnd = mulberry(seed); let hits = 0;
  for (let it = 0; it < iters; it++) {
    const k = 60 + Math.floor(rnd() * (n - 120));
    if (stat(i => x[(i + k) % n]).mx >= obs.mx) hits++;
  }
  let sd = 0; for (let i = 0; i < n; i++) sd += (x[i] - obs.gm) ** 2;
  sd = Math.sqrt(sd / n);
  return { p: (hits + 1) / (iters + 1), bin_means: obs.means, overall_mean: obs.gm,
           largest_deviation: obs.mx, largest_deviation_pct: 100 * obs.mx / obs.gm,
           cohens_d: obs.mx / sd, iterations: iters,
           null_model: "circular shift (preserves autocorrelation, decouples the calendar)" };
}
