-- Task 2, Part B: register the Wikinews tables. Run after the Wikinews Streaming job and
-- before task2/spark/news_features.py. Spark reads these tables through the Hive metastore.

CREATE DATABASE IF NOT EXISTS project;

-- Output of the Wikinews Streaming job: one row per published article first created in 2013-2017.
CREATE EXTERNAL TABLE IF NOT EXISTS project.wikinews_articles (
  page_id BIGINT,
  title STRING,
  first_ts STRING,          -- earliest revision, UTC, e.g. 2014-09-09T18:02:11Z (used as publish time)
  last_ts STRING,           -- latest revision, UTC
  n_revisions INT,
  text STRING               -- latest revision text, one line
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/project/prepared/wikinews_articles';

-- Which company names count as a mention of each ticker (task2/reference/ticker_names.csv).
CREATE EXTERNAL TABLE IF NOT EXISTS project.ticker_names (
  ticker STRING,
  company STRING,
  match_names STRING,       -- names separated by |
  rule STRING               -- auto or manual
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
STORED AS TEXTFILE
LOCATION '/project/raw/reference/ticker_names'
TBLPROPERTIES ('skip.header.line.count'='1');

-- Hive transformation: one row per (ticker, name), so Spark can match each name separately.
CREATE OR REPLACE VIEW project.ticker_name_list AS
SELECT t.ticker, trim(n.name) AS name
FROM project.ticker_names t
LATERAL VIEW explode(split(t.match_names, '[|]')) n AS name
WHERE trim(n.name) <> '';

-- Written by news_features.py: which article mentions which ticker.
CREATE EXTERNAL TABLE IF NOT EXISTS project.wikinews_matches (
  page_id BIGINT, ticker STRING, pub_date STRING)
STORED AS PARQUET
LOCATION '/project/prepared/wikinews_matches';

-- Written by news_features.py: the Part A weekly tables plus news_count.
CREATE EXTERNAL TABLE IF NOT EXISTS project.weekly_news_all (
  ticker STRING, anchor_date STRING, next_anchor_date STRING,
  vol_1w DOUBLE, vol_4w DOUBLE, vol_12w DOUBLE, vol_52w DOUBLE, vol_52w_imputed BIGINT,
  high_low_range DOUBLE, weekly_return DOUBLE, volume_vs_normal DOUBLE,
  split_flag BIGINT, target_next_vol DOUBLE, `split` STRING, news_count BIGINT)
STORED AS PARQUET
LOCATION '/project/prepared/weekly_news_all';

CREATE EXTERNAL TABLE IF NOT EXISTS project.weekly_news_train LIKE project.weekly_news_all
LOCATION '/project/prepared/weekly_news_train';
CREATE EXTERNAL TABLE IF NOT EXISTS project.weekly_news_validation LIKE project.weekly_news_all
LOCATION '/project/prepared/weekly_news_validation';
CREATE EXTERNAL TABLE IF NOT EXISTS project.weekly_news_test LIKE project.weekly_news_all
LOCATION '/project/prepared/weekly_news_test';
