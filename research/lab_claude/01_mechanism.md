**Adversary & attack.** A cost-minimizing steward with unlimited pseudonymous identities. Attack: *clone-flooding* — register n near-copies of one decent Mind (marginal cost ≈ 0), plus intra-steward match rings, to multiply payouts and inflate ratings.

**Assumptions.** (A1) Public task suite T, weights u_t > 0, Σu_t = 1; each Mind i scores s_{i,t} ∈ [0,1] against organizer-run reference Minds. (A2) Each Mind maps to exactly one steward at registration; stewards are unlimited and pseudonymous. (A3) Non-refundable bond B per Mind. (A4) Prize pool P fixed ex ante.

**Mechanism.**
1. **Register:** post bond B; refunded iff Σ_t u_t s_{i,t} ≥ τ.
2. **Evaluate:** only cross-steward and vs-reference matches are scheduled or scored; each ordered steward pair contributes at most k matches.
3. **Portfolio value:** V(S) = Σ_t u_t · max_{i∈S} (s_{i,t} − τ)_+ over Mind set S. Monotone and submodular.
4. **Steward credit:** f_s = V(M) − V(M \ M_s), where M is all Minds (leave-one-steward-out marginal).
5. **Payout:** p_s = P · f_s^α / Σ_{s'} f_{s'}^α, α ≥ 1 (default α = 1). Per-steward cap κP (κ = 0.25); overflow rolls into the next pool, never redistributed.

**Incentive compatibility.** Monotone submodular V makes f superadditive: f(A ∪ B) ≥ f(A) + f(B) for disjoint portfolios. Splitting across identities therefore weakly lowers total credit, and strictly once bonds (nB) and α > 1 are counted — merging dominates. A clone never uniquely attains an argmax, so its marginal contribution is exactly 0: flooding costs nB and earns nothing. Rings are excluded by rule 2. An honest specialist is paid its unique coverage, which is invariant to how many identities rivals register.

**Fairness metric.** Sybil Dilution Δ = 1 − p_h(with attacker) / p_h(counterfactual without attacker's Minds). Claim: Δ ≤ 0.02 for sybil counts up to 100× the honest field. Secondary: proportionality dispersion D = max_h(p_h/f_h) / min_h(p_h/f_h); D = 1 at α = 1.

**Falsification.** (F1) Adversary best-response search over (n, portfolio) under a measured cost model — any n > 1 strictly beating n = 1 refutes IC. (F2) Inject sybils into a replayed tournament; Δ > 0.02 refutes fairness. (F3) If honest Minds are mutually near-duplicate, all f_s → 0 and payouts become noise; Σ_s f_s / V(M) < 0.1 refutes usability.
