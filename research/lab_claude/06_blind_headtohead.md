# Blind head-to-head: multi-Mind lab output vs single-Mind control

Three further independent reviewer instances scored the two answers with the labels removed.
Neither was told which came from the lab and which from the solo run.
**Position control:** the lab's answer was shown as **B** to judge 1 and as **A** to judges 2 and 3.
Axes: rigor / creativity / self_critique, 0–10 each.

| judge | lab shown as | LAB (swarm) | SOLO (control) |
|---|---|---|---|
| 1 | B | rigor 9, creativity 9, self-critique 9 → **27** | rigor 7, creativity 6, self-critique 6 → **19** |
| 2 | A | rigor 9, creativity 9, self-critique 9 → **27** | rigor 7, creativity 6, self-critique 6 → **19** |
| 3 | A | rigor 9, creativity 9, self-critique 9 → **27** | rigor 7, creativity 6, self-critique 6 → **19** |

**Result: 3–0 for the lab. 27.0 vs 19.0 (+42%), identical under both presentation orders (no position bias).**

Verbatim reasons given:

- Judge 1: *"A is clean, implementable, and honestly flags cross-identity sybils, but B is more precise (winner's-curse debiaser with numbers, James-Stein shrinkage, Shapley with anti-suppression floor), invents genuinely non-obvious metrics (TSI worst-case, Suppression Cost Ratio), and pre-registers rejection criteria while naming what it failed to solve."*
- Judge 2: *"A specifies sharper machinery … plus novel suppression/cost metrics and a pre-registered rejection rule, and it openly reports what its own review killed and what remains unsolved, whereas B is a clean, implementable but more conventional decayed-top-k design whose self-critique is largely confined to naming cross-identity sybils."*
- Judge 3: *"A specifies more implementable detail … plus novel adversarial metrics (TSI worst-case, Suppression Cost Ratio) and a frank list of unsolved failures, whereas B is a clean and coherent BT/decay design with a good identity-binding caveat but a weaker sybil-resistance argument (δ-decay and the naive max both ignore winner's-curse inflation) and thinner self-attack."*
