# Baseline test — the same question, asked of an unaided general model

Prompt (no tools, no web, no code — a normal chat answer):

> "On 4 March 2026, the X account @DavidFBailey posted that Bitcoin would reach $80,000 by the end
> of March 2026. Bitcoin was around $68,300 at the time. What are the odds that this prediction came
> true? Give me a probability."

Answer, verbatim excerpts:

> "**Short answer: roughly 15% — maybe 25–30% if 'reach' means touching $80k at any point rather than
> closing there.**"
> "Modeling BTC as a lognormal random walk with an annualized volatility of ~50–55% … the required
> move is roughly 1.05 standard deviations …"
> "**I can't verify what actually happened — I don't have reliable knowledge of BTC's price at the
> end of March 2026**, and I can't confirm that specific post exists or how it was worded."

## What actually happened

- Longshot, causal base rate from prior windows only: **573 of 2,826 prior 27-day windows (20.3%)** reached +17.1%.
- Settlement against CoinGecko: **MISS**. The highest daily high in the window was **$75,988** (17 March);
  $80,000 was never touched, so even the generous "touching" reading fails.

## What this shows, precisely

The baseline is not stupid — the lognormal estimate is a reasonable *model-based prior*, and it says
so honestly. But it produced **15–30%** for an event with **no precedent in the actual recent series**
and which did not occur. Recomputed on the long series our own engine agrees with the baseline's order of magnitude — the baseline was reasonable. What it could not do is settle the claim afterwards. The difference is not intelligence,
it is having the series and the settlement source in hand:

| | unaided model | Longshot |
|---|---|---|
| probability | 15% (30% touching) | 20.3% (+17.1%) / 30.5% (+10.1%) |
| basis | a recalled volatility parameter | 8 years of closes, cut off at the posting date |
| settlement | "I can't verify what actually happened" | MISS, high $75,988 on 17 Mar |
