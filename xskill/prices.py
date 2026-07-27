#!/usr/bin/env python3
"""
prices.py — the independent ground truth. One CoinGecko range call per asset gives a daily
close series we can query offline, so resolution never depends on X, on the poster, or on us.
"""
import json, sys, time, urllib.request
from datetime import datetime, timezone

ASSETS = ["bitcoin", "ethereum", "solana"]
FROM = int(datetime(2025, 10, 1, tzinfo=timezone.utc).timestamp())
TO = int(datetime(2026, 7, 28, tzinfo=timezone.utc).timestamp())


def fetch(asset):
    url = (f"https://api.coingecko.com/api/v3/coins/{asset}/market_chart/range"
           f"?vs_currency=usd&from={FROM}&to={TO}")
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                       "User-Agent": "botm-xskill/1.0"})
            d = json.load(urllib.request.urlopen(req, timeout=90))
            series = {}
            for ms, price in d.get("prices", []):
                day = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()
                series[day] = price          # last sample of each day wins
            return series
        except Exception as e:
            print(f"  retry {asset}: {str(e)[:70]}", file=sys.stderr)
            time.sleep(8 + attempt * 8)
    return {}


if __name__ == "__main__":
    out = {}
    for a in ASSETS:
        s = fetch(a)
        out[a] = s
        if s:
            days = sorted(s)
            print(f"{a:9s} {len(s):4d} days  {days[0]} .. {days[-1]}  "
                  f"first ${s[days[0]]:,.0f}  last ${s[days[-1]]:,.0f}", file=sys.stderr)
        time.sleep(3)
    json.dump(out, open("prices.json", "w"))
    print("wrote prices.json")
