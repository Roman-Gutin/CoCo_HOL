# The Data Layer Is the Last Mile — Workshop

A 2-hour hands-on workshop for analytics engineers. Build an Account Health Intelligence product using Snowflake Cortex Code, Cortex Agents, and React — from raw data to deployed app in 90 minutes.

## Use Case: DigitalNativeCo

**DigitalNativeCo** is a B2B SaaS company selling a creative/marketing platform to enterprises.

**Products:** Canvas (design tool), Flow (workflow automation), Insight (analytics dashboard)

**The high-ROI task:** An Account Health Intelligence agent that triangulates 10 data sources to answer:

> *"Which accounts are at risk of churning? Which are ready to expand? Why?"*

| Data Source | What It Tells You |
|-------------|-------------------|
| Product events | Feature adoption, usage trends, seat utilization, drop-offs |
| Support tickets | Escalation frequency, sentiment trajectory, unresolved issues |
| Gong call transcripts | Competitor mentions, frustration signals, expansion interest, champion engagement |
| Employees | AE/CSM/SE roster, hire/departure dates, coverage gaps |
| Account assignments | Ownership history, rep transitions, handoff timing |
| Opportunities | Renewal and expansion pipeline, deal stages |
| Feature usage | Granular feature-level adoption per account per week |
| Invoices | Billing history, discounts, payment timing |
| CSM notes | Internal risk flags, escalations, meeting notes |

## Workshop Timeline

| Time | Block | Duration |
|------|-------|----------|
| 0:00 | Opening: The POV (slides) | 15 min |
| 0:15 | **Lab 1:** Data Engineering + AI Enrichment | 25 min |
| 0:40 | Debrief Lab 1 | 5 min |
| 0:45 | **Lab 2:** Cortex Agents — AI That Serves Data | 25 min |
| 1:10 | Debrief Lab 2 | 5 min |
| 1:15 | **Lab 3:** Ship the Product | 25 min |
| 1:40 | Debrief Lab 3 | 5 min |
| 1:45 | Closing: What To Do Monday (slides + Q&A) | 15 min |

## Project Structure

```
workshop/
├── README.md               # This file
├── DATA_DESIGN.md          # Account stories and data model
├── data/
│   ├── generate_data.py    # Synthetic data generator (Python)
│   ├── seed/               # Generated CSVs
│   │   ├── accounts.csv
│   │   ├── product_events.csv
│   │   ├── support_tickets.csv
│   │   ├── gong_transcripts.csv
│   │   ├── employees.csv
│   │   ├── account_assignments.csv
│   │   ├── opportunities.csv
│   │   ├── feature_usage.csv
│   │   ├── invoices.csv
│   │   └── csm_notes.csv
│   └── labs/
│       ├── lab1.md
│       ├── lab2.md
│       └── lab3.md
├── sql/
│   └── setup.sql           # Snowflake DDL + seed data loading
├── semantic_model/
│   └── account_health.yaml # Cortex Analyst semantic model
├── agent/
│   └── setup_agent.sql     # Cortex Agent + Search setup
└── app/                    # React app scaffold
    ├── package.json
    ├── src/
    │   ├── App.tsx
    │   ├── pages/
    │   │   ├── Overview.tsx
    │   │   └── AccountDetail.tsx
    │   ├── components/
    │   │   ├── Chat.tsx
    │   │   └── HealthBadge.tsx
    │   └── lib/
    │       └── snowflake.ts
    └── .env.example
```

## Prerequisites

### Snowflake Account
- Cortex AI enabled (CORTEX_USER database role)
- Cortex Code available in Snowsight
- Warehouse: `COMPUTE_WH` (or any XS warehouse)

### For Lab 3 (optional presenter demo of React app)
- Node.js 18+ (presenter only — participants use Snowflake Intelligence)

## Quick Start

### 1. Generate sample data (if regenerating)

```bash
cd workshop
python data/generate_data.py
```

This creates 10 tables (~14,000 total rows) across 20 accounts with baked-in trends (churn risk, expansion signals, etc.) — including product events (~5,300), support tickets (~513), Gong transcripts (~157), employees (20), account assignments (44), opportunities (21), feature usage (~7,800), invoices (80), and CSM notes (~55).

### 2. Set up Snowflake

```bash
# Open Snowsight and run:
sql/setup.sql

# Upload seed data to the internal stage, then COPY INTO tables
```

### 3. Run Labs 1-3

Follow the guides in `data/labs/`.

### 4. Lab 3: Ship the Product

Lab 3 uses Snowflake Intelligence (built-in Snowsight agent UI) — no local setup needed.

For the optional presenter React demo:
```bash
cd app
cp .env.example .env
# Edit .env with your Snowflake credentials
npm install
npm run dev
```

## The 20 Accounts

Each account tells a story the agent should surface:

| Category | Accounts | Key Signal |
|----------|----------|------------|
| **Churn Risk** | Meridian Media, Cascade Financial, Beacon Logistics, Prism Retail | Usage ↓, negative sentiment, competitor mentions, silent churn |
| **Expansion Ready** | Atlas Digital, Summit Healthcare, Voyager Entertainment, Ironclad Manufacturing | Usage ↑, feature requests, cross-sell interest, seat expansion |
| **Healthy** | Northstar, Ridgeline, Clearwater, Horizon, Sterling, Apex | Stable usage, low ticket volume, positive calls |
| **Needs Attention** | Cobalt Aerospace, Driftwood Media, Evergreen Education, Flux Dynamics | Onboarding stall, admin change, budget pressure, rate limits |

## Presenter Materials

- **Slide deck script:** `data/workshop_slides.md` (in parent `data/` dir)
- **POV doc:** `data/pov_analytics_engineers.md` (in parent `data/` dir)
