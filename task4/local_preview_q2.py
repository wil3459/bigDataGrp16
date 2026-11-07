import numpy as np
import pandas as pd

pred = pd.read_parquet("task3_outputs/reference_test_predictions")
wk = pd.read_parquet("task3_outputs/weekly_features")
pred["anchor_date"] = pred["anchor_date"].astype(str)
wk["anchor_date"] = wk["anchor_date"].astype(str)

# Join the baseline (vol_12w) and the stock's long-run volatility (vol_52w)
m = pred.merge(wk[["symbol", "anchor_date", "vol_12w", "vol_52w", "label"]],
               on=["symbol", "anchor_date"], how="left", suffixes=("", "_wk"))

# Sanity checks
print("prediction rows:", len(pred), "| after join:", len(m))
print("missing vol_12w:", m["vol_12w"].isna().sum(),
      "| missing vol_52w:", m["vol_52w"].isna().sum())
print("max label difference:", (m["label"] - m["label_wk"]).abs().max())

# Calm / medium / volatile, cut-offs taken from TRAINING years only (before 2016)
train = wk[wk["anchor_date"] < "2016-01-01"]
print("training cut-offs:", train["vol_52w"].quantile([1/3, 2/3]).round(5).tolist())
lo, hi = m["vol_52w"].quantile([1/3, 2/3])
print("2017 cut-offs:", round(lo, 5), round(hi, 5))
m["group"] = pd.cut(m["vol_52w"], [-np.inf, lo, hi, np.inf],
                    labels=["1_calm", "2_medium", "3_volatile"])
m["month"] = pd.to_datetime(m["anchor_date"]).dt.to_period("M").astype(str)

# Squared and absolute errors for the model and the baseline
m["se_model"] = (m["prediction"] - m["label"]) ** 2
m["se_base"] = (m["vol_12w"] - m["label"]) ** 2
m["ae_model"] = (m["prediction"] - m["label"]).abs()
m["ae_base"] = (m["vol_12w"] - m["label"]).abs()
m = m.dropna(subset=["vol_12w"])

def summarise(by):
    g = m.groupby(by, observed=True)
    out = pd.DataFrame({
        "n": g.size(),
        "rmse_model": np.sqrt(g["se_model"].mean()),
        "rmse_base": np.sqrt(g["se_base"].mean()),
        "mae_model": g["ae_model"].mean(),
        "mae_base": g["ae_base"].mean(),
    })
    return out.round(5)

pd.set_option("display.width", 200)
m["all"] = "all 2017 rows"
print("\nOVERALL\n", summarise("all"))
print("\nBY MONTH\n", summarise("month"))
print("\nBY GROUP\n", summarise("group"))