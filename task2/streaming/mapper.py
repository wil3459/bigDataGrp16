#!/usr/bin/env python3
"""Hadoop Streaming mapper: classify one price row and emit audit counts."""

import csv
import os
import sys
import traceback

# Hadoop places rules.py in the task folder, not in task2/lib.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
try:
    from rules import classify_row  # noqa: E402
except Exception:
    traceback.print_exc()
    sys.exit(1)

FIELDS = ["date", "open", "high", "low", "close", "volume", "Name"]


def main():
    # Parse each line directly. A Hadoop split does not repeat the CSV header.
    for line in sys.stdin:
        text = line.strip("\n")
        if not text or text.startswith("date,"):
            continue
        values = next(csv.reader([text]))
        row = dict(zip(FIELDS, values))
        status, reasons, _ = classify_row(row)
        print("rows\ttotal\t1")
        if status == "accepted":
            print("rows\taccepted\t1")
        else:
            print("rows\trejected\t1")
            for reason in reasons:
                print(f"reason\t{reason}\t1")


if __name__ == "__main__":
    main()
