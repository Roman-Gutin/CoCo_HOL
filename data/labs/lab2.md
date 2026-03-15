# Lab 2: Cortex Agents — AI That Serves Data

**Duration:** 25 min
**Theme:** "Your semantic layer is the brain of an AI agent"

> **POV connection:** Agents are only as good as the data contracts underneath them. You control those contracts. Without your semantic layer, agents hallucinate. You're not being replaced — you're the reason agents work.

---

## Prerequisites

- Completed Lab 1 (you need `workshop_db.lab1.mart_enriched_tickets`)
- Cortex Agents enabled on your account
- `SNOWFLAKE.CORTEX_USER` database role granted

---

## Setup (2 min)

```sql
USE SCHEMA workshop_db.lab1;
```

Verify your enriched table from Lab 1 is ready:

```sql
SELECT COUNT(*) FROM workshop_db.lab1.mart_enriched_tickets;
SELECT * FROM workshop_db.lab1.mart_enriched_tickets LIMIT 3;
```

---

## Step 1: Define a Semantic Model (8 min)

The semantic model tells the agent what your data means. This is where your expertise matters most — you're encoding business logic that the agent can't figure out on its own.

Create a YAML file. In Snowsight, open a new Python worksheet (we'll use it just to write the file to a stage):

```sql
CREATE OR REPLACE STAGE workshop_db.lab1.semantic_models
    DIRECTORY = (ENABLE = TRUE);
```

Now create the semantic model definition. Open Cortex Code and prompt:

> "Help me write a Cortex Analyst semantic model YAML for a support ticket analytics use case"

Then refine it to match your data. The final YAML should look like this:

```yaml
name: support_ticket_analytics
description: >
  Analytics model for customer support tickets enriched with AI-derived
  sentiment, classification, and urgency extraction.

tables:
  - name: mart_enriched_tickets
    base_table: workshop_db.lab1.mart_enriched_tickets
    description: Support tickets enriched with AI sentiment, category, and urgency

    dimensions:
      - name: category
        expr: category
        description: >
          AI-classified ticket category. One of: billing, technical,
          feature_request, complaint, general_inquiry.
          Derived from CORTEX.CLASSIFY_TEXT.

      - name: product
        expr: product
        description: The product the ticket relates to

      - name: urgency
        expr: urgency
        description: >
          AI-extracted urgency level (low, medium, high).
          Derived from LLM extraction via CORTEX.COMPLETE.
          "High" means the customer expressed immediate need or threatened churn.

      - name: ticket_date
        expr: ticket_date
        description: Date the ticket was created

      - name: action_requested
        expr: action_requested
        description: What the customer asked for, extracted by LLM

    measures:
      - name: ticket_count
        expr: COUNT(ticket_id)
        description: Total number of support tickets

      - name: avg_sentiment
        expr: AVG(sentiment_score)
        description: >
          Average sentiment score (-1 to 1). Below -0.3 is considered
          negative. Above 0.3 is positive. Between is neutral.

      - name: negative_ticket_count
        expr: COUNT_IF(sentiment_score < -0.3)
        description: Number of tickets with negative sentiment

      - name: high_urgency_count
        expr: COUNT_IF(urgency = 'high')
        description: Number of high-urgency tickets

    time_dimensions:
      - name: ticket_date
        expr: ticket_date
        type: date
        description: Date the ticket was submitted

    filters:
      - name: recent_tickets
        expr: ticket_date >= DATEADD('day', -30, CURRENT_DATE())
        description: Tickets from the last 30 days
```

Upload it to your stage:

```sql
-- In a Python worksheet or via SnowSQL:
PUT file:///tmp/support_ticket_analytics.yaml
    @workshop_db.lab1.semantic_models/
    AUTO_COMPRESS = FALSE
    OVERWRITE = TRUE;
```

> **Alternative:** If file upload is tricky in the workshop environment, use Cortex Code to help you create the file directly on the stage.

**Pause and reflect:** Look at that YAML. You just defined what "urgent" means. What "negative sentiment" means. What counts as a measure vs a dimension. The agent can't know this — *you* decided it. This is why your role matters.

---

## Step 2: Set Up Cortex Search (5 min)

Cortex Search lets the agent do unstructured search over raw ticket text — useful for questions like "find tickets about competitors."

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE workshop_db.lab1.ticket_search
  ON ticket_text
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT
        ticket_id,
        ticket_text,
        category,
        urgency,
        sentiment_score,
        ticket_date
    FROM workshop_db.lab1.mart_enriched_tickets
  );
```

Test it:

```sql
SELECT *
FROM TABLE(
    workshop_db.lab1.ticket_search!SEARCH(
        query => 'customer mentioned switching to competitor',
        columns => ['ticket_text', 'category', 'urgency'],
        limit => 5
    )
);
```

---

## Step 3: Create the Cortex Agent (5 min)

Now wire it all together. The agent gets two tools: Cortex Analyst (structured queries against your semantic model) and Cortex Search (unstructured text search).

```sql
CREATE OR REPLACE CORTEX AGENT workshop_db.lab1.support_agent
  COMMENT = 'Support ticket analytics agent powered by semantic model'
  LLM = 'claude-3-7-sonnet'
  TOOLS = (
    CORTEX_ANALYST(
      SEMANTIC_MODEL => '@workshop_db.lab1.semantic_models/support_ticket_analytics.yaml'
    ),
    CORTEX_SEARCH(
      SEARCH_SERVICE => workshop_db.lab1.ticket_search
    )
  );
```

---

## Step 4: Talk to Your Agent (5 min)

Now ask it questions. The agent will decide which tool to use — Analyst for structured queries, Search for unstructured lookups.

### Structured questions (should use Analyst):

```sql
SELECT * FROM TABLE(
    workshop_db.lab1.support_agent!COMPLETE(
        'What is our most common complaint category this month?'
    )
);
```

```sql
SELECT * FROM TABLE(
    workshop_db.lab1.support_agent!COMPLETE(
        'What is the average sentiment for billing issues vs technical issues?'
    )
);
```

```sql
SELECT * FROM TABLE(
    workshop_db.lab1.support_agent!COMPLETE(
        'How many high-urgency tickets did we get last week, broken down by product?'
    )
);
```

### Unstructured questions (should use Search):

```sql
SELECT * FROM TABLE(
    workshop_db.lab1.support_agent!COMPLETE(
        'Find me tickets where customers mentioned switching to a competitor'
    )
);
```

```sql
SELECT * FROM TABLE(
    workshop_db.lab1.support_agent!COMPLETE(
        'Show me examples of tickets where customers praised our support team'
    )
);
```

### Hybrid questions (agent may use both tools):

```sql
SELECT * FROM TABLE(
    workshop_db.lab1.support_agent!COMPLETE(
        'What percentage of billing tickets are negative sentiment, and show me the worst 3 examples?'
    )
);
```

Watch the agent's response. It tells you which tool it used and why. This transparency is key — you can see the semantic model driving the structured answers.

---

## Stretch Goals (if time permits)

### Add a custom tool (stored procedure)

Create a procedure that simulates creating a Jira ticket:

```sql
CREATE OR REPLACE PROCEDURE workshop_db.lab1.create_jira_ticket(
    ticket_id STRING,
    summary STRING,
    priority STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    INSERT INTO workshop_db.lab1.jira_queue (ticket_id, summary, priority, created_at)
    VALUES (:ticket_id, :summary, :priority, CURRENT_TIMESTAMP());
    RETURN 'Jira ticket created for ' || :ticket_id || ' with priority ' || :priority;
END
$$;

-- Create the queue table first
CREATE OR REPLACE TABLE workshop_db.lab1.jira_queue (
    ticket_id STRING,
    summary STRING,
    priority STRING,
    created_at TIMESTAMP_NTZ
);
```

### Multi-turn conversation with threads

```sql
-- Start a thread
SET thread_result = (
    SELECT * FROM TABLE(
        workshop_db.lab1.support_agent!COMPLETE(
            'How many high-urgency tickets did we get this week?',
            THREAD => NULL  -- starts a new thread
        )
    )
);

-- Follow up in the same thread
SELECT * FROM TABLE(
    workshop_db.lab1.support_agent!COMPLETE(
        'Break that down by category',
        THREAD => $thread_result:thread_id
    )
);
```

---

## What You Just Did

- Defined a **semantic model** encoding your business logic — what dimensions, measures, and definitions mean
- Created a **Cortex Search** service for unstructured text retrieval
- Deployed a **Cortex Agent** with two tools: structured analytics + unstructured search
- Asked natural language questions and watched the agent pick the right tool

The agent is impressive. But look at what made it work: **your semantic model**. You defined what "urgent" means. You decided which measures matter. You set the definitions that prevent hallucination.

**Without your semantic layer, this agent is useless. You're not being replaced — you're the reason agents work.**

---

*Next up: Lab 3 — you'll build a production Streamlit app on top of everything you just created.*
