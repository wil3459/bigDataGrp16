#!/usr/bin/env python3
"""Hadoop Streaming reducer for the Wikinews articles (Task 2, Part B).

Input is sorted by page_id. Keeps one row per page_id (the one with the earliest
first_ts) and counts any duplicates, so a page that appears twice is never
counted twice. Output has the same columns as the mapper.
"""
import sys


COUNTS = {}


def count(name, n=1):
    COUNTS[name] = COUNTS.get(name, 0) + n


def main():
    current, best = None, None
    for line in sys.stdin:
        fields = line.rstrip("\n").split("\t")
        if len(fields) != 6:
            count("reducer_bad_rows")
            continue
        if fields[0] != current:
            if best:
                print("\t".join(best)); count("reducer_unique_articles")
            current, best = fields[0], fields
        else:
            count("reducer_duplicates_removed")
            if fields[2] < best[2]:
                best = fields
    if best:
        print("\t".join(best)); count("reducer_unique_articles")
    for name, n in sorted(COUNTS.items()):
        sys.stderr.write(f"reporter:counter:wikinews,{name},{n}\n")


if __name__ == "__main__":
    main()
