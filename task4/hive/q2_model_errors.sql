-- Q2: Where is the model most and least reliable? (2017 test set)
-- Readable copy. The notebook (task4_analytics.ipynb) runs the same SQL inside its cells.
-- Inputs : predictions (view over Task 3's test predictions: symbol, anchor_date, prediction, label)
--          project.weekly_all (adds the baseline vol_12w and the stock's vol_52w)
-- Calm / medium / volatile = three equal-sized groups by vol_52w, a feature known
-- at prediction time. The 2017 actual outcome is not used to form the groups.

CREATE OR REPLACE TEMPORARY VIEW q2_base AS
WITH pred AS (
  SELECT DISTINCT symbol, CAST(anchor_date AS STRING) AS anchor_date, prediction, label
  FROM predictions
)
SELECT p.symbol,
       substr(p.anchor_date, 1, 7)  AS month,
       p.prediction,
       p.label,
       w.vol_12w                    AS baseline,
       NTILE(3) OVER (ORDER BY w.vol_52w) AS grp
FROM pred p
JOIN project.weekly_all w
  ON p.symbol = w.ticker
 AND p.anchor_date = CAST(w.anchor_date AS STRING);

-- Error by month
SELECT month,
       COUNT(*)                                           AS n,
       SQRT(AVG(POW(prediction - label, 2)))              AS rmse_model,
       SQRT(AVG(POW(baseline   - label, 2)))              AS rmse_base,
       AVG(ABS(prediction - label))                       AS mae_model,
       AVG(ABS(baseline   - label))                       AS mae_base
FROM q2_base
GROUP BY month
ORDER BY month;

-- Error by calm / medium / volatile group
SELECT CASE grp WHEN 1 THEN '1_calm' WHEN 2 THEN '2_medium' ELSE '3_volatile' END AS grp_name,
       COUNT(*)                                           AS n,
       SQRT(AVG(POW(prediction - label, 2)))              AS rmse_model,
       SQRT(AVG(POW(baseline   - label, 2)))              AS rmse_base,
       AVG(ABS(prediction - label))                       AS mae_model,
       AVG(ABS(baseline   - label))                       AS mae_base
FROM q2_base
GROUP BY grp
ORDER BY grp;
