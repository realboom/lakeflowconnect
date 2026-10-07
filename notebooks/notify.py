# Databricks notebook source
# MAGIC %md
# MAGIC # Part E — notify (demo placeholder)
# MAGIC Placeholder for an email / Slack / webhook notification. The `result` parameter is set by the
# MAGIC job task — `pass` on the success branch, `fail` on the `AT_LEAST_ONE_FAILED` branch.

# COMMAND ----------

# DBTITLE 1,Widget
dbutils.widgets.text("result", "pass", "Run result")

# COMMAND ----------

r = dbutils.widgets.get("result")
msg = f"NOTIFY: eligibility pipeline run {r.upper()} — downstream consumers notified (demo placeholder for email/Slack/webhook)."
print(msg)
dbutils.notebook.exit(msg)
