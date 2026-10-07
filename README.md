# Lakeflow Connect & Orchestration — Hands-on Workshop

A self-paced, hands-on lab for **Lakeflow Connect** (file ingestion, Auto Loader, resilience) and
**Lakeflow Jobs/Pipelines** (orchestration). Every participant works in their **own schema** inside
the shared `dev-sh-training` catalog, so you can all run the lab at the same time without colliding.

## What you'll build

| Part | Topic | Tool |
|------|-------|------|
| **A** | Batch file ingestion from a Volume landing zone | `COPY INTO` |
| **B** | "SFTP" ingestion (mimicked on a Volume) | **Auto Loader** (`cloudFiles`) |
| **C** | Resilience: rescued data + schema evolution | Auto Loader options |
| **E** | Orchestration: pipeline, table-update trigger, DAG, repair, for-each, retries | **Lakeflow Pipelines + Jobs** |

> Part D (SQL Server managed connector / CDC) from the instructor demo is **not** part of this lab —
> it needs a source database and an ingestion gateway. Everything here runs on **serverless** with
> synthetic data you generate yourself.

## Prerequisites
- Access to the `dev-sh-training` catalog with permission to **create a schema** in it.
- A serverless SQL warehouse (for SQL cells) and serverless notebook compute.

## Setup (do this once)
1. **Add this repo as a Git folder.** In the Databricks workspace: **Workspace → Create → Git folder**,
   URL `https://github.com/realboom/lakeflowconnect`, and clone it into your user folder.
2. Open **`notebooks/00_setup`**, set the **`schema`** widget to your own name
   (letters/numbers/underscores, e.g. `jane_doe`), and **Run all**. This creates:
   - your schema `dev-sh-training.<you>`
   - a `landing` volume with `filedrop/` and `sftp/` subfolders.
3. Every notebook has a **`schema`** widget — set it to the same name each time.

## Then follow [LAB_GUIDE.md](./LAB_GUIDE.md)
A print-friendly **[LAB_GUIDE.pdf](./LAB_GUIDE.pdf)** is included for handouts.
It walks you through Parts A → B → C → E, including **how to create each pipeline and job by hand**
in the UI.

## Notebooks
| File | Purpose |
|------|---------|
| `00_setup` | Create your schema + landing volume (run first) |
| `generate_data` | Generate synthetic files for each scenario (widget: schema, scenario, num_rows) |
| `part_a_copy_into` | Part A — `COPY INTO` into `bronze_file_eligibility` |
| `part_b_autoloader` | Part B/C — Auto Loader into `bronze_sftp_eligibility` |
| `silver_eligibility` | Part E — pipeline source for the `silver_eligibility` streaming table (append) |
| `silver_eligibility_scd` | Part E7 (optional) — AUTO CDC pipeline source: upsert by `member_id` → `silver_eligibility_current` |
| `gold_eligibility_summary` | Part E — gold aggregate (DAG task) |
| `eligibility_report` | Part E — downstream consumer (repair-demo task) |
| `notify` | Part E — notification placeholder (DAG task) |
| `for_each_lob` | Part E — per-LOB nested task for the For each loop |
| `reset` | Clean your tables + landing files to start over |

## Clean up
Run **`notebooks/reset`** (set your `schema`) to drop the lab tables and clear the landing folders.
Your schema and volume remain.
