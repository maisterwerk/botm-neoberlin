# Amendment 1 to the pre-registration — made after session 2, before sessions 3-6

## What came up
Session 2 (blind) ended with the guess PILOT scoring `asked=0, best=0, skill=0`. Only one
candidate remained, so there was no information left to obtain by any word whatsoever. The
implementation computes `min(1, asked / max(1e-9, best))`, which turns 0/0 into 0 and records the
player as having asked a worthless question — when in fact no better question existed.

The original pre-registration says "mean Skill per guess, averaged within a game". It does not
say what to do when Skill is undefined. That is a gap in my specification, not a result.

## The rule, fixed now
**Guesses where `best == 0` are excluded from the Skill average as undefined.** They are still
counted in "guesses used" and still shown in the per-game transcript, so nothing disappears.

## Why this is being written before the remaining data
The amendment **works against the hypothesis under test.** The affected guess is in a BLIND
session, so excluding it raises the blind mean from 0.630 to 0.716 and shrinks any advantage the
sighted condition might show. Deciding it now, in public, with that direction stated, is the only
way the decision cannot be accused of having been made to fit the answer.

Sessions 3-6 have not been played at the time of writing. The git commit timestamp is the proof.

## Unchanged
Everything else in PREREGISTRATION.md stands: six games, the fixed order, the stopping rule, and
the statement that three games per condition cannot establish significance and none will be
claimed.
