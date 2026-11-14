-- Task 2, Part B checks. Run after news_features.py. Paste the output into the report / Appendix B.

SELECT 'articles_2013_2017' AS check_name, COUNT(*) AS n FROM project.wikinews_articles;

SELECT 'articles_matched_to_a_ticker' AS check_name, COUNT(DISTINCT page_id) AS n FROM project.wikinews_matches;

SELECT 'article_ticker_pairs' AS check_name, COUNT(*) AS n FROM project.wikinews_matches;

SELECT substr(first_ts, 1, 4) AS yr, COUNT(*) AS articles FROM project.wikinews_articles
GROUP BY substr(first_ts, 1, 4) ORDER BY yr;

SELECT ticker, COUNT(*) AS articles FROM project.wikinews_matches
GROUP BY ticker ORDER BY articles DESC LIMIT 15;

-- Weekly tables must keep exactly the Part A row counts; news only adds a column.
SELECT a.`split`, a.n AS weekly_rows, b.n AS weekly_news_rows, b.with_news, b.total_news
FROM (SELECT `split`, COUNT(*) AS n FROM project.weekly_train GROUP BY `split`
      UNION ALL SELECT `split`, COUNT(*) FROM project.weekly_validation GROUP BY `split`
      UNION ALL SELECT `split`, COUNT(*) FROM project.weekly_test GROUP BY `split`) a
JOIN (SELECT `split`, COUNT(*) AS n, SUM(CASE WHEN news_count > 0 THEN 1 ELSE 0 END) AS with_news,
             SUM(news_count) AS total_news
      FROM project.weekly_news_all GROUP BY `split`) b
  ON a.`split` = b.`split`
ORDER BY a.`split`;
