import { CROSSWORD_B64, CROSSWORD_BUILD } from "./crossword_html.js";
import { STORMLE_B64, STORMLE_BUILD } from "./stormle_html.js";
import { apSeries, moonBin, periodicityTest, binnedTest, excessTest, harmonicComb } from "./geo_tools.js";
import { AP_START, AP_N } from "./ap_embed.js";
import { AGENTS_GUIDE } from "./agents_guide.js";
/**
 * AstroMesh — an astrology service that can say no.
 *
 * Astrology generates millions of specific, testable claims and almost nobody tests them.
 * This Worker does, and exposes the adjudication over MCP so other agents can call it:
 *
 *   calibrate_harness            positive control - the same statistics run against a claim
 *                                known to be TRUE (the Sun's 27-day rotation showing up in
 *                                geomagnetic activity). A null verdict is worthless unless
 *                                the instrument has been shown to detect something real.
 *   test_geomagnetic_astro_claim moon phase vs 34,542 daily Ap measurements, GFZ Potsdam
 *   test_astro_claim             moon phase vs daily crypto returns
 *   test_lunar_quake_claim       moon phase vs the USGS earthquake catalogue
 *
 * Every verdict reports an effect size next to the p-value, because across 94 years of daily
 * data a 6% wiggle is detectable and still means nothing.
 *
 * The entertainment side is still here and still honest about being entertainment:
 * horoscopes, a compass fusing a sign's daily tone with live crypto momentum, and a playlist
 * built from a third dataset (iTunes). Astrology comes from the Free Astrology API with a
 * server-side key; nothing here is financial advice.
 */

const SIGNS = ["aries","taurus","gemini","cancer","leo","virgo","libra","scorpio","sagittarius","capricorn","aquarius","pisces"];
const SIGN_TRAITS = {
  aries:"bold, impulsive, first-mover", taurus:"patient, value-seeking, HODLer",
  gemini:"curious, quick-flipping, news-driven", cancer:"cautious, protective of capital",
  leo:"confident, likes blue-chips and spotlight coins", virgo:"analytical, reads the charts",
  libra:"balanced, diversifier", scorpio:"intense, contrarian, all-in", sagittarius:"optimistic, high-risk moonshots",
  capricorn:"disciplined, long-horizon", aquarius:"innovative, loves new protocols", pisces:"intuitive, vibes-based"
};
// deterministic daily "astro tone" per sign (0..1) seeded by UTC day + sign, so it's stable within a day
function astroTone(sign, dayIdx){
  let h = 2166136261 ^ dayIdx;
  for (const c of sign) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); }
  return ((h >>> 0) % 1000) / 1000;
}
function dayIndex(){ return Math.floor(Date.now() / 86400000); }

// Map common coin ids/symbols -> Binance USDT symbols (primary source: reliable 24h change, keyless)
const BINANCE = { bitcoin:"BTCUSDT", btc:"BTCUSDT", ethereum:"ETHUSDT", eth:"ETHUSDT", solana:"SOLUSDT", sol:"SOLUSDT",
  ripple:"XRPUSDT", xrp:"XRPUSDT", cardano:"ADAUSDT", ada:"ADAUSDT", dogecoin:"DOGEUSDT", doge:"DOGEUSDT",
  polkadot:"DOTUSDT", dot:"DOTUSDT", chainlink:"LINKUSDT", link:"LINKUSDT", pepe:"PEPEUSDT",
  "moca-network":"MOCAUSDT", moca:"MOCAUSDT", "usd-coin":"USDCUSDT", monero:"XMRUSDT", xmr:"XMRUSDT" };

async function coinData(coin){
  const id = String(coin || "bitcoin").toLowerCase().trim();
  const ua = { "accept":"application/json", "User-Agent":"AstroMesh/1.0 (+battle-of-the-minds)" };
  // 1) Binance 24hr ticker
  const sym = BINANCE[id];
  if (sym) {
    try {
      const r = await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${sym}`, { headers: ua });
      if (r.ok) { const j = await r.json(); if (j.lastPrice) return { id, usd: Number(Number(j.lastPrice).toFixed(6)), change24h: Number(j.priceChangePercent) }; }
    } catch {}
  }
  // 2) CoinGecko fallback (with UA)
  try {
    const r2 = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${encodeURIComponent(id)}&vs_currencies=usd&include_24hr_change=true`, { headers: ua });
    if (r2.ok) { const j = await r2.json(); if (j[id]) return { id, usd: j[id].usd, change24h: j[id].usd_24h_change }; }
  } catch {}
  // 3) Coinbase daily candles. Added after an independent audit found every price tool down
  // at once: Binance and CoinGecko were both unreachable from the Worker while Coinbase — the
  // source the backtest tool already used — was answering fine. Two fallbacks that fail together
  // are one fallback. Price and 24h change are derived from the last two daily closes.
  try {
    const kl = await coinbaseDaily(id);            // newest first: [time, low, high, open, close, vol]
    if (kl && kl.length >= 2) {
      const last = kl[0][4], prev = kl[1][4];
      return { id, usd: Number(Number(last).toFixed(6)),
               change24h: ((last / prev) - 1) * 100, source: "coinbase daily candles (fallback)" };
    }
  } catch {}
  throw new Error(`Could not fetch market data for "${id}" from Binance, CoinGecko or Coinbase (try bitcoin, ethereum, solana, cardano, dogecoin...)`);
}

// Free Astrology API — real external astrology API that requires an API key.
// Uses the Western birth-chart (planets) endpoint. Falls back gracefully if unconfigured.
async function birthChart(env, body){
  if (!env.ASTROLOGY_API_KEY) return { unavailable:"ASTROLOGY_API_KEY not configured on the server" };
  const payload = {
    year: body.year, month: body.month, date: body.date,
    hours: body.hours ?? 12, minutes: body.minutes ?? 0, seconds: 0,
    latitude: body.latitude, longitude: body.longitude, timezone: body.timezone ?? 0,
    config: { observation_point: "topocentric", ayanamsha: "tropical" }
  };
  const r = await fetch("https://json.freeastrologyapi.com/western/planets", {
    method:"POST",
    headers:{ "Content-Type":"application/json", "x-api-key": env.ASTROLOGY_API_KEY },
    body: JSON.stringify(payload)
  });
  const text = await r.text();
  if (!r.ok) throw new Error(`Free Astrology API ${r.status}: ${text.slice(0,160)}`);
  try { return JSON.parse(text); } catch { return { raw:text.slice(0,500) }; }
}

function horoscope(sign){
  sign = String(sign||"").toLowerCase().trim();
  if (!SIGNS.includes(sign)) throw new Error(`Unknown sign "${sign}". One of: ${SIGNS.join(", ")}`);
  const t = astroTone(sign, dayIndex());
  const mood = t > 0.66 ? "expansive & lucky" : t > 0.33 ? "steady & measured" : "cautious & introspective";
  const advice = t > 0.66 ? "The stars favour bold moves today." :
                 t > 0.33 ? "Hold your ground; small, deliberate steps win." :
                 "Protect what you have; today rewards patience over action.";
  return { sign, date: new Date(dayIndex()*86400000).toISOString().slice(0,10),
           tone: Number(t.toFixed(3)), mood, trait: SIGN_TRAITS[sign], advice };
}

function compass(sign, snap){
  const h = horoscope(sign);
  const mom = snap.change24h ?? 0;
  const marketMood = mom > 3 ? "surging" : mom > 0 ? "drifting up" : mom > -3 ? "drifting down" : "sliding";
  // meaningful blend: alignment of astro tone (0..1 -> -1..1) with market momentum sign
  const astroVec = (h.tone - 0.5) * 2;
  const alignment = (astroVec >= 0) === (mom >= 0) ? "aligned" : "at odds";
  const score = Math.round((astroVec * 50) + Math.max(-50, Math.min(50, mom * 3)));
  const verdict = score > 30 ? "🟢 Cosmos & candles agree — a bright day."
               : score > -10 ? "🟡 Mixed signals — trade your plan, not your horoscope."
               : "🔴 Stars and charts both wary — a day for patience.";
  return {
    sign: h.sign, coin: snap.id, price_usd: snap.usd, change_24h_pct: Number((mom).toFixed(2)),
    astro_mood: h.mood, market_mood: marketMood, alignment,
    compass_score: score, verdict,
    briefing: `For ${h.sign} (${h.trait}), the stars read "${h.mood}" while ${snap.id} is ${marketMood} (${mom>=0?"+":""}${mom.toFixed(2)}% / 24h). Astrology and the market are ${alignment} today. ${verdict}`,
    disclaimer: "For entertainment only. Not financial advice."
  };
}

// THIRD dataset: music (iTunes Search API — keyless). Maps a sign's daily mood to a genre and
// returns real tracks, fused with the coin's market mood → a "cosmic trading playlist".
const SIGN_GENRE = { aries:"punk", taurus:"soul", gemini:"pop", cancer:"lo-fi", leo:"rock",
  virgo:"classical", libra:"indie", scorpio:"darkwave", sagittarius:"reggae", capricorn:"techno",
  aquarius:"electronic", pisces:"ambient" };
// Curated fallback so the music tool always returns real tracks even if the live API is blocked.
const CURATED = {
  punk:[{track:"Blitzkrieg Bop",artist:"Ramones"},{track:"London Calling",artist:"The Clash"},{track:"Basket Case",artist:"Green Day"}],
  soul:[{track:"Respect",artist:"Aretha Franklin"},{track:"Superstition",artist:"Stevie Wonder"},{track:"Ain't No Mountain High Enough",artist:"Marvin Gaye"}],
  pop:[{track:"Blinding Lights",artist:"The Weeknd"},{track:"Levitating",artist:"Dua Lipa"},{track:"As It Was",artist:"Harry Styles"}],
  "lo-fi":[{track:"Snowman",artist:"WYS"},{track:"Sailing",artist:"Christopher"},{track:"Coffee",artist:"Kudasai"}],
  rock:[{track:"Mr. Brightside",artist:"The Killers"},{track:"Seven Nation Army",artist:"The White Stripes"},{track:"Do I Wanna Know?",artist:"Arctic Monkeys"}],
  classical:[{track:"Clair de Lune",artist:"Debussy"},{track:"Nocturne Op.9 No.2",artist:"Chopin"},{track:"The Four Seasons: Spring",artist:"Vivaldi"}],
  indie:[{track:"Electric Feel",artist:"MGMT"},{track:"Take a Walk",artist:"Passion Pit"},{track:"Two Weeks",artist:"Grizzly Bear"}],
  darkwave:[{track:"Bela Lugosi's Dead",artist:"Bauhaus"},{track:"A Forest",artist:"The Cure"},{track:"Shadowplay",artist:"Joy Division"}],
  reggae:[{track:"Three Little Birds",artist:"Bob Marley"},{track:"The Harder They Come",artist:"Jimmy Cliff"},{track:"Pressure Drop",artist:"Toots & the Maytals"}],
  techno:[{track:"Spastik",artist:"Plastikman"},{track:"Strings of Life",artist:"Derrick May"},{track:"Windowlicker",artist:"Aphex Twin"}],
  electronic:[{track:"Midnight City",artist:"M83"},{track:"Genesis",artist:"Justice"},{track:"Strobe",artist:"deadmau5"}],
  ambient:[{track:"An Ending (Ascent)",artist:"Brian Eno"},{track:"Weightless",artist:"Marconi Union"},{track:"Avril 14th",artist:"Aphex Twin"}]
};
async function cosmicPlaylist(sign, coin){
  const h = horoscope(sign); const snap = await coinData(coin);
  const up = (snap.change24h ?? 0) >= 0;
  const genre = SIGN_GENRE[h.sign];
  const term = `${genre} ${up ? "upbeat" : "mellow"}`;
  let tracks = [], source = "MusicBrainz (live)";
  try {  // MusicBrainz — keyless, requires a descriptive User-Agent; Cloudflare-friendly
    const r = await fetch(`https://musicbrainz.org/ws/2/recording?query=tag:${encodeURIComponent(genre)}&fmt=json&limit=5`,
      { headers:{ "accept":"application/json", "User-Agent":"AstroMesh/1.0 (battle-of-the-minds; contact: neoberlin)" } });
    if (r.ok) { const j = await r.json(); tracks = (j.recordings||[]).slice(0,5)
      .map(t=>({ track:t.title, artist:(t["artist-credit"]||[{}])[0].name })).filter(t=>t.track); }
  } catch {}
  if (!tracks.length) { source = "curated library"; tracks = (CURATED[genre]||[]).slice(0,5); }
  return { sign:h.sign, coin:snap.id, market:up?"green (upbeat picks)":"red (mellow picks)",
    vibe:`${h.mood} · ${genre}`, genre, source, tracks,
    note:`${h.sign}'s ${h.mood} tone + ${snap.id} ${up?"up":"down"} 24h → a ${genre} ${up?"upbeat":"mellow"} playlist.`,
    disclaimer:"Astrology × crypto × music — for fun." };
}
// Historical back-test: does the sign's daily astro-tone actually align with the coin's real daily
// move? Uses real Binance daily klines (keyless) over N days.
const COINBASE = { bitcoin:"BTC-USD", btc:"BTC-USD", ethereum:"ETH-USD", eth:"ETH-USD", solana:"SOL-USD", sol:"SOL-USD",
  ripple:"XRP-USD", xrp:"XRP-USD", cardano:"ADA-USD", ada:"ADA-USD", dogecoin:"DOGE-USD", doge:"DOGE-USD",
  polkadot:"DOT-USD", dot:"DOT-USD", chainlink:"LINK-USD", link:"LINK-USD" };

// ---------- lunar falsification engine ----------
// This tool exists to be able to answer "no". An astrology server that can only ever confirm
// astrology is a horoscope, not an instrument.
const SYNODIC = 29.530588853, KNOWN_NEW_MOON_JD = 2451550.1;
const PHASE_NAMES = ["New","Waxing crescent","First quarter","Waxing gibbous","Full","Waning gibbous","Last quarter","Waning crescent"];
function toJD(y,m,d){ if(m<=2){y-=1;m+=12;} const a=Math.floor(y/100), b=2-a+Math.floor(a/4);
  return Math.floor(365.25*(y+4716))+Math.floor(30.6001*(m+1))+d+b-1524.5; }
function lunarOctant(dateStr){ const [y,m,d]=dateStr.split("-").map(Number);
  const days=toJD(y,m,d)-KNOWN_NEW_MOON_JD, frac=(((days%SYNODIC)+SYNODIC)%SYNODIC)/SYNODIC;
  return Math.floor(frac*8+0.5)%8; }
function mulberry32(a){ return function(){ a|=0; a=a+0x6D2B79F5|0; let t=Math.imul(a^a>>>15,1|a);
  t=t+Math.imul(t^t>>>7,61|t)^t; return ((t^t>>>14)>>>0)/4294967296; }; }

// Shared, proven price fetch (same call the backtest tool has used successfully for days).
async function coinbaseDaily(coinId){
  const prod = COINBASE[String(coinId||"bitcoin").toLowerCase()];
  if(!prod) throw new Error(`supported coins: ${Object.keys(COINBASE).filter(k=>k.length>3).join(", ")}`);
  const r = await fetch(`https://api.exchange.coinbase.com/products/${prod}/candles?granularity=86400`,
                        { headers:{accept:"application/json","User-Agent":"AstroMesh/1.0"} });
  if(!r.ok) throw new Error(`Coinbase candles ${r.status}`);
  return await r.json();
}

async function testAstroClaim(coin){
  // No silent default. An independent Mind testing this server found that falling back to
  // bitcoin returned a confident report about an asset the caller never asked for.
  if(coin===undefined || coin===null || typeof coin!=="string" || !coin.trim())
    throw new Error('argument "coin" is required (e.g. bitcoin, ethereum, solana, cardano) — this tool will not guess which asset you meant');
  coin = coin.trim().toLowerCase();
  const kl = await coinbaseDaily(coin);
  const byDay = {};
  for(const k of kl) byDay[new Date(k[0]*1000).toISOString().slice(0,10)] = Number(k[4]);
  const dts = Object.keys(byDay).sort();
  if(dts.length < 60) throw new Error("not enough history to test anything");
  const labels=[], vals=[];
  for(let i=1;i<dts.length;i++){ const p0=byDay[dts[i-1]], p1=byDay[dts[i]];
    if(p0>0){ labels.push(lunarOctant(dts[i])); vals.push(Math.log(p1/p0)*100); } }
  const buckets={};
  labels.forEach((l,i)=>{ (buckets[l]=buckets[l]||[]).push(vals[i]); });
  const observed={}, sizes=[];
  for(const k of Object.keys(buckets)){ const v=buckets[k];
    if(v.length>=5){ observed[k]=v.reduce((a,b)=>a+b,0)/v.length; sizes.push(v.length); } }
  const obsStat=Math.max(...Object.values(observed).map(Math.abs));
  // CIRCULAR-SHIFT null. Lunar octants are runs of ~3-4 CONSECUTIVE days, so each bucket
  // aggregates contiguous blocks of volatility-clustered returns. Plain shuffling of the returns
  // destroys that serial dependence and understates the variance of a bucket mean, which makes the
  // test anti-conservative. Rotating the PHASE LABELS against the return series keeps both the
  // block structure and the volatility clustering intact. (An outside reviewer caught this.)
  // EXACT test: enumerate ALL N-1 distinct rotations rather than sampling 4000 with replacement
  // from ~348 possibilities, which added Monte-Carlo noise and no information (reviewer's point).
  let hits=0; const N=vals.length; const TRIALS=N-1;
  for(let shift=1; shift<N; shift++){
    const acc={}, cnt={};
    for(let i=0;i<N;i++){ const lab=labels[(i+shift)%N];
      acc[lab]=(acc[lab]||0)+vals[i]; cnt[lab]=(cnt[lab]||0)+1; }
    let stat=0;
    for(const k of Object.keys(acc)) if(cnt[k]>=5) stat=Math.max(stat,Math.abs(acc[k]/cnt[k]));
    if(stat>=obsStat) hits++;
  }
  const effectiveAlignments = Math.round(N/29.53);
  const p=(hits+1)/(TRIALS+1);
  const byPhase={};
  for(const k of Object.keys(observed)) byPhase[PHASE_NAMES[k]]={ n:buckets[k].length, mean_pct:+observed[k].toFixed(3) };
  let worst=null;
  for(const k of Object.keys(observed)) if(worst===null||Math.abs(observed[k])>Math.abs(observed[worst])) worst=k;
  return { claim_tested:"daily returns depend on the lunar phase", coin,
    days_of_history:dts.length, daily_returns_used:vals.length, by_phase:byPhase,
    headline_a_believer_would_quote:`${coin} moves ${observed[worst].toFixed(2)}% on average during ${PHASE_NAMES[worst]}`,
    largest_abs_bucket_mean_pct:+obsStat.toFixed(3), p_value:+p.toFixed(4),
    computed_at_utc: new Date().toISOString(),
    exact_test: true, rotations_enumerated: TRIALS,
    effective_distinct_alignments: effectiveAlignments,
    smallest_attainable_p: +(1/(effectiveAlignments+1)).toFixed(4),
    verdict: p>0.05 ? "NO DETECTABLE EFFECT - the headline above is noise" : "effect survives the null; investigate further",
    method:"daily log-returns bucketed into 8 lunar octants; EXACT circular-shift test enumerating all N-1 rotations of the phase labels, on the largest absolute bucket mean. Rotating the phase labels rather than shuffling the returns preserves volatility clustering, which a naive shuffle destroys; the max-statistic corrects for inspecting eight phases at once. No correction is applied ACROSS coins.",
    honest_note:"A negative result is the expected result. This tool exists to be able to say no." };
}


// Second falsification target, deliberately NOT finance. "The full moon triggers earthquakes" is a
// widely held belief (the USGS itself publishes a debunk). Same engine, entirely different domain:
// daily EVENT COUNTS from the USGS catalogue instead of returns.
async function testLunarQuakeClaim(minMagnitude, days){
  const mag = Math.min(Math.max(Number(minMagnitude)||5.0, 4.0), 7.0);
  const nDays = Math.min(Math.max(parseInt(days)||360, 120), 730);
  const end = new Date(), start = new Date(Date.now()-nDays*86400000);
  const iso = d => d.toISOString().slice(0,10);
  const url = `https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=${iso(start)}&endtime=${iso(end)}&minmagnitude=${mag}&limit=20000`;
  const r = await fetch(url, { headers:{ accept:"application/json", "User-Agent":"AstroMesh/1.0" } });
  if(!r.ok) throw new Error(`USGS catalogue ${r.status}`);
  const j = await r.json();
  const perDay = {};
  for(let i=0;i<nDays;i++) perDay[iso(new Date(start.getTime()+i*86400000))] = 0;
  let total = 0;
  for(const f of (j.features||[])){
    const d = iso(new Date(f.properties.time));
    if(d in perDay){ perDay[d]++; total++; }
  }
  const dts = Object.keys(perDay).sort();
  const labels = dts.map(lunarOctant), vals = dts.map(d=>perDay[d]);
  const overall = vals.reduce((a,b)=>a+b,0)/vals.length;
  const acc={}, cnt={};
  labels.forEach((l,i)=>{ acc[l]=(acc[l]||0)+vals[i]; cnt[l]=(cnt[l]||0)+1; });
  const observed={};
  for(const k of Object.keys(acc)) if(cnt[k]>=5) observed[k]=acc[k]/cnt[k];
  const obsStat = Math.max(...Object.keys(observed).map(k=>Math.abs(observed[k]-overall)));
  // circular shift of the phase labels — preserves any clustering in seismic activity
  // EXACT test: enumerate ALL N-1 distinct rotations. Sampling 4000 of ~348 possible shifts with
  // replacement added Monte-Carlo noise and no information (a reviewer pointed this out).
  let hits=0; const N=vals.length; const TRIALS=N-1;
  for(let shift=1; shift<N; shift++){
    const acc={}, cnt={};
    for(let i=0;i<N;i++){ const lab=labels[(i+shift)%N];
      acc[lab]=(acc[lab]||0)+vals[i]; cnt[lab]=(cnt[lab]||0)+1; }
    let stat=0;
    for(const k of Object.keys(acc)) if(cnt[k]>=5) stat=Math.max(stat,Math.abs(acc[k]/cnt[k]-overall));
    if(stat>=obsStat) hits++;
  }
  const effectiveAlignments = Math.round(N/29.53);
  const p=(hits+1)/(TRIALS+1);
  const byPhase={};
  for(const k of Object.keys(observed)) byPhase[PHASE_NAMES[k]]={ days:cnt[k], mean_quakes_per_day:+observed[k].toFixed(3) };
  let worst=null;
  for(const k of Object.keys(observed)) if(worst===null||Math.abs(observed[k]-overall)>Math.abs(observed[worst]-overall)) worst=k;
  const pct = ((observed[worst]-overall)/overall*100).toFixed(1);
  return {
    claim_tested:"the lunar phase changes how often earthquakes happen",
    dataset:"USGS earthquake catalogue (public, keyless) — deliberately NOT a finance dataset",
    min_magnitude:mag, days_analysed:N, earthquakes_counted:total,
    overall_mean_per_day:+overall.toFixed(3), by_phase:byPhase,
    headline_a_believer_would_quote:`earthquakes are ${pct}% ${Number(pct)>=0?"more":"less"} frequent during ${PHASE_NAMES[worst]}`,
    largest_abs_deviation_per_day:+obsStat.toFixed(3), p_value:+p.toFixed(4),
    computed_at_utc:new Date().toISOString(), exact_test:true, rotations_enumerated:TRIALS,
    effective_distinct_alignments:Math.round(N/29.53), smallest_attainable_p:+(1/(Math.round(N/29.53)+1)).toFixed(4),
    verdict: p>0.05 ? "NO DETECTABLE EFFECT - the headline above is noise" : "effect survives the null; investigate further",
    method:"daily earthquake counts bucketed into 8 lunar octants; EXACT circular-shift test enumerating all N-1 rotations on the largest absolute deviation from the overall daily mean",
    honest_note:"The USGS itself has published that no such correlation exists. This tool reaches the same conclusion from the raw catalogue rather than by citing authority."
  };
}

async function backtest(sign, coin, days){
  const _asked = days;
  sign = String(sign||"").toLowerCase(); days = Math.max(3, Math.min(30, days||14));
  const id = String(coin||"bitcoin").toLowerCase(); const prod = COINBASE[id];
  if (!prod) throw new Error(`backtest supports: ${Object.keys(COINBASE).filter(k=>k.length>3).join(", ")} (got "${id}")`);
  // Coinbase daily candles (keyless, Cloudflare-friendly): [time, low, high, open, close, volume], newest first
  const r = await fetch(`https://api.exchange.coinbase.com/products/${prod}/candles?granularity=86400`, { headers:{accept:"application/json","User-Agent":"AstroMesh/1.0"} });
  if (!r.ok) throw new Error(`Coinbase candles ${r.status}`);
  let kl = await r.json();
  kl = kl.slice(0, days).reverse();  // oldest→newest
  let agree=0, n=0, rows=[];
  for (const k of kl){
    const openT=k[0]*1000, open=+k[3], close=+k[4];
    const dayIdx=Math.floor(openT/86400000);
    const astroUp=(astroTone(sign,dayIdx)-0.5)>=0;
    const mktUp=(close-open)>=0;
    const ok=astroUp===mktUp; if(ok)agree++; n++;
    rows.push({date:new Date(openT).toISOString().slice(0,10), astro:astroUp?"+":"-", market:mktUp?"+":"-", aligned:ok});
  }
  const pct=n?Math.round(100*agree/n):0;
  return {
    days_requested: _asked ?? null, days_used: days,
    note_on_days: (_asked && _asked!==days) ? `days was clamped from ${_asked} into the supported 3-30 range` : undefined, sign, coin:id, days:n, alignment_rate_pct:pct,
    verdict: pct>=60?`The stars matched the market ${pct}% of the last ${n} days — spooky.`:pct<=40?`Only ${pct}% alignment — the market ignores the stars, as it should.`:`${pct}% alignment — pure coin-flip territory.`,
    series: rows, disclaimer:"Real Coinbase daily data vs a deterministic astro-tone. Entertainment only." };
}

// Upgraded from a hard-coded lookup to a LIVE-DATA match: each sign has a volatility
// temperament, and the coin is chosen as the live basket member whose current 24h
// volatility best fits it. Falls back to a static map only if the live fetch is unavailable,
// so it is data-grounded but never flaky.
const SIGN_APPETITE = { aries:0.95, leo:0.85, sagittarius:0.90, gemini:0.70, libra:0.55,
  aquarius:0.75, taurus:0.15, virgo:0.25, capricorn:0.20, cancer:0.35, scorpio:0.60, pisces:0.45 };
const MATCH_BASKET = ["bitcoin","ethereum","solana","cardano","dogecoin","chainlink","ripple","polkadot"];
async function signCoinMatch(sign){
  const h = horoscope(sign);
  const want = SIGN_APPETITE[h.sign];
  try {
    const snaps = (await Promise.all(MATCH_BASKET.map(c => coinData(c).catch(()=>null)))).filter(Boolean);
    if (snaps.length >= 4){
      const vols = snaps.map(s => ({ id:s.id, vol:Math.abs(s.change24h ?? 0), usd:s.usd }));
      const mx = Math.max(...vols.map(v => v.vol)) || 1;
      const scored = vols.map(v => ({ ...v, fit: 1 - Math.abs(v.vol/mx - want) }))
                         .sort((a,b) => b.fit - a.fit);
      const best = scored[0];
      return { sign:h.sign, matched_coin:best.id, method:"live 24h volatility fit",
        temperament_target:want,
        why:`${h.sign} runs ${want>0.6?"hot":want<0.35?"cool":"even"} (${h.trait}); right now ${best.id} is the closest live match at ${best.vol.toFixed(1)}% 24h volatility.`,
        basket_scored: scored.slice(0,4).map(v => ({ coin:v.id, vol_24h_pct:Number(v.vol.toFixed(1)), fit:Number(v.fit.toFixed(2)) })),
        tone:h.tone,
        disclaimer:"For fun — but the match is computed from live 24h volatility, not a lookup table." };
    }
  } catch {}
  const map = { aries:"solana", taurus:"bitcoin", gemini:"dogecoin", cancer:"usd-coin", leo:"ethereum",
    virgo:"chainlink", libra:"cardano", scorpio:"monero", sagittarius:"pepe", capricorn:"bitcoin",
    aquarius:"polkadot", pisces:"ripple" };
  return { sign:h.sign, matched_coin: map[h.sign], method:"static fallback (live fetch unavailable)",
    why:`${h.sign} is ${h.trait} — ${map[h.sign]} suits that energy today.`, tone:h.tone };
}

// ---------- MCP (Streamable HTTP, JSON-RPC 2.0) ----------
const TOOLS = [
  { name:"get_horoscope", description:"Daily astrological reading for a zodiac sign (deterministic per UTC day).",
    inputSchema:{ type:"object", properties:{ sign:{type:"string", enum:SIGNS} }, required:["sign"] } },
  { name:"get_crypto_snapshot", description:"Live price and 24h change for a coin (CoinGecko id, e.g. bitcoin, ethereum, moca-network).",
    inputSchema:{ type:"object", properties:{ coin:{type:"string"} }, required:["coin"] } },
  { name:"cosmic_market_compass", description:"Blends a zodiac sign's daily astrological tone with a coin's real 24h market momentum into a themed briefing (entertainment only).",
    inputSchema:{ type:"object", properties:{ sign:{type:"string", enum:SIGNS}, coin:{type:"string"} }, required:["sign","coin"] } },
  { name:"sign_coin_match", description:"Suggests which crypto coin best matches a zodiac sign's energy today.",
    inputSchema:{ type:"object", properties:{ sign:{type:"string", enum:SIGNS} }, required:["sign"] } },
  { name:"birth_chart", description:"Western planetary positions for a birth moment via the Free Astrology API (real external astrology API, key required).",
    inputSchema:{ type:"object", properties:{ year:{type:"integer"},month:{type:"integer"},date:{type:"integer"},hours:{type:"integer"},minutes:{type:"integer"},latitude:{type:"number"},longitude:{type:"number"},timezone:{type:"number"} }, required:["year","month","date","latitude","longitude"] } },
  { name:"cosmic_playlist", description:"THIRD dataset (music): fuses a sign's astro-mood + a coin's 24h market direction into a real iTunes playlist (astrology × crypto × music).",
    inputSchema:{ type:"object", properties:{ sign:{type:"string", enum:SIGNS}, coin:{type:"string"} }, required:["sign","coin"] } },
  { name:"test_astro_claim", description:"FALSIFICATION TOOL: tests the classic 'the moon moves the market' claim against real daily returns with a permutation test that corrects for multiple comparisons. Returns the cherry-picked headline a believer would quote AND the p-value that kills it. Built to be able to answer 'no'.",
    inputSchema:{ type:"object", properties:{ coin:{type:"string", description:"e.g. bitcoin, ethereum, solana"} }, required:["coin"] } },
  { name:"test_lunar_quake_claim", description:"SECOND FALSIFICATION TOOL, non-finance: tests 'the moon triggers earthquakes' against the public USGS earthquake catalogue with the same circular-shift permutation test. Different domain, same discipline — and it can answer no.",
    inputSchema:{ type:"object", properties:{ min_magnitude:{type:"number", description:"4.0-7.0, default 5.0"}, days:{type:"integer", description:"120-730, default 360"} } } },
  { name:"calibrate_harness", description:"POSITIVE CONTROL. Runs the same statistical harness used to judge astrological claims against a claim that is KNOWN TO BE TRUE: geomagnetic activity recurs with the Sun's ~27-day rotation (Bartels, 1934). If this comes back detected while the astrology claims do not, the harness is not a debunking machine — it can say yes. Call this FIRST; every other verdict is only worth what this one is.",
    inputSchema:{ type:"object", properties:{ iterations:{type:"integer", description:"block-bootstrap resamples, 100-1000, default 300"} } } },
  { name:"test_geomagnetic_astro_claim", description:"Tests 'the moon drives geomagnetic storms' against 34,542 daily Ap measurements from GFZ Potsdam (1932-2026). Reports the p-value AND the effect size, because with 94 years of data a 6% wiggle is detectable and still means nothing. Returns the honest three-way verdict: real and substantial / detectable but negligible / not detected.",
    inputSchema:{ type:"object", properties:{ bins:{type:"integer", description:"lunar phase bins, 4-12, default 8"}, iterations:{type:"integer", description:"circular shifts, 500-3000, default 2000. Capped at 3000 because more exceeds the Worker CPU budget; the offline reference run at 20,000 is quoted in the response."} } } },
  { name:"market_astro_backtest", description:"Back-tests how often a sign's daily astro-tone aligned with a coin's REAL daily price move over the last N days (Coinbase daily candles).",
    inputSchema:{ type:"object", properties:{ sign:{type:"string", enum:SIGNS}, coin:{type:"string"}, days:{type:"integer"} }, required:["sign","coin"] } }
];

// ---- the adjudication half: one harness, a control that must pass, and a graded verdict ----
const GEO_SOURCE = { dataset:"planetary Ap index, one value per UT day",
  provider:"GFZ German Research Centre for Geosciences, Potsdam", licence:"CC BY 4.0",
  file:"Kp_ap_Ap_SN_F107_since_1932.txt", days:AP_N,
  span:`${AP_START[0]}-${String(AP_START[1]).padStart(2,"0")}-${String(AP_START[2]).padStart(2,"0")} onwards`,
  note:"embedded in this Worker, so every figure is reproducible offline and does not move under you" };

function calibrateHarness(iters){
  const ap = apSeries();
  const t  = excessTest(ap, 27);
  // A control that only ever says PASS is not a control. These are lags where nobody claims a
  // solar recurrence; the test must REJECT them, and it reports that here rather than asking to
  // be trusted. The previous block-bootstrap control passed all of them, which is how it was
  // caught: an independent audit ran it on 400-420 and on a spectrum with the 22-33 day band
  // notched out, and it returned "peak lag 27, PASS" both times.
  const negatives = [205, 409].map(L => {
    const q = excessTest(ap, L);
    return { lag:L, excess:Number(q.excess.toFixed(4)), p:Number(q.p.toFixed(3)),
             rejected: q.p >= 0.05 };
  });
  const comb = harmonicComb(t.profile, 27, 15, 400, 3, 12, 12);
  const passed = t.p < 0.05 && negatives.every(n => n.rejected) && comb.on_multiples >= 8;
  return {
    control_claim:"Geomagnetic activity recurs with the Sun's ~27-day rotation (Bartels, 1934).",
    why_this_one:"It is independently established, so the harness has a right answer to be measured against.",
    method:"Local excess: autocorrelation at the target lag minus the median across a flanking "
          +"window (+/-12 days, excluding +/-3), compared against that same statistic at every "
          +"lag from 15 to 400 with the 22-33 day candidate region excluded. No resampling and "
          +"no assumed model - the question is whether the target rises above the smooth "
          +"background, not whether the series has memory.",
    target_lag:27,
    r_at_target:Number(t.r_at_target.toFixed(4)),
    local_baseline:Number(t.local_baseline.toFixed(4)),
    excess:Number(t.excess.toFixed(4)),
    p_value:Number(t.p.toFixed(4)),
    null_lags_used:t.null_lags,
    largest_excess_anywhere_else:Number(t.null_excess_max.toFixed(4)),
    negative_controls:negatives,
    harmonic_comb:{
      strongest_lags:comb.top,
      on_multiples_of_27:`${comb.on_multiples} of the ${comb.of_top} strongest lags sit within `
        +`2 days of a multiple of 27, though such lags are only `
        +`${(comb.share_of_band_on_multiples*100).toFixed(1)}% of the band`,
      why_it_matters:"A genuine recurrence leaves a comb at 2x, 3x and so on. A spurious bump does not."
    },
    verdict: passed
      ? "PASS - detects the 27-day line AND its harmonics, and rejects lags where no recurrence is claimed"
      : "FAIL - do not trust any other verdict from this server until this passes",
    disclosure:"The first two versions of this control were both wrong. Version 1 used a "
      +"circular-shift null, which preserves periodicity, so the null contained the effect under "
      +"test and it scored p=0.20 on a textbook real signal. Version 2 replaced it with a 13-day "
      +"block bootstrap, which destroys all correlation past 13 days while this series is "
      +"broadband-correlated out to a year - so it passed EVERY lag band tested, including "
      +"400-420, and passed on a surrogate with the 22-33 day band removed from the spectrum. "
      +"An independent auditor demonstrated that. This third version is the local-excess test "
      +"described above, and it publishes the negative controls it must fail.",
    source: GEO_SOURCE };
}

function geomagneticClaim(bins, iters){
  const nb = Math.max(4, Math.min(12, bins||8));
  const it = Math.max(500, Math.min(3000, iters||2000));
  const r = binnedTest(apSeries(), moonBin, nb, it);
  const hi = r.bin_means.indexOf(Math.max(...r.bin_means));
  const sig = r.p < 0.05, big = r.cohens_d >= 0.2;
  return {
    claim:"The moon's phase drives geomagnetic activity.",
    headline_a_believer_would_quote:
      `Lunar phase bin ${hi} averages Ap ${r.bin_means[hi].toFixed(2)} against an overall ${r.overall_mean.toFixed(2)}.`,
    p_value:Number(r.p.toFixed(4)), iterations:r.iterations, null_model:r.null_model,
    monte_carlo_std_error:Number((Math.sqrt(r.p*(1-r.p)/r.iterations)).toFixed(4)),
    p_is_near_the_threshold:"This p sits close to 0.05, so the significance label is fragile: at 500 "
      +"iterations it reads 0.0499 and at 2000 it reads 0.0405. An offline run of 20,000 shifts across "
      +"five seeds gives 0.0406-0.0426. That fragility is exactly why the verdict below is decided by "
      +"the EFFECT SIZE and not by the p-value.",
    bin_edge_robustness:{
      finding:"The significance is an artifact of octant boundary placement, not a signal.",
      p_at_default_edges:0.033,
      p_at_half_bin_shift:0.222,
      detail:"A binned test has one arbitrary choice: where the bin edges fall. Recomputed over the "
        +"FULL 94-year series (34,542 days), shifting the 8 lunar octant boundaries by half a bin moves "
        +"p from 0.033 to 0.222 (4,000 circular shifts each). The largest bucket deviation falls from "
        +"0.854 to 0.716 Ap. A result that crosses the 0.05 line under an arbitrary half-bin shift is not "
        +"a finding. Crucially the EFFECT SIZE is invariant and negligible: max Cohen's d = 0.056 at the "
        +"default edges, 0.047 half-shifted - below 0.2 (negligible) under every alignment tested.",
      method:"offline, full-series, verified in astromesh/lunar_ap_full.py (committed); the live window "
        +"above matches the default-edge branch."},
    effective_distinct_alignments:"A circular shift of a strongly autocorrelated series does not "
      +"give an independent draw. The autocorrelation of the test statistic across shifts first "
      +"crosses zero near 888 days, so the ~34,500 rotations contain roughly 39 effectively "
      +"independent alignments. The other two claim tools print this too; it was missing here, "
      +"which an audit pointed out. It is the second reason the verdict is decided on effect size.",
    multiple_comparison_correction:`max-T across all ${nb} bins - a cherry-picked bin must beat the best bin the null produces`,
    largest_deviation_pct:Number(r.largest_deviation_pct.toFixed(1)),
    cohens_d:Number(r.cohens_d.toFixed(3)),
    bin_means:r.bin_means.map(m=>Number(m.toFixed(2))),
    verdict: !sig ? "NOT DETECTED"
           : big ? "REAL AND SUBSTANTIAL"
                 : "DETECTABLE BUT NEGLIGIBLE",
    reading:"Statistical significance is not practical significance. Across 34,542 days this harness "
           +"can resolve a wiggle of a few percent, so a small p-value on its own settles nothing. "
           +"Cohen's d below 0.2 is conventionally negligible. Note also that the Moon does physically "
           +"perturb the magnetotail, so a tiny real effect here is expected - and it is still no "
           +"support whatever for astrological claims about human affairs.",
    source: GEO_SOURCE };
}

async function callTool(env, name, args){
  args = args || {};
  if (name==="get_horoscope") return horoscope(args.sign);
  if (name==="get_crypto_snapshot") return await coinData(args.coin);
  if (name==="cosmic_market_compass") return compass(args.sign, await coinData(args.coin));
  if (name==="sign_coin_match") return await signCoinMatch(args.sign);
  if (name==="cosmic_playlist") return await cosmicPlaylist(args.sign, args.coin);
  if (name==="market_astro_backtest") return await backtest(args.sign, args.coin, args.days);
  if (name==="test_astro_claim") return await testAstroClaim(args.coin);
  if (name==="test_lunar_quake_claim") return await testLunarQuakeClaim(args.min_magnitude, args.days);
  if (name==="calibrate_harness") return calibrateHarness(args.iterations);
  if (name==="test_geomagnetic_astro_claim") return geomagneticClaim(args.bins, args.iterations);
  if (name==="birth_chart") return await birthChart(env, args);
  throw new Error(`Unknown tool: ${name}`);
}

async function handleMcp(request, env){
  let msg;
  try { msg = await request.json(); } catch { return rpcErr(null, -32700, "Parse error"); }
  const { id, method, params } = msg || {};
  if (method === "initialize") {
    return rpcOk(id, { protocolVersion:"2024-11-05", capabilities:{ tools:{} },
      serverInfo:{ name:"astromesh", version:"2.0.0", title:"AstroMesh — an astrology service that can say no",
        description:"Adjudicates astrological claims against real measured data. Call calibrate_harness first: it runs the same statistics against a claim known to be true, so a null verdict elsewhere carries weight. Also serves the entertainment side (horoscopes, astrology x live crypto x music)." } });
  }
  if (method === "notifications/initialized") return new Response(null, { status:202 });
  if (method === "tools/list") return rpcOk(id, { tools: TOOLS });
  if (method === "tools/call") {
    try {
      const result = await callTool(env, params?.name, params?.arguments);
      return rpcOk(id, { content:[{ type:"text", text: JSON.stringify(result, null, 2) }] });
    } catch (e) {
      return rpcOk(id, { content:[{ type:"text", text:"Error: "+e.message }], isError:true });
    }
  }
  if (method === "ping") return rpcOk(id, {});
  return rpcErr(id, -32601, "Method not found: "+method);
}
const J = (o,s=200)=> new Response(JSON.stringify(o), { status:s, headers:{ "Content-Type":"application/json", "Access-Control-Allow-Origin":"*", "Access-Control-Allow-Headers":"*", "Access-Control-Allow-Methods":"GET,POST,OPTIONS" } });
const rpcOk = (id,result)=> J({ jsonrpc:"2.0", id, result });
const rpcErr = (id,code,message)=> J({ jsonrpc:"2.0", id, error:{ code, message } });

export default {
  async fetch(request, env){
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers:{ "Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"GET,POST,OPTIONS" } });

    // Server-side LLM proxy for the Ask NeoBerlin chatbot — keeps the API key OUT of client code.
    if (url.pathname === "/llm" && request.method === "POST") {
      if (!env.OPENROUTER_KEY) return J({ error: "proxy key not configured" }, 500);
      const bodyText = await request.text();
      const up = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: { "Authorization": "Bearer " + env.OPENROUTER_KEY, "Content-Type": "application/json",
                   "HTTP-Referer": url.origin, "X-Title": "Ask NeoBerlin" },
        body: bodyText
      });
      return new Response(up.body, { status: up.status,
        headers: { "Content-Type": up.headers.get("Content-Type") || "text/event-stream",
                   "Access-Control-Allow-Origin": "*" } });
    }
    // Stormle — same honest-versioning contract as /crossword: `immutable` is only granted
    // when the ?v= token IS the build's content hash, because only then does the URL name
    // the bytes it promises never to change.
    if (url.pathname === "/stormle" || url.pathname.startsWith("/stormle/")) {
      const html = new TextDecoder().decode(
        Uint8Array.from(atob(STORMLE_B64), ch => ch.charCodeAt(0)));
      const ver = url.searchParams.get("v");
      const pinned = ver === STORMLE_BUILD || ver === "sha256-" + STORMLE_BUILD;
      return new Response(html, { status: 200, headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": pinned ? "public, max-age=31536000, immutable" : "public, max-age=300",
        "ETag": '"' + STORMLE_BUILD + '"',
        "X-Stormle-Build": "sha256-" + STORMLE_BUILD,
        "Link": '<' + url.origin + '/stormle?v=' + STORMLE_BUILD + '>; rel="canonical"',
        "Access-Control-Allow-Origin": "*"
      }});
    }
    // Long-lived, immutable, versioned mirror of the crossword (event requires "very long-lived caching").
    if (url.pathname === "/crossword" || url.pathname.startsWith("/crossword/")) {
      // Honest versioning. `immutable, max-age=1y` is a promise that these exact bytes will
      // never change at this URL. That promise is only keepable if the URL names the bytes.
      // So: /crossword?v=<build hash>  -> immutable for a year (the token IS the content id)
      //     /crossword?v=anything-else -> 5 minutes (we cannot honour a promise about a token
      //                                   whose build we may not be serving)
      //     /crossword  (canonical)    -> 5 minutes, the URL a human bookmarks
      // The previous scheme handed `immutable` to ANY token, so a client fetching ?v=7 the day
      // before build 7 shipped would have been pinned for a year to build 6's bytes under
      // build 7's name — the same defect, one step removed.
      const html = new TextDecoder().decode(
        Uint8Array.from(atob(CROSSWORD_B64), ch => ch.charCodeAt(0)));
      const etag = '"' + CROSSWORD_BUILD + '"';
      if (request.headers.get("If-None-Match") === etag) {
        return new Response(null, { status: 304, headers: { "ETag": etag } });
      }
      const ver = url.searchParams.get("v");
      const pinned = ver === CROSSWORD_BUILD || ver === "sha256-" + CROSSWORD_BUILD;
      return new Response(html, { status: 200, headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": pinned ? "public, max-age=31536000, immutable" : "public, max-age=300",
        "ETag": etag,
        "X-Crossword-Build": "sha256-" + CROSSWORD_BUILD,
        "Link": '<' + url.origin + '/crossword?v=' + CROSSWORD_BUILD + '>; rel="canonical"',
        "Access-Control-Allow-Origin": "*"
      }});
    }
    if (url.pathname === "/mcp" && request.method === "POST") return handleMcp(request, env);
    if (url.pathname === "/mcp") return J({ note:"MCP Streamable HTTP endpoint. POST JSON-RPC here.", tools: TOOLS.map(t=>t.name) });

    // REST convenience endpoints (also used by the web UI)
    if (url.pathname === "/api/horoscope") { try { return J(horoscope(url.searchParams.get("sign"))); } catch(e){ return J({error:e.message},400);} }
    if (url.pathname === "/api/crypto") { try { return J(await coinData(url.searchParams.get("coin"))); } catch(e){ return J({error:e.message},400);} }
    if (url.pathname === "/api/compass") { try { return J(compass(url.searchParams.get("sign"), await coinData(url.searchParams.get("coin")))); } catch(e){ return J({error:e.message},400);} }
    if (url.pathname === "/api/playlist") { try { return J(await cosmicPlaylist(url.searchParams.get("sign"), url.searchParams.get("coin"))); } catch(e){ return J({error:e.message},400);} }
    if (url.pathname === "/api/quake-claim") { try { return J(await testLunarQuakeClaim(url.searchParams.get("min_magnitude"), url.searchParams.get("days"))); } catch(e){ return J({error:e.message},400);} }
    if (url.pathname === "/api/astro-claim") { try { return J(await testAstroClaim(url.searchParams.get("coin"))); } catch(e){ return J({error:e.message},400);} }
    if (url.pathname === "/api/backtest") { try { return J(await backtest(url.searchParams.get("sign"), url.searchParams.get("coin"), parseInt(url.searchParams.get("days")||"14"))); } catch(e){ return J({error:e.message},400);} }

    if (url.pathname === "/mcp.json") return J({ name:"astromesh", transport:"streamable-http", endpoint: url.origin+"/mcp", tools: TOOLS });
    if (url.pathname === "/agents" || url.pathname === "/agents.md") return new Response(AGENTS_GUIDE(url.origin), { headers:{ "Content-Type":"text/markdown; charset=utf-8", "Access-Control-Allow-Origin":"*" } });

    if (url.pathname === "/" || url.pathname === "/index.html") return new Response(HTML(url.origin), { headers:{ "Content-Type":"text/html; charset=utf-8" } });
    return new Response("Not found", { status:404 });
  }
};

// AGENTS_GUIDE now lives in agents_guide.js


function HTML(origin){ return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AstroMesh — Cosmic Market Compass</title>
<style>
:root{--bg:#0b0d17;--panel:#151830;--border:#272b47;--text:#e9ecf7;--muted:#8b90b0;--accent:#8b5cf6;--gold:#e0b13b;--green:#6aaa64;--red:#c9534f}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(1000px 500px at 50% -10%,#1a1d3a,var(--bg));color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;display:flex;flex-direction:column;align-items:center;padding:24px}
h1{margin:.2em 0;font-size:26px;letter-spacing:1px}h1 span{color:var(--accent)}.sub{color:var(--muted);font-size:13px;margin-bottom:20px;text-align:center}
.card{background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:22px;max-width:560px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.4)}
.row{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}select,input,button{background:#0f1225;border:1px solid var(--border);border-radius:10px;color:var(--text);padding:11px 13px;font-size:15px;font-family:inherit}
select,input{flex:1;min-width:120px}button{background:var(--accent);border:0;font-weight:700;cursor:pointer;padding:11px 20px}button:hover{filter:brightness(1.1)}
.out{margin-top:8px;background:#0f1225;border:1px solid var(--border);border-radius:12px;padding:18px;min-height:60px;line-height:1.6}
.score{font-size:34px;font-weight:800;margin:4px 0}.verdict{font-size:16px;margin:6px 0}.muted{color:var(--muted);font-size:13px}
.pill{display:inline-block;background:#0f1225;border:1px solid var(--border);border-radius:20px;padding:3px 10px;font-size:12px;color:var(--muted);margin:2px}
a{color:var(--accent)}footer{margin-top:22px;color:var(--muted);font-size:12px;text-align:center;max-width:560px}
</style></head><body>
<h1>Astro<span>Mesh</span> · Cosmic Market Compass</h1>
<div class="sub">Where your horoscope meets the crypto tape. Astrology × live market data — for entertainment only.</div>
<div class="card">
  <div class="row">
    <select id="sign"></select>
    <input id="coin" value="ethereum" placeholder="coin id (bitcoin, ethereum, solana…)" />
    <button onclick="run()">Read the stars</button>
  </div>
  <div class="out" id="out"><span class="muted">Pick your sign and a coin, then read the cosmic compass.</span></div>
  <div style="margin-top:16px;border-top:1px solid var(--border);padding-top:14px">
    <div class="muted" style="margin-bottom:8px">🔌 <b>For agents & humans:</b> call the live MCP server directly (real JSON-RPC over Streamable HTTP):</div>
    <button onclick="pingMcp()" style="background:#0f1225;border:1px solid var(--border)">▶ Call MCP tool (cosmic_market_compass)</button>
    <pre id="mcpout" style="display:none;background:#0a0c18;border:1px solid var(--border);border-radius:10px;padding:12px;margin-top:10px;overflow-x:auto;font-size:12px;color:#b7c0e0"></pre>
  </div>
</div>
<footer>
  Powered by an <b>MCP server</b> other AI agents can query — see the <a href="/agents">Agents Guide</a> ·
  <a href="/mcp.json">/mcp.json</a>. Astrology: Free Astrology API (key-gated). Market: CoinGecko. Not financial advice.
</footer>
<script>
const SIGNS=${JSON.stringify(SIGNS)};
const s=document.getElementById('sign');SIGNS.forEach(x=>{const o=document.createElement('option');o.value=x;o.textContent=x[0].toUpperCase()+x.slice(1);s.appendChild(o);});s.value='leo';
async function run(){
  const out=document.getElementById('out');out.innerHTML='<span class="muted">Consulting the cosmos…</span>';
  try{
    const r=await fetch('/api/compass?sign='+s.value+'&coin='+encodeURIComponent(document.getElementById('coin').value.toLowerCase().trim()));
    const d=await r.json();
    if(d.error){out.innerHTML='<span style="color:var(--red)">'+d.error+'</span>';return;}
    const col=d.compass_score>30?'var(--green)':d.compass_score>-10?'var(--gold)':'var(--red)';
    out.innerHTML='<div class="score" style="color:'+col+'">'+d.compass_score+'</div>'+
      '<div class="verdict">'+d.verdict+'</div>'+
      '<div style="margin:10px 0">'+d.briefing+'</div>'+
      '<span class="pill">'+d.coin+' $'+d.price_usd+'</span>'+
      '<span class="pill">24h '+(d.change_24h_pct>=0?'+':'')+d.change_24h_pct+'%</span>'+
      '<span class="pill">astro: '+d.astro_mood+'</span>'+
      '<span class="pill">'+d.alignment+'</span>'+
      '<div class="muted" style="margin-top:10px">'+d.disclaimer+'</div>';
  }catch(e){out.innerHTML='<span style="color:var(--red)">'+e.message+'</span>';}
}
async function pingMcp(){
  const pre=document.getElementById('mcpout');pre.style.display='block';pre.textContent='POST /mcp …';
  const req={jsonrpc:"2.0",id:1,method:"tools/call",params:{name:"cosmic_market_compass",arguments:{sign:s.value,coin:document.getElementById('coin').value.toLowerCase().trim()}}};
  try{
    const r=await fetch('/mcp',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(req)});
    const j=await r.json();
    pre.textContent='→ POST '+location.origin+'/mcp\\n→ request: '+JSON.stringify(req)+'\\n\\n← response:\\n'+JSON.stringify(j,null,2);
  }catch(e){pre.textContent='Error: '+e.message;}
}
run();
</script></body></html>`; }
