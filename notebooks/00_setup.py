# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Setup: your schema + landing volume
# MAGIC Run this **first**. It creates your personal schema in the `dev-sh-training` catalog and a
# MAGIC `landing` volume with the subfolders the lab uses.
# MAGIC
# MAGIC Set the **schema** widget to your own name — letters, numbers, underscores only
# MAGIC (e.g. `jane_doe`). Everyone works in their own schema; the catalog is shared.

# COMMAND ----------

# DBTITLE 1,Widget — set your schema name, then run the rest
dbutils.widgets.text("schema", "firstname_lastname", "Your schema name")

# COMMAND ----------

CATALOG = "dev-sh-training"
schema = dbutils.widgets.get("schema").strip()
assert schema and schema != "firstname_lastname", "Set the 'schema' widget to your own name first."

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{schema}`")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`{schema}`.landing")

base = f"/Volumes/{CATALOG}/{schema}/landing"
for sub in ["filedrop/incoming", "sftp/incoming", "sftp/_autoloader"]:
    dbutils.fs.mkdirs(f"{base}/{sub}")

print(f"Ready: catalog={CATALOG}, schema={schema}")
print(f"  Part A  file drops  -> {base}/filedrop/incoming/")
print(f"  Part B/C SFTP drops -> {base}/sftp/incoming/")
display(spark.sql(f"SHOW VOLUMES IN `{CATALOG}`.`{schema}`"))
