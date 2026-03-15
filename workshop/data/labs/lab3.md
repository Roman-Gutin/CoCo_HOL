# Lab 3: Ship the Product

**Duration:** 25 min
**The question:** "The CRO doesn't install npm. She needs this in her browser, now."

> You built the data. You built the brain. Now ship it as a product a business user can talk to — without writing a single line of frontend code.

---

## Prerequisites

- Completed Lab 1 and Lab 2
- `DIGITALNATIVECO.MARTS.ACCOUNT_HEALTH_AGENT` exists
- Snowsight Intelligence available

---

## Step 1: Configure for the CRO (5 min)

> **Why this step:** The agent works. But right now it's a SQL function in a worksheet. The CRO doesn't open SQL worksheets. You need to package this as something she can click and use.

In Snowsight Intelligence:

1. Open your `ACCOUNT_HEALTH_AGENT` in Snowsight
2. Click **Edit**
3. Add sample questions — these become clickable prompts the CRO sees:
   - "What can I do to increase NRR by 10% right now?"
   - "Which accounts should I focus on this week?"
   - "Are there accounts we're about to lose that we can still save?"
   - "Where are the expansion opportunities?"
   - "What patterns do you see in our churn?"
   - "Which accounts renew in the next 60 days?"
   - "Draft me an email to the VP of Sales about our at-risk accounts"
   - "What would you tell the board about customer health?"

4. Customize the response instruction:

   > "When suggesting actions, name the specific person to contact, the dollar amount at stake, and the deadline. After every analysis, suggest one specific data model improvement that would make this insight easier to find next time."

5. Add the `data_to_chart` tool for visualizations
6. Save

> **Presenter:** "Those sample questions are the product design. You're deciding what the CRO sees when she opens this tool. This is product thinking, not data engineering."

---

## Step 2: Use It as the CRO (8 min)

> **Why this step:** You need to experience this as the CRO would. Not as the builder — as the user. Click a question and watch the answer stream in.

### 2a — Click a sample question

Click "What can I do to increase NRR by 10% right now?" — watch the answer stream in. If the agent has the `data_to_chart` tool, it may generate charts automatically.

> **Watch what happens.** The agent queries your semantic model, searches the transcripts and notes, and synthesizes an answer with account names, dollar amounts, and specific actions. The CRO didn't write SQL. She clicked a button.

### 2b — Multi-turn: ask a follow-up

Type in the same thread:

> "Draft me an email to my VP of Sales summarizing the three accounts we need to act on this week with specific action items and owners."

> **The agent remembers context.** It uses the prior answer — no new tool calls needed. It generates a formatted email with account names, dollar amounts, and named owners.

> **Presenter:** "Multi-turn conversation. She doesn't need to re-explain the context. Ask a follow-up and the agent builds on what it already knows."

### 2c — Follow-up: renewal urgency

Type:

> "Which of these accounts has a renewal in the next 60 days?"

> The agent queries contract_renewal_date. It should return Prism Retail (renews ~April 10) and Cascade Financial (renews ~May 1). Both are at risk.

### 2d — Explore freely

Try your own questions:

- "Compare Meridian's trajectory to our other at-risk accounts"
- "What would happen to our NRR if we lost all at-risk accounts?"
- "Which CSM has the most at-risk accounts?"

---

## Step 3: Share It (5 min)

> **Why this step:** A product isn't a product until someone else can use it. Ship it to your neighbor.

1. Click **Share** on the agent in Snowsight Intelligence
2. Grant access to your neighbor's Snowflake role
3. Your neighbor opens it in their Snowsight
4. They click "What can I do to increase NRR by 10%?"
5. **It works. Immediately. Same quality answer.**

> You didn't send a dashboard link. You didn't export a PDF. You shared a live intelligence product that can answer any question about account health. Your neighbor didn't install anything, learn SQL, or read documentation. They asked a question and got a data-backed answer.

> **Presenter:** "You just shipped a production intelligence product to a business user. They didn't install anything. They didn't learn SQL. They asked a question in English and got a data-backed answer with dollar amounts and action items. You built that. In 90 minutes."

---

## Step 4: The React Dashboard (PRESENTER DEMO ONLY) (7 min)

> **Why this step:** Snowflake Intelligence handles 80% of use cases. But sometimes you need a custom UI — a heatmap, a drill-down, an embedded chat. This is what that looks like.

> **This step is a presenter demo. Participants watch, they don't build.** The goal is to show what's possible when you need full control, not to teach React.

Presenter shows the pre-deployed React app:

1. **Heatmap view** — all 20 accounts, signal columns (usage trend, sentiment, competitor, AE change), red/yellow/green cells. "This is the portfolio view the VP of CS sees every Monday."

2. **Drill-down** — click Meridian Media Group. See the usage cliff sparkline, negative support tickets with sentiment badges, Gong transcript excerpts about SketchFlow, AE assignment timeline. "Every signal from Lab 1, visualized."

3. **Embedded chat** — same agent from Lab 2, embedded in the app. Type "What should I do about this account?" and get a contextual answer. "Same semantic model. Same search services. Different surface."

4. **Live modification** — Presenter prompts Cortex Code: "Add a column to the heatmap that shows days until contract renewal. Color it red if under 30 days, yellow if under 60." Cortex Code generates the React component diff. Apply it. Heatmap updates live.

> **Presenter:** "This React app is aspirational — it's the stretch goal for when you need full custom control. For 80% of use cases, the Snowflake Intelligence agent you just shipped IS the product."

---

## What You Just Did

- Configured the agent as a **product** with sample questions, response instructions, and visualization tools
- Experienced **multi-turn conversation** — the CRO asks follow-ups without re-explaining context
- **Shared the agent** with a colleague who used it immediately — zero setup, zero training
- Saw a **React dashboard** demo showing what full custom control looks like (heatmap, drill-down, embedded chat)

You shipped a production intelligence product. As one person. Without writing frontend code.

The CRO asked "What can I do to increase NRR by 10%?" You built the system that answers that question — and any follow-up she can think of — in 90 minutes.

**This is what "full-stack data product builder" looks like.**

---

*Head back to the main room for the closing.*
