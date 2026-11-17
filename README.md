# INF2006 Big Data Project

Predicting next-week stock volatility for 505 S&P 500 stocks (2013–2017) from daily prices and English Wikinews, built on AWS EMR with Hadoop Streaming, HDFS, Hive and PySpark.

## Assessed notebooks (run on EMR)
| File | What it is |
|---|---|
| `task5_pipeline.ipynb` | The whole pipeline: Task 2 (Streaming, Hive, Spark for prices and Wikinews) → Task 3 (models, test, saved model) → Task 4 (Q1–Q3) → run record. Exported from EMR with outputs (run `full_reference_r4`). |
| `task5_reload_check.ipynb` | Fresh-session reload of the saved model: PASS, 2026-11-16. |

Setup, data download and run order are in Appendix A of `report.pdf`.

## Folders
| Folder | Contents |
|---|---|
| `task1_outputs/` | Raw-file inventory, data dictionary, quality summaries (Task 1) |
| `task2/` | Hadoop Streaming mappers/reducers, Hive SQL, PySpark jobs, company-name list (Task 2) |
| `task4/` | Readable copies of the Q1–Q3 SQL, and the charts and result tables (Task 4) |
| `task5/` | Cluster configuration JSON and the sample-making scripts |
| `task5_outputs/` | All EMR run evidence: run records, logs, timings, saved models, input checksums (see `task5_outputs/README.md`) |

## Development history (not the assessed run)
`task1.ipynb` (local price audit and GDELT assessment; its EMR acquisition record is in Sections 9–11), `task2.ipynb`, `task3_volatility.ipynb` and `task4_analytics.ipynb` are the members' development notebooks, written before the final EMR run. Their outputs are cleared or were produced locally. The assessed results are the ones in the two notebooks above. `archive/` holds superseded runs and files.

## Not included
Raw datasets (downloaded and checked by the steps in Appendix A) and credentials.