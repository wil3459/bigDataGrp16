-- Q1: Is unusually high trading volume associated with higher same-day volatility?
-- Input: project.prices_cleaned. Volume ratio = volume / that stock's average of the previous 20 days.

WITH base AS (
  SELECT ticker,
         to_date(trade_date)        AS d,
         CAST(high AS DOUBLE)       AS h,
         CAST(low AS DOUBLE)        AS l,
         CAST(close AS DOUBLE)      AS c,
         CAST(volume AS DOUBLE)     AS v
  FROM project.prices_cleaned
  WHERE status = 'accepted'
),
ratio AS (
  SELECT ticker, d, (h - l) / c AS day_range,
         v / AVG(v) OVER (PARTITION BY ticker ORDER BY d
                          ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) AS vol_ratio,
         COUNT(*) OVER (PARTITION BY ticker ORDER BY d
                        ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) AS n_hist
  FROM base
)
SELECT CASE WHEN vol_ratio < 1.5 THEN '1_normal (<1.5x)'
            WHEN vol_ratio < 2.5 THEN '2_high (1.5-2.5x)'
            ELSE '3_very_high (>2.5x)' END AS bucket,
       COUNT(*)                          AS n_rows,
       AVG(day_range)                    AS avg_day_range,
       percentile_approx(day_range, 0.5) AS median_day_range
FROM ratio
WHERE n_hist = 20 AND vol_ratio IS NOT NULL
GROUP BY CASE WHEN vol_ratio < 1.5 THEN '1_normal (<1.5x)'
              WHEN vol_ratio < 2.5 THEN '2_high (1.5-2.5x)'
              ELSE '3_very_high (>2.5x)' END
ORDER BY bucket;