# A mislabelled field, noticed on the first live session — and deliberately NOT fixed

`__export()` writes `pool: cands.length`, which is the number of candidates REMAINING at export
time, not the size of the day's starting pool. Rob's first session therefore reads `"pool":1`
when the day's pool was 1205.

The instrument is not being changed in the middle of the experiment. Altering the build between
games would make the sighted and blind sessions incomparable, which is a worse problem than a
badly named key. The starting pool is recoverable anyway: it is a deterministic function of the
`day` field (day 20663 -> 1205 words), so nothing is lost.

The field is read as "candidates remaining at the end" everywhere in the analysis, and the name
is corrected only after the last session is in.
