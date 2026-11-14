"""Task 2, Part B: add news_count to the weekly tables. Run with spark-submit on EMR.

Inputs (registered by 03_register_news.sql):
  project.wikinews_articles  - output of the Wikinews Streaming job
  project.ticker_name_list   - one row per (ticker, company name)
  <OUT_BASE>/weekly_{train,validation,test} - Part A weekly tables from prepare_features.py
Outputs under <OUT_BASE>:
  wikinews_matches/            - page_id, ticker, pub_date
  weekly_news_{all,train,validation,test}/ - Part A columns + news_count

news_count = number of matched articles first created in the 7 days before the anchor date
(pub_date >= anchor_date - 7 and pub_date < anchor_date, dates in UTC). Markets open at
14:30 UTC, so every counted article existed before the prediction is made.
"""
import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

OUT_BASE = sys.argv[1] if len(sys.argv) > 1 else "/project/prepared"
SPLITS = ("train", "validation", "test")


def match_articles(articles, names):
    """Return one row per (page_id, ticker): the article mentions one of the ticker's names.

    Case-sensitive, whole words: "Apple" matches "Apple's" but not "Applesauce".
    \\Q...\\E makes Java treat the name literally (dots, &, * stay plain characters).
    """
    docs = articles.select(
        F.col("page_id").cast("long").alias("page_id"),
        F.substring("first_ts", 1, 10).alias("pub_date"),
        F.concat_ws(" ", "title", "text").alias("doc"))
    patterns = names.select(
        "ticker",
        F.concat(F.lit("(?<![A-Za-z0-9])\\Q"), F.col("name"), F.lit("\\E(?![A-Za-z0-9])")).alias("pattern"))
    return (docs.crossJoin(F.broadcast(patterns))            # ~500 tickers x a few thousand articles: small
                .where(F.expr("doc RLIKE pattern"))
                .select("page_id", "ticker", "pub_date")
                .distinct())                                  # several names of one ticker in one article count once


def add_news_count(weekly, matches):
    w = weekly.withColumn("_anchor", F.to_date("anchor_date"))
    m = matches.withColumn("_pub", F.to_date("pub_date")).withColumnRenamed("ticker", "_m_ticker")
    counts = (w.select("ticker", "anchor_date", "_anchor")
                .join(m, (F.col("ticker") == F.col("_m_ticker"))
                         & (F.col("_pub") >= F.date_sub(F.col("_anchor"), 7))
                         & (F.col("_pub") < F.col("_anchor")))
                .groupBy("ticker", "anchor_date")
                .agg(F.countDistinct("page_id").alias("news_count")))
    return (weekly.join(counts, ["ticker", "anchor_date"], "left")
                  .withColumn("news_count", F.coalesce(F.col("news_count"), F.lit(0)).cast("long")))


def main():
    spark = SparkSession.builder.appName("task2-news-features").enableHiveSupport().getOrCreate()
    try:
        names = spark.table("project.ticker_name_list")            # the Hive view from 03_register_news.sql
        names.limit(1).collect()
    except Exception as err:                                       # fallback: same split done in Spark
        print("WARNING: could not read the Hive view, splitting names in Spark instead:", err)
        names = (spark.table("project.ticker_names")
                      .select("ticker", F.explode(F.split("match_names", "[|]")).alias("name"))
                      .select("ticker", F.trim("name").alias("name")).where(F.col("name") != ""))
    matches = match_articles(spark.table("project.wikinews_articles"), names)
    matches.write.mode("overwrite").parquet(f"{OUT_BASE}/wikinews_matches")
    matches = spark.read.parquet(f"{OUT_BASE}/wikinews_matches")

    # Read Part A's parquet files directly (not through Hive), so column types are exactly as written.
    weekly = None
    for split in SPLITS:
        part = spark.read.parquet(f"{OUT_BASE}/weekly_{split}")
        weekly = part if weekly is None else weekly.unionByName(part)
    weekly_news = add_news_count(weekly, matches).cache()

    n_weekly, n_news = weekly.count(), weekly_news.count()
    if n_weekly != n_news:
        raise RuntimeError(f"row count changed: {n_weekly} weekly rows became {n_news}")
    weekly_news.write.mode("overwrite").parquet(f"{OUT_BASE}/weekly_news_all")
    for split in SPLITS:
        weekly_news.filter(F.col("split") == split).write.mode("overwrite").parquet(f"{OUT_BASE}/weekly_news_{split}")

    print("matched_articles", matches.select("page_id").distinct().count())
    print("article_ticker_pairs", matches.count())
    weekly_news.groupBy("split").agg(F.count("*").alias("rows"),
                                     F.sum((F.col("news_count") > 0).cast("int")).alias("rows_with_news"),
                                     F.sum("news_count").alias("total_news")).show()
    spark.stop()


if __name__ == "__main__":
    main()
