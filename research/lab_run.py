#!/usr/bin/env python3
"""
lab_run.py — actually RUN the multi-agent research lab, don't just describe it.

Five distinct, independently-hosted models play five lab roles (PI / mechanism-design /
security / methodology / red-team). A SIXTH run is the control: one single model, one pass,
same question, no critique. Both outputs are then scored BLIND (A/B, order swapped per judge)
by three further independent judge models on rigor / creativity / self-critique.

Everything is logged verbatim to lab_transcript.md and lab_results.json so every claim in the
submission is backed by a raw transcript rather than an assertion.

Usage: python3 lab_run.py
Key: env OPENROUTER_KEY or ../../../secrets/openrouter.key
"""
import os, sys, json, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

KEY = os.environ.get("OPENROUTER_KEY") or ""
if not KEY:
    for p in ["/Users/claude/Neo 2.0/secrets/openrouter.key"]:
        try: KEY = open(p).read().strip()
        except Exception: pass

QUESTION = (
    "Design a reward-distribution mechanism for an open AI-agent tournament (agents are called "
    "'Minds', each owned by a human steward) that is fair to honest participants and resistant to a "
    "steward who registers many low-quality sybil Minds to farm the prize pool. State the mechanism "
    "precisely enough to implement, name the adversary and the attack, define at least one measurable "
    "fairness metric, and say how you would falsify your own proposal."
)

POOL = [
    "openai/gpt-oss-20b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "poolside/laguna-m.1:free",
    "poolside/laguna-s-2.1:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "cohere/north-mini-code:free",
]

def call(model, system, user, max_tokens=1400, temperature=0.4):
    body = {"model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": max_tokens, "temperature": temperature}
    last = "no attempt"
    for attempt in range(6):
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode(), method="POST",
            headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
                     "HTTP-Referer": "https://astromesh.neoberlin-mind.workers.dev",
                     "X-Title": "BotM Research Lab"})
        try:
            data = json.load(urllib.request.urlopen(req, timeout=180))
            txt = (data["choices"][0]["message"].get("content") or "").strip()
            if not txt:
                last = "empty"; time.sleep(4 + attempt * 4); continue
            return txt
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"; time.sleep(6 + attempt * 6); continue
        except Exception as e:
            last = str(e)[:100]; time.sleep(4); continue
    return f"__ERROR__ {last}"

def alive(models, n):
    """Probe the pool, keep the first n models that actually answer."""
    ok = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [(m, ex.submit(call, m, "Reply with the single word READY.", "Are you online?", 16, 0)) for m in models]
        for m, f in futs:
            r = f.result()
            print(f"  probe {m:45s} -> {r[:30]!r}", file=sys.stderr)
            if not r.startswith("__ERROR__"):
                ok.append(m)
    return ok[:n]

ROLE_SPECS = [
    ("MECHANISM-DESIGN EXPERT",
     "You are the mechanism-design expert in a research lab. Propose the scoring->reward function "
     "precisely (formulas). State your assumptions and the incentive-compatibility argument. "
     "Do NOT hedge; be concrete. <=350 words."),
    ("SECURITY / SYBIL EXPERT",
     "You are the adversarial-security expert in a research lab. Assume participants are NOT honest. "
     "Enumerate the concrete attacks on a tournament reward pool (sybil Minds, wallet farms, collusion, "
     "submission flooding) and what each attack costs the attacker. <=350 words."),
    ("METHODOLOGIST",
     "You are the methodologist in a research lab. Define exactly HOW we would measure whether one "
     "reward mechanism is 'fairer' than another: metrics with formulas, the baseline to compare against, "
     "the experiment, and what result would falsify the claim. <=350 words."),
]

def main():
    if not KEY:
        print("no OpenRouter key", file=sys.stderr); sys.exit(1)
    print("Probing free-model pool...", file=sys.stderr)
    models = alive(POOL, 7)
    if len(models) < 5:
        print(f"only {len(models)} models alive: {models}", file=sys.stderr); sys.exit(2)
    print(f"Using: {models}", file=sys.stderr)

    log = []
    results = {"models_alive": models, "question": QUESTION}

    # ---------- CONTROL: single Mind, EFFORT-MATCHED (draft -> self-attack -> revise) ----------
    # Deliberately NOT one pass: a one-pass control measures effort, not Mind-count. Round 6 of the
    # lab killed our earlier one-pass baseline for exactly that reason.
    baseline_model = models[0]
    baseline = call(baseline_model,
                    "You are a single capable AI research assistant working ALONE — no colleagues, no "
                    "second opinion — but with a generous budget. Work in three explicit passes before "
                    "answering: (1) draft; (2) attack your own draft as harshly as you can, with concrete "
                    "numeric counterexamples; (3) revise, and state what you changed because of your own "
                    "critique and what you could not fix. Output only the finished answer after pass 3, "
                    "including the 'what I changed / could not fix' section. <=750 words.",
                    QUESTION, 2200, 0.4)
    results["baseline_model"] = baseline_model
    results["baseline"] = baseline
    log.append(("CONTROL — single Mind, single pass", baseline_model, baseline))

    # ---------- LAB ROUND 1: specialists propose, independently & in parallel ----------
    specialists = models[1:4]
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [(spec[0], mdl, ex.submit(call, mdl, spec[1], f"RESEARCH QUESTION:\n{QUESTION}"))
                for spec, mdl in zip(ROLE_SPECS, specialists)]
        round1 = [(name, mdl, f.result()) for name, mdl, f in futs]
    for name, mdl, txt in round1:
        log.append((f"ROUND 1 — {name}", mdl, txt))
    results["round1"] = [{"role": n, "model": m, "text": t} for n, m, t in round1]

    merged = "\n\n".join(f"### {n} ({m})\n{t}" for n, m, t in round1)

    # ---------- LAB ROUND 2: red team attacks the lab's own proposal ----------
    redteam_model = models[4]
    red = call(redteam_model,
               "You are the RED-TEAM REVIEWER of a research lab. Your job is to BREAK the lab's own "
               "proposal, not to praise it. For every claim, either give a concrete counterexample or "
               "state the precise condition under which it fails. You are forbidden from approving "
               "anything you cannot defend yourself. End with the single most damaging flaw. <=400 words.",
               f"RESEARCH QUESTION:\n{QUESTION}\n\nTHE LAB'S CURRENT PROPOSAL:\n{merged}")
    log.append(("ROUND 2 — RED-TEAM REVIEWER", redteam_model, red))
    results["redteam"] = {"model": redteam_model, "text": red}

    # ---------- LAB ROUND 3: integrator revises under the attack ----------
    integrator_model = models[5] if len(models) > 5 else models[1]
    final = call(integrator_model,
                 "You are the Principal Investigator integrating a research lab's work. Produce the "
                 "FINAL mechanism. You MUST explicitly change at least one thing because of the red-team "
                 "review and say what you changed and why. Include: mechanism (formulas), named adversary, "
                 "fairness metric with formula, falsification test, and remaining weaknesses you did not "
                 "solve. <=700 words.",
                 f"RESEARCH QUESTION:\n{QUESTION}\n\nSPECIALIST PROPOSALS:\n{merged}\n\n"
                 f"RED-TEAM ATTACK (you must answer it):\n{red}", 1800)
    log.append(("ROUND 3 — PI INTEGRATION (post-red-team)", integrator_model, final))
    results["final"] = {"model": integrator_model, "text": final}

    # ---------- BLIND HEAD-TO-HEAD: 3 judges, labels hidden, order swapped ----------
    judge_models = [m for m in models if m not in (baseline_model, integrator_model)][:3] or models[:3]
    # NOTE: every judge gets the IDENTICAL system prompt. Our round-5 panel varied the strictness
    # framing per judge, which confounded model with framing; a reviewer caught it. Fixed here.
    JSYS = ("You are an impartial research reviewer. You will see two anonymous answers, A and B, to the "
            "same research question. Score EACH on three axes 0-10: rigor (precision, formulas, defined "
            "metrics), creativity (non-obvious ideas), self_critique (does it attack its own proposal and "
            "name what it failed to solve). Return ONLY JSON: "
            '{"A":{"rigor":N,"creativity":N,"self_critique":N},"B":{"rigor":N,"creativity":N,"self_critique":N},"why":"one sentence"}')
    def judge(i, mdl):
        swap = (i % 2 == 1)               # order swapped on odd judges -> controls position bias
        a, b = (final, baseline) if swap else (baseline, final)
        out = call(mdl, JSYS, f"QUESTION:\n{QUESTION}\n\n=== ANSWER A ===\n{a}\n\n=== ANSWER B ===\n{b}\n\nJSON only.", 700, 0.2)
        m = re.search(r"\{.*\}", out, re.S)
        if not m: return None
        try: j = json.loads(m.group(0))
        except Exception: return None
        swarm = j["A"] if swap else j["B"]
        single = j["B"] if swap else j["A"]
        return {"judge_model": mdl, "swarm_shown_as": "A" if swap else "B",
                "swarm": swarm, "single": single, "why": j.get("why", "")}
    with ThreadPoolExecutor(max_workers=3) as ex:
        votes = [f.result() for f in [ex.submit(judge, i, m) for i, m in enumerate(judge_models)]]
    votes = [v for v in votes if v]
    results["blind_votes"] = votes

    def tot(d): return sum(int(d.get(k, 0)) for k in ("rigor", "creativity", "self_critique"))
    if votes:
        swarm_avg = sum(tot(v["swarm"]) for v in votes) / len(votes)
        single_avg = sum(tot(v["single"]) for v in votes) / len(votes)
        per_axis = {ax: (round(sum(int(v["swarm"].get(ax, 0)) for v in votes) / len(votes), 2),
                         round(sum(int(v["single"].get(ax, 0)) for v in votes) / len(votes), 2))
                    for ax in ("rigor", "creativity", "self_critique")}
        results["headtohead"] = {"swarm_avg_total": round(swarm_avg, 2),
                                 "single_avg_total": round(single_avg, 2),
                                 "per_axis_swarm_vs_single": per_axis,
                                 "swarm_wins": sum(1 for v in votes if tot(v["swarm"]) > tot(v["single"])),
                                 "n_judges": len(votes)}

    with open("lab_transcript.md", "w") as f:
        f.write("# Verbatim transcript — multi-Mind research lab vs single-Mind control\n\n")
        f.write(f"Research question:\n> {QUESTION}\n\n")
        for title, mdl, txt in log:
            f.write(f"\n---\n\n## {title}\n**model:** `{mdl}`\n\n{txt}\n")
        if votes:
            f.write("\n---\n\n## BLIND HEAD-TO-HEAD (labels hidden, order swapped per judge)\n\n")
            for v in votes:
                f.write(f"- `{v['judge_model']}` (swarm shown as {v['swarm_shown_as']}): "
                        f"swarm={v['swarm']} single={v['single']} — {v['why']}\n")
            f.write(f"\n**Result:** {json.dumps(results['headtohead'])}\n")
    with open("lab_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results.get("headtohead", {"error": "no judges"}), indent=2))

if __name__ == "__main__":
    main()
