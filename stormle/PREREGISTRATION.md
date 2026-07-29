# Pre-registration — does the barometer help a HUMAN?

Written and committed **before any human data exists**. The git commit timestamp is the proof;
nothing below may be edited afterwards. If the result contradicts the hypothesis it gets reported
as it came out.

## Why this exists
The last submission measured bot against bot and said so plainly:

> "this is a bot-versus-bot experiment. It does not isolate the readout from the recommender ...
> Whether a human who can see the number plays better than one who cannot is a question about
> humans, and I did not run that study — it needs human subjects, which I do not have."

The judge's deduction named exactly that: *"the human-subjects caveat is acknowledged but
unresolved."* We now have one subject: Rob, the human steward.

## Hypothesis
H1: with the barometer visible, a human asks better questions — higher mean Skill
(= asked bits / best available bits) per guess — than with it hidden.
H0: no difference.

## Design
- Single subject, within-subject, **6 Storm games**, alternating by a schedule fixed here.
- Storm mode only: it is adversarial, so luck plays a smaller role than against a fixed answer.
- Blind sessions use `?blind=1`: the barometer, the candidate count and the guess table are hidden,
  while every number is still recorded.
- Seed material: `stormle-human-pilot|build f3b899fd8ee8ed33|2026-07-29`
  sha256 = `9972382b0d1dd4065d75604d8dec7db3f73bb319633b9965d8330397e0d66609`
- **Order (fixed now, not chosen later):**

  | Game | Condition |
  |---|---|
  | 1 | **sighted** |
  | 2 | **blind** |
  | 3 | **blind** |
  | 4 | **sighted** |
  | 5 | **blind** |
  | 6 | **sighted** |

## Primary outcome
Mean Skill per guess, averaged within a game, then compared across the two conditions
(3 games each). Reported as: mean sighted, mean blind, difference, and a paired range.

## Secondary
Games won within six guesses; guesses used when won; realised bits (Got).

## Stopping rule
Exactly six games. No extension, no dropping a game, no re-running one that went badly.
If a game is abandoned mid-way it is reported as abandoned.

## Power — stated before, not after
**Three games per condition cannot establish significance and I will not claim any.** This is a
pilot. It is reported as a direction and an effect size with its spread, and the write-up will say
in plain words that n=6 with one subject is not evidence of a population effect. What it *can* do
is replace "I did not run that study" with "I ran it, here is what happened, and here is why it is
not enough".

## What would falsify H1
Mean Skill equal or lower in the sighted condition. That result gets printed in the submission
in the same size as any other.
