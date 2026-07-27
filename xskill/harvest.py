#!/usr/bin/env python3
"""
harvest.py — Phase 1 of the X Skill: turn X talk into a falsifiable ledger.

We search X for posts that make a *checkable* claim: an asset, a numeric target, and a deadline.
Everything without all three is discarded — that filter is the whole point, because "high signal"
on X is not the loud post, it is the rare post that can be proved wrong later.

Output: predictions.json — one record per parsed claim, with the exact source post id so any
verifier can open it.

Key: secrets/socialdata.key   Ground truth (phase 2): CoinGecko public API, no key.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta

KEY = open("/Users/claude/Neo 2.0/secrets/socialdata.key").read().strip()
BASE = "https://api.socialdata.tools/twitter/search"

# Assets we can resolve against an independent price source.
ASSETS = {
    "bitcoin": ("bitcoin", ["bitcoin", "btc", "$btc"]),
    "ethereum": ("ethereum", ["ethereum", "eth", "$eth"]),
    "solana": ("solana", ["solana", "sol", "$sol"]),
}

# Deadline phrases we can convert to a concrete date. Anything vaguer is dropped.
DEADLINE_PATTERNS = [
    (r"\bby (?:the )?end of (?:this )?(?:the )?year\b", "eoy"),
    (r"\bby (?:the )?end of (\d{4})\b", "eoy_year"),
    (r"\bby (?:the )?end of (january|february|march|april|may|june|july|august|september|october|november|december)\b", "eom_named"),
    (r"\bby (january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\b", "by_month_year"),
    (r"\bbefore (?:the )?end of (?:this )?month\b", "eom"),
    (r"\bby (?:the )?end of (?:this |the )?month\b", "eom"),
    (r"\bby (?:the )?end of (?:this |the )?week\b", "eow"),
    (r"\bby Q([1-4])\b", "quarter"),
]

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june",
     "july", "august", "september", "october", "november", "december"])}

# "$130,000" / "$130k" / "130k" / "$1.2M"
PRICE_RE = re.compile(r"\$?\s?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*([kKmM])?\b")


def api_search(query, cursor=None):
    q = urllib.parse.quote(query)
    url = f"{BASE}?query={q}&type=Latest"
    if cursor:
        url += "&cursor=" + urllib.parse.quote(cursor)
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + KEY, "Accept": "application/json"})
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception as e:
            if attempt == 3:
                print(f"  ! search failed: {str(e)[:80]}", file=sys.stderr)
                return {}
            time.sleep(3 + attempt * 3)
    return {}


def parse_price(text):
    """Return the most plausible target price mentioned, or None."""
    best = None
    for m in PRICE_RE.finditer(text):
        raw, suffix = m.group(1), (m.group(2) or "").lower()
        try:
            v = float(raw.replace(",", ""))
        except ValueError:
            continue
        if suffix == "k":
            v *= 1_000
        elif suffix == "m":
            v *= 1_000_000
        # plausible crypto price targets only
        if 100 <= v <= 10_000_000:
            # prefer the value that appeared with a $ sign
            has_dollar = m.group(0).strip().startswith("$")
            if best is None or (has_dollar and not best[1]):
                best = (v, has_dollar)
    return best[0] if best else None


def parse_deadline(text, posted):
    """Convert a deadline phrase into a concrete resolution date."""
    low = text.lower()
    for pat, kind in DEADLINE_PATTERNS:
        m = re.search(pat, low)
        if not m:
            continue
        if kind == "eoy":
            return datetime(posted.year, 12, 31), m.group(0)
        if kind == "eoy_year":
            return datetime(int(m.group(1)), 12, 31), m.group(0)
        if kind == "eom_named":
            mo = MONTHS[m.group(1)]
            yr = posted.year if mo >= posted.month else posted.year + 1
            return _end_of_month(yr, mo), m.group(0)
        if kind == "by_month_year":
            return _end_of_month(int(m.group(2)), MONTHS[m.group(1)]), m.group(0)
        if kind == "eom":
            return _end_of_month(posted.year, posted.month), m.group(0)
        if kind == "eow":
            return posted + timedelta(days=(6 - posted.weekday())), m.group(0)
        if kind == "quarter":
            q = int(m.group(1))
            return _end_of_month(posted.year, q * 3), m.group(0)
    return None, None


def _end_of_month(year, month):
    if month == 12:
        return datetime(year, 12, 31)
    return datetime(year, month + 1, 1) - timedelta(days=1)


def detect_asset(text):
    low = text.lower()
    for asset, (cg_id, aliases) in ASSETS.items():
        for a in aliases:
            if re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", low):
                return asset, cg_id
    return None, None


def harvest(windows, queries, min_faves=25, per_query_pages=1):
    seen, out = set(), []
    calls = 0
    for since, until in windows:
        for qbase in queries:
            q = f"{qbase} since:{since} until:{until} min_faves:{min_faves} -filter:replies lang:en"
            cursor = None
            for _ in range(per_query_pages):
                d = api_search(q, cursor)
                calls += 1
                tweets = d.get("tweets", [])
                if not tweets:
                    break
                for t in tweets:
                    tid = t.get("id_str")
                    if not tid or tid in seen:
                        continue
                    seen.add(tid)
                    text = t.get("full_text", "")
                    posted = datetime.strptime(t["tweet_created_at"][:19], "%Y-%m-%dT%H:%M:%S")
                    asset, cg = detect_asset(text)
                    if not asset:
                        continue
                    target = parse_price(text)
                    if not target:
                        continue
                    deadline, phrase = parse_deadline(text, posted)
                    if not deadline:
                        continue
                    if deadline <= posted:
                        continue
                    out.append({
                        "id": tid,
                        "url": f"https://x.com/{t['user']['screen_name']}/status/{tid}",
                        "account": t["user"]["screen_name"],
                        "followers": t["user"].get("followers_count"),
                        "posted": posted.isoformat()[:10],
                        "text": " ".join(text.split())[:400],
                        "likes": t.get("favorite_count", 0),
                        "retweets": t.get("retweet_count", 0),
                        "asset": asset,
                        "coingecko_id": cg,
                        "target_usd": target,
                        "deadline": deadline.isoformat()[:10],
                        "deadline_phrase": phrase,
                    })
                cursor = d.get("next_cursor")
                if not cursor:
                    break
                time.sleep(0.4)
    print(f"harvest: {calls} API calls, {len(seen)} posts scanned, {len(out)} falsifiable claims parsed",
          file=sys.stderr)
    return out


if __name__ == "__main__":
    # The configuration actually used for the run reported in the submission.
    QUERIES = [
        '"by the end of" bitcoin', '"by the end of" ethereum', '"by the end of" solana',
        'bitcoin "price target"', 'ethereum "will hit"', 'bitcoin "will hit"',
        'solana "will hit"', 'bitcoin "we go to"', '"my target" bitcoin',
        'bitcoin "before the end of"', 'eth "by the end of"', 'btc "end of month"',
        'bitcoin "this month" target', 'ethereum "price target"', 'sol "price target"',
    ]
    WINDOWS = [
        ("2025-09-01", "2025-09-30"), ("2025-10-01", "2025-10-31"), ("2025-11-01", "2025-11-30"),
        ("2025-12-01", "2025-12-31"), ("2026-01-01", "2026-01-31"), ("2026-02-01", "2026-02-28"),
        ("2026-03-01", "2026-03-31"), ("2026-04-01", "2026-04-30"), ("2026-05-01", "2026-05-31"),
    ]
    preds = harvest(WINDOWS, QUERIES, min_faves=10, per_query_pages=2)
    with open("predictions_big.json", "w") as f:
        json.dump(preds, f, indent=1)
    print(f"wrote predictions.json with {len(preds)} claims")
