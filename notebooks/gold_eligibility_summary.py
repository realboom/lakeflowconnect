# Databricks notebook source
# MAGIC %md
# MAGIC # Part E — gold_eligibility_summary
# MAGIC Aggregates `silver_eligibility` into a per-LOB / per-plan summary. In the repair-run demo this
# MAGIC is the **expensive upstream** task: it succeeds, and on a **Repair run** it is **skipped**
# MAGIC while the failed downstream task re-runs.
# MAGIC
# MAGIC **Schema-drift demo:** rename the `member_count` column below to `enrolled_members`, save, and
# MAGIC re-run the job — `gold` succeeds with the new name, but the downstream `eligibility_report`
# MAGIC (which still selects `member_count`) fails with UNRESOLVED_COLUMN.

# COMMAND ----------

# DBTITLE 1,Widget — set your schema
dbutils.widgets.text("schema", "firstname_lastname", "Your schema name")

# COMMAND ----------

CATALOG = "dev-sh-training"
schema = dbutils.widgets.get("schema").strip()
assert schema and schema != "firstname_lastname", "Set the 'schema' widget first."

spark.sql(f"""
CREATE OR REPLACE TABLE `{CATALOG}`.`{schema}`.gold_eligibility_summary AS
SELECT
  line_of_business,
  plan_code,
  count(*)                  AS member_count,
  count(DISTINCT member_id) AS distinct_members,
  min(eff_date)             AS earliest_eff
FROM `{CATALOG}`.`{schema}`.silver_eligibility
GROUP BY line_of_business, plan_code
""")
print("Built gold_eligibility_summary")
display(spark.table(f"`{CATALOG}`.`{schema}`.gold_eligibility_summary"))
