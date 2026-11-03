#!/usr/bin/env python3
"""Hadoop Streaming reducer: sum the mapper audit counts."""

import sys


def main():
    totals = {}
    for line in sys.stdin:
        group, key, count = line.rstrip("\n").split("\t")
        label = f"{group}\t{key}"
        totals[label] = totals.get(label, 0) + int(count)
    for label in sorted(totals):
        print(f"{label}\t{totals[label]}")


if __name__ == "__main__":
    main()
