# Databricks notebook source
# MAGIC %md
# MAGIC # Part A — COPY INTO (batch file ingestion)
# MAGIC `COPY INTO` loads **new** files from your `filedrop` landing folder into a bronze table. It is
# MAGIC **idempotent** — re-running skips files it already loaded (tracked in Delta history), so you
# MAGIC can run it on a schedule or on demand and never double-load.
# MAGIC
# MAGIC **Run the first cell** to expose the `schema` widget, set it to your schema, then **Run all**.
# MAGIC (Generate data first with `generate_data` → scenario *Part A*.)

# COMMAND ----------

# DBTITLE 1,Widget — set your schema, then run the rest
dbutils.widgets.text("schema", "firstname_lastname", "Your schema name")

# COMMAND ----------

CATALOG = "dev-sh-training"
schema = dbutils.widgets.get("schema").strip()
assert schema and schema != "firstname_lastname", "Set the 'schema' widget first."

tbl = f"`{CATALOG}`.`{schema}`.bronze_file_eligibility"
src = f"/Volumes/{CATALOG}/{schema}/landing/filedrop/incoming/"

# COMMAND ----------

# DBTITLE 1,Create the bronze table if it doesn't exist yet
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {tbl} (
  member_id        STRING,
  first_name       STRING,
  last_name        STRING,
  plan             STRING,
  line_of_business STRING,
  effective_date   STRING
)
""")

# COMMAND ----------

# DBTITLE 1,COPY INTO — loads only files not yet loaded
# Re-run this cell and num_inserted_rows = 0 -> that's idempotency (it remembers what it loaded).
result = spark.sql(f"""
COPY INTO {tbl}
FROM '{src}'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'true')
COPY_OPTIONS ('mergeSchema' = 'true')
""")
display(result)

# COMMAND ----------

# DBTITLE 1,Check what landed
display(spark.sql(f"SELECT line_of_business, count(*) AS rows FROM {tbl} GROUP BY line_of_business ORDER BY rows DESC"))
