# Domain 2 blind head-to-head, and the pooled two-domain result

Protocol fix carried over from domain 1: every judge received the **identical neutral framing**
(domain 1 varied strictness wording per judge, which confounded model with framing — a reviewer
caught it). Labels hidden; presentation order swapped (lab = A for judge 1, B for judges 2 and 3);
three different judge models.

## Domain 2 — contamination-vs-capability protocol

| judge model | lab shown as | LAB rigor/creat/self-crit | total | SOLO rigor/creat/self-crit | total | Δ |
|---|---|---|---|---|---|---|
| haiku class | A | 9 / 8 / 8 | **25** | 8 / 6 / 8 | 22 | +3 |
| sonnet class | B | 9 / 9 / 9 | **27** | 8 / 7 / 8 | 23 | +4 |
| opus class | B | 8 / 9 / 9 | **26** | 8 / 7 / 8 | 23 | +3 |
| **mean** | | **8.67 / 8.67 / 8.67** | **26.00** | **8.00 / 6.67 / 8.00** | **22.67** | **+3.33** |

Δ = **+3.33 ± 1.43** (t, n=3) → 95% CI **[+1.90, +4.77]**, excludes zero. In this domain the lab wins
**all three axes**, and the largest gap is **creativity (+2.00)**.

## Domain 1 recap (mechanism design)

Δ = **+2.00 ± 4.30** (t, n=3) → CI **[−2.30, +6.30]**, does not exclude zero. Lab won rigor (+1.67)
and creativity (+1.00) but **lost self-critique (−0.67)**.

## Pooled across both domains — the claim we actually make

Six blind judges, two unrelated research domains, per-judge deltas **+1, +4, +1, +3, +4, +3**:

**Δ = +2.67 ± 1.43 (t, n=6) → 95% CI [+1.23, +4.10]. Excludes zero.**

Every one of the six comparisons favours the lab. This is the first version of this claim that is
statistically significant rather than directional, and it took a second domain to get there — n=3
in a single domain was simply underpowered, exactly as our reviewers said.

## The nuance we are not going to hide

The **per-axis advantage is not stable across domains**:

| axis | domain 1 (mechanism design) | domain 2 (measurement / causal inference) |
|---|---|---|
| rigor | **+1.67** | +0.67 |
| creativity | +1.00 | **+2.00** |
| self-critique | **−0.67 (solo wins)** | +0.67 |

So "more Minds are better" is true on the **total**, robustly, across two domains — but *which* axis
it buys depends on the problem. In adversarial mechanism design the lab bought rigor and the solo's
self-criticism was better (two judges said the solo's was "more genuinely self-generated"). In a
measurement problem the lab bought creativity, because the red team's attack forced an identification
device the solo never reached — the counterfactual arm where contamination and capability predict
**opposite signs**.

That mechanism is the clearest single artefact of multi-Mind work in this project: the solo control
correctly diagnosed that paraphrase leakage defeats memorisation tests, but still rested its verdict
on a fresh-item transfer ratio whose exchangeability it could not prove. The red team showed the
lab's version of that same design "manufactures the null", and the integrator answered with a
statistic that does not depend on difficulty-equating at all.

## A finding only a multi-Mind setup can produce

The domain-2 red team caught an inconsistency **between two specialists** that neither could see
alone: the statistician required ~1,530 fresh items per cell; the experiment designer commissioned
**300**. A factor of five, invisible to each author, fatal to the protocol. The integrator resolved
it (the two numbers were in different units — responses vs items) and fixed the design at 600 items
× 5 seeds. A single Mind writing one document does not have two independent authors to contradict.
