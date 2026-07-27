# Domain 2, round 1 — EXPERIMENT DESIGNER (verbatim)

**Protocol: Provenance-Matched Perturbation Audit**

**Held fixed.** One third-party container, pinned harness commit; identical prompt template, few-shot exemplars, greedy decoding (T=0, fixed seed), answer parser, and scoring across every arm and model.

**Varies.** (1) *Item provenance*: A = original public items; B = answer-preserving paraphrase; C = entity/numeric substitution; D = option-order permutation; E = **answer-altering** perturbation (gold label changes); F = 300 fresh items commissioned to the benchmark's item-writing spec, authored after all cutoffs, never published. (2) *Model*: new run, its own prior checkpoint, plus ≥4 external reference models with cutoffs straddling the benchmark release.

**Statistic and threshold.** Contamination index Δ = acc(A) − acc(mean of B/C/D), paired by item. Flag contamination if Δ_new − mean(Δ_reference) > 5 points **and** the lower bound of a 95% BCa bootstrap CI (10k item-level resamples) > 0. Corroborate with: (i) arm E error rate matching the *old* gold above chance; (ii) if logprobs exist, Min-K% loss gap between A and difficulty-matched non-benchmark text. Genuine capability predicts Δ_new ≈ Δ_reference and gain replicated on F.

**Third-party requirements.** Black-box API with seed and logprobs, one-shot submission through a proxy — no retries, no provider visibility into B–F before scoring. Publish item hashes and threshold pre-registration before querying.

**Confounds neutralised.** *Cutoff*: F post-dates every model's cutoff; references bracket the release date. *Harness/formatting*: shared container; a format-perturbation arm applied equally to A and F — if the drop appears on both, it is brittleness, not leakage. *Style fine-tuning*: hand-grade 100 random parses to bound parser-leniency gains. *Difficulty drift* between A and F: accept F only if reference-model accuracy on F falls within 2 points of A; otherwise reweight by reference difficulty.

**Falsification.** Sensitivity: inject a known 20% of A into a small model's training; the protocol must flag it. Specificity: run on ≥5 certified-decontaminated models; false-positive rate must be <5%. If either fails, the threshold or the perturbation set is invalid, not the model. Additionally, contamination-driven gains should not transfer — verify on unrelated downstream tasks.
