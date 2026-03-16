# CoCo HOL — Cortex Code Hands-On Lab

**"The Data Layer Is the Last Mile"** — A 2-hour hands-on workshop for analytics engineers.

Build an Account Health Intelligence product using Snowflake Cortex Code, Cortex Agents, and Snowflake Intelligence — from raw data to a deployed product a business user can talk to. As one person. In 90 minutes.

## The Use Case

**DigitalNativeCo** is a B2B SaaS company with 20 accounts, $3.5M ARR, and a CRO who asks: *"What can I do to increase NRR by 10%?"*

The answer is spread across 10 data sources that have never been connected:

| Source | Rows | What it tells you |
|--------|------|-------------------|
| Product events | ~5,300 | Feature adoption, usage trends, drop-offs |
| Support tickets | ~513 | Sentiment, escalation patterns |
| Gong transcripts | ~157 | Competitor mentions, expansion signals, frustration |
| Employees | 20 | AE/CSM roster, departures |
| Account assignments | 44 | Ownership history, handoff timing |
| Opportunities | 21 | Renewal and expansion pipeline |
| Feature usage | ~7,800 | Feature-level adoption per account per week |
| Invoices | 80 | Discounts, payment timing, overdue |
| CSM notes | ~55 | Internal risk flags, escalations, meeting notes |
| Accounts | 20 | ARR, industry, products, NPS |

## Three Labs

| Lab | Duration | What you build |
|-----|----------|---------------|
| **Lab 1: Understand the Business** | 25 min | AI-enrich 10 sources into one account health mart using Cortex Code |
| **Lab 2: Build the Brain** | 25 min | Semantic model + 3 search services + Cortex Agent |
| **Lab 3: Ship the Product** | 25 min | Configure, use, and share via Snowflake Intelligence |

## Quick Start

### 1. Generate sample data

```bash
python workshop/data/generate_data.py
```

### 2. Set up Snowflake

```bash
# Load seed data and run setup SQL
python workshop/sql/deploy.py
```

### 3. Run the labs

Follow the guides in `workshop/data/labs/`:
- [Lab 1: Understand the Business](workshop/data/labs/lab1.md)
- [Lab 2: Build the Brain](workshop/data/labs/lab2.md)
- [Lab 3: Ship the Product](workshop/data/labs/lab3.md)

### Rebuild to any checkpoint

```bash
python workshop/sql/setup_checkpoint.py lab2   # rebuilds everything through Lab 2
python workshop/sql/teardown_lab.py --confirm   # clean slate
```

### Run the full test suite

```bash
python workshop/sql/test_full_lab.py
```

## Prerequisites

- Snowflake account with Cortex AI enabled
- `SNOWFLAKE.CORTEX_USER` database role granted
- Cortex Code available in Snowsight
- Warehouse: `COMPUTE_WH` (or any XS warehouse)

## Presenter Materials

- [Slide deck script](data/workshop_slides.md)
- [Demo script with expected outputs](workshop/data/labs/demo_script.md)
- [Data design doc](workshop/DATA_DESIGN.md)
- [POV doc](data/pov_analytics_engineers.md)

## The 20 Accounts

Each account tells a story the agent should surface:

| Category | Accounts | Signal |
|----------|----------|--------|
| **Churn Risk** | Meridian Media, Cascade Financial, Beacon Logistics, Prism Retail | Usage down, negative sentiment, competitor mentions, silent churn |
| **Expansion** | Atlas Digital, Summit Healthcare, Voyager Entertainment, Ironclad Manufacturing | Usage up, feature requests, cross-sell interest |
| **Healthy** | Northstar, Ridgeline, Clearwater, Horizon, Sterling, Apex, Pinnacle, Crestline | Stable, low drama |
| **Attention** | Cobalt Aerospace, Driftwood Media, Evergreen Education, Flux Dynamics | Onboarding stall, admin change, budget pressure, rate limits |
