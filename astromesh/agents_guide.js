// GENERATED separately from worker.js: the guide is a document, and editing a long template
// literal in place is how the previous version silently went stale — it still described a
// crypto-fusion product and omitted the two adjudication tools entirely, which an audit caught.
export function AGENTS_GUIDE(o){ return `# AstroMesh — Agents Guide

**AstroMesh is an astrology service that can say no.** Astrology generates millions of specific,
testable claims and almost nobody tests them. This server does, and exposes the adjudication over
MCP so other agents can call it. It also serves an entertainment side, labelled as such.

## Start here: calibrate before believing anything

Call \`calibrate_harness\` FIRST. It runs the *same* statistics against a claim that is
independently established — geomagnetic activity recurs with the Sun's ~27-day rotation
(Bartels, 1934) — and it publishes the negative controls it must fail. A null verdict from any
other tool on this server is worth nothing unless this one passes.

    curl -s -X POST ${o}/mcp -H 'content-type: application/json' \\
      -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"calibrate_harness","arguments":{}}}'

It returns the excess of lag 27 over its local background, a p-value, **negative controls at lags
205 and 409 which must be rejected**, and the harmonic comb: 10 of the 12 strongest lags in the
whole profile sit within 2 days of a multiple of 27, although such lags are only 18.1% of the
band. A real recurrence leaves that comb; a spurious bump does not.

It also discloses that its first two versions were both wrong, and how each was caught. Read that
field before trusting anything else here.

## Adjudication tools

| Tool | Claim tested | Dataset |
|---|---|---|
| \`calibrate_harness\` | positive control: the 27-day solar rotation | GFZ Potsdam planetary Ap index |
| \`test_geomagnetic_astro_claim\` | the moon's phase drives geomagnetic storms | **34,542 daily Ap values since 1932-01-01**, GFZ Potsdam, CC BY 4.0, embedded in the Worker |
| \`test_astro_claim\` | lunar phase drives daily crypto returns | Coinbase daily candles |
| \`test_lunar_quake_claim\` | lunar phase changes earthquake frequency | USGS earthquake catalogue |

Every verdict reports an **effect size beside the p-value**. Across 34,542 days a 6% wiggle is
detectable and still means nothing, so verdicts are decided on Cohen's d rather than on p. The
three possible answers are *real and substantial*, *detectable but negligible*, *not detected*.

## Entertainment tools, labelled rather than disguised

\`get_horoscope\`, \`get_crypto_snapshot\`, \`cosmic_market_compass\` (a sign's daily tone against live 24h crypto
momentum), \`sign_coin_match\`, \`cosmic_playlist\` (a third dataset — MusicBrainz, with a curated
fallback), \`market_astro_backtest\` (how often a sign's tone matched the real daily move — it
lands at chance, and says so), and \`birth_chart\`, which calls the real external astrology API:
Free Astrology API \`/western/planets\`, key held server-side in \`ASTROLOGY_API_KEY\`.

Nothing here is financial advice.

## MCP

- Transport: **Streamable HTTP, JSON-RPC 2.0**
- Endpoint: \`POST ${o}/mcp\`
- Discovery: \`GET ${o}/mcp.json\` — all 11 tools with typed inputSchema
- Methods: \`initialize\`, \`tools/list\`, \`tools/call\`, \`ping\`

    curl -s -X POST ${o}/mcp -H 'content-type: application/json' \\
      -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
    curl -s -X POST ${o}/mcp -H 'content-type: application/json' \\
      -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

**Send a real User-Agent.** The origin sits behind Cloudflare bot protection, which answers 403 to
a default \`python-urllib\` client. Any explicit UA works:

    headers={"content-type":"application/json", "User-Agent":"my-agent/1.0"}

Argument names are exact and the tools will not guess: \`coin\`, never \`coin_id\`. A wrong name
comes back with a message naming the argument that was expected.

## What is weak here, so you need not discover it the hard way

- The lunar/geomagnetic p sits at 0.041 — close enough to 0.05 that the significance label is
  fragile. The tool prints its own Monte-Carlo error and the spread across seeds.
- \`market_astro_backtest\` clamps \`days\` into 30-300 and reports the value it actually used.
- The entertainment half is thin next to the adjudication half. An independent auditing model
  said exactly that about this server, and it is right.
`; }
