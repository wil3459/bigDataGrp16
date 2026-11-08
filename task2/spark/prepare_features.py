"""Assessed Task 2 job. Run this with spark-submit on EMR, not on a laptop.

It reads the original CSV from HDFS, writes rejected and cleaned daily rows,
then writes the train, validation, and test weekly tables. The weekly math
is the same code as task2/lib/weekly.py. Rows stay grouped by ticker on the
executors. The full price table is not collected to the driver.
"""

import csv
import io
import statistics
import sys
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
from rules import classify_row  # noqa: E402
from weekly import build_weekly_for_ticker  # noqa: E402

RAW_PATH = sys.argv[1] if len(sys.argv) > 1 else "/project/raw/prices/all_stocks_5yr.csv"
OUT_BASE = sys.argv[2] if len(sys.argv) > 2 else "/project/prepared"


def classify_line(line):
    if not line or line.startswith("date,"):
        return None
    row = next(csv.DictReader(io.StringIO("date,open,high,low,close,volume,Name\n" + line)))
    status, reasons, trading_date = classify_row(row)
    parsed = {
        "date": trading_date.isoformat() if trading_date else row["date"],
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"],
        "volume": row["volume"],
        "Name": row["Name"].strip(),
        "status": status,
        "reasons": "|".join(reasons),
    }
    return parsed


def to_bar(row):
    return {
        "date": __import__("datetime").date.fromisoformat(row["date"]),
        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"]),
        "volume": float(row["volume"]),
    }


def build_partition(pair):
    ticker, rows = pair
    bars = [to_bar(row) for row in rows]
    return build_weekly_for_ticker(ticker, bars)


def main():
    spark = SparkSession.builder.appName("task2-weekly-features").enableHiveSupport().getOrCreate()
    classified = spark.sparkContext.textFile(RAW_PATH).map(classify_line).filter(lambda row: row is not None)
    daily = spark.createDataFrame(classified)
    # The CSV fields stay as date and Name until here. Hive matches these
    # parquet files by name, and 01_register.sql calls them trade_date and ticker.
    hive_daily = daily.withColumnRenamed("date", "trade_date").withColumnRenamed("Name", "ticker")
    hive_daily.filter(F.col("status") == "rejected").write.mode("overwrite").parquet(f"{OUT_BASE}/prices_rejected")
    cleaned = daily.filter(F.col("status") == "accepted")
    hive_daily.filter(F.col("status") == "accepted").write.mode("overwrite").parquet(f"{OUT_BASE}/prices_cleaned")

    weekly_rdd = (
        cleaned.select("Name", "date", "open", "high", "low", "close", "volume")
        .rdd.map(lambda row: (row["Name"], row.asDict()))
        .groupByKey()
        .flatMap(build_partition)
        .cache()
    )
    # One number is collected so the training median can be reused. The daily
    # price table and the weekly table stay on the executors.
    training_vols = (
        weekly_rdd.filter(lambda row: row["ready"] and row["split"] == "train" and row["vol_52w"] is not None)
        .map(lambda row: row["vol_52w"])
        .collect()
    )
    median = statistics.median(training_vols)

    def fill_vol_52(row):
        filled = dict(row)
        filled["vol_52w_imputed"] = int(filled["vol_52w"] is None)
        if filled["vol_52w"] is None:
            filled["vol_52w"] = median
        return filled

    ready = weekly_rdd.map(fill_vol_52).filter(lambda row: row["ready"]).map(
        lambda row: {key: row[key] for key in row if key not in ("ready", "exclusion")}
    )
    weekly = spark.createDataFrame(ready).cache()
    weekly.count()
    for split in ("train", "validation", "test"):
        weekly.filter(F.col("split") == split).write.mode("overwrite").parquet(f"{OUT_BASE}/weekly_{split}")
    weekly.write.mode("overwrite").parquet(f"{OUT_BASE}/weekly_all")
    print("vol_52w_training_median", median)
    spark.stop()


if __name__ == "__main__":
    main()
