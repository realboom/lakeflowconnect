-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Part E (validation) — silver_eligibility_current_audit (CDF: what each run changed)
-- MAGIC After an AUTO CDC run, the pipeline shows row **counts**, not rows — so it's easy to think
-- MAGIC "nothing happened." This notebook reads the target table's **Change Data Feed (CDF)** so you can
-- MAGIC actually *see* what each run did: how many **inserts** vs. **updates** landed, grouped by commit
-- MAGIC version (≈ one pipeline run).
-- MAGIC
-- MAGIC `_change_type` is one of: `insert` | `update_preimage` | `update_postimage` | `delete`.
-- MAGIC We drop `update_preimage` (the "before" image of an updated row) so each change counts once.
-- MAGIC
-- MAGIC **Prerequisite — CDF must be enabled on `silver_eligibility_current`.** If you see
-- MAGIC *"Change data feed is not enabled on table…"*, add
-- MAGIC `TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')` to the
-- MAGIC `CREATE OR REFRESH STREAMING TABLE silver_eligibility_current` in `silver_eligibility_scd`, then
-- MAGIC **full refresh** that pipeline and re-run the member-update step.
-- MAGIC
-- MAGIC **Run the first cell** to expose the `schema` widget, set it to your schema, then **Run all**.

-- COMMAND ----------

-- DBTITLE 1,Widget — set your schema, then run the rest
CREATE WIDGET TEXT schema DEFAULT 'firstname_lastname';

-- COMMAND ----------

-- DBTITLE 1,Point the session at your schema (table_changes needs a resolvable table name)
USE CATALOG `dev-sh-training`;
USE SCHEMA IDENTIFIER(:schema);

-- COMMAND ----------

-- DBTITLE 1,What changed, per run (commit version)
-- _change_type is one of: insert | update_preimage | update_postimage | delete
-- If this errors "CDF not enabled for version 0", the table predates CDF being turned on —
-- start from a later version or a timestamp, e.g. table_changes('silver_eligibility_current', timestamp '2026-10-06').
SELECT _change_type, _commit_version, COUNT(*) AS record_count
FROM table_changes('silver_eligibility_current', 1)
WHERE _change_type <> 'update_preimage'
GROUP BY _change_type, _commit_version
ORDER BY _commit_version DESC, _change_type;
