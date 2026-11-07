"""Q2 local preview: where is the model good or bad? (2017 test set)

Inputs : task3_outputs/reference_test_predictions  (symbol, anchor_date, prediction, label)
         task3_outputs/weekly_features             (adds vol_12w baseline and vol_52w)
Outputs: task4/outputs/q2_error_by_month.csv, q2_error_by_group.csv, two PNG charts
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------- Settings ----------
PRED_PATH = "task3_outputs/reference_test_predictions"
WEEKLY_PATH = "task3_outputs/weekly_features"
OUT_DIR = "task4/outputs"
TRAIN_END = "2016-01-01"
GROUP_LABELS = ["1_calm", "2_medium", "3_volatile"]


# ---------- 1. Load and join ----------
def load_data():
    pred = pd.read_parquet(PRED_PATH)
    wk = pd.read_parquet(WEEKLY_PATH)
    for df in (pred, wk):
        df["anchor_date"] = df["anchor_date"].astype(str)
    pred = pred.drop_duplicates(subset=["symbol", "anchor_date"])
    wk = wk.drop_duplicates(subset=["symbol", "anchor_date"])

    # Add the baseline (vol_12w) and long-run volatility (vol_52w) to each prediction
    m = pred.merge(wk[["symbol", "anchor_date", "vol_12w", "vol_52w", "label"]],
                   on=["symbol", "anchor_date"], how="left", suffixes=("", "_wk"))
    return m, wk


def run_sanity_checks(pred_rows, m):
    print("prediction rows:", pred_rows, "| after join:", len(m))
    print("missing vol_12w:", m["vol_12w"].isna().sum(),
          "| missing vol_52w:", m["vol_52w"].isna().sum())
    print("max label difference:", (m["label"] - m["label_wk"]).abs().max())


# ---------- 2. Add groups, month and errors ----------
def add_features(m, wk):
    # Cut-offs for calm / medium / volatile use vol_52w, which is known at prediction time.
    # They come from the 2017 spread (not from the 2017 outcome), because the
    # training-period cut-offs were bunched together by the filled-in median values.
    train = wk[wk["anchor_date"] < TRAIN_END]
    print("training cut-offs:", train["vol_52w"].quantile([1/3, 2/3]).round(5).tolist())
    lo, hi = m["vol_52w"].quantile([1/3, 2/3])
    print("2017 cut-offs:", round(lo, 5), round(hi, 5))

    m["group"] = pd.cut(m["vol_52w"], [-np.inf, lo, hi, np.inf], labels=GROUP_LABELS)
    m["month"] = pd.to_datetime(m["anchor_date"]).dt.to_period("M").astype(str)
    m["all"] = "all 2017 rows"

    m["se_model"] = (m["prediction"] - m["label"]) ** 2
    m["se_base"] = (m["vol_12w"] - m["label"]) ** 2
    m["ae_model"] = (m["prediction"] - m["label"]).abs()
    m["ae_base"] = (m["vol_12w"] - m["label"]).abs()
    return m.dropna(subset=["vol_12w"])


# ---------- 3. Error summary ----------
def summarise(m, by):
    g = m.groupby(by, observed=True)
    return pd.DataFrame({
        "n": g.size(),
        "rmse_model": np.sqrt(g["se_model"].mean()),
        "rmse_base": np.sqrt(g["se_base"].mean()),
        "mae_model": g["ae_model"].mean(),
        "mae_base": g["ae_base"].mean(),
    }).round(5)


# ---------- 4. Charts ----------
def plot_by_month(by_month):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(by_month.index, by_month["rmse_model"], marker="o", label="Model (linear regression)")
    ax.plot(by_month.index, by_month["rmse_base"], marker="o", label="Baseline (12-week average)")
    ax.set_xlabel("Month (2017)")
    ax.set_ylabel("RMSE of next-week volatility")
    ax.set_title("Q2: Prediction error by month, 2017 test set")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/q2_chart_by_month.png", dpi=150)
    plt.show()


def plot_by_group(by_group):
    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(by_group))
    w = 0.38
    ax.bar([i - w / 2 for i in x], by_group["rmse_model"], w, label="Model")
    ax.bar([i + w / 2 for i in x], by_group["rmse_base"], w, label="Baseline")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{g}\n(n = {n:,})" for g, n in zip(by_group.index, by_group["n"])])
    ax.set_ylabel("RMSE of next-week volatility")
    ax.set_title("Q2: Prediction error by stock volatility group, 2017")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/q2_chart_by_group.png", dpi=150)
    plt.show()


# ---------- Run everything ----------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    pd.set_option("display.width", 200)

    m, wk = load_data()
    run_sanity_checks(len(m), m)
    m = add_features(m, wk)

    overall = summarise(m, "all")
    by_month = summarise(m, "month")
    by_group = summarise(m, "group")
    print("\nOVERALL\n", overall)
    print("\nBY MONTH\n", by_month)
    print("\nBY GROUP\n", by_group)

    by_month.to_csv(f"{OUT_DIR}/q2_error_by_month.csv")
    by_group.to_csv(f"{OUT_DIR}/q2_error_by_group.csv")
    plot_by_month(by_month)
    plot_by_group(by_group)


if __name__ == "__main__":
    main()