"""Row rules for the daily price file.

A row is rejected, never repaired. Out-of-range rows are dated before
8 February 2013 or after 29 December 2017. Broken rows are inside that
window but have a blank or impossible price, or a volume that is missing,
negative, or zero.
"""

from datetime import date, datetime

WINDOW_START = date(2013, 2, 8)
WINDOW_END = date(2017, 12, 29)
SHORT_TICKERS = ("APTV", "BHF", "BHGE", "DWDP", "DXC")
SPLIT_RETURN_THRESHOLD = 0.30


def parse_number(value):
    text = (value or "").strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_date(value):
    text = (value or "").strip()
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def classify_row(row):
    """Return (status, reason_codes, trading_date).

    status is 'accepted' or 'rejected'. reason_codes is empty for an
    accepted row. An out-of-range row is not also marked broken.
    """
    trading_date = parse_date(row.get("date"))
    if trading_date is None:
        return "rejected", ["bad_date"], None
    if trading_date < WINDOW_START or trading_date > WINDOW_END:
        return "rejected", ["out_of_range"], trading_date

    prices = {name: parse_number(row.get(name)) for name in ("open", "high", "low", "close")}
    volume = parse_number(row.get("volume"))
    reasons = []
    if any(prices[name] is None for name in ("open", "high", "low", "close")):
        reasons.append("bad_price")
    else:
        open_, high, low, close = (prices[name] for name in ("open", "high", "low", "close"))
        if min(open_, high, low, close) <= 0:
            reasons.append("nonpositive_price")
        if high < low:
            reasons.append("high_below_low")
        if open_ < low or open_ > high:
            reasons.append("open_outside_range")
        if close < low or close > high:
            reasons.append("close_outside_range")
    if volume is None or volume <= 0:
        reasons.append("bad_volume")
    if reasons:
        return "rejected", reasons, trading_date
    return "accepted", [], trading_date
