# Lab 2: Build the Brain

**Duration:** 25 min

> You have the numbers. The CRO doesn't speak SQL. Time to build an agent she can talk to.

---

## Setup

```sql
USE ROLE SYSADMIN;
USE SCHEMA DIGITALNATIVECO.MARTS;
```

Verify your mart from Lab 1 exists and has 20 rows.

---

## Step 1: Teach the AI your language (5 min)

The agent needs a **semantic model** — a file that explains what your data means in business terms. Without it, the agent hallucinates.

Ask Cortex Code to create a semantic model YAML for `MARTS.MART_ACCOUNT_HEALTH`. Every column needs a description that encodes business judgment — not just "this is a number," but what the number *means*. For example:
- What does sentiment below -0.3 mean?
- Why do AE changes within 90 days matter?
- What does low seat utilization indicate?

Then upload the YAML to a stage. You'll need to:
1. Create a stage: `MARTS.SEMANTIC_MODELS`
2. Use a Python worksheet to upload the YAML file

**Read the YAML before you move on.** You're defining how an AI agent will reason about your business. This is the most important file you'll create today.

---

## Step 2: Give the AI ears (5 min)

The mart has numbers. But numbers tell you *what* happened — not *why*. The raw conversations tell you why.

Create three **Cortex Search services** so the agent can search:
1. Gong call transcripts
2. Support ticket text
3. Internal CSM notes

Test them — search for competitor mentions, or for champion departures. Read the results. These are the actual words your customers and your team wrote.

---

## Step 3: Wire the brain (3 min)

Create a **Cortex Agent** that connects:
- The semantic model (for structured data queries)
- The three search services (for unstructured text search)

This is one SQL statement. The hard part was your definitions — this is plumbing.

---

## Step 4: The moment of truth (12 min)

### 4a. Warm-up

Ask the agent a simple question to confirm it works — something like "how many accounts are in each health category?"

### 4b. THE question

Ask the agent: **"What can I do to increase NRR by 10% right now?"**

Read the response carefully. Did it:
- Name specific accounts with dollar amounts?
- Find something you didn't ask about (AE turnover? competitor threats? CSM warnings)?
- Combine structured data with unstructured conversation context?

### 4c. Discovery

Ask: **"Were there early warning signs we missed? Check the internal notes."**

What did the agent find? Were there flags your team raised months ago?

### 4d. Free explore

Ask your own questions. Some ideas:
- "What do our healthiest accounts do differently?"
- "Are we giving discounts to the wrong accounts?"
- "What would you tell the board about customer health?"

---

## What's next

The agent works. But it's in a SQL worksheet. The CRO needs it in her browser. That's Lab 3.
