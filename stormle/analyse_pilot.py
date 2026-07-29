#!/usr/bin/env python3
"""Analyses the six human sessions exactly as pre-registered in PREREGISTRATION.md.

Primary outcome: mean Skill (asked bits / best available bits) per guess, averaged within a game,
compared across the two conditions. The order was fixed before any data existed; this script does
not choose which games count, and it prints whatever came out.
"""
import json, sys, statistics as st

ORDER = ["sighted","blind","blind","sighted","blind","sighted"]   # from PREREGISTRATION.md

def load(path):
    games=[json.loads(l) for l in open(path) if l.strip()]
    if len(games)!=6: print(f"WARNING: {len(games)} games, the pre-registration says 6")
    return games

def per_game(g):
    # Amendment 1: guesses where best==0 carry no information to be had, so Skill is undefined
    # and they are excluded. This script did not implement it and therefore printed different
    # numbers from the submission — an audit caught that. Both readings are now printed.
    sk=[h["skill"] for h in g["history"] if h["best"] > 0]
    sk_raw=[h["skill"] for h in g["history"]]
    return {"blind":g["blind"], "guesses":len(g["history"]), "solved":g["solved"],
            "mean_skill":sum(sk)/len(sk) if sk else float("nan"),
            "mean_skill_raw":sum(sk_raw)/len(sk_raw) if sk_raw else float("nan"),
            "first_skill":sk[0] if sk else float("nan"),
            "words":[h["guess"] for h in g["history"]]}

if __name__=="__main__":
    games=[per_game(g) for g in load(sys.argv[1] if len(sys.argv)>1 else "pilot_sessions.jsonl")]
    print(f"{'#':<3}{'condition':<10}{'declared':<10}{'guesses':>8}{'solved':>8}{'mean skill':>12}  words")
    for i,(g,cond) in enumerate(zip(games,ORDER),1):
        agree = "ok" if (cond=="blind")==g["blind"] else "MISMATCH"
        print(f"{i:<3}{('blind' if g['blind'] else 'sighted'):<10}{cond:<10}{g['guesses']:>8}"
              f"{str(g['solved']):>8}{g['mean_skill']:>12.3f}  {' '.join(g['words'])}   {agree}")
    S=[g["mean_skill"] for g in games if not g["blind"]]
    B=[g["mean_skill"] for g in games if g["blind"]]
    print()
    print(f"sighted: n={len(S)}  mean skill {st.mean(S):.3f}  range {min(S):.3f}-{max(S):.3f}")
    print(f"blind  : n={len(B)}  mean skill {st.mean(B):.3f}  range {min(B):.3f}-{max(B):.3f}")
    print(f"difference (sighted - blind): {st.mean(S)-st.mean(B):+.3f}")
    ws=sum(1 for g in games if not g["blind"] and g["solved"]); wb=sum(1 for g in games if g["blind"] and g["solved"])
    print(f"solved: sighted {ws}/{len(S)}, blind {wb}/{len(B)}")
    print()
    Sr=[g["mean_skill_raw"] for g in games if not g["blind"]]
    Br=[g["mean_skill_raw"] for g in games if g["blind"]]
    print()
    print("WITHOUT amendment 1 (every guess counted, including the undefined ones):")
    print(f"  sighted {st.mean(Sr):.3f}  blind {st.mean(Br):.3f}  difference {st.mean(Sr)-st.mean(Br):+.3f}")
    print("  The amendment changes the size of the gap. Both readings are printed because the")
    print("  excluded guesses all fall in blind sessions, so the choice is not neutral.")
    print()
    print("Pre-registered reading: with three games per condition this cannot establish")
    print("significance and none is claimed. It is a direction and a spread, from one subject.")
