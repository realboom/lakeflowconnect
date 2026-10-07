# Databricks notebook source
# MAGIC %md
# MAGIC # Part B / C — Auto Loader (mimics an SFTP landing)
# MAGIC Instead of pulling from a real SFTP server, we land the vendor's pipe-delimited files in a
# MAGIC Volume folder (`landing/sftp/incoming/`) and let **Auto Loader** (`cloudFiles`) ingest them
# MAGIC incrementally into `bronze_sftp_eligibility`.
# MAGIC
# MAGIC Auto Loader:
# MAGIC - tracks what it has already processed in a **checkpoint** (run it again → only new files),
# MAGIC - **evolves the schema** when a new column appears (Part C — schema evolution),
# MAGIC - **rescues** values that don't fit the type into `_rescued_data` (Part C — rescued data).
# MAGIC
# MAGIC This runs in **directory-listing** mode — no cloud file-notification setup required.

# COMMAND ----------

# DBTITLE 1,Widget — set your schema
dbutils.widgets.text("schema", "firstname_lastname", "Your schema name")

# COMMAND ----------

CATALOG = "dev-sh-training"
schema = dbutils.widgets.get("schema").strip()
assert schema and schema != "firstname_lastname", "Set the 'schema' widget first."

base = f"/Volumes/{CATALOG}/{schema}/landing/sftp"
tbl  = f"`{CATALOG}`.`{schema}`.bronze_sftp_eligibility"

q = (spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("sep", "|")
        .option("header", "true")
        .option("cloudFiles.schemaLocation", f"{base}/_autoloader/schema")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .option("cloudFiles.schemaHints", "eff_date DATE")   # typed -> bad values rescue instead of staying string
        .load(f"{base}/incoming/")
     .writeStream
        .option("checkpointLocation", f"{base}/_autoloader/checkpoint")
        .option("mergeSchema", "true")
        .trigger(availableNow=True)                          # process all available files, then stop
        .toTable(f"{CATALOG}.`{schema}`.bronze_sftp_eligibility"))
q.awaitTermination()
print("Auto Loader run complete.")

# COMMAND ----------

# MAGIC %md
# MAGIC **Part C note — schema evolution:** when a file with a new column (e.g. `risk_tier`) arrives,
# MAGIC Auto Loader stops once to record the new column, then succeeds. If the cell above errors with
# MAGIC an *unknown field* / schema-change message, just **run it again** — the new column is now in
# MAGIC the schema and the data loads. (In Part E this handshake is handled automatically by a task
# MAGIC **retry**.)

# COMMAND ----------

# DBTITLE 1,Check what landed (risk_tier after schema evolution, _rescued_data after rescued-data)
display(spark.sql(f"SELECT * FROM {tbl} ORDER BY member_id LIMIT 20"))

# COMMAND ----------

# DBTITLE 1,Rescued rows (populated after the Part C rescued-data scenario)
display(spark.sql(f"SELECT member_id, eff_date, _rescued_data FROM {tbl} WHERE _rescued_data IS NOT NULL LIMIT 10"))
