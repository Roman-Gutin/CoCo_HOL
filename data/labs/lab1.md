# Lab 1: Data Engineering + AI Inference

**Duration:** 25 min
**Theme:** "Your DE skills + AI inference = superpowered pipelines"

> **POV connection:** You already build pipelines. Now add AI enrichment in SQL — no Python, no ML team, no deployment headaches. This is what "builder" means.

---

## Prerequisites

- Snowflake account with Cortex AI enabled
- `SNOWFLAKE.CORTEX_USER` database role granted
- Cortex Code available in Snowsight
- Sample dataset pre-loaded (instructions below)

---

## Setup (2 min)

### 1. Open Snowsight and create your workspace

Open a new SQL worksheet in Snowsight. Run the following to set up your working schema:

```sql
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS workshop_db;
CREATE SCHEMA IF NOT EXISTS workshop_db.lab1;
USE SCHEMA workshop_db.lab1;
```

### 2. Load sample data

The sample support tickets dataset should already be available. Verify it:

```sql
SELECT COUNT(*) FROM workshop_db.raw.support_tickets;
-- Expected: ~1000 rows
```

Preview a few rows to understand the shape:

```sql
SELECT * FROM workshop_db.raw.support_tickets LIMIT 5;
```

You should see columns like: `ticket_id`, `ticket_text`, `created_at`, `customer_id`, `product`.

---

## Step 1: Use Cortex Code to Build a Staging Model (5 min)

Open **Cortex Code** in Snowsight (the AI assistant panel).

Type this prompt:

> "Create a staging table `workshop_db.lab1.stg_support_tickets` from `workshop_db.raw.support_tickets`. Clean up the data: trim whitespace from ticket_text, cast created_at to TIMESTAMP_NTZ, add a `ticket_date` DATE column, and filter out rows where ticket_text is null or empty."

Cortex Code will generate SQL. **Review the diff** — check that it:
- Creates the table with `CREATE OR REPLACE TABLE`
- Handles the null/empty filtering
- Casts types correctly

Click **Apply** to run it.

Verify:

```sql
SELECT COUNT(*) FROM workshop_db.lab1.stg_support_tickets;
SELECT * FROM workshop_db.lab1.stg_support_tickets LIMIT 3;
```

---

## Step 2: Enrich with Cortex AI Functions (10 min)

This is the magic. You're going to add ML-powered columns using nothing but SQL.

### 2a. Sentiment analysis

```sql
SELECT
    ticket_id,
    ticket_text,
    SNOWFLAKE.CORTEX.SENTIMENT(ticket_text) AS sentiment_score
FROM workshop_db.lab1.stg_support_tickets
LIMIT 10;
```

Look at the results. Sentiment scores range from -1 (very negative) to 1 (very positive). Notice how it picks up frustration, satisfaction, urgency.

### 2b. Text classification

```sql
SELECT
    ticket_id,
    ticket_text,
    SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
        ticket_text,
        ['billing', 'technical', 'feature_request', 'complaint', 'general_inquiry']
    ) AS category
FROM workshop_db.lab1.stg_support_tickets
LIMIT 10;
```

### 2c. Structured extraction with an LLM

```sql
SELECT
    ticket_id,
    ticket_text,
    SNOWFLAKE.CORTEX.COMPLETE(
        'claude-3-7-sonnet',
        'Extract the following from this support ticket and return valid JSON with keys "product_mentioned", "urgency" (low/medium/high), and "action_requested": ' || ticket_text
    ) AS ai_extraction
FROM workshop_db.lab1.stg_support_tickets
LIMIT 10;
```

Take a minute to read the JSON outputs. The model is extracting structured data from free text — the kind of work that used to require a data science team and a deployed model.

---

## Step 3: Build the Enriched Mart Table (5 min)

Now combine everything into a downstream mart. Use Cortex Code or write it yourself:

```sql
CREATE OR REPLACE TABLE workshop_db.lab1.mart_enriched_tickets AS
SELECT
    ticket_id,
    ticket_text,
    ticket_date,
    product,
    customer_id,
    SNOWFLAKE.CORTEX.SENTIMENT(ticket_text) AS sentiment_score,
    SNOWFLAKE.CORTEX.CLASSIFY_TEXT(
        ticket_text,
        ['billing', 'technical', 'feature_request', 'complaint', 'general_inquiry']
    ):label::STRING AS category,
    PARSE_JSON(
        SNOWFLAKE.CORTEX.COMPLETE(
            'claude-3-7-sonnet',
            'Extract from this support ticket and return valid JSON with keys "product_mentioned", "urgency" (low/medium/high), and "action_requested": ' || ticket_text
        )
    ) AS ai_extraction,
    ai_extraction:urgency::STRING AS urgency,
    ai_extraction:action_requested::STRING AS action_requested
FROM workshop_db.lab1.stg_support_tickets;
```

> **Note:** This will take a minute to run since it's calling AI functions on every row. In production, you'd run this incrementally.

Verify:

```sql
SELECT category, urgency, COUNT(*), AVG(sentiment_score) AS avg_sentiment
FROM workshop_db.lab1.mart_enriched_tickets
GROUP BY 1, 2
ORDER BY 3 DESC;
```

---

## Step 4: Write a Validation Test (3 min)

Ask Cortex Code:

> "Write a SQL assertion test that checks: (1) sentiment_score is between -1 and 1, (2) category is one of the expected values, (3) no null ticket_ids in mart_enriched_tickets."

You should get something like:

```sql
-- Test: Sentiment scores in valid range
SELECT COUNT(*) AS failures
FROM workshop_db.lab1.mart_enriched_tickets
WHERE sentiment_score < -1 OR sentiment_score > 1;
-- Expected: 0

-- Test: Categories are valid
SELECT COUNT(*) AS failures
FROM workshop_db.lab1.mart_enriched_tickets
WHERE category NOT IN ('billing', 'technical', 'feature_request', 'complaint', 'general_inquiry');
-- Expected: 0

-- Test: No null ticket_ids
SELECT COUNT(*) AS failures
FROM workshop_db.lab1.mart_enriched_tickets
WHERE ticket_id IS NULL;
-- Expected: 0
```

Run them. All should return 0.

---

## Stretch Goals (if time permits)

### Translate multilingual tickets

```sql
SELECT
    ticket_id,
    ticket_text,
    SNOWFLAKE.CORTEX.TRANSLATE(ticket_text, '', 'en') AS translated_text
FROM workshop_db.lab1.stg_support_tickets
WHERE ticket_id IN (/* pick some non-English ticket IDs */);
```

### Generate executive summaries

```sql
SELECT SNOWFLAKE.CORTEX.SUMMARIZE(
    (SELECT LISTAGG(ticket_text, '\n---\n')
     FROM workshop_db.lab1.mart_enriched_tickets
     WHERE category = 'complaint'
     LIMIT 20)
) AS complaint_summary;
```

---

## What You Just Did

- Used **Cortex Code** to generate a staging pipeline from natural language
- Enriched data with **sentiment analysis**, **text classification**, and **LLM extraction** — all in SQL
- Built a production-ready **mart table** with AI-derived columns
- Wrote **validation tests** for AI outputs

No Python. No MLflow. No data science team. No deployment pipeline. Just SQL.

**This is what "builder" means.**

---

*Next up: Lab 2 — you'll build an AI agent that queries this enriched data autonomously.*
