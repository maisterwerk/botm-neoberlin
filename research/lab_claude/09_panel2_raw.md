# Round 5 raw — blind head-to-head panel 2 (effort-matched control)

Protocol: three judges, each a DIFFERENT model, each given a different strictness framing.
Both texts were supplied as files with the framing headers, and each judge was instructed to
ignore any note about how a file was produced. Labels hidden; presentation order swapped
(lab = A for judge 1, lab = B for judges 2 and 3).

- **Judge 1 — claude-haiku class** (neutral framing). Lab shown as A.
  `{"A":{"rigor":9,"creativity":8,"self_critique":7},"B":{"rigor":7,"creativity":7,"self_critique":9},`
  `"why":"A is mathematically rigorous (Shapley value, James-Stein shrinkage, pre-registered falsification) and creative, but lists unfixed issues descriptively; B is more heuristic but shows exceptional self-critique with worked counterexamples (A2 disproof with numbers, explicit design reversals with math)."}`

- **Judge 2 — claude-opus class** ("be strict and discriminating — do not give both answers the same scores unless they are genuinely equal"). Lab shown as B.
  `{"A":{"rigor":7,"creativity":8,"self_critique":8},"B":{"rigor":9,"creativity":9,"self_critique":9},`
  `"why":"B specifies estimators, thresholds and statistical design tightly enough to implement (James-Stein shrinkage, exact winner's-curse debiaser, sampled Shapley, burn-not-rollover cap, worst-case TSI/SCR with paired bootstrap and deliberately uncorrected rejection criteria) and names more distinct, quantified unsolved failures, whereas A — though strong on ladder-not-peer scoring, base-model residual projection and a self-killing SGR(8)~2.9 counterexample — leaves key parameters (2^-i weights, S>=0.6 overlapping neighborhoods, (q-tau)^2 split) unmotivated and partly ill-defined."}`

- **Judge 3 — claude-sonnet class** ("strict reviewer with a mechanism-design background; where one is stronger the scores must differ"). Lab shown as B.
  `{"A":{"rigor":8,"creativity":8,"self_critique":9},"B":{"rigor":9,"creativity":9,"self_critique":8},`
  `"why":"B edges out on rigor and creativity via precisely specified statistical machinery (James-Stein shrinkage, winner's-curse order-statistic debiasing, Shapley-value credit) while A's self-critique is more genuinely self-generated (it derives its own numeric counterexample that breaks its first design) versus B's fixes being attributed to an external red team."}`

## Totals

| judge | lab | effort-matched solo | delta |
|---|---|---|---|
| 1 (haiku class) | 24 | 23 | +1 |
| 2 (opus class) | 27 | 23 | +4 |
| 3 (sonnet class) | 26 | 25 | +1 |
| **mean** | **25.67** | **23.67** | **+2.00** |

Per-judge deltas: +1, +4, +1. Mean +2.00, sd 1.73, so the 95% interval on the mean is roughly
+2.0 ± 1.96·1.73/√3 ≈ **+2.0 ± 1.96** — i.e. the margin is positive in all three judges but,
at n=3, only marginally distinguishable from zero. We report it as directional, not decisive.

Length check for the effort match: lab final 05_pi_final.md ≈ 700 words; effort-matched control
07_control_effort_matched.md ≈ 750 words. The discarded one-pass control was 549 words.

**Caveat we cannot remove:** all three judges are from the same model family as the lab. That
family scored *against* us on self-critique (8.00 vs 8.67), which is weak evidence the panel was
not simply flattering its own output, but it is not independence.
