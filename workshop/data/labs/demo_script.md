# Workshop Demo Script — Complete Prompts & Expected Behavior

**The One Question:** "What can I do to increase NRR by 10% right now?"

**Setup:** All 10 tables preloaded in DIGITALNATIVECO.RAW. Participants open a SQL worksheet in Snowsight with Cortex Code panel open.

---

## LAB 1: "Understand the Business" (25 min)

### Step 1: Orient (3 min)

**Cortex Code prompt:**
> I just joined DigitalNativeCo as an analytics engineer. I have tables in the DIGITALNATIVECO.RAW schema but I don't know what's in them. Write me an exploration query that shows every table name, its row count, and the first 3 column names so I can understand the data landscape quickly. Use INFORMATION_SCHEMA or a UNION ALL approach.

**What Cortex Code generates:** A UNION ALL query across all 10 tables with COUNT(*) and column names.

**What participant sees after running:**
```
accounts              20 rows    (account_id, account_name, industry...)
product_events      5284 rows    (event_id, account_id, product...)
support_tickets      513 rows    (ticket_id, account_id, ticket_text...)
gong_transcripts     157 rows    (call_id, account_id, transcript_excerpt...)
employees             20 rows    (employee_id, name, role...)
account_assignments   44 rows    (assignment_id, account_id, employee_name...)
opportunities         21 rows    (opportunity_id, account_id, amount...)
feature_usage       7836 rows    (feature_usage_id, account_id, feature_name...)
invoices              80 rows    (invoice_id, account_id, discount_pct...)
csm_notes             55 rows    (note_id, account_id, note_text...)
```

**Follow-up prompt:**
> Show me a summary of the accounts table — total ARR, count of accounts, and a breakdown by industry. Also show me the min, max, and average ARR.

**What they see:** Total ARR ~$3.5M across 20 accounts. Media, Healthcare, Financial Services, Manufacturing, etc. ARR ranges from $54K to $480K.

---

### Step 2: Let AI read what you can't (7 min)

**Prompt 2a — Sentiment:**
> I have 513 support tickets in RAW.SUPPORT_TICKETS with a ticket_text column. Use SNOWFLAKE.CORTEX.SENTIMENT to score each ticket, then show me the 10 most negative tickets with their account_name, a preview of the ticket text (first 100 chars), and the sentiment score. I want to understand which customers are most frustrated.

**What Cortex Code generates:**
```sql
SELECT account_name, LEFT(ticket_text, 100) AS preview,
       SNOWFLAKE.CORTEX.SENTIMENT(ticket_text) AS sentiment
FROM RAW.SUPPORT_TICKETS
ORDER BY sentiment ASC
LIMIT 10;
```

**What they see:** Meridian, Beacon, Cascade tickets scoring -0.7 to -0.9. They can READ the actual complaints: "This is the third time Canvas has frozen mid-export..." / "URGENT: The Insight API has been returning 500 errors..." / "We've been trying to reach our account executive for three weeks..."

**Prompt 2b — Gong signal extraction:**
> Now I need to understand our sales conversations. I have 157 Gong call transcripts in RAW.GONG_TRANSCRIPTS with a transcript_excerpt column. Use SNOWFLAKE.CORTEX.COMPLETE with claude-3-7-sonnet to extract structured signals from each transcript. For each call, I need: competitor_mentioned (boolean), frustration_level (low/medium/high), expansion_signal (boolean), champion_engagement (low/medium/high), and key_themes (comma-separated). Return the extraction as a JSON column. Show me 5 results with account_name, call_type, and the extracted JSON.

**What Cortex Code generates:**
```sql
SELECT account_name, call_type,
  SNOWFLAKE.CORTEX.COMPLETE('claude-3-7-sonnet',
    'Extract from this call transcript and return ONLY valid JSON: ...'
    || transcript_excerpt
  ) AS signals
FROM RAW.GONG_TRANSCRIPTS LIMIT 5;
```

**What they see:** JSON with `competitor_mentioned: true` for Meridian calls, `expansion_signal: true` for Atlas/Voyager, `frustration_level: high` for Beacon. Specific themes like "champion_departure", "api_reliability", "competitor_evaluation".

**Prompt 2c — Ticket classification:**
> Classify the support tickets using SNOWFLAKE.CORTEX.CLASSIFY_TEXT into these categories: billing, technical, feature_request, complaint, onboarding. Show a breakdown — how many tickets per category and what's the average sentiment for each category? I want to see which types of issues correlate with the worst sentiment.

**What Cortex Code generates:**
```sql
SELECT SNOWFLAKE.CORTEX.CLASSIFY_TEXT(ticket_text,
         ['billing','technical','feature_request','complaint','onboarding']
       ):label::STRING AS category,
       COUNT(*) AS cnt,
       ROUND(AVG(SNOWFLAKE.CORTEX.SENTIMENT(ticket_text)), 3) AS avg_sentiment
FROM RAW.SUPPORT_TICKETS
GROUP BY 1 ORDER BY avg_sentiment ASC;
```

**What they see:**
```
complaint         50    -0.554
technical        196    -0.300
onboarding        49    -0.294
billing           55    -0.199
feature_request  163    -0.003
```

Complaints have the worst sentiment. Feature requests are almost neutral (positive signal — customers who request features are engaged, not leaving).

---

### Step 3: Build the mart (10 min)

**The big prompt:**
> I need to build a mart table called MARTS.MART_ACCOUNT_HEALTH that gives me one row per account with everything I need to assess account health. Join all 10 raw tables at the account level. Here's what I need for each account:
>
> From ACCOUNTS: arr, industry, licensed_seats, products, contract_renewal_date, csm_name, nps_score
>
> From SUPPORT_TICKETS: total ticket_count, avg sentiment score (use CORTEX.SENTIMENT), count of complaints (use CORTEX.CLASSIFY_TEXT), count of P1/P2 tickets
>
> From GONG_TRANSCRIPTS: use CORTEX.COMPLETE to extract competitor_mentioned and expansion_signal from each transcript, then aggregate per account — any_competitor_mentioned (boolean), any_expansion_signal (boolean), modal frustration_level, modal champion_engagement, total call count
>
> From PRODUCT_EVENTS: weekly_active_users for the most recent week, seat_utilization as pct of licensed_seats, week-over-week usage trend pct using LAG
>
> From EMPLOYEES + ACCOUNT_ASSIGNMENTS: current AE name, days since AE was assigned (ae_tenure_days), whether AE changed in last 90 days (ae_changed_recently boolean), AE's employment status
>
> From OPPORTUNITIES: total open pipeline_amount, pipeline stages, nearest close date
>
> From INVOICES: average discount pct, count of overdue invoices, average days to pay
>
> From FEATURE_USAGE: count of distinct features used, count of power features used (canvas_collab_edit, canvas_templates, flow_approvals, insight_dashboards, insight_api), feature breadth as pct of total available features
>
>
> Add a health_category column: CASE WHEN any_competitor_mentioned = TRUE OR avg_sentiment < -0.3 THEN 'at_risk' WHEN any_expansion_signal = TRUE AND usage_trend > 5 THEN 'expansion' WHEN avg_sentiment >= -0.1 AND usage_trend >= -5 THEN 'healthy' ELSE 'attention' END
>
> Write this as CREATE OR REPLACE TABLE MARTS.MART_ACCOUNT_HEALTH AS SELECT with CTEs for each source. Order the final result by arr descending.

**What Cortex Code generates:** A 80-100 line query with 7-8 CTEs. This is the showcase moment for Cortex Code — it writes production-grade analytics SQL from a natural language spec.

**What participant does:** READS the generated SQL. The lab guide says:

> Before you run this, review two things:
> 1. How did it define ae_changed_recently? Do you agree with the 90-day threshold?
> 2. Look at the Gong extraction prompt — would you change what signals it extracts?
>
> This is the moment where YOU add judgment. The AI wrote the SQL. You decide if the logic is right.

**They may edit** the thresholds, add a column, tweak the Gong extraction prompt. Then they run it.

**Runtime:** 30-90 seconds (Cortex AI functions processing 670 documents).

---

### Step 4: See the answer taking shape (5 min)

**Prompt 4a — Portfolio view:**
> Query MARTS.MART_ACCOUNT_HEALTH and show me all 20 accounts with: account_name, arr, health_category, avg_sentiment, competitor_mentioned, ae_changed_recently, overdue_invoices, feature_breadth_pct, pipeline_amount. Sort by avg_sentiment ascending so the most at-risk accounts are at the top.

**What they see:** The full portfolio. Beacon (-0.56 sentiment, AE changed), Meridian (-0.42, competitor, AE changed, overdue), Cascade (-0.52, competitor), Cobalt (-0.44, 15% feature breadth). Then the healthy accounts: Atlas (+0.18, expansion), Summit (-0.04, expansion), Voyager (+0.02, expansion, 95% feature breadth).

**Prompt 4b — Quantify the opportunity:**
> From MART_ACCOUNT_HEALTH, calculate: (1) total ARR across all accounts, (2) total ARR where health_category = 'at_risk' — call this at_risk_arr, (3) total pipeline_amount where health_category = 'expansion' — call this expansion_pipeline, (4) count of accounts per health_category. Show it as a single summary row.

**What they see:**
```
total_arr: $3,461,000
at_risk_arr: $649,000
expansion_pipeline: $402,000
at_risk_accounts: 6
expansion_accounts: 4
```

**Presenter says:** "You can see the answer to the CRO's question forming. $649K at risk. $402K in expansion pipeline. But she doesn't speak SQL. She needs an agent that speaks English. That's Lab 2."

---

## LAB 2: "Build the Brain" (25 min)

> **Timing note:** The agent creation (Step 3) is the critical path. If Step 1 (semantic model) takes longer than expected, the presenter can provide a pre-built YAML file for participants to upload.

> **Fallback:** If Cortex Search service creation is slow (can take 2-3 min per service), have participants create all three in parallel and move to Step 3 while they provision. The agent will work with just the Analyst tool — search services can be added after.

### Step 1: Define the semantic model (5 min)

**Prompt:**
> I need to create a Cortex Analyst semantic model YAML for MARTS.MART_ACCOUNT_HEALTH. This will power an AI agent that answers business questions about account health. Write the YAML with:
>
> - base_table using the object format (database: DIGITALNATIVECO, schema: MARTS, table: MART_ACCOUNT_HEALTH)
> - Every column as either a dimension or measure
> - data_type on every field (TEXT, NUMBER, or BOOLEAN)
> - Rich descriptions that explain the business meaning, not just the column name. For example:
>   - avg_sentiment: "Average sentiment across support tickets. Scale -1 to 1. Below -0.3 indicates frustrated customers."
>   - ae_changed_recently: "TRUE if the account executive was reassigned within the last 90 days. AE changes are a leading indicator of account health decline — accounts that lose their AE often experience gaps in coverage and missed check-ins."
>   - feature_breadth_pct: "Percentage of available product features actively used. Below 30% indicates shallow adoption and churn risk. Above 70% indicates sticky, deeply embedded usage."
>   - overdue_invoices: "Count of unpaid invoices. Any overdue invoice is a churn signal — customers who stop paying are already mentally gone."
>
> Make the descriptions opinionated — they should encode business judgment, not just metadata.
>
> Then write a Python worksheet that uploads this YAML to @DIGITALNATIVECO.MARTS.SEMANTIC_MODELS/account_health.yaml

**What Cortex Code generates:** The full YAML with ~12 dimensions and ~18 measures, each with business-context descriptions. Plus the Python upload script.

**What participant does:** Reviews the descriptions. The lab guide asks:

> Read the description for avg_sentiment. The threshold is -0.3. Would you change it for YOUR company? What about feature_breadth_pct — is 30% the right alarm threshold for your products?
>
> This is the moment where your domain expertise matters more than any model. You're encoding business judgment that will determine how every AI agent in the company reasons about your data.

They edit if they want, then run the Python worksheet.

**Verify:** `LIST @MARTS.SEMANTIC_MODELS;` — see `account_health.yaml`

---

### Step 2: Connect the unstructured sources (5 min)

**Prompt:**
> Create three Cortex Search services so an AI agent can search our unstructured data:
>
> 1. MARTS.GONG_TRANSCRIPT_SEARCH — searches transcript_excerpt from RAW.GONG_TRANSCRIPTS, with attributes account_name and call_type
> 2. MARTS.SUPPORT_TICKET_SEARCH — searches ticket_text from RAW.SUPPORT_TICKETS, with attributes account_name and priority
> 3. MARTS.CSM_NOTES_SEARCH — searches note_text from RAW.CSM_NOTES, with attributes account_name and note_type
>
> Use COMPUTE_WH and 1 hour target lag. Then write a test query that searches the Gong transcripts for "customer frustrated with reliability or considering alternatives" and returns 3 results.

**What Cortex Code generates:** Three CREATE CORTEX SEARCH SERVICE statements + a test query.

**They run all four.** The test search returns actual transcript excerpts — raw customer voice talking about problems, competitors, frustration.

**What participant sees:** Robert Kimball (VP Engineering) talking about API outages. Derek Huang asking about SketchFlow. Laura Singh saying "I haven't made a decision yet, but I need DigitalNativeCo to give me a reason to stay."

**The moment:** "The agent can now hear what customers actually said. Not a metric. Their voice."

---

### Step 3: Create the agent (3 min)

**Prompt:**
> Create a Cortex Agent in Snowflake Intelligence called ACCOUNT_HEALTH_AGENT with:
> - Model: claude-3-7-sonnet
> - 4 tools: cortex_analyst (using our semantic model), and three cortex_search services (gong, tickets, csm notes)
> - Also add the data_to_chart tool for visualizations
> - Response instructions: "After every answer, suggest: (a) a dbt model or YAML change to make this insight permanent, (b) a report the team should build, (c) additional data sources that would sharpen the analysis."
> - Orchestration instructions: "Use analyst for quantitative questions. Use search tools for qualitative context. For complex questions, use multiple tools. Always combine numbers with the human story."
> - 8 sample questions including "What can I do to increase NRR by 10% right now?"

**What participant does:** Either creates via the Snowsight Intelligence UI (point-and-click) or runs the REST API/SQL from Cortex Code's output.

**The moment:** "Four objects. A YAML, three search services, and an agent. That's the entire architecture."

---

### Step 4: The moment of truth (12 min)

**The CRO's question. Participant types into the agent:**

> What can I do to increase NRR by 10% right now?

**What the agent does (tool calls):**

1. **Tool: analyst** — Queries the semantic model. Generates SQL like:
   ```sql
   SELECT account_name, arr, avg_sentiment, competitor_mentioned,
          expansion_signal, ae_changed_recently, pipeline_amount,
          overdue_invoices, feature_breadth_pct
   FROM mart_account_health
   WHERE competitor_mentioned = TRUE
      OR avg_sentiment < -0.3
      OR expansion_signal = TRUE
   ORDER BY arr DESC
   ```
   Gets back: at-risk accounts with dollar amounts, expansion accounts with pipeline.

2. **Tool: gong_search** — Searches transcripts for expansion and churn signals. Finds:
   - Voyager: "launching a new streaming division, 50 people need the full suite, $180K"
   - Atlas: "VP of Marketing can approve $95K if demo shows time savings in 30 days"
   - Meridian: "VP is leaning toward SketchFlow unless something changes"

3. **Tool: ticket_search** — Searches tickets for escalation context. Finds:
   - Beacon: "Third major API outage, VP of Operations CC'ing legal"
   - Meridian: "We've been trying to reach our AE for three weeks"

4. **Tool: csm_notes_search** — Searches internal notes. Finds:
   - Sarah Chen flagged Meridian at-risk 60 days ago, no action taken
   - Rachel Goldstein: "Atlas is our strongest expansion opportunity right now"
   - Emily Thornton: "Beacon's combination of API issues + AE transition hasn't been ideal"

5. **Agent synthesizes.** Response includes:
   - **Save:** Meridian ($186K), Beacon ($97K), Cascade ($312K) — specific actions per account with named people and deadlines
   - **Grow:** Voyager ($180K), Atlas ($95K), Summit ($72K) — specific next steps with champion names and dollar amounts
   - **Total NRR impact:** $649K at risk to protect + $347K expansion to capture
   - **Suggested dbt model:** `account_health_risk_score` composite metric
   - **Suggested report:** Weekly NRR drivers dashboard with renewal countdown
   - **Missing data:** contract terms (auto-renewal clauses), product usage by feature over time, competitive win/loss history

**PAUSE. Presenter to room:**

> "You didn't tell the agent about AE turnover. You didn't tell it to check the CSM notes. You didn't tell it to search for competitor mentions. It found all of that because your semantic model defined what matters, and the search services gave it access to the raw conversations. Pull the semantic model out and this agent hallucinates. You are the reason it works."

---

**Follow-up prompts (participants explore freely, 7 min):**

**Prompt: "Were there warning signs we missed?"**

- **Agent tool calls:** csm_notes_search (primary), ticket_search, analyst
- **Finds:** Sarah Chen's risk flag from 60 days ago, James Okafor noting Prism "going dark" 45 days ago, Emily Thornton's escalation about Beacon's AE transition
- **The ooh:** "Your own team flagged these months ago. Nobody acted."

**Prompt: "What do our healthiest accounts do differently?"**

- **Agent tool calls:** analyst (primary — queries feature breadth, power features, seat utilization, NPS grouped by health status)
- **Finds:** Healthy accounts use 3+ power features, have >50% seat utilization, NPS above 7. At-risk accounts use <2 power features and have <30% feature breadth.
- **Suggested dbt model:** `feature_adoption_health_score` — composite of feature breadth + power feature count

**Prompt: "Are we giving discounts to the wrong accounts?"**

- **Agent tool calls:** analyst (primary — correlates avg_discount_pct with health signals)
- **Finds:** Meridian has 30% discount AND is churning. Evergreen has 35% discount (budget pressure). Atlas has 0% discount and is expanding. Voyager has 20% discount but is the healthiest account (volume discount, justified).
- **The insight:** "High discounts don't predict retention. Feature adoption does."

**Prompt: "Are we making the same mistakes repeatedly?"**

- **Agent tool calls:** csm_notes_search, ticket_search, gong_search
- **Finds:** AE transition failures (Meridian 3-week gap, Beacon junior replacement, Driftwood/Evergreen overloaded coverage). API reliability recurring. Onboarding mismatch (Cobalt — aerospace company getting creative agency templates).
- **The pattern:** "Three systemic failures: handoff gaps, API reliability, industry-blind onboarding."

---

## LAB 3: "Ship the Product" (25 min)

> **Timing note:** If Lab 2 ran long, Steps 1-3 (Snowflake Intelligence) are the priority. Step 4 (React demo) is optional and presenter-only.

> **Fallback:** If Snowflake Intelligence is unavailable, participants can continue testing the agent via SQL `!COMPLETE()` calls while the presenter demonstrates the Intelligence UI.

### Step 1: Configure for the CRO (5 min)

**In Snowsight Intelligence:**

1. Open ACCOUNT_HEALTH_AGENT
2. Click **Edit**
3. Add/review sample questions — these become the clickable prompts the CRO sees:
   - "What can I do to increase NRR by 10% right now?"
   - "Which accounts should I focus on this week?"
   - "Are there accounts we're about to lose that we can still save?"
   - "Where are the expansion opportunities?"
   - "What patterns do you see in our churn?"
4. Customize the response instruction — add: "When suggesting actions, name the specific person to contact, the dollar amount at stake, and the deadline."
5. Save

### Step 2: Use it as the CRO (8 min)

**Participant clicks a sample question.** Watches the answer stream in. Sees charts (data_to_chart tool).

**Then types a follow-up in the same thread:**
> Draft me an email to my VP of Sales summarizing the three accounts we need to act on this week with specific action items and owners.

**Agent tool calls:** Uses thread context (no new tool calls needed — it remembers the prior answer). Generates a formatted email with account names, dollar amounts, action items, and named owners.

**Then:**
> Which of these accounts has a renewal in the next 60 days?

**Agent tool calls:** analyst — queries contract_renewal_date vs CURRENT_DATE. Filters to accounts from the prior answer. Returns: "Prism Retail renews April 10 (26 days). Cascade Financial renews May 1 (47 days). Both are at risk."

### Step 3: Share it (5 min)

1. Click **Share** on the agent
2. Grant access to their neighbor's role
3. **Neighbor opens it, clicks "What can I do to increase NRR by 10%?"**
4. It works. Immediately. Same quality answer.

**Presenter:**
> "You just handed a production intelligence product to a business user. They didn't install anything. They didn't learn SQL. They asked a question in English and got a data-backed answer with dollar amounts and action items. You built that. In 90 minutes."

### Step 4: The React dashboard (7 min, optional demo)

Presenter shows the pre-deployed React app:

1. Heatmap — all 20 accounts, 6 signal columns, red/green cells
2. Click Meridian — drill-down with tickets, Gong transcripts, AE history
3. Open the chat — same agent, embedded in the app
4. "This is what it looks like when you go full-stack. Same semantic model. Same agent. Custom UI."

**Prompt to Cortex Code (presenter demos, participants watch):**
> Add a column to the heatmap that shows days until contract renewal. Color it red if under 30 days, yellow if under 60.

Cortex Code generates the React component diff. Presenter applies it. Heatmap updates live.

**The moment:** "The React app is the stretch goal. The Snowflake agent is the product 80% of the time. But when you need full control — the same data layer powers everything."

---

## Closing (15 min)

**Not a listicle. A callback.**

> "When you walked in this morning, the CRO asked you one question: what can I do to increase NRR by 10%? You had 10 messy tables and no documentation.
>
> In Lab 1, you let AI read 670 documents and built a mart that brings 10 sources together. In Lab 2, you encoded your business judgment into YAML and built an agent that discovers patterns nobody asked about — AE turnover, competitor threats, CSM warnings from two months ago. In Lab 3, you shipped it as a product a business user can talk to.
>
> The agent found $649K at risk and $347K in expansion. It named specific people, quoted actual customer conversations, and told you exactly what to do next. Then it suggested how to make your data model smarter.
>
> One person built all of that. In 90 minutes. With SQL and YAML.
>
> That's not a job that's going away. That's a job that's eating every other job in the building."

---

## Appendix: Agent Tool Call Patterns

| Prompt Type | Tools Used | Why |
|------------|-----------|-----|
| Quantitative ("total ARR at risk") | analyst only | Pure SQL against semantic model |
| Qualitative ("what are customers saying") | search only (1-3 services) | Unstructured text retrieval |
| Named entity ("who is Jake Torres") | search (gong + tickets) | Person not in semantic model, found in text |
| Strategic ("increase NRR by 10%") | analyst + all 3 searches | Numbers from analyst, context from every search |
| Pattern discovery ("what do they have in common") | analyst first, then search for evidence | Structured patterns, then human stories to confirm |
| Accountability ("were there warning signs") | csm_notes_search primary | Internal notes are the source of truth for missed signals |
| Self-improvement | N/A (appended to every answer) | Agent suggests dbt + reports + data sources after every response |
