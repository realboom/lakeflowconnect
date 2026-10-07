# Databricks notebook source
# MAGIC %md
# MAGIC # Generate lab data
# MAGIC Writes synthetic eligibility files into **your** landing volume for each scenario.
# MAGIC
# MAGIC 1. Set **schema** to your schema name.
# MAGIC 2. Pick a **scenario**.
# MAGIC 3. Set **num_rows**.
# MAGIC 4. **Run all.**
# MAGIC
# MAGIC Then run the matching ingestion notebook (`part_a_copy_into` or `part_b_autoloader`).

# COMMAND ----------

# DBTITLE 1,Widgets — set these, then Run all
dbutils.widgets.text("schema", "firstname_lastname", "Your schema name")
dbutils.widgets.dropdown("scenario", "Part A - file drop (COPY INTO)",
    ["Part A - file drop (COPY INTO)",
     "Part B - SFTP source (Auto Loader)",
     "Part C - rescued data (SFTP)",
     "Part C - schema evolution (SFTP)"], "Scenario")
dbutils.widgets.text("num_rows", "25", "Rows to generate")

# COMMAND ----------

# DBTITLE 1,Read widgets + helpers
import datetime, random

CATALOG = "dev-sh-training"
schema = dbutils.widgets.get("schema").strip()
scenario = dbutils.widgets.get("scenario")
n = int(dbutils.widgets.get("num_rows"))
assert schema and schema != "firstname_lastname", "Set the 'schema' widget first."

FIRST = ["Ada","Alan","Grace","Katherine","Dorothy","Margaret","Mary","Barbara","James","Linda","David","Radia","Joan","Hedy"]
LAST  = ["Lovelace","Turing","Hopper","Johnson","Vaughan","Hamilton","Jackson","Liskov","Smith","Garcia","Clarke","Perlman"]
LOBS  = ["Commercial","Medicaid","Medicare Advantage","Individual"]
PLANS = ["HMO Gold","PPO Silver","Medicare Advantage","HMO Bronze"]
PLAN_CODES = ["HMOGLD","PPOSLV","MADV","HMOBRZ"]
TIERS = ["High","Medium","Low"]

base  = f"/Volumes/{CATALOG}/{schema}/landing"
ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
today = datetime.date.today()

def write(path, lines):
    dbutils.fs.put(path, "\n".join(lines) + "\n", overwrite=True)
    print(f"Wrote {len(lines) - 1} rows -> {path}")

# COMMAND ----------

# DBTITLE 1,Run the selected scenario
m = random.randint(100000, 899000)

if scenario == "Part A - file drop (COPY INTO)":
    # COMMA-delimited, matches the COPY INTO target bronze_file_eligibility
    rows = ["member_id,first_name,last_name,plan,line_of_business,effective_date"]
    for i in range(n):
        rows.append(f"M{m+i},{random.choice(FIRST)},{random.choice(LAST)},{random.choice(PLANS)},{random.choice(LOBS)},{today.isoformat()}")
    write(f"{base}/filedrop/incoming/eligibility_{ts}.csv", rows)
    print("Next: run part_a_copy_into -> COPY INTO bronze_file_eligibility.")

elif scenario == "Part B - SFTP source (Auto Loader)":
    # PIPE-delimited, matches the Auto Loader (sep='|') target bronze_sftp_eligibility
    rows = ["member_id|first_name|last_name|birth_date|plan_code|eff_date|term_date|line_of_business"]
    for i in range(n):
        bday = (datetime.date(1950,1,1) + datetime.timedelta(days=random.randint(0,25000))).isoformat()
        rows.append(f"M{m+i}|{random.choice(FIRST)}|{random.choice(LAST)}|{bday}|{random.choice(PLAN_CODES)}|{today.isoformat()}||{random.choice(LOBS)}")
    write(f"{base}/sftp/incoming/eligibility_{ts}.csv", rows)
    print("Next: run part_b_autoloader -> bronze_sftp_eligibility.")

elif scenario == "Part C - rescued data (SFTP)":
    # Half the rows have a bad eff_date -> rescued into _rescued_data (eff_date is typed DATE via schemaHints)
    rows = ["member_id|first_name|last_name|birth_date|plan_code|eff_date|term_date|line_of_business"]
    for i in range(n):
        bday = (datetime.date(1950,1,1) + datetime.timedelta(days=random.randint(0,25000))).isoformat()
        eff = "NOT-A-DATE" if i % 2 == 0 else today.isoformat()
        rows.append(f"M{m+i}|{random.choice(FIRST)}|{random.choice(LAST)}|{bday}|{random.choice(PLAN_CODES)}|{eff}||{random.choice(LOBS)}")
    write(f"{base}/sftp/incoming/eligibility_{ts}_rescue.csv", rows)
    print("Next: run part_b_autoloader. Bad eff_date values can't cast to DATE -> parked in _rescued_data, row still ingests.")

else:  # Part C - schema evolution (SFTP)
    # Adds a NEW column risk_tier -> Auto Loader addNewColumns evolves bronze_sftp_eligibility
    rows = ["member_id|first_name|last_name|birth_date|plan_code|eff_date|term_date|line_of_business|risk_tier"]
    for i in range(n):
        bday = (datetime.date(1950,1,1) + datetime.timedelta(days=random.randint(0,25000))).isoformat()
        rows.append(f"M{m+i}|{random.choice(FIRST)}|{random.choice(LAST)}|{bday}|{random.choice(PLAN_CODES)}|{today.isoformat()}||{random.choice(LOBS)}|{random.choice(TIERS)}")
    write(f"{base}/sftp/incoming/eligibility_{ts}_evo.csv", rows)
    print("Next: run part_b_autoloader. New column risk_tier -> Auto Loader evolves the schema (it may stop once to record it; just run again).")
