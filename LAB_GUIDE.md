# Lab Guide — Lakeflow Connect & Orchestration

Work top to bottom. Everything lives in **your** schema inside the `dev-sh-training` catalog. Set the
**`schema`** widget to your own name on every notebook before you run it.

- Catalog (fixed): `dev-sh-training`
- Your schema: whatever you set in `00_setup` (e.g. `jane_doe`)
- Landing volume: `/Volumes/dev-sh-training/<you>/landing/`

> **⚠️ How to use every notebook in this lab — read first.** The widgets (`schema`, `scenario`, …)
> are defined in the **first cell**. You must **run that first cell** before anything else so the
> widget boxes appear at the top of the notebook. Then fill in your **`schema`** (and any other
> options) and run the remaining cells (or **Run all**). If you skip the first cell, the widgets
> never appear, and the notebook falls back to the placeholder default and stops with an error.
>
> The value you type is substituted everywhere automatically — via `${schema}` in SQL notebooks and
> via the widget in Python notebooks.

---

## Setup (once)
1. Add this repo as a **Git folder** (`Workspace → Create → Git folder`, URL
   `https://github.com/realboom/lakeflowconnect`).
2. Open **`notebooks/00_setup`**, **run the first cell** so the `schema` widget appears, set it to
   your name, then **Run all**.
   You now have a schema and a `landing` volume with `filedrop/` and `sftp/` subfolders.

---

## Part A — COPY INTO (batch file ingestion)

**Concept:** `COPY INTO` loads *new* files from a folder into a table and is **idempotent** — rerun it
and already-loaded files are skipped. Simple, batch, great for "a file shows up, pull it in."

1. Open **`generate_data`**, set `schema`, scenario **`Part A - file drop (COPY INTO)`**, `num_rows` = 25, **Run all**.
   → writes a comma CSV to `landing/filedrop/incoming/`.
2. Open **`part_a_copy_into`**, set `schema`, **Run all**.
   → creates `bronze_file_eligibility` and loads the file.
3. **Run the COPY INTO cell again.** It loads **0 new rows** — that's idempotency (it remembers what it already ingested).
4. Generate another Part A file (step 1 again) and re-run COPY INTO → only the **new** file is loaded.

✅ Takeaway: COPY INTO = the simplest incremental batch ingest.

---

## Part B — Auto Loader as a Job ("SFTP" source), with a retry policy

**Concept:** A vendor drops files on **SFTP**; we mimic that by landing pipe-delimited files in
`landing/sftp/incoming/` and letting **Auto Loader** (`cloudFiles`) ingest them incrementally (it keeps a
**checkpoint** of what it has already processed). We run Auto Loader as a **Job with a retry policy** — and
that retry is exactly what lets a schema change self-heal in Part C.

1. **Generate data:** open **`generate_data`**, scenario **`Part B - SFTP source (Auto Loader)`**,
   `num_rows` = 25, **Run all** → writes a pipe-delimited CSV to `landing/sftp/incoming/`.
2. **Create the ingest job:**
   - **Jobs & Pipelines** (left sidebar) → blue **Create** → **Job** → name it **`sftp_ingest_<you>`**
     (jobs are workspace-global, so include your name).
   - Add a task: **Task name** `ingest`, **Type** Notebook, **Source** Workspace, **Path**
     `notebooks/part_b_autoloader` (Select Notebook → Users → *you* → `lakeflowconnect` → `notebooks`).
   - **Cluster:** **Serverless** if offered, otherwise **All-Purpose Compute** (keep it warm — you'll run this a few times).
   - **Parameters:** `+ Add` → Key `schema`, Value = your schema.
   - **Retries:** click the ✏️ edit → set **Retry at most = 1**, **and wait 30 seconds** (change the unit
     from `mins` to `secs`). On serverless, also **uncheck "Enable serverless auto-optimization"** so your
     one retry is the only retrier → **Confirm**. This single retry is what makes the schema change in
     Part C self-heal (and stay a clean *one* retry).
   - **Create task**, then **Run now**.
3. Open the **Runs** tab → the run succeeds and `bronze_sftp_eligibility` is loaded.
4. Generate another Part B file (step 1) and **Run now** again → only the **new** file is picked up (checkpoint).

✅ Takeaway: Auto Loader = incremental, checkpointed ingestion for flat-file / "SFTP" feeds. Contrast with
Part A: COPY INTO is batch SQL; Auto Loader is a streaming source with schema evolution + rescue (next) — and
running it as a **Job** gives you retries (Part C), scheduling, and triggers (Part E).

---

## Part C — Auto Loader resilience (run via your `sftp_ingest` job)

Same `bronze_sftp_eligibility`. For each scenario, generate the file, then **Run now** your
**`sftp_ingest_<you>`** job and watch the **Runs** tab. **Rescued data first** (original schema), then
schema evolution (which permanently adds a column — and shows your retry policy in action).

### C1 — Rescued data (bad value, original schema)
1. **`generate_data`** → scenario **`Part C - rescued data (SFTP)`** → **Run all**. Half the rows have a
   bad `eff_date` of `NOT-A-DATE`. (`eff_date` is typed `DATE` via `schemaHints`.)
2. **Run now** your `sftp_ingest_<you>` job. The bad values can't cast to DATE, so Auto Loader **rescues**
   them: the row still ingests with `eff_date = NULL`, original value parked in `_rescued_data`. One clean
   attempt — no retry needed (no schema change).
3. **See it without running anything:** open the run → click the **`ingest`** task → scroll the notebook
   output. The ingest notebook already displays the **rescued rows** (`_rescued_data` populated, `eff_date`
   NULL) in its last cell. (No separate query needed.)

🗣️ A malformed value didn't crash the pipeline or get silently dropped — it's captured for audit/backfill.

### C2 — Schema evolution (a new column) — **watch the retry heal it**
1. **`generate_data`** → scenario **`Part C - schema evolution (SFTP)`** → **Run all**. The file has a
   **new** `risk_tier` column.
2. **Run now** your `sftp_ingest_<you>` job and watch the **Runs** tab. Auto Loader detects `risk_tier`:
   **Attempt 1 fails** (Auto Loader stops to *record* the new column), then the **retry — Attempt 2 —
   succeeds**, with `risk_tier` added to the table (existing rows `NULL`). The fail-then-recover is visible
   right in the run.
3. **See the new column:** click into the run → the **`ingest`** task → the **Attempt 2 (succeeded)**
   notebook output shows the data **with the new `risk_tier` column** populated. (Attempt 1 is right there
   too, showing the schema-change failure — nice to point at.)

🗣️ A new field appeared and the table evolved on its own — the task **retry** turned a one-time schema
handshake into a hands-off success. (This *is* the Part E6 retries lesson, shown live.)

> ⚠️ **If the run just *succeeds* with no failed attempt**, `risk_tier` was already in Auto Loader's schema
> from a previous run — so there's no "new column" to record and nothing to retry. The fail→retry only
> fires when `risk_tier` is **new**. To replay cleanly: run **`reset`** (your schema) — it clears the
> landing files **and** the `_autoloader` checkpoint/schema **and** drops `bronze_sftp_eligibility` — then
> run **Part B** (re-establishes the schema *without* `risk_tier`), then C2. (Clearing just the landing
> files isn't enough; the evolved schema lives in the checkpoint.)

---

## Part E — Orchestration (Lakeflow Pipelines + Jobs)

Now we orchestrate the eligibility data you just created. You'll build **one pipeline** and a few **jobs**
by hand.

**Where you build these — read this once.** In the Databricks **left sidebar**, find **Jobs & Pipelines**.
Tip: **right-click it and open in a new browser tab**, so you can keep this guide open side-by-side.
On the **Jobs & Pipelines** page, click the blue **Create** button (it has a dropdown). The dropdown lets
you pick what to build — **ETL Pipeline** or **Job**. Each step below tells you which one to choose:
- **E1** builds an **ETL Pipeline** (that's what a Spark Declarative Pipeline is).
- **E2, E3, E5** build **Jobs**.

**Picking a notebook for a task — read this once too.** Whenever a task asks for a notebook **Path**, the
**Select Notebook** dialog opens. Navigate **Workspace → Users → _your user_ → `lakeflowconnect` →
`notebooks`**, select the file, and click **Confirm**. (`lakeflowconnect` is the Git folder you cloned in
Setup.) Below, a reference like `notebooks/gold_eligibility_summary` means that file in this folder.

### E1 — The silver pipeline (an ETL Pipeline / Spark Declarative Pipeline)
This builds a streaming `silver_eligibility` table from your Auto Loader bronze (`bronze_sftp_eligibility`).

1. **Jobs & Pipelines** (left sidebar) → blue **Create** button → **ETL Pipeline**. You land in the
   pipeline editor on a new pipeline named like *New Pipeline 2026-…*, with a starter file
   `transformations/my_transformation.py`.
2. **Rename the pipeline:** click its name at the top-left and change it to `silver_eligibility_<you>`.
   If it asks **"Also rename the root folder?"**, click **Rename** (keeps the pipeline's workspace folder
   name in sync — either choice works).
3. **⚠️ Set the default catalog + schema — this is how the pipeline finds *your* tables.** Open the
   pipeline **Settings** (gear icon, or the **⋮** menu → *Settings*) and set:
   - **Default catalog = `dev-sh-training`**
   - **Default schema = your schema** (the one from `00_setup`)
   - **Serverless** compute

   (The editor shows a default like `… / default` near the top-right — you must change it to yours.)
   Because the code uses the bare name `bronze_sftp_eligibility` (no catalog/schema), it resolves
   against this default catalog + schema — so your pipeline reads *your* bronze and writes *your*
   silver. Same code for everyone; only the default schema differs.
4. **Add the transformation SQL.** The starter file is Python, but our logic is SQL:
   - Right-click `my_transformation.py` → **Rename** to `silver_eligibility.sql` (or click **+** to add
     a new `silver_eligibility.sql` and delete the empty `.py`).
   - Open `notebooks/silver_eligibility` in your Git folder, copy the
     `CREATE OR REFRESH STREAMING TABLE silver_eligibility …` statement, and paste it into the file.
   - *(Optional — AI authoring: instead of pasting, click **Create with Genie Code** / **Generate** and
     paste this prompt — then compare what it writes to the SQL in the repo before running:*
     > "Create a streaming table in SQL named `silver_eligibility` that reads incrementally from the
     > streaming table `bronze_sftp_eligibility`. `initcap` first_name and last_name; cast `eff_date` and
     > `term_date` to DATE; keep `member_id`, `plan_code`, `line_of_business`; add `silver_loaded_at` as
     > the current timestamp. Use `FROM STREAM bronze_sftp_eligibility` so it's incremental, not a reload."
     *)*
5. Click **Run** (▶ Run pipeline) → it builds `silver_eligibility` in your schema from
   `bronze_sftp_eligibility`. (Part B must have run first so your bronze table exists.)

### E2 — Table-update trigger (event-driven)
Make the silver pipeline run **automatically whenever new bronze data lands** — no schedule, no manual run.

1. **Jobs & Pipelines** (left sidebar) → blue **Create** button → **Job**. You land in the job editor on
   a job named like *New Job 2026-…*.
2. **Rename the job:** click its name at the top-left → `silver_refresh_<you>`.
3. **Add the task — and make it a *Pipeline* task** (the screen defaults to a Notebook card; don't use that):
   - Click **+ Add another task type** (the blue button under "Add your first task").
   - **Task name:** `refresh_silver`
   - **Type:** choose **Pipeline** from the Type dropdown.
   - **Pipeline:** select your `silver_eligibility_<you>` pipeline from E1.
   - **Create task** / **Save task**.
4. **Add the trigger** — it lives in the **right-hand panel**, not on the task:
   - In the right-side **Job details** panel, find **Schedules & Triggers** and click **Add trigger**.
   - **Trigger type:** **Table update**.
   - **Tables:** click the table box and browse to `dev-sh-training` → **your schema** →
     **`bronze_sftp_eligibility`**. ⚠️ Make sure it's **`bronze_sftp_eligibility`** (the Auto Loader table
     your silver pipeline streams from) — **not** `bronze_file_eligibility` (that's Part A's COPY INTO
     table; silver doesn't read it, so the job would fire but silver would see nothing new).
   - **Advanced** is optional. The **Minimum time between triggers** / **Wait after last change** fields
     are in **`hh mm`** (not seconds) — leave both at **`00h 00m`** so the job fires as soon as new data
     lands.
   - **Save**.
5. **Test it:**
   - Click the **Runs** tab (next to **Tasks**, just under the job name) so you can watch runs appear.
   - In another browser tab, run `generate_data` (scenario **Part B - SFTP source**) then
     `part_b_autoloader` so new rows commit to `bronze_sftp_eligibility`. (Plain Part B is all you need —
     you just want a fresh commit to fire the trigger. `risk_tier` already exists from Part C and silver
     doesn't use it, so there's no need to re-run schema evolution here.)
   - Within ~a minute a run **shows up on the Runs tab on its own** — its origin reads *"Triggered by
     table update"* — and it refreshes `silver_eligibility`. (No one pressed Run now.)

🗣️ The trigger baselines when you create it and fires only on **new** commits — so do the fresh bronze load *after* you've set up the trigger, or it won't have anything new to react to.

### E3 — The DAG: gold → report → notify (with a conditional branch)
Create a multi-task job.
1. **Jobs & Pipelines** → blue **Create** button → **Job**, name it `eligibility_gold_<you>`
   (include your name — jobs are workspace-global, so a bare `eligibility_gold` would collide with everyone else's).
> **Task fields — set these, ignore the rest.** Each task's config panel has a lot of fields; you only
> touch a few:
> - **Task name**, **Type** = Notebook, **Source** = Workspace, **Path** (via the Select Notebook dialog).
> - **Cluster** → open the dropdown. If **Serverless** is offered, pick it. **Jobs serverless may not be
>   enabled in this workspace** — if there's no Serverless option, choose the existing **All-Purpose
>   Compute** cluster (already running = fastest), or **Add new job cluster** if no shared cluster is
>   available (works, but ~5-min cold start). **Use the same cluster for every task in the job.**
> - **Parameters** → click **+ Add** and enter the Key/Value shown in each step (this is how the notebook
>   gets your `schema`).
> - **Retries** → only where a step says so.
>
> Leave **Dependent libraries, Notifications, Metric thresholds, Tags, Job health, Permissions, and
> Advanced settings** at their defaults.

2. Task **`gold`** — Type **Notebook**, Path `notebooks/gold_eligibility_summary`, **Cluster** = your
   compute (see note). **Parameters:** `+ Add` → Key `schema`, Value = your schema. **Retries:** `+ Add`
   → **Retries:** edit → **Retry at most = 2**, wait 30 seconds.
3. Task **`report`** — `+ Add task`, Type **Notebook**, Path `notebooks/eligibility_report`, same cluster,
   Parameter `schema` = your schema. **Depends on:** `gold`.
4. Task **`notify_pass`** — Type **Notebook**, Path `notebooks/notify`, same cluster, Parameter `result`
   = `pass`. **Depends on:** `report`. **Run if** = **All succeeded**.
5. Task **`notify_fail`** — Type **Notebook**, Path `notebooks/notify`, same cluster, Parameter `result`
   = `fail`. **Depends on:** `report`. **Run if** = **At least one failed**.
6. **Run** the job → `gold` → `report` → `notify_pass` (and `notify_fail` is skipped). Green path.

### E4 — Repair / partial re-run (recover from a schema change)
A realistic failure: someone renames a column upstream and the downstream report breaks.
1. Open **`gold_eligibility_summary`** and rename **`member_count` → `enrolled_members`** in **both cells** —
   the `count(*) AS member_count` in the `CREATE OR REPLACE TABLE` cell **and** the `ORDER BY member_count`
   in the final check cell. Save. (If you miss the check cell, the `gold` task itself errors there and you
   won't get the "gold succeeds / report fails" story.)
2. **Run** `eligibility_gold_<you>`. → `gold` **succeeds** (table rebuilt with the new name), but `report`
   **fails**: `UNRESOLVED_COLUMN … member_count … Did you mean 'enrolled_members'?`, and `notify_fail` runs.
3. **Fix** `eligibility_report`: change `member_count` → `enrolled_members`, save.
4. On the failed run click **Repair run**. → **`gold` is skipped** (already built), only `report` +
   `notify_pass` re-run → success.

🗣️ You don't rerun the expensive upstream that already succeeded — fix and resume from the failure.
(To reset for a repeat: revert both files back to `member_count`.)

### E5 — For each (fan-out + concurrency)
Run a task once per line of business, in parallel.
1. **Jobs & Pipelines** → blue **Create** button → **Job** `eligibility_by_lob_<you>`. Add a **For each** task.
   - **Inputs:** `["Commercial","Medicaid","Medicare Advantage","Individual"]`
   - **Concurrency:** `4`
2. **Add a task to loop over** → Notebook `notebooks/for_each_lob`, params `schema` = your schema and
   **`lob` = `{{input}}`**.
3. **Run** → four iterations run in parallel, each building `gold_elig_<lob>`.

**Concurrency FAQ (you'll be asked):** concurrency is **1–100** (default 1); effective parallelism =
`min(concurrency, # inputs)`; the workspace cap is **2,000 concurrent task runs**. Size it to what your
downstream can handle, not the max. See the instructor runbook for the full FAQ.

### E6 — Retries
You already saw retries do real work back in **Part C2**: when the `risk_tier` column appeared, your
`sftp_ingest` job's **Attempt 1 failed** (Auto Loader stopping to record the new column) and the **retry,
Attempt 2, succeeded** — the schema evolved with no manual intervention. That's the **Retry at most = 1**
you set on the ingest task (and **Retry at most = 2** on `gold` in E3). Retries also heal transient infra
failures. Put a retry on any task that ingests evolving files or calls flaky external systems — then open a
run and show the **Attempt 1 → Attempt 2** timeline.

### E7 — Incremental loading: upsert with AUTO CDC *(optional — a preview of the SDP workshop)*
The E1 `silver_eligibility` table is **append-only**: re-send a member and you get a **duplicate** row.
A "current state" table (eligibility, customer, account) usually wants **one row per member, updated in
place**. Databricks does this with **AUTO CDC** (the SQL `APPLY CHANGES` pattern) — you declare the
**key** and a **sequence**, and Databricks writes the insert-or-update MERGE for you (no hand-coded MERGE,
no full reload).

1. Build a **second ETL Pipeline**, set up exactly like E1 (Create → ETL Pipeline → rename, e.g.
   `silver_upsert_<you>` → **default catalog `dev-sh-training` + your schema** → Serverless), but paste
   **`notebooks/silver_eligibility_scd`** as the source. It creates `silver_eligibility_current`
   (one upserted row per `member_id`). Click **Run**.
2. Note a few members and their plans:
   `SELECT member_id, plan_code FROM silver_eligibility_current ORDER BY member_id LIMIT 5;`
3. **Send updates:** `generate_data` → scenario **`Part E - member update (upsert)`** → Run all. It
   re-sends existing members with a **new `plan_code`**. Then run **`part_b_autoloader`** so the changes
   land in bronze.
4. **Run the AUTO CDC pipeline again** (or wire a table-update trigger like E2 to fire it). Re-check the
   same members — their `plan_code` has **changed in place**: same row count, **no duplicates**.
5. **See the contrast:** the append `silver_eligibility` from E1, fed the same update, shows **two rows**
   for that member (old + new). Append vs. upsert is the core incremental-loading choice.

**The three pieces to call out:** `KEYS (member_id)` (match on the business key), `SEQUENCE BY ingested_at`
(newest wins when a key repeats), `AUTO CDC INTO` (Databricks runs the MERGE). This is the foundation we go
deep on in the SDP workshop — upserts, deletes (`APPLY AS DELETE`), and SCD Type 2 history.

---

## Clean up / start over
Run **`notebooks/reset`** (set your `schema`) to drop the lab tables and clear the landing folders.
Your schema and volume stay. Re-run `generate_data` to begin again.
