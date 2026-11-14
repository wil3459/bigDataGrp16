"""Make the development (sample) profile of a Wikinews dump: every 10th <page>, everything else unchanged.

Same idea as make_sample.py for prices (every 10th ticker), so the sample is about 10% of the
pages and the timed runs see genuine input growth from sample to full.
Runs once on the primary node before timing (untimed setup, like the price sample).

Usage: python3 make_wikinews_sample.py <input.xml.bz2> <output.xml.bz2> [every_n=10]
"""
import bz2
import sys


def main(src, dst, every_n=10):
    pages = kept = 0
    keep = True
    with bz2.open(src, "rt", encoding="utf-8") as fin, bz2.open(dst, "wt", encoding="utf-8") as fout:
        for line in fin:
            stripped = line.lstrip()
            if stripped.startswith("<page>"):
                keep = pages % every_n == 0
                pages += 1
                kept += keep
            if keep:
                fout.write(line)
            if stripped.startswith("</page>"):
                keep = True                # header text between pages and the closing </mediawiki> is always kept
    print(f"{src}: {pages} pages, kept {kept}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10)
