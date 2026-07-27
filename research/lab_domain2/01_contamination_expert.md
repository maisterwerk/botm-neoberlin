# Domain 2, round 1 — CONTAMINATION / EVALUATION-INTEGRITY EXPERT (verbatim)

**1. Verbatim memorisation.** Exact test strings in training data. Signature: near-zero perplexity on test items vs. matched-difficulty held-out items; successful *completion* of a canary — feed the first half of a test question, measure whether the model emits the second half, and whether it emits the gold answer *label* before the question is fully specified. Also: correct answers to items whose stem has been corrupted into nonsense (memorised label, not reasoning). Hardest to hide against black-box probing; trivially hidden from data audits by deleting the offending shard after training. Statistic: length-normalised logprob gap Δ = mean logprob(test) − mean logprob(matched-fresh). Threshold: Δ > 0.35 nats/token, or per-item bootstrap CI excluding zero on >5% of items, ⇒ memorisation.

**2. Paraphrase / translation leakage.** Test items rewritten, back-translated, or regenerated at semantic parity. Signature: gain collapses under semantics-preserving perturbation. The item is not memorised as a string, so §1 probes fail — but accuracy on a hand-rewritten parallel set drops sharply while a genuine model holds. This is the cheapest mechanism to hide and the most common.

**3. Ordering / format sensitivity.** Signature: shuffling MCQ answer options, renaming labels A–D → W–Z, or converting to free-form response destroys the gain. Genuine capability is roughly format-invariant; a model keyed to memorised option positions is not. Very easy to detect, easy to conceal by training on shuffled variants.

**4. Web-crawl overlap.** Passive ingestion of leaderboard mirrors, GitHub copies, dataset dumps, blog write-ups. Signature: contamination correlates with an item's *public age* and mirror count — old, widely-copied items outperform recent ones. Plausibly deniable; genuinely hard to fully prevent, which is exactly why it is the preferred alibi.

**5. Distillation from a contaminated teacher.** Synthetic data from a leaked model. Signature: the student inherits the teacher's *idiosyncratic wrong answers* — error-pattern agreement on mislabelled gold items far above chance. Very hard to hide: shared errors are a fingerprint no filtering removes.

**6. Indirect leakage via leaderboard feedback.** Repeated submissions used as gradient. Signature: gain concentrated on the submitted split only; no transfer to a fresh split of identical construction. Detectable only with a truly private split.

**Adversarial note:** a motivated lab defeats 1, 3, 4 cheaply. Mechanisms 2, 5, 6 are the load-bearing tests.
