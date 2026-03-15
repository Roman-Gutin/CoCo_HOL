# Lab 1: Understand the Business

**Duration:** 25 min
**The question:** "It's your first day. The CRO asks: what can I do to increase NRR by 10%?"

> Before you can answer, you need to understand the data. Twenty accounts. Ten data sources. One SQL worksheet. Let's go.

---

## Prerequisites

- Snowflake account with Cortex AI enabled
- `SNOWFLAKE.CORTEX_USER` database role granted
- Cortex Code available in Snowsight
- Workshop dataset pre-loaded into `DIGITALNATIVECO.RAW`

---

## Setup (2 min)

### Set your context

Open a new SQL worksheet in Snowsight. Set your working context:

```sql
USE ROLE SYSADMIN;
USE DATABASE DIGITALNATIVECO;
USE SCHEMA RAW;
```

### Verify the raw data

You have ten source tables. Confirm they're loaded:

```sql
SELECT 'accounts' AS source, COUNT(*) AS row_count FROM RAW.ACCOUNTS
UNION ALL
SELECT 'support_tickets', COUNT(*) FROM RAW.SUPPORT_TICKETS
UNION ALL
SELECT 'gong_transcripts', COUNT(*) FROM RAW.GONG_TRANSCRIPTS
UNION ALL
SELECT 'product_events', COUNT(*) FROM RAW.PRODUCT_EVENTS
UNION ALL
SELECT 'employees', COUNT(*) FROM RAW.EMPLOYEES
UNION ALL
SELECT 'account_assignments', COUNT(*) FROM RAW.ACCOUNT_ASSIGNMENTS
UNION ALL
SELECT 'opportunities', COUNT(*) FROM RAW.OPPORTUNITIES
UNION ALL
SELECT 'feature_usage', COUNT(*) FROM RAW.FEATURE_USAGE
UNION ALL
SELECT 'invoices', COUNT(*) FROM RAW.INVOICES
UNION ALL
SELECT 'csm_notes', COUNT(*) FROM RAW.CSM_NOTES;
-- Expected: 20 accounts, ~513 tickets, ~157 transcripts, ~5300 events,
--           20 employees, 44 assignments, 21 opportunities,
--           ~7800 feature_usage, 80 invoices, ~55 csm_notes
```

All ten tables loaded? Good. Let's go meet the data.

---

## Step 1: Orient — "What do I even have?" (3 min)

> **Why this step:** Before you answer the CRO, understand what data you're working with. You just joined -- you don't know these accounts, these products, or these systems.

Open **Cortex Code** in Snowsight (the AI assistant panel). Type this prompt:

> "I just joined DigitalNativeCo as an analytics engineer. Show me what's in the DIGITALNATIVECO.RAW schema -- every table, how many rows it has, and a few column names so I can get oriented."

Review the generated SQL and click **Apply**. You should see all ten tables with their shapes.

Now ask a follow-up:

> "How big is this business? Show me total ARR, number of accounts, and how ARR breaks down by industry."

> **Presenter:** "$3.5M ARR across 20 accounts. The CRO wants 10% NRR improvement -- that's $350K in saves or expansion. Keep that number in your head."

---

## Step 2: AI reads what you can't (7 min)

> **Why this step:** You have 513 support tickets and 157 Gong call transcripts. You can't read them all. But AI can -- and it can tell you who's happy, who's furious, and who's about to leave.

### 2a. FEELING: Sentiment on tickets

Prompt Cortex Code:

> "I have about 500 support tickets. Score them by sentiment and show me the 10 angriest ones -- I want to see the account name, what they actually wrote, and how negative the score is."

Review the generated SQL and click **Apply**.

**Read the previews.** Meridian is frustrated about Canvas freezing mid-export. Beacon's VP is cc'ing legal about API outages. These aren't metrics -- these are people telling you they're about to leave.

> **Presenter:** "Read those previews out loud. 'This is the third time Canvas has frozen mid-export.' That's not a data point -- that's a customer telling you they're done."

### 2b. SAYING: COMPLETE on Gong transcripts

Prompt Cortex Code:

> "Read the Gong call transcripts and tell me what's happening in each conversation. For each call, I want to know: did they mention a competitor? Are they frustrated? Is there an expansion opportunity? How engaged is our champion? Pull out the key themes. Show me 5 calls with the account name and what you found."

Review the generated SQL and click **Apply**.

**Look for Meridian.** The model found they're evaluating SketchFlow. Look for Atlas -- expansion_signal is true. The AI is reading conversations you'll never have time to listen to.

> **Presenter:** "AI found the competitor mention you didn't know about. It found the expansion signal you hadn't heard. This is why AI enrichment matters -- it reads what you can't."

### 2c. PATTERNS: Classify tickets

Prompt Cortex Code:

> "Categorize the support tickets into billing, technical, feature request, complaint, and onboarding. Then show me a breakdown -- how many in each category, and what's the average sentiment? I want to see which types of issues have the most frustrated customers."

Review the generated SQL and click **Apply**. You should see something like:

```
category          count   avg_sentiment
─────────────     ─────   ─────────────
complaint         ~50     -0.554
technical         ~196    -0.300
onboarding        ~49     -0.294
billing           ~55     -0.199
feature_request   ~163    -0.003
```

**The pattern:** Complaints average -0.55 sentiment. Feature requests average -0.003. Customers who request features are engaged -- they're building on your platform. Customers who complain are leaving.

> **Presenter:** "Feature requests are almost neutral. That's the insight -- customers who ask for features are invested. Complaints are the danger signal."

---

## Step 3: Build the mart -- one Cortex Code prompt (10 min)

> **Why this step:** You've seen the signals in isolation. Now bring everything together into one table -- one row per account -- so you can see the full picture.

This is the big one. Type this prompt into Cortex Code:

> "Build me a single mart table called MARTS.MART_ACCOUNT_HEALTH -- one row per account, joining all 10 raw tables. Here's what I need:
>
> From ACCOUNTS: arr, industry, licensed_seats, products, contract_renewal_date, csm_name, nps_score
>
> From SUPPORT_TICKETS: ticket count, average sentiment score, number of complaints, number of P1/P2 tickets
>
> From GONG_TRANSCRIPTS: use an LLM to read each transcript and extract whether a competitor was mentioned and whether there's an expansion signal. Then aggregate per account -- did any call mention a competitor, did any show expansion interest, what's the most common frustration level and champion engagement level, total call count
>
> From PRODUCT_EVENTS: weekly active users for the most recent week, seat utilization as a percent of licensed seats, week-over-week usage trend
>
> From EMPLOYEES + ACCOUNT_ASSIGNMENTS: current AE name, how long they've been assigned, whether the AE changed in the last 90 days, and whether the AE is still active or departed
>
> From OPPORTUNITIES: total open pipeline amount, stages, nearest close date
>
> From INVOICES: average discount percent, count of overdue invoices, average days to pay
>
> From FEATURE_USAGE: count of distinct features used, count of power features (canvas_collab_edit, canvas_templates, flow_approvals, insight_dashboards, insight_api), feature breadth as percent of total available
>
> Add a health_category column that classifies each account: 'at_risk' if a competitor was mentioned or sentiment is below -0.3, 'expansion' if there's an expansion signal and usage is growing more than 5%, 'healthy' if sentiment and usage are stable, and 'attention' for everything else.
>
> Write it as a CREATE TABLE with CTEs for each source, ordered by ARR descending."

**Before you run this, review two things:**

1. How did Cortex Code define `ae_changed_recently`? Do you agree with the 90-day threshold?
2. Look at the `health_category` logic -- would you set different thresholds for YOUR company?

**This is the moment where YOU add judgment.** The AI wrote the SQL. You decide if the logic is right.

When you're satisfied, click **Apply**.

> **Presenter:** "Cortex Code just generated 80-100 lines of production SQL from one natural language prompt. But the value isn't the SQL -- it's the review. YOU decide what 'at risk' means."

---

## Step 4: See the answer forming (5 min)

> **Why this step:** The CRO asked about NRR. Now you have the data to start answering. Let's see what it says.

### 4a. Portfolio view

Prompt Cortex Code:

> "Show me all 20 accounts from the mart -- name, ARR, health category, sentiment, whether a competitor was mentioned, whether the AE changed recently, and pipeline amount. Put the most at-risk accounts at the top."

Review and click **Apply**. You should see Meridian, Beacon, and Cascade clustered at the top with negative sentiment. Atlas and Voyager sit at the bottom with expansion signals.

### 4b. Quantify the opportunity

Prompt Cortex Code:

> "How much ARR is at risk? How much expansion pipeline do we have? Give me the total ARR, the at-risk ARR, the expansion pipeline, and a count of accounts in each health category."

Review and click **Apply**. Expected results:

```
total_arr:           ~$3,461,000
at_risk_arr:         ~$649,000
expansion_pipeline:  ~$402,000
at_risk_accounts:    ~6
expansion_accounts:  ~4
```

The CRO asked for $350K. You're looking at $649K in risk and $402K in expansion pipeline. The answer is taking shape.

### 4c. Meridian deep-dive

Prompt Cortex Code:

> "Show me everything we know about Meridian Media Group from MART_ACCOUNT_HEALTH -- all columns in a single row."

Review and click **Apply**.

**Five danger signals in one row:** declining usage, negative sentiment, competitor mentioned, AE changed recently, overdue invoice. This is the power of joining 10 sources -- patterns that no single system can see on its own.

---

## Bridge to Lab 2

You now have the data to answer the CRO. But the CRO doesn't speak SQL. She needs an agent that speaks English. That's Lab 2.

---

## What You Just Did

- Used **Cortex Code** to explore 10 raw data sources with natural language
- Enriched support tickets with **CORTEX.SENTIMENT()** and **CORTEX.CLASSIFY_TEXT()** -- no Python, no deployed models
- Extracted structured signals from Gong transcripts with **CORTEX.COMPLETE('claude-3-7-sonnet')** -- competitor mentions, expansion signals, frustration levels
- Built **MARTS.MART_ACCOUNT_HEALTH** -- a single table joining all ten sources with a derived `health_category` column
- Quantified the CRO's question: ~$649K at risk, ~$402K in expansion pipeline
- Surfaced **cross-source signals** like AE turnover + competitor mentions + sentiment decline -- patterns invisible to any single system

No Python. No MLflow. No data science team. Just SQL.

**Next up: Lab 2 -- you'll build an AI agent that can query this enriched data using natural language.**
