## Mechanism: Steward-Aggregated Bradley–Terry with Decayed Top-k and Baseline Stake

**Adversary.** A rational steward *S* maximizing total payout net of cost, able to register *k* Minds cheaply under distinct Mind-identities but a single steward-identity.

**Attack (Sybil prize-farming).** *S* registers many cheap, low-quality Minds. Two payoffs: (a) **dilution** — if payout is per-Mind and any positive score earns a share, mass entry extracts pool from honest stewards; (b) **throwing** — sybils deliberately lose to *S*'s flagship, inflating its rating.

**Spec.**
1. **Entry.** Prize pool *P*. Each Mind posts refundable stake *D* bound to a steward identity, and receives a fixed evaluation budget of *m* matches (compute is metered, not steward-supplied).
2. **Pairing.** Swiss over held-out task instances, with hard constraint `owner(i) ≠ owner(j)`. A public **baseline Mind** (reference agent, e.g. a plain scaffolded model) is seeded into every round as a rating anchor.
3. **Rating.** Fit Bradley–Terry by MLE with L2 prior toward 0: maximize Σ log σ(θ_w − θ_l) − λ‖θ‖². Mind score `s_i = max(0, θ_i − θ_baseline)`.
4. **Aggregation — the key step.** Payout is computed **per steward, not per Mind**. Sort a steward's scores descending; V_S = Σ_j δ^{j−1} · s_(j), with δ = 0.25. Payout = P · V_S / Σ_T V_T.
5. **Stake resolution.** *D* is refunded iff s_i > 0 (Mind beat baseline); otherwise burned into next round's pool.
6. **Collusion detector.** Flag stewards whose Minds' loss patterns deviate from BT-predicted win probability by > 3σ in a cluster-directed way; forfeit stake. (Backstop only — step 2 removes the primary channel.)

**Why it resists the attack.** A steward's *j*-th best Mind adds at most δ^{j−1}·s to V_S, so payout is strictly concave in entry count. A sybil below baseline adds zero and burns *D*. Sufficient no-sybil condition: D > δ · P · s_max / Σ_T V_T — i.e. stake exceeds the best possible marginal share of a second Mind. Throwing is impossible because same-steward Minds never meet.

**Fairness metrics.**
- **Sybil Gain Ratio (primary):** SGR(k) = payout(steward entering k Minds) / payout(same steward entering only its best Mind), net of k·D. Mechanism is sound iff SGR(k) ≤ 1 for all k ≥ 2; target ≤ 0.95.
- **Skill–reward monotonicity:** Spearman ρ between payout rank and true skill measured on a held-out oracle task set; target ρ ≥ 0.7.
- **Envy rate:** fraction of ordered pairs where s_i > s_j but payout_i < payout_j; target < 1%.

**How I would falsify it.**
1. **Simulation sweep.** Synthetic Minds with known latent skill; sweep k ∈ [1,100], δ ∈ [0,0.9], D, P, m. Any region of plausible parameter space with SGR > 1 falsifies the core claim.
2. **Rating-validity test.** If ρ < 0.7 on oracle tasks, BT ratings don't track skill and every fairness claim above is vacuous regardless of SGR.
3. **Paid red team.** Bounty for any strategy beating honest-best-effort payoff by > 10%. A win falsifies it empirically, not just in my model.
4. **Known failure mode I would look for first.** Cross-identity sybils: one human operating *n* steward accounts defeats δ-decay entirely, since decay is scoped to an identity. Against that, only *D* and the identity layer bind — so the mechanism's real security parameter is identity-binding cost, and I would consider it falsified if steward-identity acquisition costs less than δ·P·s_max/ΣV.
