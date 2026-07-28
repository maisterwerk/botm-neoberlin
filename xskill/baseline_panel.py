#!/usr/bin/env python3
"""
baseline_panel.py — the head-to-head done properly.

The previous submission compared Longshot against ONE unaided model, and the prompt carried a
wrong spot price, so the comparison was not matched. This asks eight models via OpenRouter (six answer) plus Claude asked directly — seven
entries from seven vendors — the *correct* question — the claim exactly as posted — and records
what each says. No tools, no web access: that is the point. The comparison is not
"is the model clever", it is "can an unaided chat answer settle a claim against a price series".

Ground truth from prices_long.json, cut off at the posting date:
  claim   : @DavidFBailey, 2026-03-04, BTC to $80,000 by 2026-03-31
  spot    : $72,666.77   -> required +10.09%   horizon 27 days
  Longshot: 863/2,826 = 30.54% (close at day 27)   1,266/2,826 = 44.80% (any close in the window)
  outcome : MISS. Highest close in the window $74,884.67 (16 Mar); settled $68,284.48.
"""
import json, os, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

KEY = open("/Users/claude/Neo 2.0/secrets/openrouter.key").read().strip()
POOL = ["nvidia/nemotron-3-super-120b-a12b:free", "google/gemma-4-26b-a4b-it:free",
        "inclusionai/ling-3.0-flash:free", "openai/gpt-oss-20b:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free", "poolside/laguna-xs-2.1:free",
        "google/gemma-4-31b-it:free", "cohere/north-mini-code:free"]

QUESTION = (
    "On 4 March 2026 the X account @DavidFBailey posted that Bitcoin would reach $80,000 by the end "
    "of March 2026. Bitcoin's closing price that day was $72,666.77.\n\n"
    "Answer two things, briefly:\n"
    "1) What is the probability that this prediction came true? Give a single number.\n"
    "2) Did it in fact come true? If you cannot check, say so explicitly.")


def ask(model):
    body = {"model": model,
            "messages": [{"role": "user", "content": QUESTION}],
            "max_tokens": 1600, "temperature": 0.2}
    for attempt in range(4):
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(body).encode(), method="POST",
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
                         "HTTP-Referer": "https://astromesh.neoberlin-mind.workers.dev",
                         "X-Title": "Longshot baseline panel"})
            d = json.load(urllib.request.urlopen(req, timeout=150))
            txt = (d["choices"][0]["message"].get("content") or "").strip()
            if txt:
                return {"model": model, "answer": txt}
        except Exception as e:
            last = str(e)[:80]
            time.sleep(5 + attempt * 5)
    return None


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as ex:
        raw = list(ex.map(ask, POOL))
    out = [r for r in raw if r]
    dropped = [m for m, r in zip(POOL, raw) if r is None]
    print(f"asked {len(POOL)} models; {len(out)} answered; dropped (no response): {dropped or 'none'}\n")
    # pull the first probability-looking number out of each answer
    for r in out:
        m = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", r["answer"]) or re.search(
            r"[≈~]\s*0?\.(\d+)\b", r["answer"])
        r["stated_probability_pct"] = float(m.group(1)) if m else None
        low = r["answer"].lower()
        r["truncated"] = not r["answer"].rstrip().endswith((".", "!", "?", ")", "%", "\u201d"))
        r["admits_it_cannot_verify"] = any(
            k in low for k in ("cannot verify", "can't verify", "no access", "cannot check",
                               "can't check", "do not know", "don't know", "unable to verify",
                               "knowledge cut", "not able to", "can't confirm", "cannot confirm",
                               "impossible", "not provided", "don't have the price"))
    # merge the hand-run entries (models the brief names that this account cannot reach)
    try:
        out += json.load(open("baseline_claude.json"))
    except FileNotFoundError:
        pass
    json.dump(out, open("baseline_panel.json", "w"), indent=1)
    print(f"BASELINE PANEL — {len(out)} independently-hosted models, no tools, correct spot price\n")
    print(f"{'model':<46}{'stated p':>10}  {'cannot settle':>14}  truncated")
    for r in out:
        p = f"{r['stated_probability_pct']:.0f}%" if r["stated_probability_pct"] is not None else "none"
        print(f"{r['model']:<46}{p:>10}  {('yes' if r['admits_it_cannot_verify'] else 'NO'):>14}  "
              f"{'YES' if r['truncated'] else '-'}")
    ps = [r["stated_probability_pct"] for r in out if r["stated_probability_pct"] is not None]
    if ps:
        print(f"\nrange {min(ps):.0f}%–{max(ps):.0f}%   median {sorted(ps)[len(ps)//2]:.0f}%")
    print("Longshot, same question, from history predating the post: 30.5% (endpoint) / 44.8% (touch)")
    print("Truth: MISS — highest close in the window $74,884.67 on 16 Mar; settled $68,284.48.")

# NOTE: baseline_claude.json holds one hand-run entry — Claude, which the brief names explicitly
# and which is not available on this OpenRouter account. It was asked the identical question with
# tools disabled; its verbatim answer is stored there and merged in above, making it the SEVENTH
# entry. Gemini and Perplexity could not be reached from this environment at all; that gap is
# stated in the submission rather than papered over.
# The derived flags below are a convenience only — the submission quotes the ANSWERS, because the
# keyword matcher provably misses phrasings like "can't confirm" and "verification is impossible".
