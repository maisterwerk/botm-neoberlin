# Protocol deviations — recorded as they happened

## Deviation 1: a session played in the wrong mode

The steward's third submission came back with `"mode":"calm"`. The pre-registration restricts the
pilot to **Storm** sessions, because the adversarial host removes most of the luck that a fixed
answer introduces. The game is therefore **excluded** and replayed.

This is an exclusion on a criterion fixed before any data existed — the mode — and not a decision
made after seeing how the game went. The distinction matters, so the discarded session is kept
verbatim in `protocol_deviations.jsonl` and its numbers are stated here rather than vanishing:

    blind, calm mode, 6 guesses, not solved
    mean Skill (defined guesses only) = 0.803

It is worth noting that the excluded game scores HIGHER than either included session so far
(0.641 sighted, 0.716 blind). Dropping it does not flatter the result.

## The cause is a flaw in my instrument, not in the steward

The page opens in Calm. Storm has to be selected by clicking, and in blind mode the visual cues
that would make the current mode obvious — the candidate counter, the guess table — are exactly
what is hidden. A blind session therefore looks nearly identical in either mode.

The obvious fix is a `?mode=storm` parameter in the link. I am **not** making it: changing the
build between sessions would make the sessions incomparable, which is a worse problem than a
clumsy link. The design flaw is reported instead, and the remaining sessions are run with an
explicit instruction to click Storm first and to check that `"mode":"storm"` appears in the export
before sending it.
