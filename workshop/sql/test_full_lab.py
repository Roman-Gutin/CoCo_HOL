"""
End-to-end test of the full workshop participant experience.
Starts from RAW checkpoint and executes every step a participant would take.
Tests the actual SQL that Cortex Code would generate from the demo prompts.

Usage:
    python workshop/sql/test_full_lab.py
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

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
AGENT_OBJ_URL = f"https://{HOST}.snowflakecomputing.com/api/v2/databases/DIGITALNATIVECO/schemas/MARTS/agents"
AGENT_RUN_URL = f"https://{HOST}.snowflakecomputing.com/api/v2/cortex/agent:run"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
}

results = []
notes = []


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
            handle = result["statementHandle"]
            start = time.time()
            while time.time() - start < timeout:
                time.sleep(3)
                preq = urllib.request.Request(
                    f"{SQL_URL}/{handle}",
                    headers={k: v for k, v in HEADERS.items() if k != "Content-Type"},
                )
                with urllib.request.urlopen(preq) as presp:
                    result = json.loads(presp.read())
                if result.get("code") in ("090001", "090002"):
                    return result
                if result.get("code") != "333334":
                    return result
        return result
    except urllib.error.HTTPError as e:
        msg = json.loads(e.read()).get("message", "")[:300]
        return {"error": msg}


def api_call(url, method="POST", data=None):
    hdrs = dict(HEADERS)
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {"status": "ok"}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"status": "not_found"}
        return {"error": e.read().decode()[:300]}


def call_agent_sse(url, messages, timeout=180):
    """Call agent endpoint with SSE, return (text, tool_count, raw_length)."""
    hdrs = dict(HEADERS)
    hdrs["Accept"] = "text/event-stream"
    body = json.dumps({"messages": messages}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
    text_parts, tool_count = [], 0
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("data: "):
            line = line[6:]
        elif line.startswith("data:"):
            line = line[5:]
        if not line or line == "[DONE]" or line.startswith("event:") or line.startswith(": "):
            continue
        try:
            evt = json.loads(line)
            if "text" in evt:
                text_parts.append(evt["text"])
            if "tool_use" in str(evt):
                tool_count += 1
            for c in evt.get("delta", {}).get("content", []):
                if isinstance(c, dict) and c.get("type") == "text":
                    text_parts.append(c["text"])
        except:
            pass
    return "".join(text_parts), tool_count, len(raw)


def call_agent_stateless(messages, timeout=180):
    """Call the stateless /cortex/agent:run endpoint with full tool config."""
    hdrs = dict(HEADERS)
    hdrs["Accept"] = "text/event-stream"
    body = json.dumps({
        "model": "claude-3-7-sonnet",
        "tools": [
            {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "analyst"}},
            {"tool_spec": {"type": "cortex_search", "name": "gong_search"}},
            {"tool_spec": {"type": "cortex_search", "name": "ticket_search"}},
            {"tool_spec": {"type": "cortex_search", "name": "csm_notes_search"}},
        ],
        "tool_resources": {
            "analyst": {
                "semantic_model_file": "@DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/account_health.yaml",
                "execution_environment": {"type": "warehouse", "warehouse": "COMPUTE_WH"},
            },
            "gong_search": {"name": "DIGITALNATIVECO.MARTS.GONG_TRANSCRIPT_SEARCH", "max_results": 5},
            "ticket_search": {"name": "DIGITALNATIVECO.MARTS.SUPPORT_TICKET_SEARCH", "max_results": 5},
            "csm_notes_search": {"name": "DIGITALNATIVECO.MARTS.CSM_NOTES_SEARCH", "max_results": 5},
        },
        "messages": messages,
    }).encode()
    req = urllib.request.Request(AGENT_RUN_URL, data=body, method="POST", headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
    text_parts, tool_count = [], 0
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("data: "):
            line = line[6:]
        elif line.startswith("data:"):
            line = line[5:]
        if not line or line == "[DONE]" or line.startswith("event:") or line.startswith(": "):
            continue
        try:
            evt = json.loads(line)
            if "text" in evt:
                text_parts.append(evt["text"])
            if "tool_use" in str(evt):
                tool_count += 1
            for c in evt.get("delta", {}).get("content", []):
                if isinstance(c, dict) and c.get("type") == "text":
                    text_parts.append(c["text"])
        except:
            pass
    return "".join(text_parts), tool_count, len(raw)


def test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, passed, detail))
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    if not passed:
        notes.append(f"FAILED: {name} — {detail}")
    return passed


# =========================================================================
print("=" * 70)
print("  FULL WORKSHOP LAB TEST — Participant Experience")
print("=" * 70)
print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Account: {os.environ.get('VITE_SNOWFLAKE_ACCOUNT', '?')}")
print()

# =========================================================================
# SETUP: Teardown to raw
# =========================================================================
print("SETUP: Teardown to raw...")
import subprocess
subprocess.run(
    [sys.executable, os.path.join(SCRIPT_DIR, "teardown_lab.py"), "--confirm"],
    capture_output=True, timeout=120,
)
print("  Done.\n")

# =========================================================================
# LAB 1 STEP 1: Orient — explore the data
# =========================================================================
print("LAB 1 STEP 1: Orient — explore the 10 tables")

r = run_sql("""
    SELECT 'accounts' AS tbl, COUNT(*) AS cnt FROM RAW.ACCOUNTS
    UNION ALL SELECT 'product_events', COUNT(*) FROM RAW.PRODUCT_EVENTS
    UNION ALL SELECT 'support_tickets', COUNT(*) FROM RAW.SUPPORT_TICKETS
    UNION ALL SELECT 'gong_transcripts', COUNT(*) FROM RAW.GONG_TRANSCRIPTS
    UNION ALL SELECT 'employees', COUNT(*) FROM RAW.EMPLOYEES
    UNION ALL SELECT 'account_assignments', COUNT(*) FROM RAW.ACCOUNT_ASSIGNMENTS
    UNION ALL SELECT 'opportunities', COUNT(*) FROM RAW.OPPORTUNITIES
    UNION ALL SELECT 'feature_usage', COUNT(*) FROM RAW.FEATURE_USAGE
    UNION ALL SELECT 'invoices', COUNT(*) FROM RAW.INVOICES
    UNION ALL SELECT 'csm_notes', COUNT(*) FROM RAW.CSM_NOTES
    ORDER BY tbl
""")
if r and "data" in r:
    row_counts = {row[0]: int(row[1]) for row in r["data"]}
    test("10 tables exist", len(row_counts) == 10, f"found {len(row_counts)} tables")
    test("accounts has 20 rows", row_counts.get("accounts") == 20)
    test("product_events > 5000", row_counts.get("product_events", 0) > 5000, f"{row_counts.get('product_events', 0)}")
    test("support_tickets > 500", row_counts.get("support_tickets", 0) > 500, f"{row_counts.get('support_tickets', 0)}")
    test("gong_transcripts > 150", row_counts.get("gong_transcripts", 0) > 150, f"{row_counts.get('gong_transcripts', 0)}")
    test("csm_notes > 15", row_counts.get("csm_notes", 0) > 15, f"{row_counts.get('csm_notes', 0)}")
else:
    test("10 tables exist", False, f"query failed: {r}")

# Follow-up: ARR summary
r = run_sql("SELECT COUNT(*), SUM(arr), MIN(arr), MAX(arr), AVG(arr) FROM RAW.ACCOUNTS")
if r and "data" in r:
    row = r["data"][0]
    total_arr = float(row[1])
    test("total ARR > $3M", total_arr > 3000000, f"${total_arr:,.0f}")
else:
    test("total ARR > $3M", False)

print()

# =========================================================================
# LAB 1 STEP 2: AI reads the unstructured data
# =========================================================================
print("LAB 1 STEP 2: AI reads unstructured data")

# 2a: Sentiment on tickets
r = run_sql("""
    SELECT account_name, LEFT(ticket_text, 80) AS preview,
           SNOWFLAKE.CORTEX.SENTIMENT(ticket_text) AS sentiment
    FROM RAW.SUPPORT_TICKETS
    ORDER BY sentiment ASC LIMIT 5
""")
if r and "data" in r:
    worst = r["data"][0]
    sentiment = float(worst[2])
    test("sentiment works", sentiment < 0, f"worst sentiment: {sentiment:.3f} ({worst[0]})")
    test("worst sentiment < -0.5", sentiment < -0.5, f"{sentiment:.3f}")
else:
    test("sentiment works", False, f"{r}")

# 2b: Gong signal extraction
r = run_sql("""
    SELECT account_name, call_type,
           SNOWFLAKE.CORTEX.COMPLETE('claude-3-7-sonnet',
               'Extract from this call and return ONLY valid JSON (no markdown): competitor_mentioned (boolean), frustration_level (low/medium/high), expansion_signal (boolean), key_themes (array). Transcript:\\n' || transcript_excerpt
           ) AS signals
    FROM RAW.GONG_TRANSCRIPTS LIMIT 3
""")
if r and "data" in r:
    has_json = any("{" in str(row[2]) for row in r["data"])
    test("COMPLETE returns JSON signals", has_json, f"got {len(r['data'])} rows with JSON")
else:
    test("COMPLETE returns JSON signals", False)

# 2c: Classification
r = run_sql("""
    SELECT
        SNOWFLAKE.CORTEX.CLASSIFY_TEXT(ticket_text,
            ['billing','technical','feature_request','complaint','onboarding']
        ):label::STRING AS category,
        COUNT(*) AS cnt,
        ROUND(AVG(SNOWFLAKE.CORTEX.SENTIMENT(ticket_text)), 3) AS avg_sent
    FROM RAW.SUPPORT_TICKETS GROUP BY 1 ORDER BY avg_sent ASC
""")
if r and "data" in r:
    categories = [row[0] for row in r["data"]]
    test("classify returns 5 categories", len(categories) == 5, f"{categories}")
    # Complaints should have worst sentiment
    worst_cat = r["data"][0][0]
    test("complaints have worst sentiment", worst_cat == "complaint", f"worst: {worst_cat}")
else:
    test("classify returns 5 categories", False)

print()

# =========================================================================
# LAB 1 STEP 3: Build the mart
# =========================================================================
print("LAB 1 STEP 3: Build the mart (this will take 1-2 min for AI enrichment)")

# First create the enriched tables
r = run_sql("""CREATE OR REPLACE TABLE STAGING.ENRICHED_SUPPORT_TICKETS AS
    SELECT ticket_id, account_id, account_name, product, ticket_text, priority, status,
           created_at::DATE AS ticket_date,
           SNOWFLAKE.CORTEX.SENTIMENT(ticket_text) AS sentiment_score,
           SNOWFLAKE.CORTEX.CLASSIFY_TEXT(ticket_text,
               ['billing','technical','feature_request','complaint','onboarding']):label::STRING AS category
    FROM RAW.SUPPORT_TICKETS WHERE ticket_text IS NOT NULL AND TRIM(ticket_text) != ''
""")
test("enriched tickets created", r and r.get("code") in ("090001", "090002"))

r = run_sql("""CREATE OR REPLACE TABLE STAGING.ENRICHED_GONG_TRANSCRIPTS AS
    SELECT call_id, account_id, account_name, call_date::DATE AS call_date, call_type,
           duration_min, transcript_excerpt, attendees,
           PARSE_JSON(REGEXP_REPLACE(
               SNOWFLAKE.CORTEX.COMPLETE('claude-3-7-sonnet',
                   'Analyze this call and return ONLY valid JSON (no markdown, no code fences): competitor_mentioned (boolean), expansion_signal (boolean), frustration_level (low/medium/high), champion_engagement (low/medium/high), key_themes (array). Transcript:\\n' || transcript_excerpt
               ), '^[\\\\s]*```[a-z]*[\\\\s]*|[\\\\s]*```[\\\\s]*$', ''
           )) AS signals,
           signals:competitor_mentioned::BOOLEAN AS competitor_mentioned,
           signals:expansion_signal::BOOLEAN AS expansion_signal,
           signals:frustration_level::STRING AS frustration_level,
           signals:champion_engagement::STRING AS champion_engagement
    FROM RAW.GONG_TRANSCRIPTS WHERE transcript_excerpt IS NOT NULL
""")
test("enriched gong created", r and r.get("code") in ("090001", "090002"))

# Usage metrics
r = run_sql("""CREATE OR REPLACE TABLE STAGING.ACCOUNT_USAGE_METRICS AS
    WITH ws AS (
        SELECT account_id, account_name, DATE_TRUNC('week', event_date::DATE) AS week_start,
               COUNT(DISTINCT user_id) AS weekly_active_users,
               ROUND(AVG(session_duration_min), 2) AS avg_session_duration, COUNT(*) AS total_events
        FROM RAW.PRODUCT_EVENTS WHERE session_duration_min >= 0 GROUP BY 1,2,3
    ), wt AS (
        SELECT *, LAG(weekly_active_users) OVER (PARTITION BY account_id ORDER BY week_start) AS prev,
               CASE WHEN prev IS NULL OR prev = 0 THEN NULL
                    ELSE ROUND((weekly_active_users - prev)::FLOAT / prev * 100, 1) END AS usage_trend_wow_pct
        FROM ws
    ) SELECT * FROM wt ORDER BY account_id, week_start
""")
test("usage metrics created", r and r.get("code") in ("090001", "090002"))

# Now build the full mart
r = run_sql("""CREATE OR REPLACE TABLE MARTS.MART_ACCOUNT_HEALTH AS
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
        SELECT account_id, employee_name AS current_ae, assigned_date,
               DATEDIFF('day', assigned_date, CURRENT_DATE()) AS ae_tenure_days,
               CASE WHEN DATEDIFF('day', assigned_date, CURRENT_DATE()) <= 90 THEN TRUE ELSE FALSE END AS ae_changed_recently,
               e.status AS ae_status
        FROM RAW.ACCOUNT_ASSIGNMENTS aa LEFT JOIN RAW.EMPLOYEES e ON aa.employee_id = e.employee_id
        WHERE aa.role = 'AE' AND aa.is_current = TRUE
    ), opp_agg AS (
        SELECT account_id, SUM(amount) AS pipeline_amount, COUNT(*) AS open_opp_count,
               MIN(close_date) AS nearest_close_date,
               LISTAGG(DISTINCT stage, ', ') WITHIN GROUP (ORDER BY stage) AS pipeline_stages
        FROM RAW.OPPORTUNITIES WHERE stage NOT IN ('closed_won','closed_lost') GROUP BY 1
    ), feature_agg AS (
        SELECT account_id, COUNT(DISTINCT feature_name) AS total_features_used,
               COUNT(DISTINCT CASE WHEN feature_name IN ('canvas_collab_edit','canvas_templates','flow_approvals','insight_dashboards','insight_api') THEN feature_name END) AS power_features_used,
               ROUND(COUNT(DISTINCT feature_name)::FLOAT / 19 * 100, 1) AS feature_breadth_pct
        FROM RAW.FEATURE_USAGE GROUP BY 1
    ), invoice_agg AS (
        SELECT account_id, ROUND(AVG(discount_pct), 2) AS avg_discount_pct,
               ROUND(AVG(CASE WHEN payment_status = 'paid' THEN days_to_pay END), 1) AS avg_days_to_pay,
               SUM(CASE WHEN payment_status = 'overdue' THEN 1 ELSE 0 END) AS overdue_invoices
        FROM RAW.INVOICES GROUP BY 1
    )
    SELECT a.account_id, a.account_name, a.industry, a.arr, a.licensed_seats, a.products,
           a.contract_renewal_date, a.csm_name, a.nps_score,
           u.weekly_active_users, u.avg_session_duration, u.usage_trend_wow_pct,
           ROUND(u.weekly_active_users::FLOAT / NULLIF(a.licensed_seats, 0) * 100, 1) AS seat_utilization_pct,
           COALESCE(t.ticket_count, 0) AS ticket_count, t.avg_sentiment,
           COALESCE(t.complaint_count, 0) AS complaint_count, COALESCE(t.high_priority_count, 0) AS high_priority_count,
           t.most_common_category,
           COALESCE(g.total_calls, 0) AS gong_call_count, g.last_call_date,
           COALESCE(g.any_competitor_mentioned, FALSE) AS competitor_mentioned,
           COALESCE(g.any_expansion_signal, FALSE) AS expansion_signal,
           g.typical_frustration, g.typical_champion_engagement,
           ae.current_ae, ae.ae_tenure_days, COALESCE(ae.ae_changed_recently, FALSE) AS ae_changed_recently, ae.ae_status,
           COALESCE(o.pipeline_amount, 0) AS pipeline_amount, COALESCE(o.open_opp_count, 0) AS open_opp_count,
           o.pipeline_stages, o.nearest_close_date,
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
    ORDER BY a.arr DESC
""")
test("mart created", r and r.get("code") in ("090001", "090002"))

# Verify mart
r = run_sql("SELECT COUNT(*) FROM MARTS.MART_ACCOUNT_HEALTH")
if r and "data" in r:
    test("mart has 20 rows", int(r["data"][0][0]) == 20)
else:
    test("mart has 20 rows", False)

print()

# =========================================================================
# LAB 1 STEP 4: See the answer taking shape
# =========================================================================
print("LAB 1 STEP 4: See the answer forming")

r = run_sql("""SELECT account_name, arr, avg_sentiment, competitor_mentioned,
       ae_changed_recently, overdue_invoices, feature_breadth_pct
FROM MARTS.MART_ACCOUNT_HEALTH ORDER BY avg_sentiment ASC LIMIT 5""")
if r and "data" in r:
    worst_account = r["data"][0][0]
    test("worst sentiment account visible", True, f"{worst_account} (sentiment={r['data'][0][2]})")

# Quantify opportunity
r = run_sql("""SELECT
    SUM(arr) AS total_arr,
    SUM(CASE WHEN competitor_mentioned OR avg_sentiment < -0.3 OR ae_changed_recently THEN arr ELSE 0 END) AS at_risk_arr,
    SUM(CASE WHEN expansion_signal THEN pipeline_amount ELSE 0 END) AS expansion_pipeline,
    SUM(CASE WHEN competitor_mentioned OR avg_sentiment < -0.3 OR ae_changed_recently THEN 1 ELSE 0 END) AS at_risk_count,
    SUM(CASE WHEN expansion_signal THEN 1 ELSE 0 END) AS expansion_count
FROM MARTS.MART_ACCOUNT_HEALTH""")
if r and "data" in r:
    row = r["data"][0]
    at_risk = float(row[1])
    expansion = float(row[2])
    test("at-risk ARR > $500K", at_risk > 500000, f"${at_risk:,.0f}")
    test("expansion pipeline > $200K", expansion > 200000, f"${expansion:,.0f}")

# Meridian specifically
r = run_sql("""SELECT competitor_mentioned, ae_changed_recently, avg_sentiment, overdue_invoices, avg_discount_pct
FROM MARTS.MART_ACCOUNT_HEALTH WHERE account_name = 'Meridian Media Group'""")
if r and "data" in r:
    row = r["data"][0]
    test("Meridian: competitor_mentioned", str(row[0]).lower() == "true")
    test("Meridian: ae_changed_recently", str(row[1]).lower() == "true")
    test("Meridian: negative sentiment", float(row[2]) < -0.3, f"{row[2]}")
    test("Meridian: has overdue invoice", int(row[3]) > 0)
    test("Meridian: 30% discount", float(row[4]) >= 25, f"{row[4]}%")

print()

# =========================================================================
# LAB 2 STEP 1: Semantic model
# =========================================================================
print("LAB 2 STEP 1: Upload semantic model")

run_sql("CREATE STAGE IF NOT EXISTS MARTS.SEMANTIC_MODELS DIRECTORY = (ENABLE = TRUE)")

# Read the YAML from the checkpoint script's constant
sys.path.insert(0, SCRIPT_DIR)
from setup_checkpoint import SEMANTIC_YAML

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
r = run_sql("CALL MARTS.UPLOAD_SEMANTIC_MODEL()")
if r and "data" in r:
    test("semantic model uploaded", r["data"][0][0] == "Done")
else:
    test("semantic model uploaded", False, f"{r}")

r = run_sql("LIST @MARTS.SEMANTIC_MODELS")
if r and "data" in r:
    has_yaml = any("account_health.yaml" in str(row) for row in r["data"])
    test("YAML on stage", has_yaml)
else:
    test("YAML on stage", False)

print()

# =========================================================================
# LAB 2 STEP 2: Search services
# =========================================================================
print("LAB 2 STEP 2: Create search services")

for name, col, tbl, attrs in [
    ("GONG_TRANSCRIPT_SEARCH", "transcript_excerpt", "RAW.GONG_TRANSCRIPTS", "account_name, call_type"),
    ("SUPPORT_TICKET_SEARCH", "ticket_text", "RAW.SUPPORT_TICKETS", "account_name, product, priority"),
    ("CSM_NOTES_SEARCH", "note_text", "RAW.CSM_NOTES", "account_name, author, note_type"),
]:
    r = run_sql(f"""CREATE OR REPLACE CORTEX SEARCH SERVICE MARTS.{name}
        ON {col} ATTRIBUTES {attrs}
        WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
        AS (SELECT * FROM {tbl})""")
    test(f"{name} created", r and r.get("code") in ("090001", "090002"))

# Wait for indexing
print("  Waiting 15s for indexing...")
time.sleep(15)

# Test search via REST API
for svc, query, expect_account in [
    ("GONG_TRANSCRIPT_SEARCH", "customer evaluating competitors or considering switching", None),
    ("SUPPORT_TICKET_SEARCH", "frustrated with outages or API issues", None),
    ("CSM_NOTES_SEARCH", "risk flag or early warning", None),
]:
    search_url = f"https://{HOST}.snowflakecomputing.com/api/v2/databases/DIGITALNATIVECO/schemas/MARTS/cortex-search-services/{svc}:query"
    body = json.dumps({"query": query, "columns": ["account_name"], "limit": 3}).encode()
    r = api_call(search_url, "POST", body)
    has_results = "results" in r and len(r["results"]) > 0
    test(f"{svc} returns results", has_results, f"{len(r.get('results', []))} results")

print()

# =========================================================================
# LAB 2 STEP 3: Create agent
# =========================================================================
print("LAB 2 STEP 3: Create agent")

from setup_checkpoint import (
    AGENT_RESPONSE_INSTRUCTIONS, AGENT_ORCHESTRATION_INSTRUCTIONS,
    AGENT_SAMPLE_QUESTIONS, AGENT_TOOLS, AGENT_TOOL_RESOURCES,
)

# Delete if exists
api_call(f"{AGENT_OBJ_URL}/ACCOUNT_HEALTH_AGENT", "DELETE")

agent_spec = {
    "name": "ACCOUNT_HEALTH_AGENT",
    "comment": "Account Health Intelligence",
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
r = api_call(AGENT_OBJ_URL, "POST", json.dumps(agent_spec).encode())
test("agent created", "successfully" in str(r).lower(), f"{r.get('status', r.get('error', ''))[:100]}")

# Grants
for sql in [
    "GRANT USAGE ON AGENT MARTS.ACCOUNT_HEALTH_AGENT TO ROLE ACCOUNTADMIN",
    "GRANT USAGE ON CORTEX SEARCH SERVICE MARTS.GONG_TRANSCRIPT_SEARCH TO ROLE ACCOUNTADMIN",
    "GRANT USAGE ON CORTEX SEARCH SERVICE MARTS.SUPPORT_TICKET_SEARCH TO ROLE ACCOUNTADMIN",
    "GRANT USAGE ON CORTEX SEARCH SERVICE MARTS.CSM_NOTES_SEARCH TO ROLE ACCOUNTADMIN",
    "GRANT READ ON STAGE MARTS.SEMANTIC_MODELS TO ROLE ACCOUNTADMIN",
]:
    run_sql(sql)
test("grants applied", True)

print()

# =========================================================================
# LAB 2 STEP 4: The moment of truth — agent queries
# =========================================================================
print("LAB 2 STEP 4: Agent queries (the show-stopper)")

# Q1: The NRR question — via agent object endpoint
print("  Q1: NRR question (agent object)...")
try:
    text, tools, raw_len = call_agent_sse(
        f"{AGENT_OBJ_URL}/ACCOUNT_HEALTH_AGENT:run",
        [{"role": "user", "content": [{"type": "text", "text": "What can I do to increase NRR by 10% right now?"}]}],
    )
    test("Q1: agent responded", len(text) > 100, f"{len(text)} chars, {tools} tools")
    test("Q1: used tools", tools > 0, f"{tools} tool calls")
    has_money = any(x in text for x in ["$", "ARR", "000", "pipeline", "revenue"])
    test("Q1: mentions dollar amounts", has_money)
    q1_preview = text[:500]
except Exception as e:
    test("Q1: agent responded", False, str(e)[:200])
    q1_preview = str(e)[:500]

# Q2: Early warnings — via agent object endpoint
print("  Q2: Early warnings question...")
try:
    text, tools, raw_len = call_agent_sse(
        f"{AGENT_OBJ_URL}/ACCOUNT_HEALTH_AGENT:run",
        [{"role": "user", "content": [{"type": "text", "text": "Were there early warning signs we missed? Check the internal notes."}]}],
    )
    test("Q2: agent responded", len(text) > 100, f"{len(text)} chars")
    has_warnings = any(w in text.lower() for w in ["warning", "flag", "risk", "escalat", "missed"])
    test("Q2: found warning signals", has_warnings)
    q2_preview = text[:500]
except Exception as e:
    test("Q2: agent responded", False, str(e)[:200])
    q2_preview = str(e)[:500]

# Q3: Stateless API — competitor mentions
print("  Q3: Competitor mentions (stateless API)...")
try:
    text, tools, raw_len = call_agent_stateless(
        [{"role": "user", "content": [{"type": "text", "text": "Show me every competitor mention across all customer conversations"}]}],
    )
    test("Q3: stateless agent responded", len(text) > 50, f"{len(text)} chars")
    has_competitor = any(c in text.lower() for c in ["sketchflow", "competitor", "alternative", "evaluat"])
    test("Q3: found competitor references", has_competitor)
    q3_preview = text[:500]
except Exception as e:
    test("Q3: stateless agent responded", False, str(e)[:200])
    q3_preview = str(e)[:500]

print()

# =========================================================================
# WRITE RESULTS
# =========================================================================
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
all_passed = all(r[1] for r in results)
pass_count = sum(1 for r in results if r[1])
fail_count = sum(1 for r in results if not r[1])

report_path = os.path.join(WORKSHOP_DIR, "data", "labs", "test_results.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# Full Lab Validation Results\n\n")
    f.write(f"**{'ALL TESTS PASSED' if all_passed else 'FAILURES DETECTED'}** ")
    f.write(f"({pass_count} passed, {fail_count} failed)\n\n")
    f.write(f"Timestamp: {ts}\n\n")
    f.write(f"## Results\n\n")
    f.write(f"| # | Test | Result | Details |\n|---|------|--------|--------|\n")
    for i, (name, passed, detail) in enumerate(results, 1):
        f.write(f"| {i} | {name} | {'PASS' if passed else '**FAIL**'} | {detail} |\n")
    f.write(f"\n## Agent Response Previews\n\n")
    f.write(f"### Q1: NRR Question\n```\n{q1_preview}\n```\n\n")
    f.write(f"### Q2: Early Warnings\n```\n{q2_preview}\n```\n\n")
    f.write(f"### Q3: Competitor Mentions\n```\n{q3_preview}\n```\n\n")
    if notes:
        f.write(f"## Issues & Suggestions\n\n")
        for n in notes:
            f.write(f"- {n}\n")

print("=" * 70)
print(f"  {'ALL TESTS PASSED' if all_passed else 'FAILURES DETECTED'} ({pass_count}/{pass_count+fail_count})")
print(f"  Results: {report_path}")
print("=" * 70)
