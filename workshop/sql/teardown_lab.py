"""
Tear down lab-created objects WITHOUT deleting seed data.
Removes: staging views/tables, mart, search services, agent, semantic model.
Keeps: RAW schema with all 10 tables intact.

Usage:
    python workshop/sql/teardown_lab.py
    python workshop/sql/teardown_lab.py --confirm   (skip confirmation prompt)
"""
import json
import os
import sys
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSHOP_DIR = os.path.dirname(SCRIPT_DIR)

env_path = os.path.join(WORKSHOP_DIR, "app", ".env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)

TOKEN = os.environ["VITE_SNOWFLAKE_TOKEN"]
HOST = os.environ["VITE_SNOWFLAKE_ACCOUNT"].replace("_", "-").lower()
URL = f"https://{HOST}.snowflakecomputing.com/api/v2/statements"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
}


def run_sql(sql):
    body = json.dumps({
        "statement": sql, "warehouse": "COMPUTE_WH",
        "role": "WORKSHOP_ROLE", "database": "DIGITALNATIVECO",
    }).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read())
            return r.get("message", "")[:80]
    except urllib.error.HTTPError as e:
        msg = json.loads(e.read()).get("message", "")[:120]
        if "does not exist" in msg.lower():
            return "already gone"
        return f"ERR: {msg}"


def api_delete(path):
    url = f"https://{HOST}.snowflakecomputing.com{path}"
    req = urllib.request.Request(url, method="DELETE", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return "deleted"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "already gone"
        return f"ERR: {e.code}"


TEARDOWN_STEPS = [
    # Agent (REST API delete)
    ("Agent", "api", "/api/v2/databases/DIGITALNATIVECO/schemas/MARTS/agents/ACCOUNT_HEALTH_AGENT"),

    # Search services
    ("Gong search service", "sql", "DROP CORTEX SEARCH SERVICE IF EXISTS MARTS.GONG_TRANSCRIPT_SEARCH"),
    ("Ticket search service", "sql", "DROP CORTEX SEARCH SERVICE IF EXISTS MARTS.SUPPORT_TICKET_SEARCH"),
    ("CSM notes search service", "sql", "DROP CORTEX SEARCH SERVICE IF EXISTS MARTS.CSM_NOTES_SEARCH"),

    # Mart
    ("Mart table", "sql", "DROP TABLE IF EXISTS MARTS.MART_ACCOUNT_HEALTH"),

    # Staging objects (enriched tables + views)
    ("Enriched tickets", "sql", "DROP TABLE IF EXISTS STAGING.ENRICHED_SUPPORT_TICKETS"),
    ("Enriched Gong", "sql", "DROP TABLE IF EXISTS STAGING.ENRICHED_GONG_TRANSCRIPTS"),
    ("Usage metrics", "sql", "DROP TABLE IF EXISTS STAGING.ACCOUNT_USAGE_METRICS"),
    ("Risk alerts", "sql", "DROP TABLE IF EXISTS MARTS.RISK_ALERTS"),
    ("Stg tickets view", "sql", "DROP VIEW IF EXISTS STAGING.STG_SUPPORT_TICKETS"),
    ("Stg Gong view", "sql", "DROP VIEW IF EXISTS STAGING.STG_GONG_TRANSCRIPTS"),
    ("Stg events view", "sql", "DROP VIEW IF EXISTS STAGING.STG_PRODUCT_EVENTS"),
    ("Stg employees view", "sql", "DROP VIEW IF EXISTS STAGING.STG_EMPLOYEES"),
    ("Stg assignments view", "sql", "DROP VIEW IF EXISTS STAGING.STG_ACCOUNT_ASSIGNMENTS"),
    ("Stg opportunities view", "sql", "DROP VIEW IF EXISTS STAGING.STG_OPPORTUNITIES"),
    ("Stg feature usage view", "sql", "DROP VIEW IF EXISTS STAGING.STG_FEATURE_USAGE"),
    ("Stg invoices view", "sql", "DROP VIEW IF EXISTS STAGING.STG_INVOICES"),
    ("Stg CSM notes view", "sql", "DROP VIEW IF EXISTS STAGING.STG_CSM_NOTES"),

    # Semantic model stage contents (keep the stage, remove the file)
    ("Semantic model YAML", "sql", "REMOVE @MARTS.SEMANTIC_MODELS/account_health.yaml"),

    # Stored procedures (cleanup helpers)
    ("Upload proc v2", "sql", "DROP PROCEDURE IF EXISTS MARTS.UPLOAD_SEMANTIC_MODEL_V2()"),
    ("Upload proc v3", "sql", "DROP PROCEDURE IF EXISTS MARTS.UPLOAD_SEMANTIC_MODEL_V3()"),
    ("Upload proc v4", "sql", "DROP PROCEDURE IF EXISTS MARTS.UPLOAD_SEMANTIC_MODEL_V4()"),
    ("Upload agent spec", "sql", "DROP PROCEDURE IF EXISTS MARTS.UPLOAD_AGENT_SPEC()"),
    ("Create agent proc", "sql", "DROP PROCEDURE IF EXISTS MARTS.CREATE_AGENT_V2()"),
    ("Create agent proc v3", "sql", "DROP PROCEDURE IF EXISTS MARTS.CREATE_AGENT_V3()"),
    ("Create agent from file", "sql", "DROP PROCEDURE IF EXISTS MARTS.CREATE_AGENT_FROM_FILE()"),
]


def main():
    if "--confirm" not in sys.argv:
        print("This will tear down all lab-created objects (staging, mart, agent, search services).")
        print("RAW data (10 tables) will NOT be touched.")
        resp = input("Continue? [y/N] ")
        if resp.lower() != "y":
            print("Aborted.")
            return

    print("Tearing down lab objects...\n")
    for name, method, target in TEARDOWN_STEPS:
        if method == "sql":
            result = run_sql(target)
        else:
            result = api_delete(target)
        status = "OK" if "success" in result.lower() or "deleted" in result.lower() or "gone" in result.lower() else result
        print(f"  [{status:12s}] {name}")

    # Verify RAW is intact
    print("\nVerifying RAW data is intact...")
    result = run_sql("""
        SELECT 'accounts' t, COUNT(*) c FROM RAW.ACCOUNTS
        UNION ALL SELECT 'product_events', COUNT(*) FROM RAW.PRODUCT_EVENTS
        UNION ALL SELECT 'support_tickets', COUNT(*) FROM RAW.SUPPORT_TICKETS
        UNION ALL SELECT 'gong_transcripts', COUNT(*) FROM RAW.GONG_TRANSCRIPTS
        UNION ALL SELECT 'employees', COUNT(*) FROM RAW.EMPLOYEES
        UNION ALL SELECT 'account_assignments', COUNT(*) FROM RAW.ACCOUNT_ASSIGNMENTS
        UNION ALL SELECT 'opportunities', COUNT(*) FROM RAW.OPPORTUNITIES
        UNION ALL SELECT 'feature_usage', COUNT(*) FROM RAW.FEATURE_USAGE
        UNION ALL SELECT 'invoices', COUNT(*) FROM RAW.INVOICES
        UNION ALL SELECT 'csm_notes', COUNT(*) FROM RAW.CSM_NOTES
    """)
    print(f"  RAW tables: {result}")
    print("\nTeardown complete. Run the lab setup script to rebuild from any checkpoint.")


if __name__ == "__main__":
    main()
