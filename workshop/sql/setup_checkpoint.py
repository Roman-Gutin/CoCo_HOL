"""
Set up the lab at a specific checkpoint. Tears down everything first, then
rebuilds to the target phase. Participants can reset to any point.

Checkpoints:
  raw     — Just the 10 RAW tables (start of Lab 1)
  lab1    — After Lab 1: staging + enriched tables + mart built
  lab2    — After Lab 2: Lab 1 + semantic model + search services + agent
  lab3    — After Lab 3: Lab 2 + agent configured with sample questions

Usage:
    python workshop/sql/setup_checkpoint.py raw
    python workshop/sql/setup_checkpoint.py lab1
    python workshop/sql/setup_checkpoint.py lab2
    python workshop/sql/setup_checkpoint.py lab3
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
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)

TOKEN = os.environ["VITE_SNOWFLAKE_TOKEN"]
HOST = os.environ["VITE_SNOWFLAKE_ACCOUNT"].replace("_", "-").lower()
SQL_URL = f"https://{HOST}.snowflakecomputing.com/api/v2/statements"
AGENT_URL = f"https://{HOST}.snowflakecomputing.com/api/v2/databases/DIGITALNATIVECO/schemas/MARTS/agents"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
}


def run_sql(sql, timeout=300):
    body = json.dumps({
        "statement": sql, "warehouse": "COMPUTE_WH",
        "role": "WORKSHOP_ROLE", "database": "DIGITALNATIVECO",
        "timeout": timeout,
    }).encode()
    req = urllib.request.Request(SQL_URL, data=body, method="POST", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
        if result.get("code") == "333334":
            return poll(result["statementHandle"], timeout)
        return result
    except urllib.error.HTTPError as e:
        msg = json.loads(e.read()).get("message", "")[:200]
        if "does not exist" not in msg.lower():
            print(f"    SQL ERROR: {msg}")
        return None


def poll(handle, timeout=300):
    url = f"{SQL_URL}/{handle}"
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(3)
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {TOKEN}", "Accept": "application/json",
            "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN"})
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        if result.get("code") in ("090001", "090002"):
            return result
        if result.get("code") != "333334":
            return result
        print(f"    ... still running ({int(time.time()-start)}s)")
    return None


def api_call(url, method="POST", data=None):
    req = urllib.request.Request(url, data=data, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {"status": "ok"}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"status": "not_found"}
        body = e.read().decode()
        try:
            return json.loads(body)
        except:
            return {"error": body[:200]}


def step(name):
    print(f"\n  [{name}]")


# =========================================================================
# TEARDOWN — remove all lab objects
# =========================================================================
def teardown():
    step("Teardown")
    # Agent
    api_call(f"{AGENT_URL}/ACCOUNT_HEALTH_AGENT", "DELETE")
    # Search services
    for svc in ["GONG_TRANSCRIPT_SEARCH", "SUPPORT_TICKET_SEARCH", "CSM_NOTES_SEARCH"]:
        run_sql(f"DROP CORTEX SEARCH SERVICE IF EXISTS MARTS.{svc}")
    # Mart + staging
    for t in ["MARTS.MART_ACCOUNT_HEALTH", "MARTS.RISK_ALERTS",
              "STAGING.ENRICHED_SUPPORT_TICKETS", "STAGING.ENRICHED_GONG_TRANSCRIPTS",
              "STAGING.ACCOUNT_USAGE_METRICS"]:
        run_sql(f"DROP TABLE IF EXISTS {t}")
    for v in ["STG_SUPPORT_TICKETS", "STG_GONG_TRANSCRIPTS", "STG_PRODUCT_EVENTS",
              "STG_EMPLOYEES", "STG_ACCOUNT_ASSIGNMENTS", "STG_OPPORTUNITIES",
              "STG_FEATURE_USAGE", "STG_INVOICES", "STG_CSM_NOTES"]:
        run_sql(f"DROP VIEW IF EXISTS STAGING.{v}")
    # Semantic model file
    run_sql("REMOVE @MARTS.SEMANTIC_MODELS/account_health.yaml")
    # Procs
    for p in ["UPLOAD_SEMANTIC_MODEL", "UPLOAD_SEMANTIC_MODEL_V2",
              "UPLOAD_SEMANTIC_MODEL_V3", "UPLOAD_SEMANTIC_MODEL_V4",
              "UPLOAD_AGENT_SPEC", "CREATE_AGENT_V2", "CREATE_AGENT_V3",
              "CREATE_AGENT_FROM_FILE", "CREATE_AGENT"]:
        run_sql(f"DROP PROCEDURE IF EXISTS MARTS.{p}()")
    print("    Done — all lab objects removed, RAW data intact.")


# =========================================================================
# LAB 1 — Staging + Enrichment + Mart
# =========================================================================
def setup_lab1():
    step("Lab 1: Staging views")
    views = {
        "STG_SUPPORT_TICKETS": """CREATE OR REPLACE VIEW STAGING.STG_SUPPORT_TICKETS AS
            SELECT TICKET_ID, ACCOUNT_ID, ACCOUNT_NAME, PRODUCT, TRIM(TICKET_TEXT) AS TICKET_TEXT,
                   PRIORITY, STATUS, CREATED_AT::TIMESTAMP_NTZ AS CREATED_AT, CREATED_AT::DATE AS TICKET_DATE
            FROM RAW.SUPPORT_TICKETS WHERE TICKET_TEXT IS NOT NULL AND TRIM(TICKET_TEXT) != ''""",
        "STG_GONG_TRANSCRIPTS": """CREATE OR REPLACE VIEW STAGING.STG_GONG_TRANSCRIPTS AS
            SELECT CALL_ID, ACCOUNT_ID, ACCOUNT_NAME, CALL_DATE::TIMESTAMP_NTZ AS CALL_DATE,
                   CALL_DATE::DATE AS CALL_DATE_DT, CALL_TYPE, DURATION_MIN,
                   TRIM(TRANSCRIPT_EXCERPT) AS TRANSCRIPT_EXCERPT, ATTENDEES
            FROM RAW.GONG_TRANSCRIPTS WHERE TRANSCRIPT_EXCERPT IS NOT NULL""",
        "STG_PRODUCT_EVENTS": """CREATE OR REPLACE VIEW STAGING.STG_PRODUCT_EVENTS AS
            SELECT EVENT_ID, ACCOUNT_ID, ACCOUNT_NAME, USER_ID, PRODUCT, EVENT_TYPE,
                   EVENT_DATE::TIMESTAMP_NTZ AS EVENT_DATE, EVENT_DATE::DATE AS EVENT_DATE_DT,
                   SESSION_DURATION_MIN
            FROM RAW.PRODUCT_EVENTS WHERE SESSION_DURATION_MIN IS NOT NULL AND SESSION_DURATION_MIN >= 0""",
        "STG_EMPLOYEES": """CREATE OR REPLACE VIEW STAGING.STG_EMPLOYEES AS
            SELECT EMPLOYEE_ID, NAME, TITLE, ROLE, DEPARTMENT, HIRE_DATE::DATE AS HIRE_DATE,
                   DEPARTURE_DATE::DATE AS DEPARTURE_DATE, DEPARTURE_REASON, STATUS,
                   CASE WHEN STATUS = 'active' THEN TRUE ELSE FALSE END AS IS_ACTIVE
            FROM RAW.EMPLOYEES""",
        "STG_ACCOUNT_ASSIGNMENTS": """CREATE OR REPLACE VIEW STAGING.STG_ACCOUNT_ASSIGNMENTS AS
            SELECT ASSIGNMENT_ID, ACCOUNT_ID, ACCOUNT_NAME, EMPLOYEE_ID, EMPLOYEE_NAME, ROLE,
                   ASSIGNED_DATE::DATE AS ASSIGNED_DATE, UNASSIGNED_DATE::DATE AS UNASSIGNED_DATE, IS_CURRENT
            FROM RAW.ACCOUNT_ASSIGNMENTS""",
        "STG_OPPORTUNITIES": """CREATE OR REPLACE VIEW STAGING.STG_OPPORTUNITIES AS
            SELECT OPPORTUNITY_ID, ACCOUNT_ID, ACCOUNT_NAME, OPP_TYPE, OPP_NAME,
                   AMOUNT::NUMBER(12,2) AS AMOUNT, STAGE, CLOSE_DATE::DATE AS CLOSE_DATE,
                   OWNER_ID, OWNER_NAME, CREATED_DATE::DATE AS CREATED_DATE, NOTES
            FROM RAW.OPPORTUNITIES""",
    }
    for name, sql in views.items():
        run_sql(sql)
        print(f"    {name}")

    step("Lab 1: Enriched support tickets (AI sentiment + classification)")
    run_sql("""CREATE OR REPLACE TABLE STAGING.ENRICHED_SUPPORT_TICKETS AS
        SELECT ticket_id, account_id, account_name, product, ticket_text, priority, status, ticket_date,
               SNOWFLAKE.CORTEX.SENTIMENT(ticket_text) AS sentiment_score,
               SNOWFLAKE.CORTEX.CLASSIFY_TEXT(ticket_text,
                   ['billing','technical','feature_request','complaint','onboarding']):label::STRING AS category,
               SNOWFLAKE.CORTEX.CLASSIFY_TEXT(ticket_text,
                   ['billing','technical','feature_request','complaint','onboarding']):score::FLOAT AS category_confidence
        FROM STAGING.STG_SUPPORT_TICKETS""")
    print("    ENRICHED_SUPPORT_TICKETS")

    step("Lab 1: Enriched Gong transcripts (AI signal extraction)")
    run_sql("""CREATE OR REPLACE TABLE STAGING.ENRICHED_GONG_TRANSCRIPTS AS
        SELECT call_id, account_id, account_name, call_date_dt AS call_date, call_type,
               duration_min, transcript_excerpt, attendees,
               PARSE_JSON(REGEXP_REPLACE(
                   SNOWFLAKE.CORTEX.COMPLETE('claude-3-7-sonnet',
                       'Analyze this call transcript and return ONLY valid JSON (no markdown, no code fences) with keys: competitor_mentioned (boolean), expansion_signal (boolean), frustration_level (low/medium/high), champion_engagement (low/medium/high), key_themes (array of strings). Transcript:\\n' || transcript_excerpt
                   ), '^[\\\\s]*```[a-z]*[\\\\s]*|[\\\\s]*```[\\\\s]*$', ''
               )) AS signals,
               signals:competitor_mentioned::BOOLEAN AS competitor_mentioned,
               signals:expansion_signal::BOOLEAN AS expansion_signal,
               signals:frustration_level::STRING AS frustration_level,
               signals:champion_engagement::STRING AS champion_engagement,
               signals:key_themes::ARRAY AS key_themes
        FROM STAGING.STG_GONG_TRANSCRIPTS""")
    print("    ENRICHED_GONG_TRANSCRIPTS")

    step("Lab 1: Usage metrics with WoW trend")
    run_sql("""CREATE OR REPLACE TABLE STAGING.ACCOUNT_USAGE_METRICS AS
        WITH weekly_stats AS (
            SELECT account_id, account_name, DATE_TRUNC('week', event_date_dt) AS week_start,
                   COUNT(DISTINCT user_id) AS weekly_active_users,
                   ROUND(AVG(session_duration_min), 2) AS avg_session_duration, COUNT(*) AS total_events
            FROM STAGING.STG_PRODUCT_EVENTS GROUP BY 1, 2, 3
        ), with_trend AS (
            SELECT *, LAG(weekly_active_users) OVER (PARTITION BY account_id ORDER BY week_start) AS prev,
                   CASE WHEN prev IS NULL OR prev = 0 THEN NULL
                        ELSE ROUND((weekly_active_users - prev)::FLOAT / prev * 100, 1) END AS usage_trend_wow_pct
            FROM weekly_stats
        ) SELECT * FROM with_trend ORDER BY account_id, week_start""")
    print("    ACCOUNT_USAGE_METRICS")

    step("Lab 1: Build MART_ACCOUNT_HEALTH")
    run_sql("""CREATE OR REPLACE TABLE MARTS.MART_ACCOUNT_HEALTH AS
        WITH latest_usage AS (
            SELECT * FROM STAGING.ACCOUNT_USAGE_METRICS
            QUALIFY ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY week_start DESC) = 1
        ), ticket_agg AS (
            SELECT account_id, COUNT(*) AS ticket_count, ROUND(AVG(sentiment_score), 3) AS avg_sentiment,
                   SUM(CASE WHEN category = 'complaint' THEN 1 ELSE 0 END) AS complaint_count,
                   SUM(CASE WHEN priority IN ('P1','P2') THEN 1 ELSE 0 END) AS high_priority_count,
                   MODE(category) AS most_common_category
            FROM STAGING.ENRICHED_SUPPORT_TICKETS GROUP BY 1
        ), gong_agg AS (
            SELECT account_id, COUNT(*) AS total_calls, MAX(call_date) AS last_call_date,
                   BOOLOR_AGG(competitor_mentioned) AS any_competitor_mentioned,
                   BOOLOR_AGG(expansion_signal) AS any_expansion_signal,
                   MODE(frustration_level) AS typical_frustration,
                   MODE(champion_engagement) AS typical_champion_engagement
            FROM STAGING.ENRICHED_GONG_TRANSCRIPTS GROUP BY 1
        ), current_ae AS (
            SELECT aa.account_id, aa.employee_name AS current_ae, aa.assigned_date,
                   DATEDIFF('day', aa.assigned_date, CURRENT_DATE()) AS ae_tenure_days,
                   CASE WHEN DATEDIFF('day', aa.assigned_date, CURRENT_DATE()) <= 90 THEN TRUE ELSE FALSE END AS ae_changed_recently,
                   e.status AS ae_status
            FROM STAGING.STG_ACCOUNT_ASSIGNMENTS aa
            LEFT JOIN STAGING.STG_EMPLOYEES e ON aa.employee_id = e.employee_id
            WHERE aa.role = 'AE' AND aa.is_current = TRUE
        ), opp_agg AS (
            SELECT account_id, SUM(amount) AS pipeline_amount, COUNT(*) AS open_opp_count,
                   MIN(close_date) AS nearest_close_date,
                   LISTAGG(DISTINCT stage, ', ') WITHIN GROUP (ORDER BY stage) AS pipeline_stages
            FROM STAGING.STG_OPPORTUNITIES WHERE stage NOT IN ('closed_won','closed_lost') GROUP BY 1
        ), feature_agg AS (
            SELECT account_id, COUNT(DISTINCT feature_name) AS total_features_used,
                   SUM(usage_count) AS total_feature_usage,
                   COUNT(DISTINCT CASE WHEN feature_name IN ('canvas_collab_edit','canvas_templates','flow_approvals','insight_dashboards','insight_api') THEN feature_name END) AS power_features_used,
                   ROUND(COUNT(DISTINCT feature_name)::FLOAT / 19 * 100, 1) AS feature_breadth_pct
            FROM RAW.FEATURE_USAGE GROUP BY 1
        ), invoice_agg AS (
            SELECT account_id, ROUND(AVG(discount_pct), 2) AS avg_discount_pct,
                   ROUND(AVG(CASE WHEN payment_status = 'paid' THEN days_to_pay END), 1) AS avg_days_to_pay,
                   SUM(CASE WHEN payment_status = 'overdue' THEN 1 ELSE 0 END) AS overdue_invoices,
                   SUM(net_amount) AS total_invoiced
            FROM RAW.INVOICES GROUP BY 1
        )
        SELECT a.account_id, a.account_name, a.industry, a.arr, a.licensed_seats, a.products,
               a.contract_renewal_date, a.csm_name, a.nps_score,
               u.weekly_active_users, u.avg_session_duration, u.usage_trend_wow_pct,
               ROUND(u.weekly_active_users::FLOAT / NULLIF(a.licensed_seats, 0) * 100, 1) AS seat_utilization_pct,
               COALESCE(t.ticket_count, 0) AS ticket_count, t.avg_sentiment,
               COALESCE(t.complaint_count, 0) AS complaint_count,
               COALESCE(t.high_priority_count, 0) AS high_priority_count, t.most_common_category,
               COALESCE(g.total_calls, 0) AS gong_call_count, g.last_call_date,
               COALESCE(g.any_competitor_mentioned, FALSE) AS competitor_mentioned,
               COALESCE(g.any_expansion_signal, FALSE) AS expansion_signal,
               g.typical_frustration, g.typical_champion_engagement,
               ae.current_ae, ae.ae_tenure_days,
               COALESCE(ae.ae_changed_recently, FALSE) AS ae_changed_recently, ae.ae_status,
               COALESCE(o.pipeline_amount, 0) AS pipeline_amount,
               COALESCE(o.open_opp_count, 0) AS open_opp_count, o.pipeline_stages, o.nearest_close_date,
               COALESCE(f.total_features_used, 0) AS total_features_used,
               COALESCE(f.power_features_used, 0) AS power_features_used,
               COALESCE(f.feature_breadth_pct, 0) AS feature_breadth_pct,
               COALESCE(inv.avg_discount_pct, 0) AS avg_discount_pct,
               COALESCE(inv.avg_days_to_pay, 0) AS avg_days_to_pay,
               COALESCE(inv.overdue_invoices, 0) AS overdue_invoices,
               CASE
                   WHEN COALESCE(g.any_competitor_mentioned, FALSE) = TRUE OR t.avg_sentiment < -0.3 THEN 'at_risk'
                   WHEN COALESCE(g.any_expansion_signal, FALSE) = TRUE AND u.usage_trend_wow_pct > 5 THEN 'expansion'
                   WHEN COALESCE(t.avg_sentiment, 0) >= -0.1 AND COALESCE(u.usage_trend_wow_pct, 0) >= -5 THEN 'healthy'
                   ELSE 'attention'
               END AS health_category
        FROM RAW.ACCOUNTS a
        LEFT JOIN latest_usage u ON a.account_id = u.account_id
        LEFT JOIN ticket_agg t ON a.account_id = t.account_id
        LEFT JOIN gong_agg g ON a.account_id = g.account_id
        LEFT JOIN current_ae ae ON a.account_id = ae.account_id
        LEFT JOIN opp_agg o ON a.account_id = o.account_id
        LEFT JOIN feature_agg f ON a.account_id = f.account_id
        LEFT JOIN invoice_agg inv ON a.account_id = inv.account_id
        ORDER BY a.arr DESC""")
    print("    MART_ACCOUNT_HEALTH")

    # Verify
    r = run_sql("SELECT COUNT(*) FROM MARTS.MART_ACCOUNT_HEALTH")
    if r and "data" in r:
        print(f"    Verified: {r['data'][0][0]} accounts in mart")


# =========================================================================
# LAB 2 — Semantic model + Search services + Agent
# =========================================================================
def setup_lab2():
    step("Lab 2: Upload semantic model YAML")

    # Use the proven procedure approach
    run_sql("CREATE STAGE IF NOT EXISTS MARTS.SEMANTIC_MODELS DIRECTORY = (ENABLE = TRUE)")

    # Embed the YAML inside the procedure using triple-double-quotes.
    # The procedure body is delimited by single quotes, so the YAML content
    # must not contain any single quotes (verified: it does not).
    yaml_escaped = SEMANTIC_YAML.strip().replace("\\", "\\\\")
    sproc_sql = (
        "CREATE OR REPLACE PROCEDURE MARTS.UPLOAD_SEMANTIC_MODEL()\n"
        "RETURNS STRING LANGUAGE PYTHON RUNTIME_VERSION = '3.11'\n"
        "PACKAGES = ('snowflake-snowpark-python') HANDLER = 'main'\n"
        "AS\n"
        "'\n"
        'def main(session):\n'
        '    yaml = """\n'
        + yaml_escaped + '\n'
        + '"""\n'
        '    with open("/tmp/account_health.yaml", "w") as f:\n'
        '        f.write(yaml.strip())\n'
        '    session.file.put("/tmp/account_health.yaml", "@DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/", auto_compress=False, overwrite=True)\n'
        '    return "Done"\n'
        "'"
    )
    run_sql(sproc_sql)
    run_sql("CALL MARTS.UPLOAD_SEMANTIC_MODEL()")
    print("    Semantic model uploaded")

    step("Lab 2: Create search services")
    run_sql("""CREATE OR REPLACE CORTEX SEARCH SERVICE MARTS.GONG_TRANSCRIPT_SEARCH
        ON transcript_excerpt ATTRIBUTES account_name, call_type
        WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
        AS (SELECT call_id, account_name, call_type, call_date, transcript_excerpt, duration_min, attendees
            FROM RAW.GONG_TRANSCRIPTS)""")
    print("    GONG_TRANSCRIPT_SEARCH")

    run_sql("""CREATE OR REPLACE CORTEX SEARCH SERVICE MARTS.SUPPORT_TICKET_SEARCH
        ON ticket_text ATTRIBUTES account_name, product, priority
        WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
        AS (SELECT ticket_id, account_name, product, priority, ticket_text, status, created_at
            FROM RAW.SUPPORT_TICKETS)""")
    print("    SUPPORT_TICKET_SEARCH")

    run_sql("""CREATE OR REPLACE CORTEX SEARCH SERVICE MARTS.CSM_NOTES_SEARCH
        ON note_text ATTRIBUTES account_name, author, note_type
        WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
        AS (SELECT note_id, account_name, author, note_type, created_date, note_text
            FROM RAW.CSM_NOTES)""")
    print("    CSM_NOTES_SEARCH")

    step("Lab 2: Create agent")
    # Use the create_agent.py approach (REST API)
    agent_spec = {
        "name": "ACCOUNT_HEALTH_AGENT",
        "comment": "Account Health Intelligence - triangulates 10 data sources",
        "profile": {"display_name": "Account Health Agent", "avatar": "chart_increasing", "color": "blue"},
        "instructions": {
            "response": AGENT_RESPONSE_INSTRUCTIONS,
            "orchestration": AGENT_ORCHESTRATION_INSTRUCTIONS,
            "sample_questions": AGENT_SAMPLE_QUESTIONS,
        },
        "models": {"orchestration": "claude-3-7-sonnet"},
        "orchestration": {"budget": {"seconds": 120, "tokens": 64000}},
        "tools": AGENT_TOOLS,
        "tool_resources": AGENT_TOOL_RESOURCES,
    }
    result = api_call(AGENT_URL, "POST", json.dumps(agent_spec).encode())
    print(f"    Agent: {result.get('status', result.get('message', ''))[:80]}")

    # Grants
    for sql in [
        "GRANT USAGE ON AGENT MARTS.ACCOUNT_HEALTH_AGENT TO ROLE ACCOUNTADMIN",
        "GRANT USAGE ON CORTEX SEARCH SERVICE MARTS.GONG_TRANSCRIPT_SEARCH TO ROLE ACCOUNTADMIN",
        "GRANT USAGE ON CORTEX SEARCH SERVICE MARTS.SUPPORT_TICKET_SEARCH TO ROLE ACCOUNTADMIN",
        "GRANT USAGE ON CORTEX SEARCH SERVICE MARTS.CSM_NOTES_SEARCH TO ROLE ACCOUNTADMIN",
        "GRANT READ ON STAGE MARTS.SEMANTIC_MODELS TO ROLE ACCOUNTADMIN",
    ]:
        run_sql(sql)
    print("    Grants applied")

    # Wait for search indexing
    print("    Waiting 10s for search services to index...")
    time.sleep(10)


# =========================================================================
# Constants
# =========================================================================
SEMANTIC_YAML = """name: account_health
description: Account health analytics for DigitalNativeCo.
tables:
  - name: mart_account_health
    base_table:
      database: DIGITALNATIVECO
      schema: MARTS
      table: MART_ACCOUNT_HEALTH
    description: Pre-computed account health metrics. One row per account.
    dimensions:
      - name: account_name
        expr: account_name
        description: Customer account name
        data_type: TEXT
        unique: true
      - name: industry
        expr: industry
        description: Customer industry vertical
        data_type: TEXT
      - name: products
        expr: products
        description: Products used (Canvas, Flow, Insight)
        data_type: TEXT
      - name: csm_name
        expr: csm_name
        description: Customer Success Manager
        data_type: TEXT
      - name: current_ae
        expr: current_ae
        description: Current Account Executive
        data_type: TEXT
      - name: ae_changed_recently
        expr: ae_changed_recently
        description: TRUE if AE was reassigned within last 90 days - a leading churn indicator
        data_type: BOOLEAN
      - name: ae_status
        expr: ae_status
        description: AE employment status (active, departed, on_leave)
        data_type: TEXT
      - name: competitor_mentioned
        expr: competitor_mentioned
        description: TRUE if competitors mentioned in Gong calls
        data_type: BOOLEAN
      - name: expansion_signal
        expr: expansion_signal
        description: TRUE if expansion interest detected in Gong calls
        data_type: BOOLEAN
      - name: health_category
        expr: health_category
        description: "Account health classification: at_risk (competitor mentioned or sentiment below -0.3), expansion (expansion signal with growing usage), healthy (stable sentiment and usage), attention (mixed signals). Use this to filter or group accounts by risk level."
        data_type: TEXT
      - name: typical_frustration
        expr: typical_frustration
        description: Modal frustration from Gong calls (low, medium, high)
        data_type: TEXT
      - name: most_common_category
        expr: most_common_category
        description: Most common support ticket category
        data_type: TEXT
      - name: pipeline_stages
        expr: pipeline_stages
        description: Open pipeline stages
        data_type: TEXT
    measures:
      - name: arr
        expr: arr
        description: Annual recurring revenue in dollars
        data_type: NUMBER
        synonyms:
          - revenue
          - annual revenue
      - name: ticket_count
        expr: ticket_count
        description: Total support tickets filed
        data_type: NUMBER
      - name: avg_sentiment
        expr: avg_sentiment
        description: Avg ticket sentiment (-1 to 1). Below -0.3 is negative.
        data_type: NUMBER
      - name: complaint_count
        expr: complaint_count
        description: Number of complaint tickets
        data_type: NUMBER
      - name: high_priority_count
        expr: high_priority_count
        description: Number of P1 and P2 tickets
        data_type: NUMBER
      - name: weekly_active_users
        expr: weekly_active_users
        description: Active users in most recent week
        data_type: NUMBER
      - name: seat_utilization_pct
        expr: seat_utilization_pct
        description: Percent of licensed seats used
        data_type: NUMBER
      - name: usage_trend_wow_pct
        expr: usage_trend_wow_pct
        description: Week-over-week usage change pct. Below -15 is alarming.
        data_type: NUMBER
      - name: ae_tenure_days
        expr: ae_tenure_days
        description: Days since current AE assigned
        data_type: NUMBER
      - name: pipeline_amount
        expr: pipeline_amount
        description: Open pipeline dollars
        data_type: NUMBER
      - name: nps_score
        expr: nps_score
        description: Net Promoter Score 1-10
        data_type: NUMBER
      - name: gong_call_count
        expr: gong_call_count
        description: Number of Gong calls recorded
        data_type: NUMBER
      - name: total_features_used
        expr: total_features_used
        description: Count of distinct features used by this account
        data_type: NUMBER
      - name: power_features_used
        expr: power_features_used
        description: Count of sticky power features used. 3+ correlates with high retention.
        data_type: NUMBER
      - name: feature_breadth_pct
        expr: feature_breadth_pct
        description: Pct of available features adopted. Below 30 is shallow adoption.
        data_type: NUMBER
      - name: avg_discount_pct
        expr: avg_discount_pct
        description: Average discount given. High discounts plus churn signals means we discount to retain not grow.
        data_type: NUMBER
      - name: overdue_invoices
        expr: overdue_invoices
        description: Count of overdue invoices. Any overdue invoice is a churn signal.
        data_type: NUMBER
      - name: avg_days_to_pay
        expr: avg_days_to_pay
        description: Average days to pay invoices. Increasing payment times precede churn.
        data_type: NUMBER
"""

AGENT_RESPONSE_INSTRUCTIONS = (
    "You are an Account Health Intelligence agent. You must SHOW YOUR WORK in every answer.\n\n"
    "1. ALWAYS start by querying the structured data to get the numbers. Present these as a data table.\n\n"
    "2. THEN search the unstructured sources to find the HUMAN STORY behind the numbers. "
    "Quote specific people by name and title. Include exact dollar amounts, dates, and competitor names.\n\n"
    "3. For every claim, cite the evidence.\n\n"
    "4. When recommending actions, quantify the impact with dollar amounts.\n\n"
    "5. End every answer with THREE suggestions:\n"
    "   a) A dbt model or semantic YAML change to make this insight permanent\n"
    "   b) A report or dashboard the team should build\n"
    "   c) Additional data sources that would sharpen the analysis"
)

AGENT_ORCHESTRATION_INSTRUCTIONS = (
    "For EVERY question, use MULTIPLE tools. "
    "First use analyst for numbers, then search tools for human context. "
    "For complex questions, use ALL tools. Never answer with just data or just search."
)

AGENT_SAMPLE_QUESTIONS = [
    {"question": "What can I do to increase NRR by 10 percent right now?"},
    {"question": "Why are accounts churning? What do they have in common?"},
    {"question": "Were there early warning signs we missed? Check the internal notes."},
    {"question": "What do our healthiest accounts do differently from our struggling ones?"},
    {"question": "Are we giving discounts to the wrong accounts?"},
    {"question": "Show me every competitor mention across all customer conversations"},
    {"question": "Are we making the same mistakes repeatedly?"},
    {"question": "What should I tell the board about customer health right now?"},
]

AGENT_TOOLS = [
    {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "analyst",
        "description": "Query structured account health metrics: ARR, feature adoption, discounts, usage trends, NPS, seat utilization, pipeline"}},
    {"tool_spec": {"type": "cortex_search", "name": "gong_search",
        "description": "Search Gong call transcripts for customer conversations"}},
    {"tool_spec": {"type": "cortex_search", "name": "ticket_search",
        "description": "Search support tickets for customer complaints and escalations"}},
    {"tool_spec": {"type": "cortex_search", "name": "csm_notes_search",
        "description": "Search internal CSM notes for risk flags and early warnings"}},
    {"tool_spec": {"type": "data_to_chart", "name": "data_to_chart",
        "description": "Generate charts from query results"}},
]

AGENT_TOOL_RESOURCES = {
    "analyst": {
        "semantic_model_file": "@DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/account_health.yaml",
        "execution_environment": {"type": "warehouse", "warehouse": "COMPUTE_WH"},
    },
    "gong_search": {"name": "DIGITALNATIVECO.MARTS.GONG_TRANSCRIPT_SEARCH", "max_results": 5},
    "ticket_search": {"name": "DIGITALNATIVECO.MARTS.SUPPORT_TICKET_SEARCH", "max_results": 5},
    "csm_notes_search": {"name": "DIGITALNATIVECO.MARTS.CSM_NOTES_SEARCH", "max_results": 5},
}


# =========================================================================
# Main
# =========================================================================
CHECKPOINTS = {
    "raw": [],
    "lab1": [setup_lab1],
    "lab2": [setup_lab1, setup_lab2],
    "lab3": [setup_lab1, setup_lab2],  # lab3 is lab2 + agent already configured
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CHECKPOINTS:
        print(f"Usage: python {sys.argv[0]} <checkpoint>")
        print(f"  Checkpoints: {', '.join(CHECKPOINTS.keys())}")
        sys.exit(1)

    target = sys.argv[1]
    print(f"Setting up lab at checkpoint: {target}")
    print(f"  Account: {os.environ.get('VITE_SNOWFLAKE_ACCOUNT', '?')}")
    print()

    teardown()

    for fn in CHECKPOINTS[target]:
        fn()

    print(f"\n{'='*50}")
    print(f"  Checkpoint '{target}' ready!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
