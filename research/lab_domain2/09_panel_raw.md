# Domain 2, round 5 raw — blind judge outputs, verbatim

Published in the same format as domain 1's `lab_claude/09_panel2_raw.md`, because a pre-flight
reviewer correctly pointed out that the three judgements which carry this project's significance
were the only ones with no raw artifact.

Protocol: identical neutral framing for all three judges (domain 1 varied strictness wording per
judge — that confound is fixed here). Labels hidden. Order swapped: lab = A for judge 1, lab = B
for judges 2 and 3.

- **Judge 1 — claude-haiku class.** Lab shown as A.
  `{"A":{"rigor":9,"creativity":8,"self_critique":8},"B":{"rigor":8,"creativity":6,"self_critique":8},`
  `"why":"A's opposite-sign predictions via counterfactuals and injection-calibrated thresholds show deeper statistical novelty; B's transfer ratio is sound but straightforward, though both exhibit strong self-critique."}`

- **Judge 2 — claude-sonnet class.** Lab shown as B.
  `{"A":{"rigor":8,"creativity":7,"self_critique":8},"B":{"rigor":9,"creativity":9,"self_critique":9},`
  `"why":"B's counterfactual-answer arm (contamination and capability predict opposite signs) plus clustered-SE power calc and empirical null-distribution calibration edge out A's cleaner but simpler transfer-ratio design, though A's worked paraphrase counterexample is the sharper single piece of self-critique."}`

- **Judge 3 — claude-opus class.** Lab shown as B.
  `{"A":{"rigor":8,"creativity":7,"self_critique":8},"B":{"rigor":8,"creativity":9,"self_critique":9},`
  `"why":"Both are executable and honestly self-critical, but B's answer-altering counterfactual arm gives contamination and capability opposite signs — a genuinely non-obvious identification device — plus clustered-SE power math and an injection ladder that declares undetectable rungs, whereas A's transfer-ratio design is cleaner and better-sized but rests on a fresh-set exchangeability assumption it admits it cannot prove."}`

## Two things this raw file makes visible that the summary hid

1. **The solo's domain-2 scores are near-constant** (rigor 8/8/8, self-critique 8/8/8). That is the
   same low-variance pattern our own reviewers used to reject domain-1 panel 1. The lab's scores do
   vary (25/27/26), so this is not the identical pathology — but we are flagging it rather than
   waiting to be caught, since we wrote the rejection criterion ourselves.
2. **Length:** domain-2 lab text is **814 words**, the control **754** — the lab is 8% *longer* in
   the domain that carries the significance. Domain 1 ran the other way (lab 653, control 769). Our
   earlier drafts said "~750 vs ~700 throughout", which was wrong in both domains. Real counts are
   published here.
