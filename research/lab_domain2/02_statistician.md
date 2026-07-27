# Domain 2, round 1 — STATISTICIAN (verbatim)

**H0 (primary):** contamination effect Δ = 0 — the 12-point gain is homogeneous across leaked-eligible and leak-impossible items. H1: Δ > 0.

**Design.** Four cells: {model M_new, model M_old} × {O = original public items, F = fresh items authored after M_new's cutoff, difficulty-equated to O via 2PL IRT anchoring on a third reference-model panel, writers blind to condition}.

**Statistic 1 — difference-in-differences.**
D̂ = (p̂_new,O − p̂_new,F) − (p̂_old,O − p̂_old,F).
Var(D̂) = Σ_cells p(1−p)/n, cluster-robust by item-writer. Z = D̂/SE(D̂).

**Power.** At p≈0.5, Var(D̂) ≈ 1/n per cell, SE = n^(−1/2). For α = 0.05 (two-sided), 80% power, (1.96+0.84)=2.80:
n ≥ (2.80/Δ)². Δ = 0.10 → **n = 784 items/cell (≈3,200 total)**; Δ = 0.05 → n = 3,136/cell; Δ = 0.15 → n = 349/cell. Writer clustering with ICC 0.05 and 20 items/writer inflates by design effect 1.95 → budget **~1,530 items/cell for Δ = 0.10**.

**Statistic 2 — exchangeability (permutation, exact).** Under no contamination, log-likelihood is exchangeable over item order: S = Σ log P(x_i | canonical order). Shuffle R = 10,000 times; p = (1 + #{S_perm ≥ S})/(1 + R). Finite-sample valid, no distributional assumption.

**Statistic 3 — verbatim completion.** Exact-match rate on second-half completion given first half, vs. matched-length control corpus; two-proportion binomial.

**Decision.** Pre-registered: reject H0 iff Holm-adjusted p < 0.05 across the three tests, with DiD primary. Declare contamination iff D̂ > 0.05 **and** its 95% CI excludes 0 — effect-size floor prevents significance-without-magnitude.

**Confounds.** Difficulty drift O vs. F (IRT equating, not eyeballing); topical drift making F out-of-distribution; legitimate training on near-duplicate-but-not-identical data — DiD cannot separate this from leakage and this is the protocol's hard limit; checkpoint cherry-picking; prompt-format sensitivity.

**Falsification.** Inject known leakage: fine-tune M_old on k ∈ {0, 1, 2, 5, 10}% of O, run the protocol 200× per k. The protocol is rejected if (a) empirical false-positive rate at k = 0 exceeds 0.05 (CI upper bound), or (b) detection rate at k = 5% falls below the nominal 0.80. Publish the calibration curve; no qualitative claim substitutes for it.
