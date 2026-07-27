#!/usr/bin/env python3
"""
extract.py — the part that is actually hard: deciding which posts carry a FIRST-PARTY,
FALSIFIABLE price claim.

The rules below are not invented. They are the drop reasons that two independent adjudicator
runs produced on a 49-post pilot, encoded so they run at scale:
  THIRD_PARTY_FORECAST (14/44 drops)  "Arthur Hayes confirmed his forecast..."   -> not the author's claim
  NOT_A_PRICE          (18/44 drops)  "$MSTR to own 1,000,000 Bitcoin"          -> quantity / other ticker / market cap
  QUESTION              (4/44 drops)  "100K by the end of the week?"            -> not a claim
  HYPOTHETICAL          (2/44 drops)  "Imagine the payout if BTC went to..."    -> not a claim
Pilot precision of the naive regex parser: 5/49 = 10.2%. Everything here exists to raise that.
"""
import re

ASSET_ALIASES = {
    "bitcoin": ["bitcoin", "btc"],
    "ethereum": ["ethereum", "eth", "ether"],
    "solana": ["solana", "sol"],
}

# Someone else's forecast being reported.
ATTRIBUTION = re.compile(
    r"\b(says?|said|predicts?|predicted|forecasts?|forecasted|expects?|expected|"
    r"according to|per |confirmed his|confirmed her|confirmed their|reiterat\w+|"
    r"analyst|analysts|survey|poll|respondents|of people|of investors|"
    r"target from|call from|price target by)\b", re.I)

HYPOTHETICAL = re.compile(r"\b(imagine|what if|hypothetical|if bitcoin (?:went|goes)|would be|could have)\b", re.I)
NOT_PRICE_CTX = re.compile(r"\b(market ?cap|mcap|valuation|volume|inflow|outflow|aum|"
                           r"revenue|profit|fees?|tvl|supply|holdings?|treasury|reserves?)\b", re.I)
# "1,000,000 Bitcoin" / "500 BTC" -> a quantity of coins, not a price
QUANTITY = re.compile(r"\b\d[\d,\.]*\s*(k|m|million|thousand)?\s*(bitcoin|btc|eth|ethereum|sol|solana)\b", re.I)
# a competing ticker in the post ($MSTR, $IREN ...) that is not our asset
OTHER_TICKER = re.compile(r"\$([A-Z]{2,6})\b")
OUR_TICKERS = {"BTC", "ETH", "SOL"}

PRICE_RE = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*([kKmM])?|"
                      r"\b(\d{1,3}(?:,\d{3})+|\d{2,7}(?:\.\d+)?)\s*([kK])\b")

DOWN_WORDS = re.compile(r"\b(down to|drop to|fall to|crash to|dump to|revisit|retest|bottom at|"
                        r"below|under|sub)\b", re.I)


def _price_value(m):
    raw = m.group(1) or m.group(3)
    suf = (m.group(2) or m.group(4) or "").lower()
    if raw is None:
        return None
    try:
        v = float(raw.replace(",", ""))
    except ValueError:
        return None
    if suf == "k":
        v *= 1_000
    elif suf == "m":
        v *= 1_000_000
    return v


def sentence_of(text, pos):
    start = max(text.rfind(".", 0, pos), text.rfind("!", 0, pos), text.rfind("\n", 0, pos)) + 1
    end = min([x for x in [text.find(".", pos), text.find("!", pos), text.find("\n", pos), len(text)] if x != -1])
    return text[start:end + 1]


def extract(text, asset):
    """Return (target_usd, direction, reject_reason). target is None when rejected."""
    aliases = ASSET_ALIASES[asset]
    low = text.lower()

    if HYPOTHETICAL.search(text):
        return None, None, "HYPOTHETICAL"

    # a competing ticker that is not ours -> the number probably belongs to it
    others = {t for t in OTHER_TICKER.findall(text)} - OUR_TICKERS
    if others:
        return None, None, "WRONG_ASSET"

    best = None
    for m in PRICE_RE.finditer(text):
        v = _price_value(m)
        if v is None or not (100 <= v <= 10_000_000):
            continue
        sent = sentence_of(text, m.start())
        sl = sent.lower()

        if "?" in sent:
            return None, None, "QUESTION"
        if ATTRIBUTION.search(sent):
            return None, None, "THIRD_PARTY_FORECAST"
        if NOT_PRICE_CTX.search(sent):
            continue
        if QUANTITY.search(sent[max(0, m.start() - sentence_of(text, m.start()).find(sent)):]):
            # number immediately followed by the coin name = quantity of coins
            tail = sent[sent.lower().find(m.group(0).lower()) + len(m.group(0)):][:20].lower()
            if any(a in tail for a in aliases):
                continue
        # the asset must be mentioned in the same sentence
        if not any(re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", sl) for a in aliases):
            continue

        direction = "below" if DOWN_WORDS.search(sl) else "above"
        has_dollar = m.group(0).strip().startswith("$")
        if best is None or (has_dollar and not best[2]):
            best = (v, direction, has_dollar)

    if best is None:
        return None, None, "NOT_A_PRICE"
    return best[0], best[1], None
