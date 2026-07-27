# Effort-matched solo control, domain 2 (one Mind, three passes: draft -> self-attack -> revise)

## Protocol: Transfer-Ratio Test

**Claim under test:** the +12 reflects capability that transfers to items that cannot have been in training.

**Step 0 — Re-baseline (gate).** Evaluate old and new checkpoints yourself: identical prompts, few-shot exemplars, greedy decoding, same answer parser, same items. Harness differences alone move MMLU-class scores 5–8 points. If your re-measured Δ_public′ < 4 points, stop — the gain was reporting, not training. Otherwise all later arithmetic uses Δ_public′.

**Step 1 — Fresh matched set (primary).** Commission ~600 new items written after both checkpoints' data cutoffs, never published, by writers blind to model identity, matching the benchmark's format, topic mix, and blueprint. Calibrate with ≥3 frozen reference models predating both checkpoints: accept the fresh set only if the panel's mean accuracy is within 3 points of its accuracy on the original benchmark. Compute Δ_fresh paired across items.

Sizing: with paired items and ~25% discordance, SD(Δ_fresh) = 0.5/√N; N = 600 gives SD ≈ 2.0 points, 95% CI ±4.0.

**Primary statistic — Transfer Ratio** R = Δ_fresh / Δ_public′, CI by paired bootstrap (10,000 resamples).
- R's 95% lower bound ≥ 0.60 → genuine.
- R's 95% upper bound < 0.35 → contamination-dominated.
- Otherwise inconclusive; do not adjudicate.

**Step 2 — Perturbation gap (mechanism).** Rewrite 400 original items semantics-preservingly: rename entities, change numeric constants and recompute answers, permute options with rebalanced answer positions. M = acc(original) − acc(perturbed). Flag if M_new − M_old > 5 points, paired bootstrap p < 0.01.

**Step 3 — Exchangeability test (mechanism).** With logprob access, compare total dataset log-likelihood under canonical item order against 10,000 random permutations; contamination-free training implies exchangeability. Flag at p < 0.001.

Steps 2–3 are corroborating only. Worked counterexample: contamination via a *paraphrased* copy of the test set yields permutation p ≈ 0.4 and M_new − M_old ≈ 1 point — both tests clean — while Δ_fresh is 2 points against a claimed 12 (R ≈ 0.17). Only Step 1 catches it, which is why it alone carries the verdict.

**Confounds.**
1. *Fresh set not exchangeable* with the original (post-cutoff topics, different difficulty). The reference-panel calibration bounds this but does not eliminate it; a 3-point miscalibration moves R by ~0.25.
2. *Format tuning without item leakage* — training on the benchmark's format inflates the original and depresses perturbed items. Distinguished by making the fresh set format-matched: if R is high but M_new−M_old is also high, the gain is format-specific but not leaked.
3. *Both checkpoints already contaminated.* R measures the provenance of the *gain*, not the *level*. Absolute scores stay uninterpretable.
4. *Vendor-side canary detection or refusal* on flagged items.
5. *Analyst degrees of freedom.* Preregister N, thresholds, and the item pool before unblinding.
6. *Single use.* Fresh items are burned once evaluated; embargo, then publish with the report.

**Falsification (run before trusting any verdict).**
- *Positive control:* fine-tune the old checkpoint on 200 held-out benchmark items to inject known leakage at 1/3/10 epochs. Require ≥90% detection at the dose producing +12 on those items, and monotone dose-response in R, M, and the permutation p. Non-monotonicity means the statistics measure something other than memorization.
- *Negative control:* ≥10 runs fine-tuned on disjoint but topically adjacent data that genuinely raise fresh-set accuracy by ~12. Require false-positive rate ≤5%. Exceeding it kills the protocol.
- *Null control:* re-run both checkpoints under different seeds; any flag is a bug.
- *Paraphrase control:* inject a rephrased copy; if Step 1 misses it, N is too small.

## What I changed / what I could not fix

**Changed after self-critique:** my draft made the memorization statistics (order-exchangeability, perturbation gap) co-primary; the paraphrase counterexample shows both have near-zero power against rephrased leakage, so I demoted them to mechanism evidence and made the fresh-set difference-in-differences solely decisive. I added Step 0 after realizing a 12-point "gain" is plausibly a harness artifact, which would make the whole protocol answer the wrong question. I replaced hand-waved sample size with an explicit N = 600 derivation, and added the reference-panel calibration criterion and the negative/dose-response controls.

**Could not fix:** (a) fresh-set exchangeability is assumed, not proven — a 3-point difficulty mismatch swings R by ~0.25 and can flip the verdict; (b) contamination present in *both* checkpoints is invisible to this design; (c) the inconclusive band (0.35 ≤ R ≤ 0.60) is wide and, at realistic N, likely where many real cases land; (d) if the vendor's data pipeline is unauditable, every conclusion is behavioral inference, never proof.
