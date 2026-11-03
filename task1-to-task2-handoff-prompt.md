# Prompt: finish the Task 1 handoff so Task 2 can start

You are working in the `bigDataGrp16` repo for INF2006. Another teammate owns Task 2. Your job is only the missing Task 1 handoff. Do not build weekly features, do not train a model, and do not delete or edit the original data files.

The price audit in `task1.ipynb` is a local check, not a finished Task 1. Use those results as a starting point. Measure again from the file. If a number below does not match the file, keep the measured number and say so.

## Team decisions (already made)

- Main source: the official daily price CSV from the link in the project brief. In this repo it is named `all_stocks_5yr.csv`.
- Extra source: the two official Wikinews history dumps from October 2026. Filter to 2013–2017 later, in Task 2. Do not filter or unpack them in this task.
- Not used: GDELT and SEC filings. Do not download them. Leave any old GDELT sample outputs in place. Add a short note that the project will not use them.
- Prediction task, for context only: next-week volatility regression. Do not start it.

## What the existing audit already measured

Do not treat these as final until you remeasure:

- File fingerprint already recorded: SHA-256 `6aea253cd19de60b568143991aaf1fa482456565c389205658d236e595e716cf`, size 29,580,549 bytes.
- 619,040 rows, 505 tickers, columns `date`, `open`, `high`, `low`, `close`, `volume`, `Name`.
- Dates found: 2013-02-08 through 2018-02-07.
- Issue counts, which can describe the same row more than once: blank or non-numeric open 11, high 8, low 8; high below low 1; open outside the high–low range 4; close outside that range 9. No bad dates, no negative volume, no duplicate ticker–date keys were found.
- Zero volume was never checked.
- Source URL and download time are still the placeholders `REPLACE_WITH_LECTURER_SOURCE_OR_DOWNLOAD_REFERENCE` and `REPLACE_WITH_ACTUAL_DOWNLOAD_DATE_UTC`.
- The CSV is not in this repo. `task1.ipynb` read it from `dataset/all_stocks_5yr.csv` on the machine that ran the audit.
- Nothing has been copied to HDFS. `RUN_MODE` was `local`.

The brief’s accepted price set is 605,887 bars from 8 February 2013 to 29 December 2017. A working theory, which you must test rather than force, is: 619,040 total, about 13,130 rows dated after 2017-12-29, then about 23 broken rows inside the remaining range, leaving 605,887. Prove or correct that with unique row counts.

## Do this

### 1. Put the original price file where Task 2 can read it

- Copy the unchanged CSV to `dataset/all_stocks_5yr.csv`.
- Recompute SHA-256 and byte size. They must match the fingerprint above. If they do not, stop and report both fingerprints. Do not continue with a different file.
- Fill in the real brief URL and the real download date (UTC). If you no longer know the download date, say `unknown` and give the file’s save date. Do not leave `REPLACE_WITH_...`.
- Do not commit the CSV. Add `dataset/` to `.gitignore` if it is not already ignored. The submission ZIP must not contain raw data.

### 2. Remeasure the price file and write a reject list

Read the CSV in chunks. Do not load-and-fix it, and do not overwrite it.

Count unique rows in these groups:

- Dated before 2013-02-08.
- Dated after 2017-12-29.
- Inside 2013-02-08 to 2017-12-29 inclusive, and broken.
- Inside that range and kept.

A row is broken only if at least one of these is true:

- `open`, `high`, `low`, or `close` is blank or not a number.
- `high` < `low`.
- `open` is outside `[low, high]`, or `close` is outside `[low, high]`.
- `volume` is blank, not a number, negative, or zero.

Large price jumps are not broken. Do not flag the stock-split weeks for LNT, EBAY, NI, or DISCA. Do not drop tickers with a short history (APTV, BHF, BHGE, DWDP, DXC). Task 2 will handle those.

Write:

- `task1_outputs/handoff/price_reconciliation.json` with the four counts above, the issue counts, and this identity: total rows = before range + after range + broken in range + kept in range.
- `task1_outputs/handoff/price_reject_rows.csv` with one row per rejected row: `Name`, `date`, `reason_codes`, and the original `open`, `high`, `low`, `close`, `volume`. A row after 2017-12-29 can also be broken; give it both reasons. This file is the list Task 2 will use. Do not delete those rows from the CSV.
- If kept rows are not 605,887, stop and explain the gap. Show which extra rule would close the gap and how many rows it would remove. Do not change the rule silently so the total matches the brief.

### 3. Record Wikinews, or stop with a clear blocker

The two files are:

- `enwikinews-20261001-pages-meta-history1.xml-p1p481753.bz2`
- `enwikinews-20261001-pages-meta-history1.xml-p481754p3096188.bz2`

About 662 MB together. Official page links have returned 404; the files should come from the official mirror named in the brief or course page.

- Save them under `dataset/wikinews/`. Do not commit them.
- For each file record the URL actually used, download time (UTC), bytes, and SHA-256.
- Do not decompress them and do not parse articles. Task 2 will keep namespace 0, use the first revision as the publish date, and count articles per company per week.
- If you cannot download them, write `task1_outputs/handoff/wikinews_blocker.md` with the URL you tried, the error, and what is left to do. Do not invent checksums.

### 4. Write the inventory and the source decision

Write `task1_outputs/handoff/raw_file_inventory.csv` with one row per price file and Wikinews file: source, filename, relative path, bytes, SHA-256, acquired UTC, and source URL.

Write `task1_outputs/handoff/source_decision.md` in a few short paragraphs:

- Price file is the core source. Wikinews is the only extra source.
- GDELT is not used. The old notebook only checked three archives (27–29 December 2017), which are outside July 2015–June 2017. The full set is about 55 GB unpacked. The provisional cluster has two 100 GiB data disks and HDFS replication 2, so usable shared space is about 100 GiB. State that as the storage reason.
- SEC is not used. No ticker mapping was verified.
- The price `Name` column is a ticker, not a company name. Task 2 still needs a separate ticker-to-company list to match Wikinews. If you already have that list, put it in `dataset/reference/` and add one inventory row. If you do not, say it is still missing. Do not invent the mapping.

### 5. Leave HDFS commands, and run them only if the cluster exists

The assessed originals have to live on HDFS. The full timed run is not part of this task. The teaching team has not confirmed the final cluster yet. Develop against the local files until then.

Write `task1_outputs/handoff/hdfs_stage_commands.sh` that, on EMR, will:

- create `/project/raw/prices` and `/project/raw/wikinews`
- `hdfs dfs -put` the original files only
- `hdfs dfs -ls -R` and `hdfs dfs -du -h` on `/project/raw`
- not overwrite files already there

If a cluster is already up and you can reach it, run that script and save the command output to `task1_outputs/handoff/hdfs_ls.txt`. If no cluster is up, do not launch one. Say that the commands are ready and unrun.

Use this provisional setup only as a note in the decision file, not as a cluster you create now: EMR `emr-7.10.0`, 1 primary and 2 core `m5.xlarge`, 100 GiB gp3 per core node, `dfs.replication` 2, Spark starting at 2 executors × 2 cores × 6 GiB with dynamic allocation off. A Q&A post said 200 GiB per core node. The later 11-page brief says 100 GiB. Follow the brief until the teaching team says otherwise.

## Done when

- `dataset/all_stocks_5yr.csv` exists locally, is gitignored, and its SHA-256 matches the fingerprint above.
- The reconciliation identity holds, and `price_reject_rows.csv` lists every rejected row with reasons.
- Wikinews files are inventoried with real checksums, or the blocker note explains why they are absent.
- `raw_file_inventory.csv` has real URLs and dates, with no `REPLACE_WITH_...` text.
- `source_decision.md` states price + Wikinews, and why GDELT and SEC are out.
- HDFS commands exist, and either `hdfs_ls.txt` is real output or the note says they were not run.
- The original CSV and the Wikinews dumps are byte-for-byte unchanged.
- No model, weekly table, Hive job, or Task 2 cleaning script was added.

Reply with the four counts, whether kept rows equal 605,887, the Wikinews checksums or the blocker, and whether HDFS was actually run.
