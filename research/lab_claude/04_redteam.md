**1. LOO-marginal + normalization is a free griefing weapon (kills the whole design).** V is submodular and f_s = V(M) − V(M\M_s). Mirror an honest steward h's top Mind (open tournament ⇒ behavior is observable and distillable). Now h is never the unique argmax on any task, so f_h → 0 — h's payout drops from ~0.5%·P to ~0, i.e. Δ ≈ 1.0, not ≤ 0.02. Worse: the clone scores ≥ τ by construction, so bond B is **refunded**. Attack cost ≈ compute only. The submodularity argument proves clones earn nothing; it never proves clones *cost* nothing to the victim. Falsifier: replay with 5 clones of the top-5 Minds; predicted Δ ≥ 0.9.

**2. "max over own Minds" is a winner's-curse pump.** Both experts aggregate by max of noisy scores. k iid clones of *identical* true quality yield E[max] ≈ μ + σ√(2 ln k). At σ=0.1: k=20 → +0.173, k=100 → +0.303. SGR > 1 by construction; the "target SGR ≤ 1.0" is unreachable at any k > 1. Fix requires shrinkage/empirical-Bayes on q_S with a k-dependent penalty; neither proposal has one.

**3. Fixed 20,000-match budget makes #2 worse and adds a DoS.** 200 stewards → 100 matches/Mind; +200 sybils → 50, so σ rises ×1.41 and the max-pump gain rises with it. Honest collateral L is non-zero even at SGR = 1: the attacker degrades everyone's measurement for free. No metric captures this.

**4. κ = 0.25 is not a cap.** Fair share with 200 stewards is 0.005; κ binds at 50× fair. It constrains nothing, and overflow "rolls to next pool" pays the attacker later.

**5. 3σ collusion flag is noise.** 19,900 ordered pairs × p=0.0027 ⇒ ~54 false positives/tournament. A 5-ring throwing 1 match in 8 stays inside 3σ while lifting combined payout >10% — the pre-registered failure condition is met by the detector's own arithmetic.

**6. The evaluation cannot detect its own errors.** Ground truth q_s = θ⁺_s/Σθ⁺ *assumes* best-Mind aggregation is correct, so D structurally favors max mechanisms (#2 invisible). Holm across 243 cells raises the bar for *rejecting* the mechanism — correction applied in the direction that protects the proposal. Falsifiers must be non-inferiority tests with burden on the mechanism.

**Most damaging flaw:** the payout rule is not sybil-proof but *rival-suppression-proof-less* — an attacker deletes an honest steward's entire payout by cloning them, at refunded-bond (zero) cost, and no proposed metric (Δ, SGR, SPR, D, L, β) measures harm inflicted on a targeted third party.
