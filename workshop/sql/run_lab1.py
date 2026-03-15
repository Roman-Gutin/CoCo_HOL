"""
Run Lab 1 SQL statements against Snowflake via SQL API.
Skips Cortex Code interactive steps — runs the SQL directly.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSHOP_DIR = os.path.dirname(SCRIPT_DIR)

# Load env
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
    body = {
        "statement": stmt,
        "warehouse": WH,
        "role": ROLE,
        "database": DB,
        "timeout": timeout,
    }
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
        print(f"  ERROR: {err.get('message', '')[:200]}")
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
        elapsed = int(time.time() - start)
        print(f"    ... still running ({elapsed}s)", flush=True)
    print("  TIMEOUT")
    return None


def show_results(result, max_rows=10):
    if not result or "data" not in result:
        return
    meta = result.get("resultSetMetaData", {})
    cols = [c["name"] for c in meta.get("rowType", [])]
    num_rows = meta.get("numRows", 0)

    # Print header
    if cols:
        header = " | ".join(f"{c[:25]:25s}" for c in cols)
        print(f"  {header}")
        print(f"  {'-' * len(header)}")

    for i, row in enumerate(result["data"][:max_rows]):
        vals = " | ".join(f"{str(v)[:25]:25s}" for v in row)
        print(f"  {vals}")

    if num_rows > max_rows:
        print(f"  ... ({num_rows} total rows)")
    print()


def step(name, sql, show=True, max_rows=10):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  SQL: {sql[:120]}...")
    start = time.time()
    result = run_sql(sql)
    elapsed = round(time.time() - start, 1)

    if result and result.get("code") in ("090001", "090002"):
        num_rows = result.get("resultSetMetaData", {}).get("numRows", 0)
        print(f"  OK ({elapsed}s, {num_rows} rows)")
        if show:
            show_results(result, max_rows)
    else:
        print(f"  FAILED ({elapsed}s)")
        if result:
            print(f"  {result.get('message', '')[:300]}")
    return result


def main():
    print("=" * 60)
    print("  LAB 1: Data Engineering + AI Enrichment")
    print("=" * 60)

    # Setup: verify data
    step("Setup: Row counts", """
        SELECT 'accounts' AS source, COUNT(*) AS row_count FROM RAW.ACCOUNTS
        UNION ALL SELECT 'support_tickets', COUNT(*) FROM RAW.SUPPORT_TICKETS
        UNION ALL SELECT 'gong_transcripts', COUNT(*) FROM RAW.GONG_TRANSCRIPTS
        UNION ALL SELECT 'product_events', COUNT(*) FROM RAW.PRODUCT_EVENTS
        UNION ALL SELECT 'employees', COUNT(*) FROM RAW.EMPLOYEES
        UNION ALL SELECT 'account_assignments', COUNT(*) FROM RAW.ACCOUNT_ASSIGNMENTS
        UNION ALL SELECT 'opportunities', COUNT(*) FROM RAW.OPPORTUNITIES
    """)

    # Step 1: Staging views
    step("Step 1a: Stage support tickets", """
        CREATE OR REPLACE VIEW STAGING.STG_SUPPORT_TICKETS AS
        SELECT
            TICKET_ID, ACCOUNT_ID, ACCOUNT_NAME, PRODUCT,
            TRIM(TICKET_TEXT) AS TICKET_TEXT,
            PRIORITY, STATUS,
            CREATED_AT::TIMESTAMP_NTZ AS CREATED_AT,
            CREATED_AT::DATE AS TICKET_DATE
        FROM RAW.SUPPORT_TICKETS
        WHERE TICKET_TEXT IS NOT NULL AND TRIM(TICKET_TEXT) != ''
    """, show=False)

    step("Step 1b: Stage Gong transcripts", """
        CREATE OR REPLACE VIEW STAGING.STG_GONG_TRANSCRIPTS AS
        SELECT
            CALL_ID, ACCOUNT_ID, ACCOUNT_NAME,
            CALL_DATE::TIMESTAMP_NTZ AS CALL_DATE,
            CALL_DATE::DATE AS CALL_DATE_DT,
            CALL_TYPE, DURATION_MIN,
            TRIM(TRANSCRIPT_EXCERPT) AS TRANSCRIPT_EXCERPT,
            ATTENDEES
        FROM RAW.GONG_TRANSCRIPTS
        WHERE TRANSCRIPT_EXCERPT IS NOT NULL AND TRIM(TRANSCRIPT_EXCERPT) != ''
    """, show=False)

    step("Step 1c: Stage product events", """
        CREATE OR REPLACE VIEW STAGING.STG_PRODUCT_EVENTS AS
        SELECT
            EVENT_ID, ACCOUNT_ID, ACCOUNT_NAME, USER_ID, PRODUCT,
            EVENT_TYPE,
            EVENT_DATE::TIMESTAMP_NTZ AS EVENT_DATE,
            EVENT_DATE::DATE AS EVENT_DATE_DT,
            SESSION_DURATION_MIN
        FROM RAW.PRODUCT_EVENTS
        WHERE SESSION_DURATION_MIN IS NOT NULL AND SESSION_DURATION_MIN >= 0
    """, show=False)

    step("Step 1d: Stage employees", """
        CREATE OR REPLACE VIEW STAGING.STG_EMPLOYEES AS
        SELECT
            EMPLOYEE_ID, NAME, TITLE, ROLE, DEPARTMENT,
            HIRE_DATE::DATE AS HIRE_DATE,
            DEPARTURE_DATE::DATE AS DEPARTURE_DATE,
            DEPARTURE_REASON, STATUS,
            CASE WHEN STATUS = 'active' THEN TRUE ELSE FALSE END AS IS_ACTIVE
        FROM RAW.EMPLOYEES
    """, show=False)

    step("Step 1e: Stage account assignments", """
        CREATE OR REPLACE VIEW STAGING.STG_ACCOUNT_ASSIGNMENTS AS
        SELECT
            ASSIGNMENT_ID, ACCOUNT_ID, ACCOUNT_NAME,
            EMPLOYEE_ID, EMPLOYEE_NAME, ROLE,
            ASSIGNED_DATE::DATE AS ASSIGNED_DATE,
            UNASSIGNED_DATE::DATE AS UNASSIGNED_DATE,
            IS_CURRENT
        FROM RAW.ACCOUNT_ASSIGNMENTS
    """, show=False)

    step("Step 1f: Stage opportunities", """
        CREATE OR REPLACE VIEW STAGING.STG_OPPORTUNITIES AS
        SELECT
            OPPORTUNITY_ID, ACCOUNT_ID, ACCOUNT_NAME,
            OPP_TYPE, OPP_NAME,
            AMOUNT::NUMBER(12,2) AS AMOUNT,
            STAGE,
            CLOSE_DATE::DATE AS CLOSE_DATE,
            OWNER_ID, OWNER_NAME,
            CREATED_DATE::DATE AS CREATED_DATE,
            NOTES
        FROM RAW.OPPORTUNITIES
    """, show=False)

    print("\n  All 6 staging views created.")

    # Step 2: Enrich support tickets
    step("Step 2a: Sentiment preview (5 rows)", """
        SELECT
            ticket_id,
            account_name,
            LEFT(ticket_text, 60) AS preview,
            SNOWFLAKE.CORTEX.SENTIMENT(ticket_text) AS sentiment
        FROM STAGING.STG_SUPPORT_TICKETS
        LIMIT 5
    """)

    step("Step 2b: Classification preview (5 rows)", """
        SELECT
            ticket_id,
            account_name,
            SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
                ticket_text,
                ['billing', 'technical', 'feature_request', 'complaint', 'onboarding']
            ):label::STRING AS category,
            ROUND(SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
                ticket_text,
                ['billing', 'technical', 'feature_request', 'complaint', 'onboarding']
            ):score::FLOAT, 3) AS confidence
        FROM STAGING.STG_SUPPORT_TICKETS
        LIMIT 5
    """)

    print("\n  Creating ENRICHED_SUPPORT_TICKETS (this calls AI on ~513 rows, may take 1-2 min)...")
    step("Step 2c: Persist enriched tickets", """
        CREATE OR REPLACE TABLE STAGING.ENRICHED_SUPPORT_TICKETS AS
        SELECT
            ticket_id, account_id, account_name, product, ticket_text,
            priority, status, ticket_date,
            SNOWFLAKE.CORTEX.SENTIMENT(ticket_text) AS sentiment_score,
            SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
                ticket_text,
                ['billing', 'technical', 'feature_request', 'complaint', 'onboarding']
            ):label::STRING AS category,
            SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
                ticket_text,
                ['billing', 'technical', 'feature_request', 'complaint', 'onboarding']
            ):score::FLOAT AS category_confidence
        FROM STAGING.STG_SUPPORT_TICKETS
    """, show=False)

    step("Step 2d: Category breakdown", """
        SELECT category, COUNT(*) AS cnt, ROUND(AVG(sentiment_score), 3) AS avg_sentiment
        FROM STAGING.ENRICHED_SUPPORT_TICKETS
        GROUP BY 1 ORDER BY 2 DESC
    """)

    # Step 3: Enrich Gong transcripts
    print("\n  Creating ENRICHED_GONG_TRANSCRIPTS (AI on ~157 transcripts, may take 2-4 min)...")
    step("Step 3: Persist enriched Gong transcripts", """
        CREATE OR REPLACE TABLE STAGING.ENRICHED_GONG_TRANSCRIPTS AS
        SELECT
            call_id, account_id, account_name,
            call_date_dt AS call_date, call_type, duration_min,
            transcript_excerpt, attendees,
            PARSE_JSON(
                REGEXP_REPLACE(
                    SNOWFLAKE.CORTEX.COMPLETE(
                        'claude-3-7-sonnet',
                        'Analyze this sales/CS call transcript and return ONLY valid JSON (no markdown, no code fences, just the raw JSON object) with these keys: competitor_mentioned (boolean), expansion_signal (boolean), frustration_level (low/medium/high), champion_engagement (low/medium/high), key_themes (array of short strings). Transcript:\\n' || transcript_excerpt
                    ),
                    '^[\\\\s]*```[a-z]*[\\\\s]*|[\\\\s]*```[\\\\s]*$', ''
                )
            ) AS signals,
            signals:competitor_mentioned::BOOLEAN AS competitor_mentioned,
            signals:expansion_signal::BOOLEAN AS expansion_signal,
            signals:frustration_level::STRING AS frustration_level,
            signals:champion_engagement::STRING AS champion_engagement,
            signals:key_themes::ARRAY AS key_themes
        FROM STAGING.STG_GONG_TRANSCRIPTS
    """, show=False)

    step("Step 3 verify: Gong signals sample", """
        SELECT account_name, competitor_mentioned, expansion_signal,
               frustration_level, champion_engagement
        FROM STAGING.ENRICHED_GONG_TRANSCRIPTS
        ORDER BY account_name LIMIT 10
    """)

    # Step 4: Usage metrics
    step("Step 4: Usage metrics with WoW trend", """
        CREATE OR REPLACE TABLE STAGING.ACCOUNT_USAGE_METRICS AS
        WITH weekly_stats AS (
            SELECT
                account_id, account_name,
                DATE_TRUNC('week', event_date_dt) AS week_start,
                COUNT(DISTINCT user_id) AS weekly_active_users,
                ROUND(AVG(session_duration_min), 2) AS avg_session_duration,
                COUNT(*) AS total_events
            FROM STAGING.STG_PRODUCT_EVENTS
            GROUP BY 1, 2, 3
        ),
        with_trend AS (
            SELECT *,
                LAG(weekly_active_users) OVER (PARTITION BY account_id ORDER BY week_start) AS prev_week_active_users,
                CASE
                    WHEN prev_week_active_users IS NULL OR prev_week_active_users = 0 THEN NULL
                    ELSE ROUND((weekly_active_users - prev_week_active_users)::FLOAT / prev_week_active_users * 100, 1)
                END AS usage_trend_wow_pct
            FROM weekly_stats
        )
        SELECT * FROM with_trend ORDER BY account_id, week_start
    """, show=False)

    step("Step 4 verify: Meridian usage trend", """
        SELECT week_start, weekly_active_users, usage_trend_wow_pct
        FROM STAGING.ACCOUNT_USAGE_METRICS
        WHERE account_name = 'Meridian Media Group'
        ORDER BY week_start
    """)

    # Step 5: Build the mart
    step("Step 5: Build MART_ACCOUNT_HEALTH", """
        CREATE OR REPLACE TABLE MARTS.MART_ACCOUNT_HEALTH AS
        WITH latest_usage AS (
            SELECT * FROM STAGING.ACCOUNT_USAGE_METRICS
            QUALIFY ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY week_start DESC) = 1
        ),
        ticket_agg AS (
            SELECT account_id, COUNT(*) AS ticket_count,
                ROUND(AVG(sentiment_score), 3) AS avg_sentiment,
                SUM(CASE WHEN category = 'complaint' THEN 1 ELSE 0 END) AS complaint_count,
                SUM(CASE WHEN priority IN ('P1', 'P2') THEN 1 ELSE 0 END) AS high_priority_count,
                MODE(category) AS most_common_category
            FROM STAGING.ENRICHED_SUPPORT_TICKETS GROUP BY 1
        ),
        gong_agg AS (
            SELECT account_id, COUNT(*) AS total_calls, MAX(call_date) AS last_call_date,
                BOOLOR_AGG(competitor_mentioned) AS any_competitor_mentioned,
                BOOLOR_AGG(expansion_signal) AS any_expansion_signal,
                MODE(frustration_level) AS typical_frustration,
                MODE(champion_engagement) AS typical_champion_engagement
            FROM STAGING.ENRICHED_GONG_TRANSCRIPTS GROUP BY 1
        ),
        current_ae AS (
            SELECT aa.account_id, aa.employee_name AS current_ae, aa.assigned_date,
                DATEDIFF('day', aa.assigned_date, CURRENT_DATE()) AS ae_tenure_days,
                CASE WHEN DATEDIFF('day', aa.assigned_date, CURRENT_DATE()) <= 90 THEN TRUE ELSE FALSE END AS ae_changed_recently,
                e.status AS ae_status
            FROM STAGING.STG_ACCOUNT_ASSIGNMENTS aa
            LEFT JOIN STAGING.STG_EMPLOYEES e ON aa.employee_id = e.employee_id
            WHERE aa.role = 'AE' AND aa.is_current = TRUE
        ),
        opp_agg AS (
            SELECT account_id, SUM(amount) AS pipeline_amount, COUNT(*) AS open_opp_count,
                MAX(close_date) AS nearest_close_date,
                LISTAGG(DISTINCT stage, ', ') WITHIN GROUP (ORDER BY stage) AS pipeline_stages
            FROM STAGING.STG_OPPORTUNITIES
            WHERE stage NOT IN ('closed_won', 'closed_lost')
            GROUP BY 1
        )
        SELECT
            a.account_id, a.account_name, a.industry, a.arr, a.licensed_seats,
            a.products, a.contract_renewal_date, a.csm_name, a.nps_score,
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
            COALESCE(o.open_opp_count, 0) AS open_opp_count,
            o.pipeline_stages, o.nearest_close_date,
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
        ORDER BY a.arr DESC
    """, show=False)

    # Final: show the mart
    step("FINAL: Account Health Mart", """
        SELECT account_name, arr, seat_utilization_pct, avg_sentiment,
               competitor_mentioned, expansion_signal, typical_frustration,
               current_ae, ae_changed_recently, pipeline_amount
        FROM MARTS.MART_ACCOUNT_HEALTH
        ORDER BY arr DESC
    """, max_rows=20)

    step("BONUS: Accounts with AE changes", """
        SELECT account_name, arr, current_ae, ae_tenure_days, ae_changed_recently,
               avg_sentiment, usage_trend_wow_pct
        FROM MARTS.MART_ACCOUNT_HEALTH
        WHERE ae_changed_recently = TRUE
        ORDER BY arr DESC
    """)

    print("\n" + "=" * 60)
    print("  LAB 1 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
