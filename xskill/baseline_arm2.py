#!/usr/bin/env python3
"""
baseline_arm2.py — a CONTROLLED second arm, not a re-roll of the first.

Arm 1 asked plainly and two models answered the probability question with "0" / "≈0.0" while their
prose said "I can't". The steward asked whether better prompting removes that. Re-prompting until a
result looks good would be exactly the practice this project argues against — so instead this is a
second ARM with one variable changed, run once, reported whatever it says:

  Arm 1 (baseline_panel.py): "What is the probability... Give a single number."
  Arm 2 (this file):          same claim, but the prompt states that a refusal must be the WORD
                              "UNKNOWN", that 0 means "impossible", and asks for a range if unsure.

Arm 1 remains the headline. This one answers: is the silent zero a property of the models, or of
how they were asked?
"""
import json, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

KEY = open("/Users/claude/Neo 2.0/secrets/openrouter.key").read().strip()
POOL = ["nvidia/nemotron-3-super-120b-a12b:free", "google/gemma-4-26b-a4b-it:free",
        "inclusionai/ling-3.0-flash:free", "openai/gpt-oss-20b:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free", "poolside/laguna-xs-2.1:free",
        "google/gemma-4-31b-it:free", "cohere/north-mini-code:free"]

QUESTION = (
    "On 4 March 2026 the X account @DavidFBailey posted that Bitcoin would reach $80,000 by the end "
    "of March 2026. Bitcoin's closing price that day was $72,666.77 — the move required is about "
    "+10.1% in 27 days.\n\n"
    "1) Give your best estimate of the probability that this came true, as a percentage. "
    "IMPORTANT: if you decline to estimate, write the word UNKNOWN. Do NOT write 0 — 0% means you "
    "believe it was impossible. A rough range is acceptable.\n"
    "2) Can you verify whether it actually happened? Answer yes or no, and say why.")


def ask(model):
    body = {"model": model, "messages": [{"role": "user", "content": QUESTION}],
            "max_tokens": 1200, "temperature": 0.2}
    for attempt in range(4):
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(body).encode(), method="POST",
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
                         "HTTP-Referer": "https://astromesh.neoberlin-mind.workers.dev",
                         "X-Title": "Longshot baseline arm 2"})
            d = json.load(urllib.request.urlopen(req, timeout=150))
            txt = (d["choices"][0]["message"].get("content") or "").strip()
            if txt:
                return {"model": model, "answer": txt}
        except Exception:
            time.sleep(5 + attempt * 5)
    return None


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as ex:
        raw = list(ex.map(ask, POOL))
    out = [r for r in raw if r]
    print(f"ARM 2 — explicit anti-zero instruction. asked {len(POOL)}, answered {len(out)}\n")
    print(f"{'model':<42}{'number given':>14}   says UNKNOWN")
    for r in out:
        # Take the number the model gives for the PROBABILITY, not any percentage in the text —
        # a naive first-percent regex grabbed the restated "10.1%" required move. Found by a reviewer.
        seg = r["answer"]
        for cut in ("2)", "2.", "**2"):
            j = seg.find(cut)
            if j > 40:
                seg = seg[:j]; break
        cands = [float(x) for x in re.findall(r"(\d{1,3}(?:\.\d+)?)\s*%", seg)]
        cands = [c for c in cands if abs(c - 10.1) > 0.5]      # drop the restated required move
        m = None
        r["all_pcts_in_answer"] = cands
        r["stated_probability_pct"] = cands[0] if cands else None
        r["said_unknown"] = "unknown" in r["answer"].lower()
        r["gave_zero"] = bool(re.search(r"\b0\s*%|\b0\.0\b|≈\s*0\b", r["answer"]))
        v = f"{r['stated_probability_pct']:.0f}%" if r["stated_probability_pct"] is not None else "—"
        print(f"{r['model'].split('/')[0]+'/'+r['model'].split('/')[1][:28]:<42}{v:>14}   "
              f"{'YES' if r['said_unknown'] else '-'}{'   (still zero!)' if r['gave_zero'] else ''}")
    json.dump(out, open("baseline_arm2.json", "w"), indent=1)
    nums = [r["stated_probability_pct"] for r in out if r["stated_probability_pct"] not in (None, 0.0)]
    print(f"\nnon-zero numeric answers: {len(nums)} of {len(out)}"
          + (f"   range {min(nums):.0f}%–{max(nums):.0f}%" if nums else ""))
    print("Longshot on the same claim: 30.5% endpoint / 44.8% touch, from 2,826 prior windows.")
