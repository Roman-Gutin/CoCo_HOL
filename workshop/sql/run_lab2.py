"""
Run Lab 2 SQL statements against Snowflake via SQL API.
Corrected for actual mart schema from Lab 1.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSHOP_DIR = os.path.dirname(SCRIPT_DIR)

env_path = os.path.join(WORKSHOP_DIR, "app", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)

ACCOUNT = os.environ["VITE_SNOWFLAKE_ACCOUNT"]
TOKEN = os.environ["VITE_SNOWFLAKE_TOKEN"]
ACCOUNT_HOST = ACCOUNT.replace("_", "-").lower()
API_URL = f"https://{ACCOUNT_HOST}.snowflakecomputing.com/api/v2/statements"
WH = "COMPUTE_WH"
ROLE = "WORKSHOP_ROLE"
DB = "DIGITALNATIVECO"


def run_sql(stmt, timeout=300):
    body = {"statement": stmt, "warehouse": WH, "role": ROLE, "database": DB, "timeout": timeout}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, method="POST", headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("code") == "333334":
            return poll(result["statementHandle"], timeout)
        return result
    except urllib.error.HTTPError as e:
        err = json.loads(e.read().decode("utf-8"))
        print(f"  ERROR: {err.get('message', '')[:300]}")
        return None


def poll(handle, timeout=300):
    url = f"{API_URL}/{handle}"
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(3)
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json",
            "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
        })
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("code") in ("090001", "090002"):
            return result
        if result.get("code") != "333334":
            print(f"  Poll error: {result.get('message')}")
            return result
        print(f"    ... still running ({int(time.time()-start)}s)", flush=True)
    return None


def show_results(result, max_rows=5):
    if not result or "data" not in result:
        return
    meta = result.get("resultSetMetaData", {})
    cols = [c["name"] for c in meta.get("rowType", [])]
    if cols:
        print(f"  Columns: {', '.join(cols[:8])}")
    for i, row in enumerate(result["data"][:max_rows]):
        # Truncate long values
        vals = [str(v)[:80] for v in row]
        print(f"  Row {i+1}: {' | '.join(vals[:6])}")
    num = meta.get("numRows", 0)
    if num > max_rows:
        print(f"  ... ({num} total rows)")
    print()


def step(name, sql, show=True, max_rows=5):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    start = time.time()
    result = run_sql(sql)
    elapsed = round(time.time() - start, 1)
    if result and result.get("code") in ("090001", "090002"):
        num = result.get("resultSetMetaData", {}).get("numRows", 0)
        print(f"  OK ({elapsed}s, {num} rows)")
        if show:
            show_results(result, max_rows)
    else:
        print(f"  FAILED ({elapsed}s)")
        if result:
            print(f"  {result.get('message', '')[:400]}")
    return result


def main():
    print("=" * 60)
    print("  LAB 2: Cortex Agents — AI That Serves Data")
    print("=" * 60)

    # Verify mart exists
    step("Setup: Verify mart", """
        SELECT account_name, arr, avg_sentiment, competitor_mentioned,
               ae_changed_recently, pipeline_amount
        FROM MARTS.MART_ACCOUNT_HEALTH LIMIT 5
    """)

    # Step 1: Create stage for semantic model
    step("Step 1a: Create semantic model stage",
         "CREATE OR REPLACE STAGE MARTS.SEMANTIC_MODELS DIRECTORY = (ENABLE = TRUE)",
         show=False)

    # Upload YAML via a SQL trick: write it as a file using a stored procedure
    # Since we can't PUT via REST API, we'll use EXECUTE IMMEDIATE with a Python UDF
    yaml_content = r"""name: account_health
description: >
  Account health analytics for DigitalNativeCo. One row per account with
  pre-aggregated signals from product_events, support_tickets, gong_transcripts,
  employees, account_assignments, and opportunities.

tables:
  - name: mart_account_health
    base_table: DIGITALNATIVECO.MARTS.MART_ACCOUNT_HEALTH
    description: Pre-computed account health metrics. One row per account.

    dimensions:
      - name: account_name
        expr: account_name
        description: Customer account name
      - name: industry
        expr: industry
        description: Customer industry vertical
      - name: products
        expr: products
        description: Comma-separated list of products (Canvas, Flow, Insight)
      - name: csm_name
        expr: csm_name
        description: Assigned Customer Success Manager
      - name: current_ae
        expr: current_ae
        description: Current Account Executive assigned to this account
      - name: ae_changed_recently
        expr: ae_changed_recently
        description: >
          TRUE if the AE was reassigned within the last 90 days.
          AE changes are a leading indicator of account health decline.
      - name: ae_status
        expr: ae_status
        description: Employment status of current AE (active, departed, on_leave)
      - name: competitor_mentioned
        expr: competitor_mentioned
        description: TRUE if competitors (SketchFlow, Canva, etc.) were mentioned in recent Gong calls
      - name: expansion_signal
        expr: expansion_signal
        description: TRUE if expansion interest detected in recent Gong calls
      - name: typical_frustration
        expr: typical_frustration
        description: Modal frustration level from Gong calls (low, medium, high)
      - name: typical_champion_engagement
        expr: typical_champion_engagement
        description: Modal champion engagement from Gong calls (low, medium, high)
      - name: most_common_category
        expr: most_common_category
        description: Most frequent support ticket category for this account
      - name: pipeline_stages
        expr: pipeline_stages
        description: Comma-separated list of open pipeline stages

    measures:
      - name: arr
        expr: arr
        description: Annual recurring revenue in dollars
      - name: ticket_count
        expr: ticket_count
        description: Total support tickets filed by this account
      - name: avg_sentiment
        expr: avg_sentiment
        description: >
          Average sentiment across support tickets (-1 to 1).
          Below -0.3 is negative. Above 0.3 is positive.
      - name: complaint_count
        expr: complaint_count
        description: Number of tickets classified as complaints
      - name: high_priority_count
        expr: high_priority_count
        description: Number of P1/P2 priority tickets
      - name: weekly_active_users
        expr: weekly_active_users
        description: Active users in the most recent week
      - name: seat_utilization_pct
        expr: seat_utilization_pct
        description: Percentage of licensed seats actively used
      - name: usage_trend_wow_pct
        expr: usage_trend_wow_pct
        description: >
          Week-over-week usage change (%). Below -15% is alarming decline.
          Above 15% is rapid growth.
      - name: ae_tenure_days
        expr: ae_tenure_days
        description: Days since current AE was assigned. Low tenure + churn signals = risk.
      - name: pipeline_amount
        expr: pipeline_amount
        description: Total open pipeline dollars for this account
      - name: nps_score
        expr: nps_score
        description: Net Promoter Score (1-10)
      - name: gong_call_count
        expr: gong_call_count
        description: Number of Gong calls in the analysis period
"""

    # Write YAML to stage via Python stored procedure
    escaped_yaml = yaml_content.replace("'", "\\'").replace("\n", "\\n")

    step("Step 1b: Upload semantic model YAML", f"""
        CREATE OR REPLACE PROCEDURE MARTS.UPLOAD_SEMANTIC_MODEL()
        RETURNS STRING
        LANGUAGE PYTHON
        RUNTIME_VERSION = '3.11'
        PACKAGES = ('snowflake-snowpark-python')
        HANDLER = 'main'
        AS
        $$
def main(session):
    yaml = {repr(yaml_content)}
    with open('/tmp/account_health.yaml', 'w') as f:
        f.write(yaml.strip())
    session.file.put('/tmp/account_health.yaml',
                     '@DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/',
                     auto_compress=False, overwrite=True)
    return 'Uploaded account_health.yaml'
        $$
    """, show=False)

    step("Step 1c: Execute upload procedure",
         "CALL MARTS.UPLOAD_SEMANTIC_MODEL()")

    step("Step 1d: Verify YAML on stage",
         "LIST @MARTS.SEMANTIC_MODELS")

    # Step 2: Cortex Search services
    step("Step 2a: Gong transcript search service", """
        CREATE OR REPLACE CORTEX SEARCH SERVICE MARTS.GONG_TRANSCRIPT_SEARCH
          ON transcript_excerpt
          ATTRIBUTES account_name, call_type
          WAREHOUSE = COMPUTE_WH
          TARGET_LAG = '1 hour'
          AS (
            SELECT call_id, account_name, call_type, call_date,
                   transcript_excerpt, duration_min, attendees
            FROM RAW.GONG_TRANSCRIPTS
          )
    """, show=False)

    step("Step 2b: Support ticket search service", """
        CREATE OR REPLACE CORTEX SEARCH SERVICE MARTS.SUPPORT_TICKET_SEARCH
          ON ticket_text
          ATTRIBUTES account_name, product, priority
          WAREHOUSE = COMPUTE_WH
          TARGET_LAG = '1 hour'
          AS (
            SELECT ticket_id, account_name, product, priority,
                   ticket_text, status, created_at
            FROM RAW.SUPPORT_TICKETS
          )
    """, show=False)

    # Test search services
    print("\n  Waiting 10s for search services to index...")
    time.sleep(10)

    step("Step 2c: Test Gong search (SketchFlow mentions)", """
        SELECT transcript_excerpt, account_name, call_type
        FROM TABLE(
            MARTS.GONG_TRANSCRIPT_SEARCH!SEARCH(
                query => 'customer mentioned SketchFlow or evaluating competitors',
                columns => ['transcript_excerpt', 'account_name', 'call_type'],
                limit => 3
            )
        )
    """, max_rows=3)

    step("Step 2d: Test ticket search (frustration)", """
        SELECT ticket_text, account_name, priority
        FROM TABLE(
            MARTS.SUPPORT_TICKET_SEARCH!SEARCH(
                query => 'frustrated with outages or performance issues',
                columns => ['ticket_text', 'account_name', 'priority'],
                limit => 3
            )
        )
    """, max_rows=3)

    # Step 3: Create agent
    step("Step 3: Create Cortex Agent", """
        CREATE OR REPLACE CORTEX AGENT MARTS.ACCOUNT_HEALTH_AGENT
          COMMENT = 'Account health intelligence agent'
          LLM = 'claude-3-7-sonnet'
          TOOLS = (
            CORTEX_ANALYST(
              SEMANTIC_MODEL => '@MARTS.SEMANTIC_MODELS/account_health.yaml'
            ),
            CORTEX_SEARCH(
              SEARCH_SERVICE => MARTS.GONG_TRANSCRIPT_SEARCH
            ),
            CORTEX_SEARCH(
              SEARCH_SERVICE => MARTS.SUPPORT_TICKET_SEARCH
            )
          )
    """, show=False)

    # Step 4: Agent queries
    print("\n" + "=" * 60)
    print("  AGENT QUERIES — The Show-Stopper Demo")
    print("=" * 60)

    step("Q1: Why are at-risk accounts struggling?", """
        SELECT * FROM TABLE(
            MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
                'Why are our at-risk accounts struggling? Look at all available signals.'
            )
        )
    """, max_rows=1)

    step("Q2: What do at-risk accounts have in common?", """
        SELECT * FROM TABLE(
            MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
                'What do our at-risk accounts have in common?'
            )
        )
    """, max_rows=1)

    step("Q3: Total ARR at risk", """
        SELECT * FROM TABLE(
            MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
                'What is our total ARR at risk and what is driving it?'
            )
        )
    """, max_rows=1)

    step("Q4: Deep dive — Meridian Media", """
        SELECT * FROM TABLE(
            MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
                'What is going on with Meridian Media Group?'
            )
        )
    """, max_rows=1)

    step("Q5: SketchFlow mentions across all conversations", """
        SELECT * FROM TABLE(
            MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
                'Show me every mention of SketchFlow across all customer conversations'
            )
        )
    """, max_rows=1)

    step("Q6: CRO recommendation", """
        SELECT * FROM TABLE(
            MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
                'If you were our CRO, what would you fix first?'
            )
        )
    """, max_rows=1)

    print("\n" + "=" * 60)
    print("  LAB 2 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
