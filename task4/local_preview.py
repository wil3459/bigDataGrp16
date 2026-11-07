import pandas as pd

# Check the file name in the dataset folder and change it if it's different
df = pd.read_csv("dataset/all_stocks_5yr.csv")

# Simple cleaning (the real cleaning is done in Task 2)
df = df.dropna(subset=["open", "high", "low", "close", "volume"])
df = df[(df["volume"] > 0) & (df["high"] >= df["low"]) & (df["close"] > 0)]
df["date"] = pd.to_datetime(df["date"])
df = df[df["date"] <= "2017-12-29"]
df = df.sort_values(["Name", "date"])

# Same-day volatility, and volume vs the stock's own previous 20 days
df["day_range"] = (df["high"] - df["low"]) / df["close"]
prev_avg = df.groupby("Name")["volume"].transform(
    lambda s: s.shift(1).rolling(20).mean())
df["vol_ratio"] = df["volume"] / prev_avg
df = df.dropna(subset=["vol_ratio"])

# Same buckets as the SQL
df["bucket"] = pd.cut(df["vol_ratio"], [0, 1.5, 2.5, float("inf")],
                      labels=["1_normal (<1.5x)", "2_high (1.5-2.5x)", "3_very_high (>2.5x)"],
                      right=False)

result = df.groupby("bucket", observed=True)["day_range"].agg(
    n_rows="count", avg_day_range="mean", median_day_range="median")
print(result)