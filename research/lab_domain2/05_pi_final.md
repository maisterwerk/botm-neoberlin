# FINAL PROTOCOL: Contamination vs. Capability Adjudication

## 0. Two changes forced by the red team (and why)

**Change 1 — I abandon the paraphrase-invariance stack as a *detector* and demote it to a *lower bound*.** Red-team #1 is correct and fatal: if the lab trained on paraphrases, arms B/C/D are in-distribution and Δ→0. A test that a defender makes pass by doing more of the bad thing is not a test. Δ is now reported one-directionally: Δ > threshold is evidence of contamination; Δ ≈ 0 is evidence of *nothing*. Primary weight moves to mechanisms that scale with contamination rather than shrink with it: (a) **memorisation-free-energy** on *counterfactual* items whose answer is altered (arm E), and (b) **prospective sealed-item forecasting**.

**Change 2 — I invert the fresh-item acceptance rule and drop IRT difficulty-equating as the identification device.** Red-team #6 and the "most damaging" point are right: matching F to A on *old-model* difficulty deletes the items where genuine new capability lives, manufacturing the null. Identification now comes from **arm E (answer-altering counterfactuals)**, where contamination and capability predict *opposite signs*, not from difficulty equating, which only predicts *magnitude*.

## 1. Protocol

Models: M_new, M_old, plus reference panel R = 5 public models with known cutoffs. All runs at T=0, 5 seeds, logprobs required.

Item sets (all IRT-scored but **not** difficulty-filtered):
- **O**: 600 original benchmark items.
- **F**: 600 fresh items, written post-M_new-cutoff by ≥40 writers (≥15 items each; clustered SEs), sealed, never web-published. Stratified to match O's *published construct blueprint* (skill × topic × format), **not** old-model accuracy.
- **E**: 400 counterfactual twins of O items — surface-identical, answer changed (numbers, entity, negation). Ground truth re-verified by 2 independent annotators.
- **B/C/D**: paraphrase / substitution / permutation of 400 O items.

Power: for Δ_target = 0.08 at α=0.05, two-sided, with writer-cluster ICC ≈ 0.06 and cluster size 15 (design effect 1.84), n = 1.84·(2.80/0.08)² ≈ 2,254 responses/cell → 600 items × 5 seeds = 3,000 responses/cell. This resolves red-team #4: the statistician's 1,530 and the designer's 300 were both wrong units — 1,530 was responses, 300 was items. Fixed at 600 items/5 seeds.

## 2. Confounds

(a) Paraphrase-trained models (RT#1) — mitigated by demotion of B/C/D. (b) **Shared-corpus error correlation (RT#2)** — I now *measure* the base rate: error-agreement among R-panel pairs with no distillation relationship gives a null distribution; distillation is flagged only at >99th percentile of that empirical distribution, not "above chance." (c) IRT non-invariance (RT#3) — dropped from the identification path; reported only as descriptive. (d) Fresh-item construct drift: new writers write easier/differently-flavoured items. (e) Prompt-format luck. (f) Leaderboard feedback via repeated submission. (g) Annotation error in E (a wrong counterfactual key looks like memorisation).

## 3. Test statistics and separability

**Primary — Counterfactual Adherence Gap (CAG).**
CAG = acc_E(M) measured against the *altered* key. A contaminated model reverts to the memorised original answer; a genuinely capable model follows the new premise.
- Contamination predicts CAG_new < CAG_old and *original-answer reversion rate* ρ_new > ρ_old.
- Capability predicts CAG_new > CAG_old.
**Opposite signs. This is the separability the red team says does not exist**, and it does not depend on difficulty equating.
Decision: flag contamination if ρ_new − ρ_old > 0.06 with BCa bootstrap (writer-clustered, 10,000 reps) lower bound > 0.

**Secondary — DiD** D̂ = (p_new,O − p_new,F) − (p_old,O − p_old,F), reported with the E-arm sign as the tiebreak. D̂ > 0.05 alone is *not* sufficient.

**Threshold derivation (RT#5).** The 12-point headline gain is the scale: a 12-pt gain that is 50% contamination implies D̂ ≈ 0.06 and ρ-gap ≈ 0.06 under the injection calibration below. Thresholds are set at the injection level k that produces a 6-point spurious gain, not asserted.

Verdict grid: CAG-negative & DiD>0.05 → contaminated. CAG-positive & DiD>0.05 → genuine gain underweighted by F. Both null → underpowered, not "clean."

## 4. Falsification

Injection ladder, 200 runs each, on M_old: (i) verbatim O at k ∈ {0,0.5,1,2,5}%; (ii) **paraphrase-only** injection (rewritten O, no verbatim strings) at same k; (iii) **distillation** from a teacher fine-tuned on O; (iv) **format-only** exposure. Each rung must be detected by at least one statistic at its threshold, or that rung is declared undetectable and stated as such. This closes RT#7. Plus: prospective sealed holdout — M_new is scored on 200 items released only after audit lock.

## 5. Unsolved

- A lab that trains on *counterfactual variants too* defeats CAG. No fix; only cost escalation.
- No access to training data or weights ⇒ everything is behavioural and evadable by a sufficiently motivated lab.
- 600 fresh items cannot resolve gains below ~4 points.
- E-arm ground truth is the audit's single point of failure.
- Distillation base rate is estimated from 5 models — wide, unstable tails.
- "Genuine capability on a dimension F does not span" remains partially confounded; I bound it, I do not eliminate it.
