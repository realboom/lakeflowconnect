-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Part E — silver_eligibility (ETL Pipeline / Spark Declarative Pipeline source)
-- MAGIC A **streaming table** that cleans the Auto Loader bronze **incrementally** — it processes only the
-- MAGIC *new* rows from the bronze stream each run and **appends** them (append-only; no full reload).
-- MAGIC It does **not** upsert or delete — that would need `AUTO CDC` / `APPLY CHANGES` with `KEYS(...)`
-- MAGIC and a sequence column (used when the source is a CDC feed, not an append feed like this one).
-- MAGIC
-- MAGIC **This is the SQL you paste into the pipeline file in E1.** It uses **unqualified** table names
-- MAGIC (just `bronze_sftp_eligibility`, not `catalog.schema.table`). Unqualified names resolve against
-- MAGIC the pipeline's **default catalog** (`dev-sh-training`) and **default schema** (your schema),
-- MAGIC which you set in the pipeline before running. That's how each person's pipeline reads their own
-- MAGIC bronze and writes their own silver with the exact same code — no hard-coded names, no backticks.

-- COMMAND ----------

CREATE OR REFRESH STREAMING TABLE silver_eligibility
COMMENT 'Cleaned eligibility — incrementally appends new rows from the Auto Loader bronze stream (append-only, no reload)'
AS SELECT
  member_id,
  initcap(first_name)         AS first_name,
  initcap(last_name)          AS last_name,
  plan_code,
  line_of_business,
  try_cast(eff_date  AS DATE) AS eff_date,
  try_cast(term_date AS DATE) AS term_date,
  current_timestamp()         AS silver_loaded_at
FROM STREAM bronze_sftp_eligibility;
