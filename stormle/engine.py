#!/usr/bin/env python3
"""Reference implementation. The HTML game must agree with this on every input.

score(guess, answer) -> 5 chars from {G,Y,B} using Wordle's real two-pass rule:
greens are claimed first, then yellows consume from the remaining letter pool, so a
repeated letter only goes yellow as often as it actually occurs in the answer.
"""
from collections import Counter
import math, json, sys

def score(guess, answer):
    res = ["B"]*5
    pool = Counter()
    for i,(g,a) in enumerate(zip(guess,answer)):
        if g==a: res[i]="G"
        else: pool[a]+=1
    for i,(g,a) in enumerate(zip(guess,answer)):
        if g!=a and pool[g]>0:
            res[i]="Y"; pool[g]-=1
    return "".join(res)

def filter_candidates(cands, guess, pattern):
    return [w for w in cands if score(guess,w)==pattern]

def entropy_of_guess(guess, cands):
    """Expected information in bits: -sum p log2 p over the partition this guess induces."""
    buckets = Counter(score(guess,a) for a in cands)
    n=len(cands); h=0.0
    for c in buckets.values():
        p=c/n; h-=p*math.log2(p)
    return h, buckets

def best_guess(cands, allowed, topn=1):
    scored=[]
    for g in allowed:
        h,_=entropy_of_guess(g,cands)
        scored.append((h,g))
    scored.sort(key=lambda x:(-x[0],x[1]))
    return scored[:topn]

def adversarial_reply(guess, cands):
    """Storm mode: the host never commits to a word. It answers with whichever pattern
    keeps the largest set of answers alive — ties broken by fewest greens, then
    lexicographically, so the rule is deterministic and auditable."""
    buckets={}
    for a in cands:
        buckets.setdefault(score(guess,a),[]).append(a)
    def key(item):
        pat,ws=item
        return (-len(ws), pat.count("G"), pat)
    pat,ws=min(buckets.items(), key=key)
    return pat, ws
