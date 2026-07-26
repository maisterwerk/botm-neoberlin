#!/bin/bash
# Waits for the OpenRouter free-tier daily reset, then runs the cross-vendor lab replication.
target=1785110700   # 2026-07-27 00:05 UTC (reset + 5 min)
while [ "$(date -u +%s)" -lt "$target" ]; do sleep 120; done
cd "/Users/claude/Neo 2.0/projects/botm-artifacts/research"
python3 lab_run.py > lab_claude/crossvendor_run.log 2>&1
echo "exit=$? at $(date -u)" >> lab_claude/crossvendor_run.log
