"""Development check for the Task 2 rules.

This writes the same reject list and weekly tables as the Spark job, using
the shared rule code. It is the laptop check. The assessed run is still the
EMR job in task2/spark/prepare_features.py.
"""

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "task2" / "lib"))

from rules import classify_row  # noqa: E402
from weekly import build_weekly_for_ticker, impute_vol_52  # noqa: E402

PRICE_FILE = ROOT / "dataset" / "all_stocks_5yr.csv"
OUTPUT_DIR = ROOT / "task2_outputs"
COLUMNS = [
    "ticker",
    "anchor_date",
    "next_anchor_date",
    "vol_1w",
    "vol_4w",
    "vol_12w",
    "vol_52w",
    "vol_52w_imputed",
    "high_low_range",
    "weekly_return",
    "volume_vs_normal",
    "split_flag",
    "target_next_vol",
    "split",
]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_rows(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            packed = {}
            for column in COLUMNS:
                value = row[column]
                packed[column] = f"{value:.10g}" if isinstance(value, float) else value
            writer.writerow(packed)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    accepted = defaultdict(list)
    rejected = []
    reason_counts = Counter()
    total = 0
    with PRICE_FILE.open(newline="") as handle:
        for row in csv.DictReader(handle):
            total += 1
            status, reasons, trading_date = classify_row(row)
            if status == "accepted":
                accepted[row["Name"].strip()].append(
                    {
                        "date": trading_date,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]),
                    }
                )
            else:
                for reason in reasons:
                    reason_counts[reason] += 1
                rejected.append(
                    {
                        "Name": row["Name"].strip(),
                        "date": row["date"],
                        "reasons": "|".join(reasons),
                        "open": row["open"],
                        "high": row["high"],
                        "low": row["low"],
                        "close": row["close"],
                        "volume": row["volume"],
                    }
                )

    accepted_rows = sum(len(bars) for bars in accepted.values())
    weekly = []
    for ticker, bars in sorted(accepted.items()):
        weekly.extend(build_weekly_for_ticker(ticker, bars))
    median = impute_vol_52(weekly)
    ready = [row for row in weekly if row["ready"]]
    exclusions = Counter(row["exclusion"] for row in weekly if not row["ready"])
    split_counts = Counter(row["split"] for row in ready)
    split_flags = sum(row["split_flag"] for row in ready)

    with (OUTPUT_DIR / "rejected_rows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rejected[0]))
        writer.writeheader()
        writer.writerows(rejected)
    for split in ("train", "validation", "test"):
        write_rows(OUTPUT_DIR / f"weekly_{split}.csv", [row for row in ready if row["split"] == split])

    summary = {
        "price_file": "dataset/all_stocks_5yr.csv",
        "sha256": sha256(PRICE_FILE),
        "bytes": PRICE_FILE.stat().st_size,
        "source_url": "https://raw.githubusercontent.com/plotly/datasets/master/all_stocks_5yr.csv",
        "total_rows": total,
        "rejected_rows": len(rejected),
        "accepted_rows": accepted_rows,
        "reason_counts": dict(reason_counts),
        "tickers_accepted": len(accepted),
        "weekly_ready_rows": len(ready),
        "split_counts": dict(split_counts),
        "split_flag_rows": split_flags,
        "vol_52w_training_median": median,
        "exclusions": dict(exclusions),
        "identity_ok": total == len(rejected) + accepted_rows,
    }
    (OUTPUT_DIR / "reconciliation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not summary["identity_ok"]:
        raise SystemExit("Row identity failed")
    if total != 619040 or accepted_rows != 605887 or reason_counts["out_of_range"] != 13130:
        raise SystemExit("Counts do not match the brief's accepted-bar figure")


if __name__ == "__main__":
    main()
