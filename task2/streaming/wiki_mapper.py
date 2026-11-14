#!/usr/bin/env python3
"""Hadoop Streaming mapper for the Wikinews history dumps (Task 2, Part B).

Reads the MediaWiki XML one line at a time and keeps one row per published news
article first created in 2013-2017. Every dropped page is counted with a Hadoop
counter (group "wikinews"), so the job log doubles as the raw-data audit.

Output (tab separated): page_id, title, first_ts, last_ts, n_revisions, text
- first_ts: earliest revision timestamp, used as the publish time
- text: title-free text of the latest revision, tabs and newlines turned into spaces

Run with one map task per dump file (split.minsize larger than the file),
so a page is never cut in half by an input split.
"""
import html
import re
import sys

FIRST_YEAR, LAST_YEAR = 2013, 2017
MAX_TEXT = 20000                      # characters kept per article; enough for any news story
PUBLISHED = re.compile(r"\{\{\s*publish", re.IGNORECASE)
TAG_VALUE = re.compile(r"<(\w+)[^>]*>(.*)</\1>")


COUNTS = {}


def count(name, n=1):
    COUNTS[name] = COUNTS.get(name, 0) + n          # sent to Hadoop once at the end, not once per page


def value(line):
    m = TAG_VALUE.search(line)
    return html.unescape(m.group(2)) if m else ""


def clean(text):
    return re.sub(r"\s+", " ", text).strip()[:MAX_TEXT]


def finish_page(page):
    count("pages_total")
    if page["ns"] != "0":
        return count("dropped_not_article")
    if page["redirect"]:
        return count("dropped_redirect")
    if page["first_ts"] is None:
        return count("dropped_no_timestamp")
    year = int(page["first_ts"][:4])
    if year < FIRST_YEAR or year > LAST_YEAR:
        return count("dropped_outside_2013_2017")
    text = page["last_text"] or ""
    if not PUBLISHED.search(text):
        return count("dropped_unpublished")
    count("kept_articles")
    title = clean(page["title"])
    print("\t".join([page["id"], title, page["first_ts"], page["last_ts"], str(page["revisions"]), clean(text)]))


def main():
    page = None
    in_revision = in_text = False
    rev_ts, rev_text = None, []
    expanded_bytes = 0
    for raw in sys.stdin:
        expanded_bytes += len(raw)
        line = raw.strip()
        if in_text:                                        # inside a multi-line <text> element
            if line.endswith("</text>"):
                rev_text.append(raw.rsplit("</text>", 1)[0])
                in_text = False
            else:
                rev_text.append(raw)
            continue
        if line.startswith("<page>"):
            page = {"id": None, "title": "", "ns": None, "redirect": False, "first_ts": None,
                    "last_ts": None, "last_text": None, "revisions": 0}
        elif page is None:
            continue                                       # siteinfo header before the first page
        elif line.startswith("<revision>"):
            in_revision, rev_ts, rev_text = True, None, []
        elif line.startswith("</revision>"):
            in_revision = False
            page["revisions"] += 1
            if rev_ts and (page["first_ts"] is None or rev_ts < page["first_ts"]):
                page["first_ts"] = rev_ts
            if rev_ts and (page["last_ts"] is None or rev_ts >= page["last_ts"]):
                page["last_ts"] = rev_ts
                if page["ns"] == "0":                      # only keep text for articles (saves memory and time)
                    page["last_text"] = html.unescape("".join(rev_text))
        elif line.startswith("</page>"):
            finish_page(page)
            page = None
        elif in_revision:
            if line.startswith("<timestamp>"):
                rev_ts = value(line)
            elif line.startswith("<text") and page["ns"] == "0":
                if line.endswith("/>"):                    # empty or deleted text
                    rev_text = []
                else:
                    body = raw.split(">", 1)[1]
                    if body.rstrip().endswith("</text>"):
                        rev_text = [body.rsplit("</text>", 1)[0]]
                    else:
                        rev_text, in_text = [body], True
        elif line.startswith("<title>"):
            page["title"] = value(line)
        elif line.startswith("<ns>"):
            page["ns"] = value(line)
        elif line.startswith("<id>") and page["id"] is None:
            page["id"] = value(line)
        elif line.startswith("<redirect"):
            page["redirect"] = True
    count("expanded_bytes", expanded_bytes)
    for name, n in sorted(COUNTS.items()):
        sys.stderr.write(f"reporter:counter:wikinews,{name},{n}\n")


if __name__ == "__main__":
    main()
