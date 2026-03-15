"""
Deploy DigitalNativeCo workshop to Snowflake via SQL API.

Creates database, schemas, tables, loads all seed data via INSERT statements,
and sets up grants. Uses the Snowflake SQL REST API with PAT auth.

Usage:
    python workshop/sql/deploy.py
"""

import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Config from .env or environment
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSHOP_DIR = os.path.dirname(SCRIPT_DIR)
SEED_DIR = os.path.join(WORKSHOP_DIR, "data", "seed")

# Try to load from app/.env
env_path = os.path.join(WORKSHOP_DIR, "app", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

ACCOUNT = os.environ.get("VITE_SNOWFLAKE_ACCOUNT", "")
TOKEN = os.environ.get("VITE_SNOWFLAKE_TOKEN", "")
WAREHOUSE = os.environ.get("VITE_SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
ROLE = os.environ.get("VITE_SNOWFLAKE_ROLE", "WORKSHOP_ROLE")
DATABASE = "DIGITALNATIVECO"

if not ACCOUNT or not TOKEN:
    print("ERROR: Set VITE_SNOWFLAKE_ACCOUNT and VITE_SNOWFLAKE_TOKEN in app/.env")
    sys.exit(1)

# Snowflake org-account identifiers with underscores don't work in SSL certs.
# Replace underscores with hyphens for the URL hostname.
ACCOUNT_HOST = ACCOUNT.replace("_", "-").lower()
API_URL = f"https://{ACCOUNT_HOST}.snowflakecomputing.com/api/v2/statements"


def run_sql(statement, database=None, schema=None, timeout=60):
    """Execute a single SQL statement via the Snowflake SQL API."""
    body = {
        "statement": statement,
        "warehouse": WAREHOUSE,
        "role": ROLE,
        "timeout": timeout,
    }
    if database:
        body["database"] = database
    if schema:
        body["schema"] = schema

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        # Check for async execution
        if result.get("code") == "333334":
            # Statement still running, poll
            handle = result["statementHandle"]
            return poll_statement(handle, timeout)

        if result.get("code") not in ("090001", "090002"):
            print(f"  WARNING: {result.get('message', 'Unknown error')}")
            return result

        return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            err = json.loads(error_body)
            print(f"  ERROR: {err.get('message', error_body[:200])}")
        except json.JSONDecodeError:
            print(f"  ERROR: HTTP {e.code}: {error_body[:200]}")
        return None


def poll_statement(handle, timeout=120):
    """Poll for async statement completion."""
    url = f"{API_URL}/{handle}"
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Accept": "application/json",
                "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
            },
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("code") in ("090001", "090002"):
            return result
        if result.get("code") != "333334":
            print(f"  Poll error: {result.get('message')}")
            return result
    print("  TIMEOUT waiting for statement")
    return None


def escape_sql_string(s):
    """Escape a string for SQL single quotes."""
    if s is None or s == "":
        return "NULL"
    return "'" + s.replace("'", "''").replace("\\", "\\\\") + "'"


def load_csv_via_inserts(table_name, csv_file, columns, batch_size=50):
    """Load a CSV file into a Snowflake table using batched INSERT statements."""
    filepath = os.path.join(SEED_DIR, csv_file)
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    inserted = 0

    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]
        values_list = []
        for row in batch:
            vals = []
            for col in columns:
                v = row.get(col, "")
                if v == "" or v is None:
                    vals.append("NULL")
                elif col.upper() in ("ARR", "AMOUNT", "SESSION_DURATION_MIN", "DURATION_MIN", "LICENSED_SEATS", "NPS_SCORE", "GROSS_AMOUNT", "DISCOUNT_PCT", "NET_AMOUNT", "USAGE_COUNT", "DAYS_TO_PAY"):
                    vals.append(str(v))
                else:
                    vals.append(escape_sql_string(v))
            values_list.append(f"({', '.join(vals)})")

        col_list = ", ".join(columns)
        values_str = ",\n".join(values_list)
        sql = f"INSERT INTO {DATABASE}.RAW.{table_name} ({col_list}) VALUES\n{values_str}"

        result = run_sql(sql, database=DATABASE, schema="RAW")
        if result:
            inserted += len(batch)

        # Progress
        pct = min(100, int(inserted / total * 100))
        print(f"\r    {csv_file}: {inserted}/{total} rows ({pct}%)", end="", flush=True)

    print()  # newline after progress
    return inserted


def main():
    print(f"Deploying DigitalNativeCo to {ACCOUNT}...")
    print(f"  Role: {ROLE}")
    print(f"  Warehouse: {WAREHOUSE}")
    print()

    # --- DDL ---
    print("[1/5] Creating database and schemas...")
    run_sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
    run_sql(f"CREATE SCHEMA IF NOT EXISTS {DATABASE}.RAW")
    run_sql(f"CREATE SCHEMA IF NOT EXISTS {DATABASE}.STAGING")
    run_sql(f"CREATE SCHEMA IF NOT EXISTS {DATABASE}.MARTS")
    print("  Done.")

    print("\n[2/5] Creating tables...")

    tables = {
        "ACCOUNTS": """CREATE OR REPLACE TABLE {db}.RAW.ACCOUNTS (
            ACCOUNT_ID VARCHAR(10) NOT NULL, ACCOUNT_NAME VARCHAR(100) NOT NULL,
            INDUSTRY VARCHAR(100), ARR NUMBER(12,2), LICENSED_SEATS INTEGER,
            PRODUCTS VARCHAR(200), CONTRACT_RENEWAL_DATE DATE, CSM_NAME VARCHAR(100),
            PRIMARY_AE VARCHAR(100), HEALTH_STATUS VARCHAR(20), NPS_SCORE INTEGER
        )""",
        "PRODUCT_EVENTS": """CREATE OR REPLACE TABLE {db}.RAW.PRODUCT_EVENTS (
            EVENT_ID VARCHAR(20) NOT NULL, ACCOUNT_ID VARCHAR(10) NOT NULL,
            ACCOUNT_NAME VARCHAR(100), USER_ID VARCHAR(20), PRODUCT VARCHAR(20),
            EVENT_TYPE VARCHAR(30), EVENT_DATE TIMESTAMP_NTZ, SESSION_DURATION_MIN NUMBER(8,2)
        )""",
        "SUPPORT_TICKETS": """CREATE OR REPLACE TABLE {db}.RAW.SUPPORT_TICKETS (
            TICKET_ID VARCHAR(20) NOT NULL, ACCOUNT_ID VARCHAR(10) NOT NULL,
            ACCOUNT_NAME VARCHAR(100), PRODUCT VARCHAR(20), TICKET_TEXT VARCHAR(5000),
            PRIORITY VARCHAR(5), STATUS VARCHAR(20), CREATED_AT TIMESTAMP_NTZ
        )""",
        "GONG_TRANSCRIPTS": """CREATE OR REPLACE TABLE {db}.RAW.GONG_TRANSCRIPTS (
            CALL_ID VARCHAR(20) NOT NULL, ACCOUNT_ID VARCHAR(10) NOT NULL,
            ACCOUNT_NAME VARCHAR(100), CALL_DATE TIMESTAMP_NTZ, CALL_TYPE VARCHAR(30),
            DURATION_MIN INTEGER, TRANSCRIPT_EXCERPT VARCHAR(16777216), ATTENDEES VARCHAR(2000)
        )""",
        "EMPLOYEES": """CREATE OR REPLACE TABLE {db}.RAW.EMPLOYEES (
            EMPLOYEE_ID VARCHAR(10) NOT NULL, NAME VARCHAR(100) NOT NULL,
            TITLE VARCHAR(100), ROLE VARCHAR(20), DEPARTMENT VARCHAR(50),
            HIRE_DATE DATE, DEPARTURE_DATE DATE, DEPARTURE_REASON VARCHAR(50), STATUS VARCHAR(20)
        )""",
        "ACCOUNT_ASSIGNMENTS": """CREATE OR REPLACE TABLE {db}.RAW.ACCOUNT_ASSIGNMENTS (
            ASSIGNMENT_ID VARCHAR(20) NOT NULL, ACCOUNT_ID VARCHAR(10) NOT NULL,
            ACCOUNT_NAME VARCHAR(100), EMPLOYEE_ID VARCHAR(10) NOT NULL,
            EMPLOYEE_NAME VARCHAR(100), ROLE VARCHAR(20), ASSIGNED_DATE DATE,
            UNASSIGNED_DATE DATE, IS_CURRENT BOOLEAN
        )""",
        "OPPORTUNITIES": """CREATE OR REPLACE TABLE {db}.RAW.OPPORTUNITIES (
            OPPORTUNITY_ID VARCHAR(10) NOT NULL, ACCOUNT_ID VARCHAR(10) NOT NULL,
            ACCOUNT_NAME VARCHAR(100), OPP_TYPE VARCHAR(30), OPP_NAME VARCHAR(200),
            AMOUNT NUMBER(12,2), STAGE VARCHAR(30), CLOSE_DATE DATE,
            OWNER_ID VARCHAR(10), OWNER_NAME VARCHAR(100), CREATED_DATE DATE, NOTES VARCHAR(5000)
        )""",
        "FEATURE_USAGE": """CREATE OR REPLACE TABLE {db}.RAW.FEATURE_USAGE (
            FEATURE_USAGE_ID VARCHAR(20) NOT NULL, ACCOUNT_ID VARCHAR(10) NOT NULL,
            ACCOUNT_NAME VARCHAR(100), USER_ID VARCHAR(20), FEATURE_NAME VARCHAR(50),
            USAGE_COUNT INTEGER, USAGE_WEEK DATE
        )""",
        "INVOICES": """CREATE OR REPLACE TABLE {db}.RAW.INVOICES (
            INVOICE_ID VARCHAR(20) NOT NULL, ACCOUNT_ID VARCHAR(10) NOT NULL,
            ACCOUNT_NAME VARCHAR(100), INVOICE_DATE DATE, QUARTER VARCHAR(20),
            GROSS_AMOUNT NUMBER(12,2), DISCOUNT_PCT NUMBER(5,2), NET_AMOUNT NUMBER(12,2),
            PAYMENT_STATUS VARCHAR(20), DAYS_TO_PAY INTEGER
        )""",
        "CSM_NOTES": """CREATE OR REPLACE TABLE {db}.RAW.CSM_NOTES (
            NOTE_ID VARCHAR(20) NOT NULL, ACCOUNT_ID VARCHAR(10) NOT NULL,
            ACCOUNT_NAME VARCHAR(100), AUTHOR VARCHAR(100), CREATED_DATE DATE,
            NOTE_TYPE VARCHAR(30), NOTE_TEXT VARCHAR(10000)
        )""",
    }

    for name, ddl in tables.items():
        run_sql(ddl.format(db=DATABASE), database=DATABASE, schema="RAW")
        print(f"    {name}")
    print("  Done.")

    # --- Load Data ---
    print("\n[3/5] Loading seed data via INSERT statements...")

    loads = [
        ("ACCOUNTS", "accounts.csv",
         ["account_id", "account_name", "industry", "arr", "licensed_seats",
          "products", "contract_renewal_date", "csm_name", "primary_ae", "health_status", "nps_score"]),
        ("EMPLOYEES", "employees.csv",
         ["employee_id", "name", "title", "role", "department",
          "hire_date", "departure_date", "departure_reason", "status"]),
        ("ACCOUNT_ASSIGNMENTS", "account_assignments.csv",
         ["assignment_id", "account_id", "account_name", "employee_id",
          "employee_name", "role", "assigned_date", "unassigned_date", "is_current"]),
        ("OPPORTUNITIES", "opportunities.csv",
         ["opportunity_id", "account_id", "account_name", "opp_type", "opp_name",
          "amount", "stage", "close_date", "owner_id", "owner_name", "created_date", "notes"]),
        ("SUPPORT_TICKETS", "support_tickets.csv",
         ["ticket_id", "account_id", "account_name", "product",
          "ticket_text", "priority", "status", "created_at"]),
        ("GONG_TRANSCRIPTS", "gong_transcripts.csv",
         ["call_id", "account_id", "account_name", "call_date",
          "call_type", "duration_min", "transcript_excerpt", "attendees"]),
        ("PRODUCT_EVENTS", "product_events.csv",
         ["event_id", "account_id", "account_name", "user_id",
          "product", "event_type", "event_date", "session_duration_min"]),
        ("FEATURE_USAGE", "feature_usage.csv",
         ["feature_usage_id", "account_id", "account_name", "user_id",
          "feature_name", "usage_count", "usage_week"]),
        ("INVOICES", "invoices.csv",
         ["invoice_id", "account_id", "account_name", "invoice_date", "quarter",
          "gross_amount", "discount_pct", "net_amount", "payment_status", "days_to_pay"]),
        ("CSM_NOTES", "csm_notes.csv",
         ["note_id", "account_id", "account_name", "author", "created_date",
          "note_type", "note_text"]),
    ]

    for table, csv_file, cols in loads:
        count = load_csv_via_inserts(table, csv_file, cols)

    print("  Done.")

    # --- Grants ---
    print("\n[4/5] Setting up grants...")
    grants = [
        f"GRANT USAGE ON DATABASE {DATABASE} TO ROLE {ROLE}",
        f"GRANT USAGE ON SCHEMA {DATABASE}.RAW TO ROLE {ROLE}",
        f"GRANT USAGE ON SCHEMA {DATABASE}.STAGING TO ROLE {ROLE}",
        f"GRANT USAGE ON SCHEMA {DATABASE}.MARTS TO ROLE {ROLE}",
        f"GRANT SELECT ON ALL TABLES IN SCHEMA {DATABASE}.RAW TO ROLE {ROLE}",
        f"GRANT CREATE TABLE ON SCHEMA {DATABASE}.STAGING TO ROLE {ROLE}",
        f"GRANT CREATE VIEW ON SCHEMA {DATABASE}.STAGING TO ROLE {ROLE}",
        f"GRANT CREATE TABLE ON SCHEMA {DATABASE}.MARTS TO ROLE {ROLE}",
        f"GRANT CREATE VIEW ON SCHEMA {DATABASE}.MARTS TO ROLE {ROLE}",
        f"GRANT SELECT ON FUTURE TABLES IN SCHEMA {DATABASE}.STAGING TO ROLE {ROLE}",
        f"GRANT SELECT ON FUTURE TABLES IN SCHEMA {DATABASE}.MARTS TO ROLE {ROLE}",
    ]
    for g in grants:
        run_sql(g)
    print("  Done.")

    # --- Verify ---
    print("\n[5/5] Verifying row counts...")
    result = run_sql(f"""
        SELECT 'ACCOUNTS' AS t, COUNT(*) AS c FROM {DATABASE}.RAW.ACCOUNTS
        UNION ALL SELECT 'PRODUCT_EVENTS', COUNT(*) FROM {DATABASE}.RAW.PRODUCT_EVENTS
        UNION ALL SELECT 'SUPPORT_TICKETS', COUNT(*) FROM {DATABASE}.RAW.SUPPORT_TICKETS
        UNION ALL SELECT 'GONG_TRANSCRIPTS', COUNT(*) FROM {DATABASE}.RAW.GONG_TRANSCRIPTS
        UNION ALL SELECT 'EMPLOYEES', COUNT(*) FROM {DATABASE}.RAW.EMPLOYEES
        UNION ALL SELECT 'ACCOUNT_ASSIGNMENTS', COUNT(*) FROM {DATABASE}.RAW.ACCOUNT_ASSIGNMENTS
        UNION ALL SELECT 'OPPORTUNITIES', COUNT(*) FROM {DATABASE}.RAW.OPPORTUNITIES
        UNION ALL SELECT 'FEATURE_USAGE', COUNT(*) FROM {DATABASE}.RAW.FEATURE_USAGE
        UNION ALL SELECT 'INVOICES', COUNT(*) FROM {DATABASE}.RAW.INVOICES
        UNION ALL SELECT 'CSM_NOTES', COUNT(*) FROM {DATABASE}.RAW.CSM_NOTES
        ORDER BY t
    """, database=DATABASE)

    if result and "data" in result:
        for row in result["data"]:
            print(f"    {row[0]:25s} {row[1]:>6s} rows")

    print("\nDeployment complete!")


if __name__ == "__main__":
    main()
