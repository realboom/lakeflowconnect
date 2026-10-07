-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Part E (level-up) — silver_eligibility_current via AUTO CDC (upsert by member_id)
-- MAGIC The E1 `silver_eligibility` table is **append-only** — re-send a member and you get a *second* row.
-- MAGIC A "current state" table (like eligibility) usually wants **one row per member, updated in place**.
-- MAGIC
-- MAGIC Databricks does this with **AUTO CDC** (the SQL `APPLY CHANGES` pattern): you declare the **key**
-- MAGIC and a **sequence**, and Databricks writes the insert-or-update MERGE for you — no hand-coded MERGE,
-- MAGIC no full reload. When the same `member_id` arrives again, the existing row is **updated** (latest
-- MAGIC wins), not duplicated.
-- MAGIC
-- MAGIC Paste this into its **own** ETL Pipeline, set up exactly like E1 (default catalog `dev-sh-training`
-- MAGIC + your schema, Serverless). Unqualified names resolve to your schema.
-- MAGIC
-- MAGIC The three pieces to notice:
-- MAGIC - **KEYS (member_id)** — the business key to match/dedupe on.
-- MAGIC - **SEQUENCE BY ingested_at** — how to pick the latest when a key repeats (newest ingest wins).
-- MAGIC - **AUTO CDC INTO** — Databricks runs the MERGE; you just declare intent.

-- COMMAND ----------

-- DBTITLE 1,Target table (declared empty; the AUTO CDC flow below populates it)
CREATE OR REFRESH STREAMING TABLE silver_eligibility_current
COMMENT 'Current eligibility — one upserted row per member_id (AUTO CDC / APPLY CHANGES)';

-- COMMAND ----------

-- DBTITLE 1,Streaming view: clean bronze and stamp each row with its ingest time (the sequence)
CREATE TEMPORARY VIEW eligibility_changes AS
SELECT
  member_id,
  initcap(first_name)         AS first_name,
  initcap(last_name)          AS last_name,
  plan_code,
  line_of_business,
  try_cast(eff_date  AS DATE) AS eff_date,
  try_cast(term_date AS DATE) AS term_date,
  current_timestamp()         AS ingested_at
FROM STREAM bronze_sftp_eligibility;

-- COMMAND ----------

-- DBTITLE 1,Upsert by member_id (newest ingest wins). No deletes — an eligibility file feed has none.
CREATE FLOW silver_eligibility_upsert AS AUTO CDC INTO silver_eligibility_current
FROM STREAM eligibility_changes
  KEYS (member_id)
  SEQUENCE BY ingested_at;
