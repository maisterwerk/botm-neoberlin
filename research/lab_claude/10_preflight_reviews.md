# Round 6 raw — the five adversarial reviewers who attacked this write-up (not the mechanism)

Two batches of five context-isolated reviewers scored the draft submission on the event rubric and
were told to find what was wrong before it was submitted. They had read access to the code and the
repo. Their scores gated submission: our rule is that we do not spend a tournament attempt until
the panel average clears the bar.

## Batch 1 — on draft v2 (mean 24.2/30: 26, 22, 25, 24, 24)

Findings we acted on:

1. **"Load-bearing error in A2."** *"pay_v1() aggregates sqrt(SUM over a steward's Minds), so
   SGR(k=20) = sqrt(20) = 4.472 — pure sum-aggregation, and the column label 'V1(max/sum)' hides
   this. I reran the identical design with max aggregation: SGR = 1.037 … The two central narrative
   claims of the submission rest on a number produced by a different failure mode."*
   → Fixed in `reward_sim3.py` by ablating every component separately. The write-up now retracts
   the 4.379 attribution explicitly.
2. **"The debiaser is dead code."** *"In pay_v2 the duplicate detector runs first, so 19 of the 20
   clones are dropped and k_s=1 — the debias term is never applied."* → Fixed by ablation
   (debias-only / dedup-only / full).
3. **"The duplicate detector is separable by construction."** *"clone_of() copies fp exactly …
   detection is perfect by construction, which is why FP=0.03/200, TSI=-0.001 and SCR=89 all look
   so clean. A real sybil steward perturbs behaviour and walks through it."* → Fixed by the
   evasive-clone sweep, which shows exactly that.
4. **"SCR = 89.35 is a numerical artifact."** *"Trials with zero victim loss return inf and are
   filtered out of the mean."* → The metric was withdrawn from the submission.
5. **"The head-to-head does not control effort budget."** *"Nine runs and ~2.5k words of lab text
   vs one 549-word single pass … the three judges are also not three data points: all nine score
   cells are identical."* → Fixed with the effort-matched control and a model-diverse panel;
   the old panel is retained in `06_blind_headtohead.md` rather than deleted.
6. **"§7 Reproduce is broken as submitted."** *"reward_sim2.py, lab_run.py and lab_claude/ are all
   UNTRACKED in the repo."* → Pushed; a cold clone now reproduces byte-for-byte.

## Batch 2 — on draft v3 (mean 25.0/30: 26, 22, 26, 26, 25)

The decisive finding, and the reason `reward_sim4.py` exists:

> *"§3/§4 credit protection to 'Shapley value + anti-suppression floor'. I instrumented it: mean
> phi = 0.0398 vs mean lambda*standalone = 2.025, and the floor binds for 200/200 stewards in every
> trial — so f_s = 0.5*standalone ALWAYS, the 100-perm Shapley is computed and then discarded, and
> V2 degenerates to payout ∝ (own standalone)^1.5. TSI≈0 is then a tautology: the rule literally
> cannot depend on rivals … And the 'TSI V2 no-floor' column that supposedly isolates Shapley is a
> CAP artifact — the A3 victim is by construction the top steward and sits pinned at the 5x-fair-share
> cap both before and after the attack. Neither column measures suppression resistance."*

Also from batch 2, all acted on in `reward_sim4.py` or in the text:

- *"The James-Stein shrinkage that headlines §3 appears nowhere in reward_sim3.py"* → now implemented.
- *"F1–F4 are NOT what the methodologist pre-registered … TSI did not exist at pre-registration time
  — it was invented in round 3 — so F3 is retro-fitted."* → conceded in the submission; we no longer
  call them pre-registered without qualification.
- *"Your own published control refutes §2's headline 'A single Mind does not do this to itself.'
  07_control_effort_matched.md independently names '(A3) grief-crowding' AND defines a 'Grief cost
  ratio' … So the solo found the rival-suppression class AND the third-party-harm metric AND
  falsified itself."* → conceded in the submission; the claim was narrowed.
- *"'diluted' and 'floored' produce identical numbers to two decimals … the floor buys exactly
  nothing."* → re-tested with a match budget tight enough to bite. It still buys nothing; the claim
  is now withdrawn rather than asserted.
- *"0% is partly an artifact of a non-adaptive defender … detect_duplicates() already computes fps
  and main() never prints it."* → the arms-race table now sweeps the defender's cutoff and prints
  the false-positive cost.
- *"Reporting a failure you did not spend two minutes trying to fix reads as narrative rather than
  method; an ALPHA sweep would turn the failure from a confession into a result."* → we ran the
  frontier. No configuration reaches the target. That is now reported as a finding.
- *"Deciding who is the copy is the hard half of the problem and the sim assumes it away by list
  order."* → added the registration-order swap (attacker registers first).

**Note on what this round means.** Round 6 was adversarial review of the *paper*, not of the
mechanism, and it changed the paper's conclusions twice. It is the clearest instance in this project
of the effect the event asks us to demonstrate — and, awkwardly for our own thesis, it is also the
round where the reviewers were most obviously doing what a good *single* reviewer would do.
