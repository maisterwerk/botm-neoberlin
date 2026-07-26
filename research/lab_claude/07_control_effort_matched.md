# Effort-matched solo control (one Mind, three internal passes: draft -> self-attack -> revise)

Run because our own pre-flight reviewers said the first control (one pass, 549 words) was not a fair
baseline against a 9-run lab. This control gets the same question, a generous budget, and an explicit
instruction to red-team itself. It is one Mind. Verbatim output:

---

## Adversary and attack

**The Farmer**: a rational steward with capital B who maximizes expected take from prize pool P, can register n Minds under distinct identities, and can cheaply produce perturbed variants of one base Mind (temperature/prompt jitter, paraphrase wrappers, distilled students). Ownership is self-declared and unverifiable.

Attacks: **(A1) split-and-farm** — one good Mind entered k times to multiply tail/participation payouts; **(A2) decorrelated farming** — copies deliberately randomize their *errors* to defeat similarity detection; **(A3) grief-crowding** — mimic a rival's behavioral signature to dilute them; **(A4) match-throwing** to boost a flagship.

## Mechanism (RCSD)

**0. Entry bond.** Each Mind posts b, refunded iff final quality q_m >= tau (tau = prior tournament's median). Forfeits go to P. Set b >= expected payout of a tau-level Mind (e.g. P=$100k, b=$250).

**1. Scoring against a fixed ladder, not peers.** Every Mind answers a fresh held-out probe set of K=200 graded items under identical seeds, plus a calibration ladder of frozen reference opponents. q_m derives from the ladder, never from head-to-head results against other entrants — this kills A4, since throwing transfers no value.

**2. Residualization.** Fit a 2-parameter IRT model (item difficulty d_k, Mind ability a_m) to the score matrix; let r_{m,k} be residuals. Additionally project out the residual directions of a set of *reference base models*, so shared foundation models don't register as collusion. Similarity S_mm' = max(0, corr(r_m, r_m')).

**3. Top-heavy core (80% of P).** Rank by q; pay ranks 1-10 with geometric weights ~ 2^-i. Nothing below rank 10.

**4. Neighborhood collapse at the top.** For each paid Mind, form soft neighborhood N(m) = {m' : S_mm' >= 0.6}. A neighborhood receives the prize of its *best* member only, split internally ~ f(q) = (q-tau)^2_+. For k identical copies this yields exactly f/k each — total unchanged (sybil-neutral). Caps are applied at neighborhood level, never per-Mind; a per-Mind cap would itself reward splitting.

**5. Diversity dividend (20%).** Paid at neighborhood level, split by the same rule — sybil-neutral by construction, but keeps honest mid-tier stewards solvent.

## Fairness metrics

**Sybil Gain Ratio** SGR(k) = E[total payout to a steward splitting one Mind into k] / E[payout at k=1], net of bonds. Target: SGR(k) < 1, strictly decreasing in k.
**Grief cost ratio**: sybils needed to halve an honest top Mind's payout x b, divided by that payout. Target > 1. Under step 4 a q ~ tau mimic steals ~ f_mimic/f_victim; with q_victim=0.85, q_mimic=0.55, tau=0.5: 0.0025/0.1225 ~ 2% each, so ~50 bonded griefers to halve.
**Honest displacement**: Spearman rho between q and payout among honest Minds before/after injecting n sybils; target delta-rho < 0.02 at n = |M|.

## Falsification

Run a shadow tournament with pre-registered planted sybil families at k in {2,4,8,16,32} across four perturbation levels (jitter, wrapper, distillation, independent-same-recipe). The mechanism is **falsified** if (i) SGR(k) > 1 at any k; (ii) the ROC-AUC of S for separating known-copy from known-independent pairs falls below 0.90 at K=200 — the entire premise dies here; (iii) grief cost ratio < 1; (iv) honest displacement exceeds target. Add an open red-team bounty paying more than the exploit's expected yield.

## What I changed, and what I could not fix

My first draft paid P proportionally to a similarity-discounted score. I killed it with my own counterexample: **A2**. Base Mind q=0.8, tau=0.5, f=(q-tau)^2=0.09. Randomizing 20% of answers decorrelates the copies (S -> 0) at cost q -> 0.68, f=0.032; eight copies yield 0.26 vs 0.09, so SGR(8) ~ 2.9. Similarity discounting alone is *not* sybil-proof. Fix: top-heaviness (step 3) is the primary defense — degraded copies land near rank 200 and earn zero; similarity collapse now only guards near-copies *at the top*. I also switched asymmetric (rank-priority) crowding to symmetric-with-best-member-value, because asymmetric crowding gives k copies f*H_k ~ f*ln k > f.

Unfixed: (1) an adversary with k *genuinely* strong, genuinely diverse Minds is indistinguishable from k honest stewards, and should arguably be paid — but this makes concentration unbounded; (2) base-model projection is imperfect, so honest wrapper-Minds on one popular model may be over-collapsed; (3) top-heaviness trades sybil-resistance against mid-tier fairness, and I have no principled setting for that exchange rate; (4) b excludes poor stewards, which is a fairness cost I mitigate (refunds) but do not eliminate.
