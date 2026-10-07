# Databricks notebook source
# MAGIC %md
# MAGIC # Reset your lab
# MAGIC Cleans the landing files, clears the Auto Loader checkpoint, and drops the lab tables so you
# MAGIC can start the scenarios fresh. It does **not** drop your schema or volume.

# COMMAND ----------

# DBTITLE 1,Widget
dbutils.widgets.text("schema", "firstname_lastname", "Your schema name")

# COMMAND ----------

CATALOG = "dev-sh-training"
schema = dbutils.widgets.get("schema").strip()
assert schema and schema != "firstname_lastname", "Set the 'schema' widget first."
base = f"/Volumes/{CATALOG}/{schema}/landing"

for t in ["bronze_file_eligibility", "bronze_sftp_eligibility", "silver_eligibility",
          "gold_eligibility_summary", "eligibility_report"]:
    spark.sql(f"DROP TABLE IF EXISTS `{CATALOG}`.`{schema}`.{t}")

# drop the per-LOB for-each outputs
for r in spark.sql(f"SHOW TABLES IN `{CATALOG}`.`{schema}`").collect():
    if r.tableName.startswith("gold_elig_"):
        spark.sql(f"DROP TABLE IF EXISTS `{CATALOG}`.`{schema}`.{r.tableName}")

for sub in ["filedrop/incoming", "sftp/incoming", "sftp/_autoloader"]:
    try:
        dbutils.fs.rm(f"{base}/{sub}", recurse=True)
    except Exception as e:
        print(e)
    dbutils.fs.mkdirs(f"{base}/{sub}")

print("Reset complete. Re-run generate_data to start again.")
