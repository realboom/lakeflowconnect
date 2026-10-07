-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Part E — silver_eligibility (ETL Pipeline / Spark Declarative Pipeline source)
-- MAGIC A **streaming table** that incrementally cleans the Auto Loader bronze — append/upsert, no reload.
-- MAGIC
-- MAGIC **This is the SQL you paste into the pipeline file in E1.** It uses **unqualified** table names
-- MAGIC (just `bronze_sftp_eligibility`, not `catalog.schema.table`). Unqualified names resolve against
-- MAGIC the pipeline's **default catalog** (`dev-sh-training`) and **default schema** (your schema),
-- MAGIC which you set in the pipeline before running. That's how each person's pipeline reads their own
-- MAGIC bronze and writes their own silver with the exact same code — no hard-coded names, no backticks.

-- COMMAND ----------

CREATE OR REFRESH STREAMING TABLE silver_eligibility
COMMENT 'Cleaned eligibility, streamed incrementally from the Auto Loader bronze (no reload)'
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
