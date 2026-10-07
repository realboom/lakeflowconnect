-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Part E — gold_eligibility_summary
-- MAGIC Aggregates `silver_eligibility` into a per-LOB / per-plan summary. In the repair-run demo this
-- MAGIC is the **expensive upstream** task: it succeeds, and on a **Repair run** it is **skipped**
-- MAGIC while the failed downstream task re-runs.
-- MAGIC
-- MAGIC **Schema-drift demo:** rename the `member_count` column below to `enrolled_members`, save, and
-- MAGIC re-run the job — `gold` succeeds with the new name, but the downstream `eligibility_report`
-- MAGIC (which still selects `member_count`) fails with `UNRESOLVED_COLUMN`.
-- MAGIC
-- MAGIC **Run the first cell** to expose the `schema` widget, set it, then **Run all**.
-- MAGIC (`:schema` is substituted from the widget; `IDENTIFIER()` turns it into the table name.)

-- COMMAND ----------

-- DBTITLE 1,Widget — set your schema, then run the rest
CREATE WIDGET TEXT schema DEFAULT 'firstname_lastname';

-- COMMAND ----------

-- DBTITLE 1,Build the gold summary from silver
CREATE OR REPLACE TABLE IDENTIFIER('`dev-sh-training`.' || :schema || '.gold_eligibility_summary') AS
SELECT
  line_of_business,
  plan_code,
  count(*)                  AS member_count,
  count(DISTINCT member_id) AS distinct_members,
  min(eff_date)             AS earliest_eff
FROM IDENTIFIER('`dev-sh-training`.' || :schema || '.silver_eligibility')
GROUP BY line_of_business, plan_code;

-- COMMAND ----------

-- DBTITLE 1,Check it
SELECT * FROM IDENTIFIER('`dev-sh-training`.' || :schema || '.gold_eligibility_summary')
ORDER BY member_count DESC;
