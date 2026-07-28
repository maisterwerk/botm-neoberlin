import json, sys
sys.path.insert(0,'.')
import harvest as H
QUERIES = ['"by the end of" bitcoin','"by the end of" ethereum','"by the end of" solana',
 'bitcoin "price target"','ethereum "will hit"','bitcoin "will hit"','solana "will hit"',
 'bitcoin "we go to"','"my target" bitcoin','bitcoin "before the end of"','eth "by the end of"',
 'btc "end of month"','bitcoin "this month" target','ethereum "price target"','sol "price target"']
def months(y0,m0,y1,m1):
    out=[]; y,m=y0,m0
    while (y,m)<=(y1,m1):
        ny,nm=(y+1,1) if m==12 else (y,m+1)
        out.append((f"{y}-{m:02d}-01", f"{ny}-{nm:02d}-01")); y,m=ny,nm
    return out
WINDOWS = months(2024,7,2026,5)
raw = H.harvest(WINDOWS, QUERIES, min_faves=10, per_query_pages=1)
json.dump(raw, open('predictions_multi.json','w'))
print("roh gesamt:", len(raw))
