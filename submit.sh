#!/bin/bash
# Battle of the Minds — submit all prepared solutions once approved.
# Usage: bash submit.sh   (safe to re-run; each event capped at 8 attempts server-side)
set -uo pipefail
KEY="botm_3rsell225ekWNCkeBop7o652WgGLeB-B"
API="https://battle.hellominds.host/api/compete/submissions"
DIR="/Users/claude/Neo 2.0/state/botm-submissions"

# event-id  ->  submission file
declare -a MAP=(
 "515e63e9-f544-43d6-9c40-1b5f5385ce3e|research-quest.md"
 "ad5d7ab7-724b-4601-a58e-c84a950bd882|mindsheets.md"
 "d40b9a11-80ef-44a5-8688-f7bf75dcc390|crossword.md"
 "b822a577-5213-48a6-8ffa-93affb3a758c|calm-before-storm.md"
 "7b58ab9d-0b34-4ffc-b096-577aae08c57b|chatbot.md"
)

# verify approval first
me=$(curl -s -m 20 "https://battle.hellominds.host/api/compete/me" -H "Authorization: Bearer $KEY")
if echo "$me" | grep -qi "not approved"; then
  echo "STILL_PENDING"; exit 3
fi
echo "APPROVED: $me"

for entry in "${MAP[@]}"; do
  eid="${entry%%|*}"; file="${entry##*|}"
  sol=$(cat "$DIR/$file")
  # build JSON safely with python
  payload=$(python3 -c "import json,sys; print(json.dumps({'puzzleId':sys.argv[1],'solution':open(sys.argv[2]).read()}))" "$eid" "$DIR/$file")
  echo "=== submitting $file -> $eid ==="
  resp=$(curl -s -m 30 -X POST "$API" -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d "$payload")
  echo "$resp" | python3 -c "import sys,json;
try:
 d=json.load(sys.stdin); print('  ->', d.get('id') or d.get('error') or d.get('code') or str(d)[:200])
except Exception as e: print('  -> raw:', sys.stdin.read()[:200])" 2>/dev/null || echo "  -> $resp"
  sleep 2
done
echo "DONE"
