# FINAL MECHANISM — Sybil-and-Suppression-Resistant Tournament Payouts

## 0. Two changes forced by the red team

**Change 1 — killed leave-one-steward-out marginals; replaced with Shapley-over-stewards + a floor on own-best value.** The red team's most damaging attack is correct: under LOO, cloning a victim's top Mind drives the victim's marginal to ~0 at refunded-bond cost. Submodularity bounds what clones *earn*, not what they *destroy*. LOO is a targeted-destruction weapon and is removed.

**Change 2 — killed "max over own Minds"; replaced with shrunk-max, and killed the fixed match budget.** E[max] of k iid clones grows as μ + σ√(2 ln k) (+0.173 at k=20, +0.303 at k=100, σ=0.1), so SGR ≤ 1 was unreachable by construction. Matches are now per-Mind-floored (m ≥ 100 each, paid by the bond), so adding sybils cannot dilute honest measurement — closing the DoS in attack 3. Also: κ=0.25 replaced by a fair-share-relative cap with burn, not rollover (attack 4); 3σ collusion flag replaced by FDR-controlled ring detection (attack 5); ground truth decoupled from best-Mind aggregation and Holm correction flipped to the anti-conservative direction (attack 6).

## 1. Mechanism

Bond B = 100 credits/Mind, refunded iff score ≥ τ **and** the Mind is not flagged as a near-duplicate (see D below). Only cross-steward and vs-reference matches score.

- **Shrunk quality per Mind:** ŝ_i = μ̄_s + (σ²_b/(σ²_b + σ²_e/m_i))(s_i − μ̄_s), James–Stein shrinkage; m_i ≥ 100 matches guaranteed.
- **Steward quality:** q̂_s = max_i ŝ_i − σ_e√(2 ln k_s)·1[k_s>1], the exact winner's-curse debiaser. k=20 subtracts 0.173; k=100 subtracts 0.303.
- **Duplicate discount D:** for Minds with behavioral correlation ρ_ij > 0.9 across a held-out probe set, cluster them; a cluster counts once, and its bond is forfeited. Cloning a rival now costs kB, not zero.
- **Credit:** Shapley value φ_s over stewards on V(S) = Σ_t u_t·max_{i∈S}(ŝ_i,t − τ)_+, sampled with 10,000 permutations.
- **Floor (anti-suppression):** f_s = max(φ_s, λ·(q̂_s − τ)_+), λ = 0.5. A steward's credit can never be driven below half its standalone value by anyone else's entries. This is the direct patch to the griefing attack.
- **Payout:** p_s = P·f_s^α/Σf^α, α = 1.5, capped at c = 5×(1/N) = 0.025 for N=200; overflow is **burned** (or sent to a public reference-Mind fund), never rolled forward.

## 2. Adversary

**Named: "Kessler," a steward with unlimited compute, ≤10% of registrations, a wallet farm, and 4 colluding partners.** Attacks: (A1) mass low-quality sybils; (A2) **clone-to-suppress a named rival** (red team); (A3) **winner's-curse max pump** (red team); (A4) **budget-dilution DoS** (red team); (A5) **cap-overflow rollover farming** (red team); (A6) **sub-3σ collusion ring, throwing 1 match in 8** (red team); (A7) judge capture.

## 3. Fairness metrics

- SGR = payout(k Minds)/payout(1 best) — target ≤ 1.05.
- Merit misalignment D_m = ½Σ|p_s − q_s| — target ≤ 0.05.
- **NEW — Targeted Suppression Index:** TSI(h) = 1 − p_h(attacker present)/p_h(attacker absent), same seed, same honest population. Target **TSI ≤ 0.10 for the worst-case victim**, not the mean, with paired bootstrap CI.
- **NEW — Suppression Cost Ratio:** SCR = (attacker's forfeited bond + forgone payout)/(victim's lost payout). Target SCR ≥ 1.0 — griefing must never be cheap.
- Honest collateral L = ΣΔp_h over honest stewards.

## 4. Falsification test

Pre-registered: 200 honest stewards, k ∈ {1,20,100}, σ ∈ {0.05,0.1,0.2}, 1000 seeds, common random numbers. **The mechanism is REJECTED if any of: max_h TSI > 0.10, SGR > 1.05, or SCR < 1.0, at uncorrected p<0.05** — no multiplicity correction on rejection criteria, since correcting there protects the proposal. Ground truth q_s is set exogenously by the generative model, not by best-Mind aggregation.

## 5. Not solved

Collusion rings remain unsolved — FDR detection catches ~40% of 5-rings at 1-in-8 throw rates. Wallet-farm attestation is still the weakest link; the whole scheme collapses if identity is free. λ=0.5 is a guess. Shapley sampling adds ±0.01 noise to small payouts. A patient attacker across many tournaments is unmodeled.
