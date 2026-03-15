# Lab 2: Build the Brain

**Duration:** 25 min
**The question:** "You have the numbers. The CRO doesn't speak SQL."

> In Lab 1 you built the data. Now you build the intelligence layer — a semantic model, three search services, and an agent that reasons across all of them.

---

## Prerequisites

- Completed Lab 1 (you need `DIGITALNATIVECO.MARTS.MART_ACCOUNT_HEALTH`)
- Cortex Agents enabled on your account
- `SNOWFLAKE.CORTEX_USER` database role granted

---

## Setup (2 min)

```sql
USE ROLE SYSADMIN;
USE SCHEMA DIGITALNATIVECO.MARTS;
```

Verify your account health mart from Lab 1 is ready:

```sql
SELECT COUNT(*) FROM DIGITALNATIVECO.MARTS.MART_ACCOUNT_HEALTH;
SELECT * FROM DIGITALNATIVECO.MARTS.MART_ACCOUNT_HEALTH LIMIT 5;
```

You should see columns like `account_name`, `industry`, `arr`, `licensed_seats`, `products`, `health_category`, `nps_score`, `weekly_active_users`, `avg_sentiment`, `usage_trend_wow_pct`, `seat_utilization_pct`, `competitor_mentioned`, `current_ae`, `ae_changed_recently`, `pipeline_amount`, and more.

---

## Step 1: Teach the AI Your Language (5 min)

> **Why this step:** Without a semantic model, the agent doesn't know what "at risk" means, what a good sentiment score looks like, or that AE changes within 90 days predict churn. You're writing a business dictionary for AI. Without it, the agent hallucinates.

**Metaphor:** A business dictionary for AI.

Open Cortex Code and use this prompt:

> "I need to teach an AI agent what my data means so it can answer business questions about account health. Create a semantic model YAML for MARTS.MART_ACCOUNT_HEALTH. For every column, write a description that explains the business meaning — not just what the column is, but what it means. For example, avg_sentiment below -0.3 means frustrated customers. AE changes within 90 days predict churn. Seat utilization below 50% means people are paying for seats nobody uses. Make the descriptions opinionated — they should encode business judgment. Then write me a Python worksheet to upload it to @DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/account_health.yaml"

Review the YAML that Cortex Code generates. The descriptions should encode business judgment — thresholds, interpretations, leading indicators. If anything looks generic, edit it before running.

### Create the stage and upload

First, create the stage:

```sql
CREATE OR REPLACE STAGE DIGITALNATIVECO.MARTS.SEMANTIC_MODELS
    DIRECTORY = (ENABLE = TRUE);
```

Then open a **Python worksheet** in Snowsight and run the upload code. It should look like this:

```python
import snowflake.snowpark as snowpark

def main(session: snowpark.Session) -> str:
    yaml_content = """
name: account_health
description: >
  Account health analytics model for DigitalNativeCo. Combines product usage
  trends, support ticket sentiment, Gong call signals, CSM notes, AE assignment
  history, and pipeline data into a unified view of account risk and expansion
  readiness. Built from mart_account_health which aggregates data from
  product_events, support_tickets, gong_transcripts, csm_notes, employees,
  account_assignments, and opportunities.

tables:
  - name: mart_account_health
    base_table:
      database: DIGITALNATIVECO
      schema: MARTS
      table: MART_ACCOUNT_HEALTH
    description: >
      Pre-computed account health metrics combining product usage, support
      ticket analysis, Gong call intelligence, CSM observations, AE assignment
      history, and pipeline data per account.

    dimensions:
      - name: account_name
        expr: account_name
        data_type: VARCHAR
        description: Customer account name (e.g., "Meridian Media Group")

      - name: industry
        expr: industry
        data_type: VARCHAR
        description: >
          The customer's industry vertical. Values include: Media & Advertising,
          Financial Services, Logistics & Supply Chain, Retail, Healthcare,
          Education, Technology, Entertainment, Consulting, Manufacturing.

      - name: products
        expr: products
        data_type: VARCHAR
        description: >
          DigitalNativeCo products the account uses. One or more of: Canvas
          (design tool), Flow (workflow automation), Insight (analytics dashboard).

      - name: health_category
        expr: health_category
        data_type: VARCHAR
        description: >
          Overall account health classification. Values:
          - "at_risk": Account showing multiple negative signals — declining usage,
            negative support sentiment, competitor mentions, or AE turnover.
            Needs immediate CSM intervention.
          - "expansion": Account showing positive signals — growing usage, feature
            requests, cross-sell/upsell interest in Gong calls.
          - "healthy": Stable usage, no red flags, routine engagement.
          - "attention": Mixed signals that warrant monitoring — could be onboarding
            issues, admin changes, or early warning signs without active churn
            indicators.

      - name: csm_name
        expr: csm_name
        data_type: VARCHAR
        description: Customer success manager assigned to this account.

      - name: current_ae
        expr: current_ae
        data_type: VARCHAR
        description: >
          The account executive currently assigned to this account. Useful for
          understanding coverage and identifying accounts affected by recent
          AE changes.

      - name: ae_changed_recently
        expr: ae_changed_recently
        data_type: BOOLEAN
        description: >
          TRUE if the account executive was reassigned within the last 90 days
          — a leading indicator of account health decline. Accounts that lose
          their AE often experience relationship gaps, missed check-ins, and
          delayed renewals.

      - name: ae_status
        expr: ae_status
        data_type: VARCHAR
        description: >
          Current status of the assigned AE. Values like "active", "on_leave",
          "departed". Departed AEs combined with no reassignment is a red flag.

      - name: competitor_mentioned
        expr: competitor_mentioned
        data_type: BOOLEAN
        description: >
          TRUE if any competitor (SketchFlow, Miro, Monday.com, Asana, etc.)
          was mentioned in recent Gong calls. Any competitor mention warrants
          CSM review — it means the customer is actively evaluating alternatives.

      - name: expansion_signal
        expr: expansion_signal
        data_type: BOOLEAN
        description: >
          TRUE if Gong calls or CSM notes indicate expansion interest — new team
          onboarding, additional seat requests, cross-product interest.

      - name: typical_frustration
        expr: typical_frustration
        data_type: VARCHAR
        description: >
          Most common frustration theme from support tickets and Gong calls.
          Examples: "API reliability", "onboarding complexity", "reporting gaps".

      - name: typical_champion_engagement
        expr: typical_champion_engagement
        data_type: VARCHAR
        description: >
          How engaged the internal champion is. Values like "active", "declining",
          "silent". A silent champion is an early churn signal.

      - name: most_common_category
        expr: most_common_category
        data_type: VARCHAR
        description: Most frequent support ticket category for this account.

      - name: pipeline_stages
        expr: pipeline_stages
        data_type: VARCHAR
        description: >
          Current stages of open pipeline opportunities. Values include:
          Discovery, Negotiation, Proposal, Closed Won, Closed Lost.

    measures:
      - name: arr
        expr: arr
        data_type: NUMBER
        description: >
          Annual recurring revenue for the account. The dollar amount at stake
          if this account churns.

      - name: licensed_seats
        expr: licensed_seats
        data_type: NUMBER
        description: Total seats the account has licensed.

      - name: nps_score
        expr: nps_score
        data_type: NUMBER
        description: >
          Net Promoter Score. Above 50 is strong. Below 20 is a retention risk.
          Below 0 means detractors outnumber promoters — escalate immediately.

      - name: weekly_active_users
        expr: weekly_active_users
        data_type: NUMBER
        description: >
          Count of unique users who logged in during the measurement period.
          Compare against licensed_seats via seat_utilization_pct to gauge adoption.

      - name: avg_session_duration
        expr: avg_session_duration
        data_type: NUMBER
        description: >
          Average session duration in minutes. Below 5 minutes suggests users
          are logging in but not engaging meaningfully.

      - name: usage_trend_wow_pct
        expr: usage_trend_wow_pct
        data_type: NUMBER
        description: >
          Week-over-week percentage change in product usage.
          Below -15%: Alarming decline — potential disengagement.
          Between -15% and -5%: Moderate decline — worth monitoring.
          Between -5% and 5%: Stable.
          Above 5%: Growing — healthy adoption signal.
          Above 15%: Rapid growth — possible expansion candidate.

      - name: seat_utilization_pct
        expr: seat_utilization_pct
        data_type: NUMBER
        description: >
          Percentage of licensed seats actively used. Below 50% means the
          account is paying for seats nobody uses — a churn risk and a
          conversation starter for right-sizing or training.

      - name: ticket_count
        expr: ticket_count
        data_type: NUMBER
        description: Total number of support tickets filed by the account.

      - name: avg_sentiment
        expr: avg_sentiment
        data_type: NUMBER
        description: >
          Average sentiment score across support tickets. Scale -1 to 1.
          Below -0.3: Frustrated customers — needs immediate attention.
          Between -0.3 and 0.3: Neutral — routine interactions.
          Above 0.3: Positive — feature requests, praise, satisfaction.

      - name: complaint_count
        expr: complaint_count
        data_type: NUMBER
        description: Number of tickets classified as complaints.

      - name: high_priority_count
        expr: high_priority_count
        data_type: NUMBER
        description: >
          Count of high-priority support tickets. More than 2 in a 30-day
          window is a strong churn indicator.

      - name: gong_call_count
        expr: gong_call_count
        data_type: NUMBER
        description: Total Gong calls recorded for this account.

      - name: ae_tenure_days
        expr: ae_tenure_days
        data_type: NUMBER
        description: >
          Number of days the current AE has been assigned. Low tenure (under
          90 days) combined with at_risk health category signals that the AE
          transition is contributing to account instability.

      - name: pipeline_amount
        expr: pipeline_amount
        data_type: NUMBER
        description: >
          Total dollar value of open pipeline for this account. Combined with
          health_category, shows how much revenue sits in at-risk accounts.

      - name: open_opp_count
        expr: open_opp_count
        data_type: NUMBER
        description: Number of open opportunities for this account.

    time_dimensions:
      - name: contract_renewal_date
        expr: contract_renewal_date
        data_type: DATE
        description: >
          Date the contract is up for renewal. Accounts renewing within 90 days
          that are at_risk need immediate intervention.

      - name: last_call_date
        expr: last_call_date
        data_type: DATE
        description: Date of the most recent Gong call with this account.

      - name: nearest_close_date
        expr: nearest_close_date
        data_type: DATE
        description: Closest expected close date across open opportunities.

    filters:
      - name: at_risk_only
        expr: health_category = 'at_risk'
        description: Filter to accounts classified as at risk

      - name: expansion_only
        expr: health_category = 'expansion'
        description: Filter to accounts showing expansion signals

      - name: ae_changed_recently_only
        expr: ae_changed_recently = TRUE
        description: Filter to accounts where the AE changed in the last 90 days
"""

    with open('/tmp/account_health.yaml', 'w') as f:
        f.write(yaml_content.strip())

    session.file.put(
        '/tmp/account_health.yaml',
        '@DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/',
        auto_compress=False,
        overwrite=True
    )

    return "Semantic model uploaded to @DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/account_health.yaml"
```

Verify the upload:

```sql
LIST @DIGITALNATIVECO.MARTS.SEMANTIC_MODELS;
```

You should see `account_health.yaml` in the listing.

> **Pause and read that YAML.** You defined what "at risk" means. You set the threshold where sentiment becomes alarming (-0.3). You wrote the business rule that AE changes within 90 days predict churn. The agent cannot know any of this — *you* decided it. **This is why your role matters.**

> **Presenter:** "That YAML is maybe 50 lines. It's the most important file in the company. Pull it out and the agent hallucinates every metric."

---

## Step 2: Give the AI Ears (5 min)

> **Why this step:** The mart has numbers — sentiment scores, usage trends, pipeline amounts. But numbers tell you *what* happened. The raw conversations tell you *why*. Search services let the agent hear what customers actually said.

**Metaphor:** Numbers tell what happened. Conversations tell why.

Open Cortex Code and use this prompt:

> "I want the agent to be able to search the actual text of our Gong calls, support tickets, and internal CSM notes. Create three Cortex Search services — one for each source. Include the account name and a few useful attributes on each one so results have context."

Review the SQL, then run it:

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE DIGITALNATIVECO.MARTS.GONG_TRANSCRIPT_SEARCH
  ON transcript_excerpt
  ATTRIBUTES account_name, call_type, call_date
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT
        call_id,
        account_name,
        call_type,
        call_date,
        transcript_excerpt,
        duration_min,
        attendees
    FROM DIGITALNATIVECO.RAW.GONG_TRANSCRIPTS
  );
```

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE DIGITALNATIVECO.MARTS.SUPPORT_TICKET_SEARCH
  ON ticket_text
  ATTRIBUTES account_name, priority, product
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT
        ticket_id,
        account_name,
        product,
        priority,
        ticket_text,
        sentiment_score
    FROM DIGITALNATIVECO.RAW.SUPPORT_TICKETS
  );
```

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE DIGITALNATIVECO.MARTS.CSM_NOTES_SEARCH
  ON note_text
  ATTRIBUTES account_name, author, note_type
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT
        note_id,
        account_name,
        author,
        note_type,
        note_text,
        created_at
    FROM DIGITALNATIVECO.RAW.CSM_NOTES
  );
```

### Test the search services

Test 1 — Gong transcripts:

```sql
SELECT * FROM TABLE(
    DIGITALNATIVECO.MARTS.GONG_TRANSCRIPT_SEARCH!SEARCH(
        query => 'customer mentioned switching to SketchFlow or evaluating competitors',
        columns => ['transcript_excerpt', 'account_name', 'call_type'],
        limit => 5
    )
);
```

Test 2 — CSM notes:

```sql
SELECT * FROM TABLE(
    DIGITALNATIVECO.MARTS.CSM_NOTES_SEARCH!SEARCH(
        query => 'executive sponsor left or champion departure risk',
        columns => ['note_text', 'account_name', 'author', 'note_type'],
        limit => 5
    )
);
```

> **Read the results.** Robert Kimball is talking about API outages. Derek Huang is asking about SketchFlow. Sarah Chen flagged Meridian as at-risk 60 days ago. **The agent can now hear what customers actually said — and what your own team flagged internally.**

> **Presenter:** "The agent can now hear what customers actually said. Not a metric. Their voice."

---

## Step 3: Wire the Brain (3 min)

> **Why this step:** You've built the dictionary (semantic model) and the ears (search services). Now connect them to a brain.

The hard part was your definitions. The assembly is plumbing.

```sql
CREATE OR REPLACE CORTEX AGENT DIGITALNATIVECO.MARTS.ACCOUNT_HEALTH_AGENT
  COMMENT = 'Account health agent — triangulates product usage, support tickets, Gong calls, CSM notes, AE assignments, and pipeline data'
  LLM = 'claude-3-7-sonnet'
  TOOLS = (
    CORTEX_ANALYST(
      SEMANTIC_MODEL => '@DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/account_health.yaml'
    ),
    CORTEX_SEARCH(
      SEARCH_SERVICE => DIGITALNATIVECO.MARTS.GONG_TRANSCRIPT_SEARCH
    ),
    CORTEX_SEARCH(
      SEARCH_SERVICE => DIGITALNATIVECO.MARTS.SUPPORT_TICKET_SEARCH
    ),
    CORTEX_SEARCH(
      SEARCH_SERVICE => DIGITALNATIVECO.MARTS.CSM_NOTES_SEARCH
    )
  );
```

> **Presenter:** "Four objects. A dictionary, three ears, and a brain. That's the whole architecture."

---

## Step 4: The Moment of Truth (12 min)

> **Why this step:** This is why you built everything. The CRO asked a question. Let's see if the agent can answer it.

### 4a — Warm-up (2 min)

Simple question to confirm the plumbing works:

```sql
SELECT * FROM TABLE(
    DIGITALNATIVECO.MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
        'How many accounts do we have in each health category?'
    )
);
```

If this works, the plumbing is correct. The agent should return counts by health_category.

### 4b — THE question (3 min)

```sql
SELECT * FROM TABLE(
    DIGITALNATIVECO.MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
        'What can I do to increase NRR by 10% right now?'
    )
);
```

**PAUSE.** Let the room read the answer.

The agent should identify at-risk accounts ($649K) and expansion opportunities ($402K). It should name specific accounts, quote dollar amounts, and suggest actions.

**Look for something you didn't ask about.** Did the agent mention AE turnover? Did it find the CSM warning from 60 days ago? Did it discover the competitor evaluation you didn't know about?

> **Presenter:** "You didn't ask about AE turnover. You didn't tell it to check the CSM notes. It found all of that because your semantic model defined what matters and the search services gave it access to the raw conversations. Pull the semantic model out and this agent hallucinates."

### 4c — Discovery (4 min)

```sql
SELECT * FROM TABLE(
    DIGITALNATIVECO.MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
        'Were there early warning signs we missed? Check the internal notes.'
    )
);
```

The agent should search CSM notes and find: Sarah Chen flagged Meridian 60 days ago. James Okafor noted Prism "going dark" 45 days ago. Emily Thornton escalated about Beacon's AE transition.

**The ooh moment:** "Your own team flagged these months ago. Nobody acted."

### 4d — Free explore (3 min)

Ask your own questions. Here are some to try:

- "What do our healthiest accounts do differently from our struggling ones?"
- "Are we giving discounts to the wrong accounts?"
- "Show me every mention of a competitor across all conversations"
- "What would you tell our board about customer health right now?"

The agent has access to structured data (analyst), Gong transcripts, support tickets, and CSM notes. See what it discovers.

---

## Stretch Goals (if time permits)

### Add a custom tool: risk alert stored procedure

Create a stored procedure the agent can call to log risk alerts:

```sql
CREATE OR REPLACE TABLE DIGITALNATIVECO.MARTS.RISK_ALERTS (
    alert_id STRING DEFAULT UUID_STRING(),
    account_name STRING,
    risk_summary STRING,
    recommended_action STRING,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE PROCEDURE DIGITALNATIVECO.MARTS.GENERATE_RISK_ALERT(
    account_name STRING,
    risk_summary STRING,
    recommended_action STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    INSERT INTO DIGITALNATIVECO.MARTS.RISK_ALERTS (account_name, risk_summary, recommended_action)
    VALUES (:account_name, :risk_summary, :recommended_action);
    RETURN 'Risk alert created for ' || :account_name || ': ' || :risk_summary;
END
$$;
```

### Multi-turn conversation

```sql
SELECT * FROM TABLE(
    DIGITALNATIVECO.MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
        'How many accounts are in each health category?'
    )
);
```

Copy the `thread_id` from the response, then follow up:

```sql
SELECT * FROM TABLE(
    DIGITALNATIVECO.MARTS.ACCOUNT_HEALTH_AGENT!COMPLETE(
        'Now drill into the at-risk ones — what are their usage trends?',
        THREAD => '<paste_thread_id_here>'
    )
);
```

---

## What You Just Did

- Defined a **semantic model** encoding your business logic — what "at risk" means, what thresholds matter
- Created **three search services** over Gong transcripts, support tickets, and CSM notes — giving the agent access to raw customer voice and internal observations
- Deployed a **Cortex Agent** with four tools that decides which source to query based on the question
- Asked **the CRO's question** and watched the agent discover insights you didn't ask about — AE turnover, competitor threats, missed warnings
- Experienced the agent **triangulating** across structured and unstructured data to tell complete account stories

**The agent is impressive. But look at what made it work: your semantic model.** You defined what matters. Without your definitions, the agent hallucinates. Your data layer is what makes agents useful — and now you can build the whole stack.

**Next up: Lab 3 — you'll ship this as a product the CRO can actually use.**
