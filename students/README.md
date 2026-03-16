# Workshop: The Data Layer Is the Last Mile

Welcome! Over the next 90 minutes you're going to build an AI-powered intelligence product — from raw data to a deployed app a business user can talk to.

## The Scenario

It's your first day at **DigitalNativeCo**, a B2B SaaS company with three products: Canvas (design), Flow (workflow automation), and Insight (analytics). You have 20 accounts, $3.5M in ARR, and a CRO who just asked:

> **"What can I do to increase NRR by 10%?"**

The answer is buried across 10 data sources that have never been connected. Your job is to find it.

## The Three Labs

| Lab | Duration | What you'll build |
|-----|----------|-------------------|
| [Lab 1: Understand the Business](lab1.md) | 25 min | Use Cortex Code to explore, enrich, and model the data into one account health mart |
| [Lab 2: Build the Brain](lab2.md) | 25 min | Create a semantic model, search services, and a Cortex Agent |
| [Lab 3: Ship the Product](lab3.md) | 25 min | Configure and share a production intelligence product via Snowflake Intelligence |

## Before You Start

1. Open **Snowsight** in your browser
2. Open a **SQL worksheet**
3. Open the **Cortex Code** panel (AI assistant on the right side)
4. Run this to set your context:

```sql
USE ROLE SYSADMIN;
USE DATABASE DIGITALNATIVECO;
USE SCHEMA RAW;
```

## Tips

- **Talk to Cortex Code like a person.** Don't write SQL — describe what you want in plain English. The coding agent figures out the implementation.
- **Read before you run.** Every time Cortex Code generates SQL, review it. Check the logic. Decide if you agree with the thresholds. The AI writes the code — you decide if it's right.
- **The CRO thread.** Every step connects back to the CRO's question. Keep $350K in your head — that's 10% of $3.5M ARR.
- **Ask your own questions.** The suggested prompts are starting points. The best moments happen when you go off-script.
- **If you get stuck,** ask the presenter or check with your neighbor. The prompts don't need to be exact — Cortex Code is flexible.
