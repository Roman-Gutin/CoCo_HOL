"""Recreate the Account Health Agent with show-your-work instructions."""
import json
import os
import urllib.request
import urllib.error
import time

env_path = os.path.join(os.path.dirname(__file__), "..", "app", ".env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)

TOKEN = os.environ["VITE_SNOWFLAKE_TOKEN"]
HOST = os.environ["VITE_SNOWFLAKE_ACCOUNT"].replace("_", "-").lower()
BASE = f"https://{HOST}.snowflakecomputing.com/api/v2/databases/DIGITALNATIVECO/schemas/MARTS/agents"
SQL_URL = f"https://{HOST}.snowflakecomputing.com/api/v2/statements"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
}


def api(url, method="GET", data=None):
    req = urllib.request.Request(url, data=data, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {"status": resp.status}
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": e.read().decode()[:300]}


def run_sql(sql):
    body = json.dumps({
        "statement": sql, "warehouse": "COMPUTE_WH",
        "role": "WORKSHOP_ROLE", "database": "DIGITALNATIVECO",
    }).encode()
    return api(SQL_URL, "POST", body)


# Delete existing
print("Deleting old agent...")
api(f"{BASE}/ACCOUNT_HEALTH_AGENT", "DELETE")

# Create with full spec
print("Creating agent with show-your-work instructions...")

response_instructions = (
    "You are an Account Health Intelligence agent. You must SHOW YOUR WORK in every answer.\n\n"
    "1. ALWAYS start by querying the structured data to get the numbers (ARR, usage trends, "
    "sentiment scores, feature adoption, discounts, pipeline amounts). Present these as a data table.\n\n"
    "2. THEN search the unstructured sources (Gong calls, support tickets, CSM notes) to find the "
    "HUMAN STORY behind the numbers. Quote specific people by name and title. Include exact dollar "
    "amounts, dates, and competitor names from conversations.\n\n"
    "3. For every claim, cite the evidence: 'Usage dropped 40% (analyst query) and their VP of "
    "Creative said she is evaluating alternatives (Gong call, Feb 20).'\n\n"
    "4. When recommending actions, quantify the impact: 'Saving this account preserves $186K ARR. "
    "The expansion opportunity is worth $95K. Total NRR impact: $281K.'\n\n"
    "5. End every answer with THREE improvement suggestions:\n"
    "   a) A dbt model or semantic YAML change that would make the insight queryable as a permanent metric\n"
    "   b) A report or dashboard the team should build to track this ongoing (describe the columns, filters, and refresh cadence)\n"
    "   c) Additional data sources that would sharpen the analysis (what data are we missing? where would it come from? what questions could we answer with it?)\n\n"
    "Your answers should feel like a senior analyst presenting to the C-suite with receipts. "
    "Not a summary — a data-backed narrative where every insight is grounded in specific numbers "
    "and specific customer quotes."
)

orchestration_instructions = (
    "For EVERY question, use MULTIPLE tools. "
    "First use the analyst tool to pull structured metrics (ARR, sentiment, usage, features, "
    "discounts, pipeline). Then use at least one search tool to find the human context "
    "(customer quotes, CSM flags, competitor mentions). "
    "For broad questions, use ALL tools: analyst for numbers, gong_search for customer voice, "
    "ticket_search for complaints, csm_notes_search for internal flags. "
    "Never answer with just structured data OR just search results — always combine both."
)

agent = {
    "name": "ACCOUNT_HEALTH_AGENT",
    "comment": "Account Health Intelligence - triangulates 10 data sources with show-your-work analysis",
    "profile": {
        "display_name": "Account Health Agent",
        "avatar": "chart_increasing",
        "color": "blue",
    },
    "instructions": {
        "response": response_instructions,
        "orchestration": orchestration_instructions,
        "sample_questions": [
            {"question": "What can I do to increase NRR by 10 percent right now?"},
            {"question": "Why are accounts churning? What do they have in common?"},
            {"question": "Were there early warning signs we missed? Check the internal notes."},
            {"question": "What do our healthiest accounts do differently from our struggling ones?"},
            {"question": "Are we giving discounts to the wrong accounts?"},
            {"question": "Show me every competitor mention across all customer conversations"},
            {"question": "Are we making the same mistakes repeatedly?"},
            {"question": "What should I tell the board about customer health right now?"},
        ],
    },
    "models": {"orchestration": "claude-3-7-sonnet"},
    "orchestration": {"budget": {"seconds": 120, "tokens": 64000}},
    "tools": [
        {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "analyst",
            "description": "Query structured account health metrics: ARR, feature adoption breadth, power features, discounts, overdue invoices, usage trends, NPS, seat utilization, complaints, pipeline data across 20 accounts"}},
        {"tool_spec": {"type": "cortex_search", "name": "gong_search",
            "description": "Search Gong call transcripts for the customer voice: competitor mentions, expansion interest, frustration, champion engagement, budget discussions, renewal concerns"}},
        {"tool_spec": {"type": "cortex_search", "name": "ticket_search",
            "description": "Search support tickets for customer complaints: performance issues, AE transition gaps, product frustrations, escalation requests"}},
        {"tool_spec": {"type": "cortex_search", "name": "csm_notes_search",
            "description": "Search internal CSM/AE notes for risk flags, escalations, early warnings, and account strategy context that customers never see"}},
        {"tool_spec": {"type": "data_to_chart", "name": "data_to_chart",
            "description": "Generate charts and visualizations from query results"}},
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
}

result = api(BASE, "POST", json.dumps(agent).encode())
print(f"Result: {result}")

# Re-grant
time.sleep(1)
print("\nApplying grants...")
grants = [
    "GRANT USAGE ON AGENT DIGITALNATIVECO.MARTS.ACCOUNT_HEALTH_AGENT TO ROLE ACCOUNTADMIN",
    "GRANT USAGE ON CORTEX SEARCH SERVICE DIGITALNATIVECO.MARTS.GONG_TRANSCRIPT_SEARCH TO ROLE ACCOUNTADMIN",
    "GRANT USAGE ON CORTEX SEARCH SERVICE DIGITALNATIVECO.MARTS.SUPPORT_TICKET_SEARCH TO ROLE ACCOUNTADMIN",
    "GRANT USAGE ON CORTEX SEARCH SERVICE DIGITALNATIVECO.MARTS.CSM_NOTES_SEARCH TO ROLE ACCOUNTADMIN",
    "GRANT READ ON STAGE DIGITALNATIVECO.MARTS.SEMANTIC_MODELS TO ROLE ACCOUNTADMIN",
]
for sql in grants:
    run_sql(sql)
print("Done. Agent ready in Snowsight.")
