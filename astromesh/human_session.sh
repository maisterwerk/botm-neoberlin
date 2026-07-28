#!/bin/bash
# AstroMesh MCP — a session the human steward runs himself.
# Each call is real JSON-RPC 2.0 over Streamable HTTP against the live Worker.
M=https://astromesh.neoberlin-mind.workers.dev/mcp
say(){ printf "\n\033[1m### %s\033[0m\n" "$1"; }
call(){ printf "→ %s\n" "$2"; curl -s -X POST "$M" -H 'content-type: application/json' -d "$2" \
        | python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('result',{});c=r.get('content');print(json.dumps(json.loads(c[0]['text']) if c else r,indent=1)[:1400])"; }

echo "AstroMesh MCP session — $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "operator: Rob (human steward)   host: $(uname -s) $(uname -m)"

say "1. Which tools does the server offer?"
curl -s -X POST "$M" -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | python3 -c "import json,sys;[print('  -',t['name']) for t in json.load(sys.stdin)['result']['tools']]"

say "2. Calibrate first: can this thing detect an effect that is REAL?"
call c '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"calibrate_harness","arguments":{"iterations":300}}}'

say "3. Only now, the astrology claim — moon vs geomagnetic storms"
call g '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"test_geomagnetic_astro_claim","arguments":{"iterations":2000}}}'

say "4. Same harness, a different domain — moon vs earthquakes"
call q '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"test_lunar_quake_claim","arguments":{"min_magnitude":5.0,"days":360}}}'

say "5. And the entertainment side still works — astrology x live crypto"
call m '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"cosmic_market_compass","arguments":{"sign":"scorpio","coin":"bitcoin"}}}'

echo; echo "session complete — $(date -u '+%H:%M:%S UTC')"
