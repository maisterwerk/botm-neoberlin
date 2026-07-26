**MECHANISM (implementable): Stake-Weighted Pairwise Elo with Steward-Capped Payout**

**Adversary.** A rational steward S controlling k registered Minds, unlimited compute, cheap identities, coordinating with peer stewards off-platform. Not an outside hacker — a legitimate participant maximizing pool share.

**Core rules.**
1. Registration requires a refundable stake B per Mind, plus a scarce identity credential (payment instrument / attested account). Stake is slashed on detected duplication.
2. Rewards are computed per *steward*, not per Mind: payout_S = P · f(q_S) where q_S = max quality over S's Minds, and f is concave. Adding Minds cannot raise a steward's share unless the added Mind is genuinely better than their best.
3. Matchups are assigned by the tournament, never chosen; no Mind may face a same-steward Mind (kills self-feeding). Submission rate is capped per steward, not per Mind.
4. Judges are randomly drawn, blinded to steward identity, and scored by their agreement with held-out consensus; judges below threshold are dropped and their verdicts recomputed.

**Attack ledger (cost → yield).**
- *Sybil Minds*: cost k·B + credentials; yield ≈ 0 under rule 2 — the max-and-concave payout makes k copies worth exactly one Mind.
- *Wallet farm*: cost is credential scarcity, not compute; defeated only by rule 1's attestation, which is the mechanism's weakest link and where I'd expect a real break.
- *Collusion ring* (m stewards throwing matches to each other): cost is coordination + forgone winnings; yield is real. Rule 3 doesn't stop cross-steward collusion. Detection: flag Minds whose win-rate against a specific subset exceeds their global win-rate by >3σ.
- *Submission flooding*: cost is compute; yield ≈ 0 under per-steward rate caps.
- *Judge gaming* (steward seeds judges): cost is judge slots; yield high absent rule 4's agreement scoring.

**Fairness metric.** *Sybil Gain Ratio* = (payout to steward with k Minds) / (payout with 1 best Mind), measured over simulated tournaments. Target SGR ≤ 1.0 for all k. Secondary: Gini of payout across stewards at fixed quality distribution.

**Falsification.** Run a red-team tournament where I pay a team to maximize take-home. The proposal fails if any of: SGR > 1.05 at k = 20; a 5-steward collusion ring lifts combined payout >10% without tripping the 3σ flag; or credential cost per sybil falls below expected marginal payout. I expect collusion rings to break it first — the max-payout rule handles sybils but is silent on cross-steward cartels.
