-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Part A — COPY INTO (batch file ingestion)
-- MAGIC `COPY INTO` loads **new** files from your `filedrop` landing folder into a bronze table.
-- MAGIC It is **idempotent** — re-running skips files it already loaded (tracked in Delta history),
-- MAGIC so you can run it on a schedule or on demand and never double-load.
-- MAGIC
-- MAGIC Set the **schema** widget to your schema, then Run all. (Generate data first with
-- MAGIC `generate_data` → scenario *Part A*.)

-- COMMAND ----------

-- DBTITLE 1,Widget — set your schema
CREATE WIDGET TEXT schema DEFAULT 'firstname_lastname';

-- COMMAND ----------

-- DBTITLE 1,Create the bronze table if it doesn't exist yet
CREATE TABLE IF NOT EXISTS `dev-sh-training`.`${schema}`.bronze_file_eligibility (
  member_id       STRING,
  first_name      STRING,
  last_name       STRING,
  plan            STRING,
  line_of_business STRING,
  effective_date  STRING
);

-- COMMAND ----------

-- DBTITLE 1,COPY INTO — loads only files not yet loaded
COPY INTO `dev-sh-training`.`${schema}`.bronze_file_eligibility
FROM '/Volumes/dev-sh-training/${schema}/landing/filedrop/incoming/'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true')
COPY_OPTIONS ('mergeSchema' = 'true');

-- COMMAND ----------

-- DBTITLE 1,Check what landed (run COPY INTO again — it loads nothing new = idempotent)
SELECT line_of_business, count(*) AS rows
FROM `dev-sh-training`.`${schema}`.bronze_file_eligibility
GROUP BY line_of_business
ORDER BY rows DESC;
