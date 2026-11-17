-- Q3: next-week volatility after weeks with 0, 1 or 2+ Wikinews articles (2013-2017, all splits)
-- Input: project.weekly_news_all
SELECT CASE WHEN news_count = 0 THEN '1_none (0)'
            WHEN news_count = 1 THEN '2_one (1)'
            ELSE '3_several (2+)' END                    AS news_group,
       COUNT(*)                                          AS n_weeks,
       COUNT(DISTINCT ticker)                            AS n_stocks,
       AVG(target_next_vol)                              AS avg_next_vol,
       percentile_approx(target_next_vol, 0.5)           AS median_next_vol,
       AVG(target_next_vol / vol_12w)                    AS avg_vs_own_12w,
       percentile_approx(target_next_vol / vol_12w, 0.5) AS median_vs_own_12w
FROM project.weekly_news_all
WHERE target_next_vol IS NOT NULL AND vol_12w > 0
GROUP BY CASE WHEN news_count = 0 THEN '1_none (0)'
              WHEN news_count = 1 THEN '2_one (1)'
              ELSE '3_several (2+)' END
ORDER BY news_group;