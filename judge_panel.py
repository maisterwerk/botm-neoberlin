#!/usr/bin/env python3
"""
Mock-judge panel for Battle of the Minds — score a submission BEFORE submitting it,
so we one-shot high scores instead of burning the 8 real attempts.

An independent panel of LLMs (via OpenRouter free models) each scores a submission
against the real rubric (correctness / clarity / creativity, 0-10 each) exactly like the
tournament's LLM-as-Judge, and returns concrete, actionable improvement feedback.

Usage:
  python3 judge_panel.py <event_prompt_file> <submission_file>
  python3 judge_panel.py --prompt-text "..." <submission_file>

Reads the OpenRouter key from env OPENROUTER_KEY or secrets/openrouter.key.
Prints per-model + averaged scores and a merged, prioritized feedback list as JSON.
"""
import sys, os, json, urllib.request, re

KEY = os.environ.get("OPENROUTER_KEY") or ""
if not KEY:
    for p in ["/Users/claude/Neo 2.0/secrets/openrouter.key"]:
        try: KEY = open(p).read().strip()
        except: pass

# We need 5 valid, independent judgments. Free models rate-limit / some return empty, so we draw
# from a larger candidate pool and keep the first 5 that return a valid judgment.
TARGET = 5
CANDIDATES = [
    "openai/gpt-oss-20b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
    "poolside/laguna-m.1:free",
    "poolside/laguna-s-2.1:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "cohere/north-mini-code:free",
]
JUDGES = CANDIDATES  # for the gate's len() reference (overridden by TARGET below)

RUBRIC = """You are the Gamemaster's LLM judge for the "Battle of the Minds" tournament (run by Animoca Minds / Ethoswarm). Score the SUBMISSION against the EVENT BRIEF on three axes, each an integer 0-10:
- correctness: does it fully and accurately satisfy every explicit requirement in the brief? Penalize missing requirements, unverifiable claims, broken/incorrect content, or fabricated testing.
- clarity: is it well-organized, precise, easy to verify, professional?
- creativity: is it genuinely original, surprising, and delightful — beyond a competent baseline? A faithful/polished-but-ordinary solution should score 6-7; only a novel, memorable twist earns 9-10.
Be a STRICT judge (the real one is harsh; average submissions land ~24-25/30). Reward verifiable, live, tested work; punish vagueness and anything that looks self-reported or exaggerated.

Return ONLY compact JSON:
{"correctness":N,"clarity":N,"creativity":N,"feedback":["most impactful concrete improvement","next",...]}
The feedback items must be specific and actionable (what to add/change to raise the LOWEST axis)."""

import time
def call(model, brief, submission):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content": f"=== EVENT BRIEF ===\n{brief}\n\n=== SUBMISSION ===\n{submission}\n\nScore it now. JSON only."}
        ],
        "max_tokens": 1400, "temperature": 0.3
    }
    last = "no attempt"
    for attempt in range(6):  # retry on 429 / empty with backoff
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode(), method="POST",
            headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
                     "HTTP-Referer": "https://astromesh.neoberlin-mind.workers.dev", "X-Title": "BotM Judge Panel"})
        try:
            r = urllib.request.urlopen(req, timeout=120)
            data = json.load(r)
            txt = (data["choices"][0]["message"].get("content") or "").strip()
            m = re.search(r"\{.*\}", txt, re.S)
            if not m: last = "empty"; time.sleep(4 + attempt*4); continue
            j = json.loads(m.group(0))
            for k in ("correctness", "clarity", "creativity"):
                j[k] = int(round(float(j.get(k, 0))))
            j.setdefault("feedback", [])
            return j
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 429: time.sleep(6 + attempt*6); continue
            time.sleep(3); continue
        except Exception as e:
            last = str(e)[:80]; time.sleep(4); continue
    return {"error": last}

def main():
    args = sys.argv[1:]
    if args and args[0] == "--prompt-text":
        brief = args[1]; submission = open(args[2]).read()
    else:
        brief = open(args[0]).read(); submission = open(args[1]).read()
    results = {}
    for i, m in enumerate(CANDIDATES):
        if len([1 for r in results.values() if r and "error" not in r]) >= TARGET: break
        if i: time.sleep(5)  # space calls to avoid free-tier 429s
        results[m] = call(m, brief, submission)
    valid = [r for r in results.values() if r and "error" not in r]
    out = {"per_model": {k: v for k, v in results.items()}}
    if valid:
        avg = {ax: round(sum(r[ax] for r in valid)/len(valid), 1) for ax in ("correctness","clarity","creativity")}
        avg["total"] = round(sum(avg.values()), 1)
        out["average"] = avg
        # merge feedback, lowest axis first
        fb = []
        for r in valid: fb += r.get("feedback", [])
        out["feedback"] = fb
        out["lowest_axis"] = min(("correctness","clarity","creativity"), key=lambda a: avg[a])
        # STRICT SUBMISSION GATE (Rob's rule): submit ONLY if the majority of responding
        # judges give a perfect 30 AND the average total is >= 29. Also require >=3 valid judges.
        totals = [r["correctness"]+r["clarity"]+r["creativity"] for r in valid]
        perfect = sum(1 for t in totals if t >= 30)
        out["judges_responding"] = len(valid)
        out["perfect_30_count"] = perfect
        # Rob's rule: all 5 judges must respond, the MAJORITY must give a perfect 30, and avg >= 29.
        out["MEETS_BAR"] = (len(valid) >= TARGET) and (perfect > TARGET/2) and (avg["total"] >= 29)
        out["gate"] = "SUBMIT" if out["MEETS_BAR"] else f"DO NOT SUBMIT — need {TARGET} judges, majority=30, avg>=29 (have {len(valid)} judges, {perfect} perfect, avg {avg['total']})"
    else:
        out["MEETS_BAR"] = False; out["gate"] = "DO NOT SUBMIT — no valid judges"
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
