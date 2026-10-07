-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Part E — silver_eligibility (Spark Declarative Pipeline source)
-- MAGIC A **streaming table** that incrementally cleans the Auto Loader bronze — upserts/append with
-- MAGIC no reload. This file is the **source for a pipeline you create in Part E** (do not "Run" it
-- MAGIC like a normal notebook).
-- MAGIC
-- MAGIC When you create the pipeline, set:
-- MAGIC - **Catalog** = `dev-sh-training`, **Schema (target)** = your schema
-- MAGIC - a pipeline **Configuration** key `schema` = your schema  (referenced as `${schema}` below)

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
FROM STREAM `dev-sh-training`.`${schema}`.bronze_sftp_eligibility;
