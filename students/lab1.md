# Lab 1: Understand the Business

**Duration:** 25 min

> It's your first day. The CRO asks: what can I do to increase NRR by 10%? Before you can answer, you need to understand the data.

---

## Setup

Set your context and verify the 10 raw tables are loaded:

```sql
USE ROLE SYSADMIN;
USE DATABASE DIGITALNATIVECO;
USE SCHEMA RAW;
```

Run the row count query from the README to confirm all tables are present.

---

## Step 1: Orient (3 min)

Open **Cortex Code** and ask it to show you what's in the RAW schema — what tables exist, how many rows, what columns.

Then ask: how big is this business? What's the total ARR and how does it break down?

---

## Step 2: AI reads what you can't (7 min)

You have ~500 support tickets and ~150 Gong call transcripts. You can't read them all. But AI can.

### 2a. Sentiment

Ask Cortex Code to score the support tickets by sentiment and show you the angriest ones. Read the actual ticket text — what are customers saying?

### 2b. Gong signal extraction

Ask Cortex Code to read the Gong call transcripts and extract signals from each one: did they mention a competitor? Are they frustrated? Is there an expansion opportunity? How engaged is the champion?

### 2c. Ticket classification

Ask Cortex Code to categorize the tickets (billing, technical, feature request, complaint, onboarding) and show you which categories have the worst sentiment.

---

## Step 3: Build the mart (10 min)

This is the big one. Ask Cortex Code to build a single mart table — `MARTS.MART_ACCOUNT_HEALTH` — with one row per account, joining all 10 raw tables.

You'll need columns from:
- **Accounts:** ARR, industry, seats, products, renewal date, CSM, NPS
- **Support tickets:** count, average sentiment, complaint count, P1/P2 count
- **Gong transcripts:** competitor mentioned, expansion signal, frustration, champion engagement, call count
- **Product events:** weekly active users, seat utilization, usage trend
- **Employees + assignments:** current AE, tenure, whether AE changed recently
- **Opportunities:** pipeline amount, stages, closest close date
- **Invoices:** average discount, overdue count, days to pay
- **Feature usage:** features used, power features, feature breadth

Add a `health_category` column that classifies accounts as at_risk, expansion, healthy, or attention.

**Before you run it:** review the SQL. Do you agree with the thresholds? Would you define "at risk" differently for your company?

---

## Step 4: See the answer forming (5 min)

### 4a. Portfolio view

Query the mart — show all 20 accounts sorted with the most at-risk at the top.

### 4b. Quantify the opportunity

How much ARR is at risk? How much expansion pipeline is there? How many accounts are in each health category?

### 4c. Deep-dive

Pick an at-risk account and look at all its columns in one row. How many danger signals can you spot?

---

## What's next

You have the data. But the CRO doesn't speak SQL. She needs an agent. That's Lab 2.
