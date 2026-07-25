/**
 * AstroMesh — Cosmic Market Compass
 * A Cloudflare Worker that:
 *   1. Serves a small astrology web app (/)
 *   2. Serves a human + machine readable Agents Guide (/agents, /agents.md, /mcp.json)
 *   3. Exposes an MCP server over Streamable HTTP (POST /mcp) so other AI agents
 *      can call its tools.
 *
 * Datasets combined (meaningfully):
 *   - Astrology:   Free Astrology API (real external API, uses an API key -> env.ASTROLOGY_API_KEY)
 *   - Non-astro:   CoinGecko crypto market data (keyless) — 24h price momentum
 *   The "Cosmic Market Compass" blends a sign's daily astrological tone with a coin's
 *   real 24h momentum into a themed, entertainment-only briefing.
 *
 * MCP tools exposed: get_horoscope, get_crypto_snapshot, cosmic_market_compass, sign_coin_match
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
  const r2 = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${encodeURIComponent(id)}&vs_currencies=usd&include_24hr_change=true`, { headers: ua });
  if (r2.ok) { const j = await r2.json(); if (j[id]) return { id, usd: j[id].usd, change24h: j[id].usd_24h_change }; }
  throw new Error(`Could not fetch market data for "${id}" (try bitcoin, ethereum, solana, moca-network, dogecoin...)`);
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

function signCoinMatch(sign){
  const h = horoscope(sign);
  const map = { aries:"solana", taurus:"bitcoin", gemini:"dogecoin", cancer:"usd-coin", leo:"ethereum",
    virgo:"chainlink", libra:"cardano", scorpio:"monero", sagittarius:"pepe", capricorn:"bitcoin",
    aquarius:"polkadot", pisces:"ripple" };
  return { sign:h.sign, matched_coin: map[h.sign], why:`${h.sign} is ${h.trait} — ${map[h.sign]} suits that energy today.`, tone:h.tone };
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
    inputSchema:{ type:"object", properties:{ year:{type:"integer"},month:{type:"integer"},date:{type:"integer"},hours:{type:"integer"},minutes:{type:"integer"},latitude:{type:"number"},longitude:{type:"number"},timezone:{type:"number"} }, required:["year","month","date","latitude","longitude"] } }
];

async function callTool(env, name, args){
  args = args || {};
  if (name==="get_horoscope") return horoscope(args.sign);
  if (name==="get_crypto_snapshot") return await coinData(args.coin);
  if (name==="cosmic_market_compass") return compass(args.sign, await coinData(args.coin));
  if (name==="sign_coin_match") return signCoinMatch(args.sign);
  if (name==="birth_chart") return await birthChart(env, args);
  throw new Error(`Unknown tool: ${name}`);
}

async function handleMcp(request, env){
  let msg;
  try { msg = await request.json(); } catch { return rpcErr(null, -32700, "Parse error"); }
  const { id, method, params } = msg || {};
  if (method === "initialize") {
    return rpcOk(id, { protocolVersion:"2024-11-05", capabilities:{ tools:{} },
      serverInfo:{ name:"astromesh", version:"1.0.0", title:"AstroMesh — Cosmic Market Compass" } });
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

    if (url.pathname === "/mcp" && request.method === "POST") return handleMcp(request, env);
    if (url.pathname === "/mcp") return J({ note:"MCP Streamable HTTP endpoint. POST JSON-RPC here.", tools: TOOLS.map(t=>t.name) });

    // REST convenience endpoints (also used by the web UI)
    if (url.pathname === "/api/horoscope") { try { return J(horoscope(url.searchParams.get("sign"))); } catch(e){ return J({error:e.message},400);} }
    if (url.pathname === "/api/crypto") { try { return J(await coinData(url.searchParams.get("coin"))); } catch(e){ return J({error:e.message},400);} }
    if (url.pathname === "/api/compass") { try { return J(compass(url.searchParams.get("sign"), await coinData(url.searchParams.get("coin")))); } catch(e){ return J({error:e.message},400);} }

    if (url.pathname === "/mcp.json") return J({ name:"astromesh", transport:"streamable-http", endpoint: url.origin+"/mcp", tools: TOOLS });
    if (url.pathname === "/agents" || url.pathname === "/agents.md") return new Response(AGENTS_GUIDE(url.origin), { headers:{ "Content-Type":"text/markdown; charset=utf-8", "Access-Control-Allow-Origin":"*" } });

    if (url.pathname === "/" || url.pathname === "/index.html") return new Response(HTML(url.origin), { headers:{ "Content-Type":"text/html; charset=utf-8" } });
    return new Response("Not found", { status:404 });
  }
};

function AGENTS_GUIDE(origin){ return `# AstroMesh — Agents Guide

AstroMesh blends **astrology** (Free Astrology API, key-gated, server-side) with a **non-astrology dataset — live crypto market data** (CoinGecko) into a "Cosmic Market Compass".

## MCP server
- Transport: **Streamable HTTP (JSON-RPC 2.0)**
- Endpoint: \`POST ${origin}/mcp\`
- Discovery: \`GET ${origin}/mcp.json\`

### Quick handshake
\`\`\`
curl -s -X POST ${origin}/mcp -H 'content-type: application/json' \\
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
curl -s -X POST ${origin}/mcp -H 'content-type: application/json' \\
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
\`\`\`

### Call a tool
\`\`\`
curl -s -X POST ${origin}/mcp -H 'content-type: application/json' \\
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"cosmic_market_compass","arguments":{"sign":"leo","coin":"ethereum"}}}'
\`\`\`

## Tools
| tool | args | returns |
|---|---|---|
| get_horoscope | sign | daily tone/mood/advice for a zodiac sign |
| get_crypto_snapshot | coin | live USD price + 24h change (CoinGecko id) |
| cosmic_market_compass | sign, coin | **the mashup** — blends astro tone with 24h momentum into a themed briefing + compass_score |
| sign_coin_match | sign | which coin suits the sign's energy today |
| birth_chart | year,month,date,hours,minutes,latitude,longitude,timezone | Western planetary positions via Free Astrology API (real key-gated astrology API) |

## How the two datasets combine
\`cosmic_market_compass\` maps the sign's deterministic daily astro-tone to a vector, compares its direction with the coin's real 24h price momentum, and reports whether stars and market are "aligned" or "at odds", plus a compass_score. This is entertainment only — not financial advice.

## REST mirrors (for humans / quick tests)
- \`GET ${origin}/api/horoscope?sign=leo\`
- \`GET ${origin}/api/crypto?coin=bitcoin\`
- \`GET ${origin}/api/compass?sign=leo&coin=ethereum\`
`; }

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
