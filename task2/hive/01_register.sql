-- Register the original price file and the tables written by prepare_features.py.
-- Spark SQL does not replace this step. Run these statements in Hive on EMR.

CREATE DATABASE IF NOT EXISTS project;

CREATE EXTERNAL TABLE IF NOT EXISTS project.prices_raw (
  trade_date STRING,
  open STRING,
  high STRING,
  low STRING,
  close STRING,
  volume STRING,
  ticker STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/project/raw/prices'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE IF NOT EXISTS project.prices_rejected (
  trade_date STRING,
  open STRING,
  high STRING,
  low STRING,
  close STRING,
  volume STRING,
  ticker STRING,
  status STRING,
  reasons STRING
)
STORED AS PARQUET
LOCATION '/project/prepared/prices_rejected';

CREATE EXTERNAL TABLE IF NOT EXISTS project.prices_cleaned (
  trade_date STRING,
  open STRING,
  high STRING,
  low STRING,
  close STRING,
  volume STRING,
  ticker STRING,
  status STRING,
  reasons STRING
)
STORED AS PARQUET
LOCATION '/project/prepared/prices_cleaned';

CREATE EXTERNAL TABLE IF NOT EXISTS project.weekly_all (
  ticker STRING,
  anchor_date STRING,
  next_anchor_date STRING,
  vol_1w DOUBLE,
  vol_4w DOUBLE,
  vol_12w DOUBLE,
  vol_52w DOUBLE,
  vol_52w_imputed INT,
  high_low_range DOUBLE,
  weekly_return DOUBLE,
  volume_vs_normal DOUBLE,
  split_flag INT,
  target_next_vol DOUBLE,
  split STRING
)
STORED AS PARQUET
LOCATION '/project/prepared/weekly_all';

CREATE EXTERNAL TABLE IF NOT EXISTS project.weekly_train (
  ticker STRING, anchor_date STRING, next_anchor_date STRING,
  vol_1w DOUBLE, vol_4w DOUBLE, vol_12w DOUBLE, vol_52w DOUBLE, vol_52w_imputed BIGINT,
  high_low_range DOUBLE, weekly_return DOUBLE, volume_vs_normal DOUBLE,
  split_flag BIGINT, target_next_vol DOUBLE, `split` STRING)
STORED AS PARQUET
LOCATION '/project/prepared/weekly_train';

CREATE EXTERNAL TABLE IF NOT EXISTS project.weekly_validation (
  ticker STRING, anchor_date STRING, next_anchor_date STRING,
  vol_1w DOUBLE, vol_4w DOUBLE, vol_12w DOUBLE, vol_52w DOUBLE, vol_52w_imputed BIGINT,
  high_low_range DOUBLE, weekly_return DOUBLE, volume_vs_normal DOUBLE,
  split_flag BIGINT, target_next_vol DOUBLE, `split` STRING)
STORED AS PARQUET
LOCATION '/project/prepared/weekly_validation';

CREATE EXTERNAL TABLE IF NOT EXISTS project.weekly_test (
  ticker STRING, anchor_date STRING, next_anchor_date STRING,
  vol_1w DOUBLE, vol_4w DOUBLE, vol_12w DOUBLE, vol_52w DOUBLE, vol_52w_imputed BIGINT,
  high_low_range DOUBLE, weekly_return DOUBLE, volume_vs_normal DOUBLE,
  split_flag BIGINT, target_next_vol DOUBLE, `split` STRING)
STORED AS PARQUET
LOCATION '/project/prepared/weekly_test';