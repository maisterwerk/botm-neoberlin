#!/usr/bin/env python3
"""Does the instrument actually help against the storm?

A: barometer play  — each turn, the highest-expected-information word (the page's own advice).
B: informed play   — each turn, a word chosen at random from those still possible. This is not a
                     strawman: player B never wastes a guess on a word already ruled out, which is
                     how most people play. B simply has no way to tell a sharp question from a
                     blunt one.
Same adversarial host, same tie-break (fewest greens, then the shipped FNV-1a salt), six guesses.
"""
import json, math, random
from engine import score

W = json.load(open("words.json"))
PROBES = [w for w, h in json.load(open("openers.json"))][:250]
SALT = "0"

def fnv(s):
    h = 2166136261
    for c in s:
        h ^= ord(c); h = (h * 16777619) & 0xFFFFFFFF
    return h

def adversarial(guess, cands):
    b = {}
    for a in cands: b.setdefault(score(guess, a), []).append(a)
    best = None
    for pat, ws in b.items():
        if best is None: best = (pat, ws); continue
        bp, bws = best
        if len(ws) > len(bws): best = (pat, ws)
        elif len(ws) == len(bws):
            if pat.count("G") < bp.count("G"): best = (pat, ws)
            elif pat.count("G") == bp.count("G") and fnv(pat+SALT) < fnv(bp+SALT): best = (pat, ws)
    return best

def entropy(g, cands):
    b = {}
    for a in cands: p = score(g, a); b[p] = b.get(p, 0) + 1
    n = len(cands); return -sum((c/n)*math.log2(c/n) for c in b.values())

def barometer_pick(cands):
    if len(cands) == len(W): return "TEARS"
    if len(cands) == 1: return cands[0]
    pool = W if len(cands) <= 150 else list(set(cands) | set(PROBES))
    best, bh, bc = None, -1, False
    s = set(cands)
    for g in pool:
        h = entropy(g, cands); c = g in s
        if h > bh + 1e-9 or (abs(h-bh) <= 1e-9 and c and not bc): bh, best, bc = h, g, c
    return best

def play(pick, rng=None):
    c = W[:]
    for turn in range(1, 7):
        g = pick(c, rng)
        pat, c = adversarial(g, c)
        if pat == "GGGGG": return turn
    return None

if __name__ == "__main__":
    a = play(lambda c, r: barometer_pick(c))
    print(f"A  barometer play : {'won on guess '+str(a) if a else 'LOST'}  (deterministic, one game)")
    rng = random.Random(11)
    wins, turns, left = 0, [], []
    N = 400
    for _ in range(N):
        c = W[:]
        res = None
        for turn in range(1, 7):
            g = rng.choice(c)
            pat, c = adversarial(g, c)
            if pat == "GGGGG": res = turn; break
        if res: wins += 1; turns.append(res)
        else: left.append(len(c))
    print(f"B  informed play  : won {wins}/{N} ({100*wins/N:.1f}%)  "
          f"mean winning guess {sum(turns)/len(turns):.2f}" if turns else
          f"B  informed play  : won {wins}/{N} ({100*wins/N:.1f}%)")
    if left:
        left.sort()
        print(f"   when it lost, median candidates still standing at the end: {left[len(left)//2]}")
    json.dump({"A_won_on":a,"B_wins":wins,"B_trials":N,
               "B_median_left_when_lost":(left[len(left)//2] if left else None)},
              open("ab_test.json","w"), indent=1)
