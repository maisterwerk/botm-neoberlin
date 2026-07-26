# Blind head-to-head, v2 — with an effort-matched control and a model-diverse panel

Our pre-flight reviewers rejected the first panel for two reasons, both correct:
1. the control was ONE pass (549 words) against a nine-run lab — an effort confound, not a Mind-count test;
2. the three judges returned byte-identical vectors (9/9/9 vs 7/6/6), i.e. one evaluator sampled three
   times, so "3-0" carried no variance information.

Both are fixed here. The control is now effort-matched (one Mind, three passes: draft -> self-attack ->
revise, same question, comparable length). The panel is three DIFFERENT models, each given a different
strictness framing, labels hidden, and presentation order swapped (lab shown as A to judge 1, as B to
judges 2 and 3).

## Panel 1 (superseded): lab vs ONE-PASS control

| judge | LAB | SOLO (1 pass) |
|---|---|---|
| 1 (lab as B) | 27 | 19 |
| 2 (lab as A) | 27 | 19 |
| 3 (lab as A) | 27 | 19 |
| **mean** | **27.0** | **19.0** |

Zero variance. We do not use this result; it is kept here because deleting it would be dishonest.

## Panel 2 (the one that counts): lab vs EFFORT-MATCHED control

| judge model | shown as | LAB rigor/creat/self-crit | total | CONTROL rigor/creat/self-crit | total |
|---|---|---|---|---|---|
| small  | lab = A | 9 / 8 / 7 | **24** | 7 / 7 / 9 | 23 |
| large  | lab = B | 9 / 9 / 9 | **27** | 7 / 8 / 8 | 23 |
| medium | lab = B | 9 / 9 / 8 | **26** | 8 / 8 / 9 | 25 |
| **mean** | | **9.00 / 8.67 / 8.00** | **25.67** | **7.33 / 7.67 / 8.67** | **23.67** |

**Lab wins 3-0, but by +2.0 points (+8.4%), not the +8.0 (+42%) the unmatched panel claimed.**

Per-axis, this is the honest result:

| axis | lab | effort-matched solo | delta |
|---|---|---|---|
| rigor | 9.00 | 7.33 | **+1.67 lab** |
| creativity | 8.67 | 7.67 | **+1.00 lab** |
| self-critique | 8.00 | 8.67 | **-0.67 — the solo Mind WINS** |

Two of the three judges said why, unprompted:
- *"A is mathematically rigorous … but lists unfixed issues descriptively; B is more heuristic but shows exceptional self-critique with worked counterexamples (A2 disproof with numbers, explicit design reversals with math)."* (small model, lab = A)
- *"B edges out on rigor and creativity via precisely specified statistical machinery … while A's self-critique is more genuinely self-generated (it derives its own numeric counterexample that breaks its first design) versus B's fixes being attributed to an external red team."* (medium model, lab = B)

## What this actually shows

- The multi-Mind lab's advantage is real but **concentrated in rigor**, not in everything.
- **Roughly three quarters of the naive "swarm wins by 42%" margin was an effort artifact.** Give one Mind
  the same budget and an explicit self-attack pass and it closes most of the gap.
- On **self-critique the single Mind is at least as good** — a forced self-attack pass is a cheaper way to
  buy self-criticism than a second Mind, and two judges independently found the solo's self-critique more
  *authentic* because it was self-generated.
- The lab's remaining edge comes from a division of labour a single pass cannot easily fake: an adversary
  whose only job is to break the proposal, and who does not have to preserve the author's ego or narrative.
