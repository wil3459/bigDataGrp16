-- Row-count checks. The three counts at the bottom must add up to the raw count.

SELECT 'raw_rows' AS check_name, COUNT(*) AS row_count FROM project.prices_raw;

SELECT 'cleaned_rows' AS check_name, COUNT(*) AS row_count FROM project.prices_cleaned
WHERE status = 'accepted';

SELECT 'rejected_rows' AS check_name, COUNT(*) AS row_count FROM project.prices_rejected;

SELECT reasons, COUNT(*) AS row_count
FROM project.prices_rejected
GROUP BY reasons
ORDER BY row_count DESC;

SELECT `split`, COUNT(*) AS row_count, MIN(anchor_date) AS first_anchor, MAX(anchor_date) AS last_anchor
FROM project.weekly_all
GROUP BY `split`
ORDER BY `split`;
