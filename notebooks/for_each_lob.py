# Databricks notebook source
# MAGIC %md
# MAGIC # Part E — for_each_lob (nested task)
# MAGIC Runs **once per line of business** (fan-out from a For each task). Writes a per-LOB extract
# MAGIC table `gold_elig_<lob>`. The For each task passes the LOB via the `lob` parameter — set the
# MAGIC nested task's parameter `lob` = `{{input}}`.

# COMMAND ----------

# DBTITLE 1,Widgets
dbutils.widgets.text("schema", "firstname_lastname", "Your schema name")
dbutils.widgets.text("lob", "Commercial", "Line of business")

# COMMAND ----------

CATALOG = "dev-sh-training"
schema = dbutils.widgets.get("schema").strip()
lob = dbutils.widgets.get("lob").strip()
assert schema and schema != "firstname_lastname", "Set the 'schema' widget first."

safe = lob.lower().replace(" ", "_")
spark.sql(f"""
CREATE OR REPLACE TABLE `{CATALOG}`.`{schema}`.gold_elig_{safe} AS
SELECT * FROM `{CATALOG}`.`{schema}`.silver_eligibility
WHERE line_of_business = '{lob}'
""")
print(f"Built gold_elig_{safe} for line_of_business = {lob}")
