"""Build one weekly row per stock from accepted daily bars.

Prediction time is the anchor morning, when that day's open is known and
the rest of that day is not. The anchor is the last trading day in the
Monday-Friday week. If Friday is a holiday, the anchor is the last earlier
trading day in that week.

Features use completed weeks only. The target is the next week's realized
volatility, and it is kept only when that next anchor still falls inside
the same year split.
"""

import math
import statistics
from datetime import date, timedelta

from rules import SHORT_TICKERS, SPLIT_RETURN_THRESHOLD

TRAIN_END = date(2015, 12, 31)
VALIDATION_END = date(2016, 12, 31)
TEST_END = date(2017, 12, 29)
REQUIRED_FEATURES = (
    "vol_1w",
    "vol_4w",
    "vol_12w",
    "high_low_range",
    "weekly_return",
    "volume_vs_normal",
    "target_next_vol",
)


def week_ending_friday(trading_date):
    return trading_date + timedelta(days=(4 - trading_date.weekday()))


def _std(values):
    if len(values) < 2:
        return None
    return statistics.stdev(values)


def _log_returns(bars):
    returns = []
    for previous, current in zip(bars, bars[1:]):
        if previous["close"] <= 0 or current["close"] <= 0:
            continue
        returns.append(math.log(current["close"] / previous["close"]))
    return returns


def build_weekly_for_ticker(ticker, bars):
    """bars are accepted daily dicts with date, open, high, low, close, volume."""
    ordered = sorted(bars, key=lambda bar: bar["date"])
    if not ordered:
        return []
    first, last = ordered[0]["date"], ordered[-1]["date"]
    short_history = ticker in SHORT_TICKERS or (last - first).days < 365

    grouped = {}
    for bar in ordered:
        grouped.setdefault(week_ending_friday(bar["date"]), []).append(bar)
    anchors = []
    for friday in sorted(grouped):
        days = grouped[friday]
        anchor = days[-1]
        anchors.append(
            {
                "friday": friday,
                "date": anchor["date"],
                "open": anchor["open"],
                "days": days,
            }
        )

    date_index = {bar["date"]: index for index, bar in enumerate(ordered)}
    spans = []
    for index in range(1, len(anchors)):
        previous = anchors[index - 1]
        current = anchors[index]
        days = ordered[date_index[previous["date"]] : date_index[current["date"]]]
        spans.append(
            {
                "previous": previous,
                "current": current,
                "days": days,
                "returns": _log_returns(days),
                "volume": sum(bar["volume"] for bar in days),
                "high": max(bar["high"] for bar in days),
                "low": min(bar["low"] for bar in days),
            }
        )

    rows = []
    for index, span in enumerate(spans):
        current = span["current"]
        previous = span["previous"]
        reasons = []
        if short_history:
            reasons.append("short_history")
        weekly_return = None
        high_low_range = None
        if previous["open"] > 0 and span["days"]:
            weekly_return = current["open"] / previous["open"] - 1
            high_low_range = (span["high"] - span["low"]) / previous["open"]
        else:
            reasons.append("insufficient_history")

        def trailing_std(n_weeks):
            if index + 1 < n_weeks:
                return None
            values = []
            for older in spans[index + 1 - n_weeks : index + 1]:
                values.extend(older["returns"])
            return _std(values)

        vol_1w = _std(span["returns"])
        vol_4w = trailing_std(4)
        vol_12w = trailing_std(12)
        vol_52w = trailing_std(52)
        volume_vs_normal = None
        if index >= 12:
            prior_volumes = [spans[older]["volume"] for older in range(index - 12, index)]
            baseline = statistics.median(prior_volumes)
            if baseline > 0:
                volume_vs_normal = span["volume"] / baseline
        if vol_1w is None or vol_4w is None or vol_12w is None or volume_vs_normal is None:
            reasons.append("insufficient_history")

        target = None
        next_anchor = None
        if index + 1 < len(spans):
            target = _std(spans[index + 1]["returns"])
            next_anchor = spans[index + 1]["current"]["date"]
        elif index + 1 < len(anchors):
            next_anchor = anchors[index + 1]["date"]
        if target is None:
            reasons.append("unavailable_target")

        split = None
        anchor_date = current["date"]
        if next_anchor is None:
            pass
        elif anchor_date.year <= 2015 and next_anchor <= TRAIN_END:
            split = "train"
        elif anchor_date.year == 2016 and next_anchor <= VALIDATION_END:
            split = "validation"
        elif anchor_date.year == 2017 and next_anchor <= TEST_END:
            split = "test"
        else:
            reasons.append("target_crosses_split")

        split_flag = int(weekly_return is not None and abs(weekly_return) >= SPLIT_RETURN_THRESHOLD)
        ready = split is not None and not reasons
        rows.append(
            {
                "ticker": ticker,
                "anchor_date": anchor_date.isoformat(),
                "next_anchor_date": next_anchor.isoformat() if next_anchor else "",
                "vol_1w": vol_1w,
                "vol_4w": vol_4w,
                "vol_12w": vol_12w,
                "vol_52w": vol_52w,
                "high_low_range": high_low_range,
                "weekly_return": weekly_return,
                "volume_vs_normal": volume_vs_normal,
                "split_flag": split_flag,
                "target_next_vol": target,
                "split": split or "",
                "ready": int(ready),
                "exclusion": "|".join(dict.fromkeys(reasons)),
            }
        )
    return rows


def impute_vol_52(rows):
    """Fill missing 52-week volatility with the training median only."""
    training_values = [
        row["vol_52w"]
        for row in rows
        if row["ready"] and row["split"] == "train" and row["vol_52w"] is not None
    ]
    if not training_values:
        return None
    median = statistics.median(training_values)
    for row in rows:
        row["vol_52w_imputed"] = int(row["vol_52w"] is None)
        if row["vol_52w"] is None:
            row["vol_52w"] = median
    return median
