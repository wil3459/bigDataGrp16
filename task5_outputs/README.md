# Task 5 run evidence

**Counted timing runs (Section 6 of the report):**
- `sample_reference_r1`–`r3` (timings.jsonl lines 1–3)
- `full_reference_r1` (line 4), `full_reference_r2` (line 5), `full_reference_r3` (line 12, the last `full_reference_r3` line, finished 2026-11-15 08:51 UTC)
- `full_alt_partitions8_r1`–`r3` (lines 13–15)

**Not counted, kept unedited:** lines 6–11 are six extra runs with the reference setting. They were logged as `full_reference_r3` because the notebook was open in two tabs that shared one kernel. Each run overwrote the folder, so `full_reference_r3/` holds the last one; `commands.log` has all seven runs one after another. Line 16 (`full_reference_r4`) was run on the 16 Nov cluster to check it performed like the 15 Nov cluster (974.6 s, within the reference range), and it's the run used for the reload check.

**Other files:**
- `model_best_r4/`: the saved PipelineModel verified by the reload check (`full_reference_r4/task3_reload_check/`, PASS). 
- `<run>/run_record.json`: stage timings, row counts, test metrics, HDFS sizes, executor memory, Spark UI totals, Wikinews counters.
- `<run>/task3_evidence/`: Task 3 candidate models, A vs B comparison, test metrics, weights.
- `inputs_records/`: download times, checksums, sizes, HDFS listings.
- `hdfs_report_*.txt`, `yarn_applications*.txt`: HDFS use per node, and YARN application IDs.
- `task5_versions.txt`: software versions (recorded 10 Nov on the same EMR release, emr-7.10.0).