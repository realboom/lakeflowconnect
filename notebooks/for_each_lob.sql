-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Part E — for_each_lob (nested task)
-- MAGIC Runs **once per line of business** (fan-out from a For each task). Writes a per-LOB extract
-- MAGIC table `gold_elig_<lob>`. In the For each task, set the nested task's parameters
-- MAGIC `schema` = your schema and **`lob` = `{{input}}`**.
-- MAGIC
-- MAGIC (`:lob` filters the rows; `IDENTIFIER()` builds the per-LOB table name from it.)

-- COMMAND ----------

-- DBTITLE 1,Widgets
CREATE WIDGET TEXT schema DEFAULT 'firstname_lastname';
CREATE WIDGET TEXT lob DEFAULT 'Commercial';

-- COMMAND ----------

CREATE OR REPLACE TABLE
  IDENTIFIER('`dev-sh-training`.' || :schema || '.gold_elig_' || replace(lower(:lob), ' ', '_')) AS
SELECT * FROM IDENTIFIER('`dev-sh-training`.' || :schema || '.silver_eligibility')
WHERE line_of_business = :lob;
