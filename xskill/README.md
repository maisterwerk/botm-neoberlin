# Longshot — X price-call odds engine + settlement ledger

Pipeline (run in order; `prices.json`, `ledger.json` and the outputs are committed so the
numbers reprint without any API key):

    harvest.py       broad, recall-first X search        -> predictions_big.json
    extract.py       rule prefilter (first-party only)   -> candidates.json
    (adjudication)   strict keep/drop stage              -> adjB*.json
    resolve.py       settle vs CoinGecko                 -> ledger.json + findings_ledger.txt
    plausibility.py  ex-ante base rates                  -> findings_plausibility.txt

Headline numbers: 3,648 posts scanned -> 11 first-party falsifiable claims (0.3%) -> 0 hits.
Median required move 18.5% vs median realised 30-day move 8.5% (BTC). 11/11 were long shots
at the moment they were posted.

Settlement uses CoinGecko, deliberately a different source than the claims, so the ledger
cannot be gamed by the platform it reads.
