#!/bin/bash
# Assessed Task 2 order on EMR. Run from the project root after the CSV is on HDFS.
# This does not start the cluster and it does not download the file.
set -euo pipefail

STREAMING_JAR="${STREAMING_JAR:-/usr/lib/hadoop-mapreduce/hadoop-streaming.jar}"

hdfs dfs -mkdir -p /project/raw/prices /project/audit /project/prepared
hdfs dfs -put -f dataset/all_stocks_5yr.csv /project/raw/prices/all_stocks_5yr.csv

hdfs dfs -rm -r -f /project/audit/price_row_audit
hadoop jar "$STREAMING_JAR" \
  -D mapreduce.job.reduces=1 \
  -D stream.num.map.output.key.fields=2 \
  -files "task2/streaming/mapper.py#mapper.py,task2/streaming/reducer.py#reducer.py,task2/lib/rules.py#rules.py" \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py" \
  -input /project/raw/prices/all_stocks_5yr.csv \
  -output /project/audit/price_row_audit

hive -f task2/hive/01_register.sql

spark-submit \
  --py-files task2/lib/rules.py,task2/lib/weekly.py \
  task2/spark/prepare_features.py \
  /project/raw/prices/all_stocks_5yr.csv \
  /project/prepared

hive -f task2/hive/02_reconcile.sql
