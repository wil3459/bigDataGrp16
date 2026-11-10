import csv, sys
src, dst, step = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10
with open(src, newline="") as f:
    rows = list(csv.reader(f))
header, body = rows[0], rows[1:]
tickers = sorted({r[6] for r in body})
keep = set(tickers[::step])
with open(dst, "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(header)
    w.writerows(r for r in body if r[6] in keep)
print(f"kept {len(keep)} of {len(tickers)} tickers")
