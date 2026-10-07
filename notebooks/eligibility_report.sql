-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Part E — eligibility_report (downstream consumer)
-- MAGIC Reads `gold_eligibility_summary` and references the **`member_count`** column. If an upstream
-- MAGIC schema change renames that column (the repair-run demo in Part E), this task fails with
-- MAGIC `UNRESOLVED_COLUMN`. Fix the column name here, then **Repair run** — `gold` is skipped and only
-- MAGIC this task + `notify` re-run.

-- COMMAND ----------

-- DBTITLE 1,Widget — set your schema
CREATE WIDGET TEXT schema DEFAULT 'firstname_lastname';

-- COMMAND ----------

CREATE OR REPLACE TABLE IDENTIFIER('`dev-sh-training`.' || :schema || '.eligibility_report') AS
SELECT
  line_of_business,
  sum(member_count)         AS members,
  count(DISTINCT plan_code) AS plans
FROM IDENTIFIER('`dev-sh-training`.' || :schema || '.gold_eligibility_summary')
GROUP BY line_of_business
ORDER BY members DESC;
