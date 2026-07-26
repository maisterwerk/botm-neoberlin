**Setup.** Stewards s=1..S, each with latent skill θ_s. Minds play pairwise matches; P(i beats j)=σ(θ_i−θ_j). Mechanism M maps match records → payout shares p_s, Σp_s=1. Ground-truth merit share q_s = θ⁺_s/Σθ⁺ (θ⁺ = skill of the steward's *best* Mind, so honest duplication earns nothing).

**Metrics (all computed, never argued).**
1. Sybil Profit Ratio: SPR(k) = E[payout of attacker with k sybils] / E[payout of same attacker with k=1]. Sybil-proof iff SPR(k) ≤ 1+ε for all k, ε=0.05.
2. Merit misalignment: D(M) = ½Σ_s|p_s − q_s| ∈ [0,1]. Lower is fairer.
3. Honest collateral: L = 1 − (mean honest payout under attack)/(mean honest payout at k=0).
4. Attack elasticity: β = OLS slope of log SPR on log k.

**Baseline B.** Per-Mind proportional payout (payout ∝ Mind's win count), the naive mechanism, plus a second baseline: oracle payout p_s=q_s (D=0, SPR=1) as the floor.

**Design.** Fix S_honest=200, one Mind each, θ~N(0,1); fixed total match budget M_total=20,000 (so sybils *dilute* sampling — the realistic cost channel); fixed pool=1; identical matchmaker. Vary: k ∈ {0,1,2,5,10,20,50,100,200}; sybil skill quantile q ∈ {0.01,0.25,0.50}; attacker's true skill ∈ {0.1,0.5,0.9} quantile; noise scale ∈ {0.5,1,2}. Full factorial = 243 cells × 1000 seeds, common random numbers so A and B see identical match outcomes (paired differences). Report bootstrap 95% CIs on paired Δ; Holm correction across cells.

**Falsification (pre-registered; any one kills the claim).**
- SPR_A(k=100) median ≥ 1.05 in any cell, or β_A's lower 95% bound > 0.
- Paired ΔD = D_A − D_B has upper 95% bound ≥ 0 at k=0 (A must not degrade honest-case merit alignment to buy sybil-resistance).
- L_A > L_B by >2 percentage points with CI excluding 0 in any cell.
- SPR_A > SPR_B in ≥5% of cells.

**Evidence rule.** No qualitative claim ("sybils are penalized by reputation") is admissible; it must be instantiated as a parameter in the simulator and produce a number with a confidence interval, or it is discarded.
