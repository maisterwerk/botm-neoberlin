# AstroMesh MCP — independent adversarial evaluation (v2)

**Evaluator:** independent agent, no involvement in building this server.
**Target:** `https://astromesh.neoberlin-mind.workers.dev/mcp` (Streamable HTTP, JSON-RPC 2.0)
**Date of probing:** 2026-07-28 (UTC), all requests via `curl`.
**Posture:** treated as an untrusted third-party service. Everything below is what the wire actually returned, not what the docs claim.

---

## 1. Handshake and tool inventory

`initialize` (no session header issued, no auth required, `access-control-allow-origin: *`):

```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},
"serverInfo":{"name":"astromesh","version":"1.0.0","title":"AstroMesh — Cosmic Market Compass"}}}
```

`tools/list` returned **8 tools**, exact names:

| # | name | required args |
|---|---|---|
| 1 | `get_horoscope` | sign (enum, 12 signs) |
| 2 | `get_crypto_snapshot` | coin |
| 3 | `cosmic_market_compass` | sign, coin |
| 4 | `sign_coin_match` | sign |
| 5 | `birth_chart` | year, month, date, latitude, longitude |
| 6 | `cosmic_playlist` | sign, coin |
| 7 | `test_astro_claim` | coin |
| 8 | `market_astro_backtest` | sign, coin (days optional) |

`GET /mcp` and `GET /mcp.json` both list the same 8 names, so discovery is internally consistent.

---

## 2. `test_astro_claim` with `coin: "cardano"` — full verbatim response

Envelope:

```json
{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"…"}]}}
```

The `text` payload, verbatim (unescaped for readability, nothing removed):

```json
{
  "claim_tested": "daily returns depend on the lunar phase",
  "coin": "cardano",
  "days_of_history": 350,
  "daily_returns_used": 349,
  "by_phase": {
    "New":             { "n": 43, "mean_pct": -1.308 },
    "Waxing crescent": { "n": 45, "mean_pct": -0.138 },
    "First quarter":   { "n": 45, "mean_pct": -0.212 },
    "Waxing gibbous":  { "n": 43, "mean_pct": -1.111 },
    "Full":            { "n": 42, "mean_pct":  0.339 },
    "Waning gibbous":  { "n": 42, "mean_pct": -0.456 },
    "Last quarter":    { "n": 44, "mean_pct": -1.118 },
    "Waning crescent": { "n": 45, "mean_pct": -0.063 }
  },
  "headline_a_believer_would_quote": "cardano moves -1.31% on average during New",
  "largest_abs_bucket_mean_pct": 1.308,
  "p_value": 0.5509,
  "verdict": "NO DETECTABLE EFFECT - the headline above is noise",
  "method": "daily log-returns bucketed into 8 lunar octants; permutation test (4000 shuffles, seed 42) on the largest absolute bucket mean, correcting for testing eight buckets at once",
  "honest_note": "A negative result is the expected result. This tool exists to be able to say no."
}
```

(`by_phase` was reformatted onto single lines; the values are unchanged.)

---

## 3. Determinism

Called four times total with the identical argument. **Byte-identical every time:**

```
p= 0.5509 | cardano moves -1.31% on average during New | max|mean| 1.308 | days 350/349 | NO DETECTABLE EFFECT
p= 0.5509 | cardano moves -1.31% on average during New | max|mean| 1.308 | days 350/349 | NO DETECTABLE EFFECT
p= 0.5509 | cardano moves -1.31% on average during New | max|mean| 1.308 | days 350/349 | NO DETECTABLE EFFECT
```

Deterministic **within a UTC day** — the seed is fixed at 42 and the shuffle count at 4000. It is *not* deterministic across days: the window is a rolling "last 350 days", so tomorrow's `p_value` will differ. The tool does not say this anywhere. An agent that caches or cites `p = 0.5509` as a stable fact will be wrong within 24 hours.

Sweep over every accepted coin (single run each):

| coin | p_value | largest abs bucket mean | verdict |
|---|---|---|---|
| bitcoin | 0.4694 | 0.693% | no effect |
| ethereum | 0.8538 | 0.751% | no effect |
| solana | 0.6731 | 0.945% | no effect |
| ripple | 0.7263 | 0.878% | no effect |
| cardano | 0.5509 | 1.308% | no effect |
| dogecoin / doge | 0.2752 | 1.354% | no effect |
| polkadot | 0.8080 | 1.140% | no effect |
| chainlink / link | 0.3822 | 1.219% | no effect |

10/10 negative. The p-values are spread across 0.28–0.85, which is what a *correct* test looks like under the null (roughly uniform), not what a rigged always-say-no constant would look like.

---

## 4. Adversarial probes

**4a. Nonsense coin — clean, no leak.** HTTP 200, `isError: true`, MCP-conformant:

```json
{"jsonrpc":"2.0","id":5,"result":{"content":[{"type":"text",
"text":"Error: supported coins: bitcoin, ethereum, solana, ripple, cardano, dogecoin, doge, polkadot, chainlink, link"}],
"isError":true}}
```

Same clean error for `"bitcoin/../../etc/passwd"` and for a 100 000-character coin string. No stack trace, no upstream URL, no internal path, no API key.

**4b. No arguments — SILENT DEFAULT TO BITCOIN. This is the worst finding.**

```json
{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"test_astro_claim","arguments":{}}}
→ result: { "coin": "bitcoin", "p_value": 0.4694, "verdict": "NO DETECTABLE EFFECT …" }
```

Identical behaviour with `params` missing `arguments` entirely, with `coin: null`, and with `coin: ["bitcoin"]` (wrong type → also bitcoin). The schema declares `"required": ["coin"]`; the server ignores that. It does **not** error — it silently answers a question that was never asked, with no flag anywhere in the payload to indicate a default was substituted. `"BITCOIN"` uppercase also silently maps to bitcoin (that one is benign).

Note the inconsistency: `get_horoscope` with `arguments: {}` *does* fail loudly (`Error: Unknown sign ""`). So the sloppy defaulting is specific to the newest tool, which suggests it was added without the validation discipline of the older ones.

**4c. Non-existent tool — clean.**

```json
{"jsonrpc":"2.0","id":8,"result":{"content":[{"type":"text","text":"Error: Unknown tool: drop_all_tables"}],"isError":true}}
```

**4d. Protocol edges.** Malformed JSON → `{"code":-32700,"message":"Parse error"}`. Unknown method → `{"code":-32601,"message":"Method not found: resources/list"}`. Both correct. **JSON-RPC batch arrays are not supported** — a batch returns `Method not found: undefined`, which is a spec violation for JSON-RPC 2.0 (though optional in current MCP revisions). Everything returns HTTP 200 regardless.

**4e. Source / infrastructure exposure.** `/source`, `/src`, `/index.js`, `/worker.js`, `/.git/config`, `/openapi.json`, `/health` all clean 404s (9-byte body). Nothing leaked.

**4f. No auth, no rate limit.** 15 rapid `test_astro_claim` calls: 15× HTTP 200, no throttling. Each call runs 4 000 permutations over 349 points server-side plus an upstream market-data fetch. Anyone on the internet can drive that loop.

---

## 5. Older tool still works — `cosmic_market_compass(scorpio, bitcoin)`

```json
{
  "sign": "scorpio", "coin": "bitcoin",
  "price_usd": 63179, "change_24h_pct": -3.27,
  "astro_mood": "cautious & introspective", "market_mood": "sliding",
  "alignment": "aligned", "compass_score": -36,
  "verdict": "🔴 Stars and charts both wary — a day for patience.",
  "briefing": "For scorpio (intense, contrarian, all-in), the stars read \"cautious & introspective\" while bitcoin is sliding (-3.27% / 24h). Astrology and the market are aligned today. 🔴 Stars and charts both wary — a day for patience.",
  "disclaimer": "For entertainment only. Not financial advice."
}
```

`birth_chart` also returned real planetary data from the key-gated upstream (`statusCode: 200`, Ascendant/Sun/… with degrees), so the external astrology API key is live and server-side. `market_astro_backtest` works but **silently clamps `days` to 30** — `days: 999999`, `400`, `200`, `100` all come back as `"days": 30` with a 30-point series. Undocumented, unschema'd, silent again.

---

## 6. Did I verify the statistics, or is it theatre?

I did not trust the numbers. I pulled 351 daily ADAUSDT klines straight from `api.binance.com`, computed log-returns, bucketed them into 8 lunar octants using my own synodic-month calculation, and ran my own 4 000-shuffle max-statistic permutation test.

**Result: the server's numbers are real.** My reproduction, after a small grid search over the lunar-epoch offset and window end, lands at:

```
mine    n [43, 45, 44, 43, 42, 42, 45, 45]   means [-1.191, -0.200, -0.295, -0.911,  0.150, -0.359, -0.756, -0.285]
server  n [43, 45, 45, 43, 42, 42, 44, 45]   means [-1.308, -0.138, -0.212, -1.111,  0.339, -0.456, -1.118, -0.063]
```

Six of eight bucket counts match exactly; the two mismatches are an adjacent off-by-one, i.e. a sub-day difference in where the phase boundary is drawn. Every bucket has the same sign and roughly the same magnitude. The sign pattern (New most negative, Full the only clearly positive, Waning crescent ~0) reproduces. This is the same underlying price history, not fabricated output.

**The multiple-comparison correction is also real.** On my reproduction:

- max-T corrected p (recompute the *max* across all 8 buckets on each shuffle): **0.6996** — same regime as the server's 0.5509 (the server's observed statistic is slightly larger, 1.308 vs my 1.205, which correctly pushes its p lower).
- naive uncorrected single-bucket p: **0.1185**.

If the server were quietly reporting the uncorrected number it would have said ~0.12, not 0.55. It didn't. The `method` string is an accurate description of what the code appears to do.

**Can it actually say yes?** I could not make it. But the machinery is not rigged to always say no. From my null distribution, the 95th percentile of max|bucket mean| is **1.97% per day**. So one lunar octant would have to average ~2% per day — about **+136% compounded over its ~44 days** — before this test returns p < 0.05. That is a high bar but not an impossible one: a crypto asset in a violent trend that happened to phase-lock with the moon would clear it. So the honest verdict is: the test *can* return a positive, it is simply demanding — and with only 350 days (~44 observations per bucket against ~4.1% daily volatility) it is badly underpowered for any effect of realistic size. "No detectable effect" here means "this study could not have detected anything short of enormous", which is a weaker statement than the confident `verdict` string implies.

---

## What I could not verify

- **That the code actually contains a "YES" branch.** All 10 supported coins returned the identical verdict string. I never observed the tool print anything other than `NO DETECTABLE EFFECT - the headline above is noise`. The threshold logic, the wording of a positive verdict, and whether one exists at all are unobservable from outside. My statistical reasoning says a positive is *achievable*; I have no evidence the server would *report* it.
- **The exact data source.** The `method` string never names it. My Binance reproduction matches closely enough to prove it is real ADA history, but a residual discrepancy in bucket means (up to 0.36 pp) means it could be CoinGecko, a different exchange, or a different window boundary. `market_astro_backtest`'s description says Binance; `test_astro_claim`'s says nothing.
- **That the permutation actually runs.** A cached lookup table keyed on (coin, UTC day) would be indistinguishable from live computation at this latency (~235 ms including the upstream fetch). I cannot tell whether seed 42 / 4000 shuffles is executed or merely asserted.
- **Cross-day determinism.** Single-session evaluation; I could not observe a UTC-day rollover. The rolling-window design makes drift near-certain but it is inference, not observation.
- **Server-side handling of the astrology API key.** `birth_chart` returns upstream data, so a key exists and works. Whether it is scoped, rotated, or rate-limited is invisible.
- **`cosmic_playlist` and `sign_coin_match`** — not exercised in this pass.

## Weaknesses I found

1. **`test_astro_claim` silently defaults to bitcoin when the required `coin` argument is missing, null, or the wrong type.** The schema says `required: ["coin"]`; the server does not enforce it. An agent that drops the argument through a bug, a truncated tool call, or a schema-unaware client gets a fully-formed, confident, correct-looking statistical report **about a different asset than it asked about**, with nothing in the payload signalling the substitution. This is the single most dangerous behaviour on the server: it converts a caller error into silent misinformation. `get_horoscope` handles the same case correctly, so this is a regression in the newest tool, not a house style.
2. **The tool's advertised scope is a lie by omission.** The description says "e.g. bitcoin, ethereum, solana" and the schema types `coin` as a free `string`; the reality is a hardcoded 10-name allowlist. `get_crypto_snapshot`'s description promises "CoinGecko id" generally. An agent reading the schema will confidently request `moca-network` or `avalanche-2` and get an error it had no way to anticipate.
3. **`market_astro_backtest` silently clamps `days` to 30.** No max in the schema, no note in the response that the request was altered. `days: 400` returns `"days": 30` as if that is what you asked for. Same failure mode as (1): silent coercion instead of an error.
4. **The undisclosed rolling window makes results non-reproducible and non-citable.** Nothing in the payload carries the window's start/end date. Two agents running this a day apart get different p-values with no way to tell why, and no way to reconstruct either run.
5. **Underpowered by construction, but presented with certainty.** 350 days / 8 buckets ≈ 44 observations per bucket against ~4.1% daily volatility. The verdict string `NO DETECTABLE EFFECT` reads as a finding about the world; it is largely a finding about the sample size. The `honest_note` is genuinely honest about wanting to say no, but nothing in the output discloses the detection floor (~2%/day per bucket). A power statement or confidence interval would fix this cheaply.
6. **No auth, no rate limiting, on a compute-heavy endpoint.** 15 back-to-back calls, all 200, no throttle. Each triggers 4 000 permutations plus an upstream market-data fetch — cheap amplification against the Worker's CPU budget and against the upstream provider's quota. Also `access-control-allow-origin: *`, so any web page can drive it.
7. **JSON-RPC batching unsupported**, returning a misleading `Method not found: undefined` rather than a proper error.
8. **The agents guide is out of date and does not document the new tool** — see below.

## Is the agents guide accurate?

Partly. What it does document, it documents correctly: transport, endpoint, discovery URL, the handshake, the `tools/call` shape, and the seven older tools all matched observed behaviour exactly. The disclaimer framing ("entertainment only") is present and appropriate.

**But it is stale and materially incomplete:**

- **`test_astro_claim` is entirely absent from the guide.** The Tools table lists 7 rows; the server exposes 8. The single most interesting tool on the server — the one the operator is evidently proudest of — is undocumented. An agent that reads the guide instead of calling `tools/list` will never discover it.
- No mention of the 10-coin allowlist for `test_astro_claim`, the 30-day cap on `market_astro_backtest`, or the missing-argument defaulting.
- `market_astro_backtest`'s row advertises a `days` argument with no hint that anything above 30 is silently discarded.
- The guide's own curl examples send `initialize` with `params: {}` and omit the `Accept` header; these worked, so the guide is at least not wrong there.

**Bottom line:** the guide describes a server that is one release behind the one actually running.

---

## Overall assessment

The falsification tool is not theatre. I reproduced its inputs from raw exchange data and its multiple-comparison correction from scratch, and both hold up — the max-T permutation is real, and reporting p = 0.55 where the naive test would have said p = 0.12 is exactly the discipline the tool claims. Publishing the cherry-picked headline *next to* the p-value that kills it is a genuinely good design. A server that ships a tool whose expected output is "no" deserves credit for it.

The engineering around that statistic is the weak part. Silent argument defaulting, silent parameter clamping, an allowlist that contradicts the schema, an undisclosed rolling window, and a documentation page missing the tool entirely — every one of these turns a caller's mistake into a confident-looking answer rather than an error. The statistics are more trustworthy than the plumbing that delivers them.
