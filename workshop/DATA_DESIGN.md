# DigitalNativeCo — Data Design

## Company Profile
**DigitalNativeCo** — B2B SaaS company selling a creative/marketing platform to enterprises.
Products: **Canvas** (design tool), **Flow** (workflow automation), **Insight** (analytics dashboard).
Think Adobe-shaped: enterprise accounts, multi-product, seat-based + usage-based pricing.

## Accounts (20 accounts, each tells a story)

### Churn Risk (4 accounts)
| Account | Story | Signals |
|---------|-------|---------|
| **Meridian Media Group** | Was heavy Canvas user, usage cratering over 8 weeks. Support tickets spiking (negative). Gong: champion left, new stakeholder mentioned evaluating SketchFlow. | Usage ↓↓, Support ↑↑ (neg), Gong: competitor + champion loss |
| **Cascade Financial** | Bought all 3 products but only uses Flow. Support: repeated complaints about Canvas onboarding. Gong: "we might not renew Canvas and Insight." | Low adoption (2/3 products), Support: onboarding complaints, Gong: partial churn signal |
| **Beacon Logistics** | Mid-size account, steady usage until 3 weeks ago — sudden drop. Support: 4 P1 tickets about API outages. Gong: frustrated tone, asking about SLA credits. | Usage cliff, Support: P1 cluster, Gong: SLA/credit demands |
| **Prism Retail** | Small account, usage slowly declining for 3 months. No support tickets (silent churn). Last Gong call: short, disengaged, "we'll circle back." | Slow usage decay, no support (bad sign), Gong: disengagement |

### Expansion Ready (4 accounts)
| Account | Story | Signals |
|---------|-------|---------|
| **Atlas Digital** | Heavy Canvas user, usage growing 15% MoM. Support: mostly feature requests (positive signal). Gong: asked about Flow pricing, wants to automate design workflows. | Usage ↑↑, Support: feature requests, Gong: cross-sell interest |
| **Summit Healthcare** | Recently onboarded, ramping fast. 90% seat utilization in 6 weeks. Support: "how do I do X?" questions (learning, not complaining). Gong: champion is evangelizing internally. | Fast ramp, high utilization, Support: learning questions, Gong: internal champion |
| **Voyager Entertainment** | Enterprise account, uses all 3 products. Usage stable and high. Gong: discussing adding 50 more seats for a new division. Support: zero tickets (self-sufficient). | Stable high usage, Gong: seat expansion, Support: quiet (good sign) |
| **Ironclad Manufacturing** | Mid-market, bought Canvas 6 months ago. Usage growing. Gong: "can Insight connect to our Snowflake warehouse?" — upsell signal for Insight. | Usage ↑, Gong: product interest |

### Healthy / Stable (6 accounts)
| Account | Story |
|---------|-------|
| **Northstar Consulting** | Steady usage, occasional support ticket, positive Gong calls |
| **Ridgeline Media** | Power user of Flow, stable |
| **Clearwater Tech** | All 3 products, moderate usage, no drama |
| **Horizon Pharma** | Canvas-heavy, seasonal spikes |
| **Sterling Partners** | Small but loyal, high NPS signals |
| **Apex Marketing** | Mid-size, growing slowly |

### Needs Attention (4 accounts)
| Account | Story |
|---------|-------|
| **Cobalt Aerospace** | New account, onboarding stalled — low usage at week 4, support tickets about confusing UI |
| **Driftwood Media** | Admin changed, new admin filing basic "how to" tickets, usage dipped temporarily |
| **Evergreen Education** | Budget pressure mentioned in Gong, but usage is actually fine — watch but don't panic |
| **Flux Dynamics** | Heavy API user, hit rate limits, filed angry tickets. Usage still high though — needs technical resolution, not a churn risk |

### Accounts with Adobe resonance
The company structure (creative tool + workflow + analytics) mirrors Adobe (Creative Cloud + Workfront + Analytics). Audience will recognize the patterns.

## Three Data Sources

### 1. Product Events (~5000 rows)
- `event_id`, `account_id`, `account_name`, `user_id`, `product` (Canvas/Flow/Insight), `event_type` (login, feature_use, export, api_call, invite_sent), `event_date`, `session_duration_min`
- Date range: 90 days (Dec 15 2025 → Mar 14 2026)
- Trends baked in per account story above

### 2. Support Tickets (~500 rows)
- `ticket_id`, `account_id`, `account_name`, `product`, `ticket_text`, `priority` (P1-P4), `status` (open/resolved/escalated), `created_at`
- Realistic ticket text with sentiment signals
- Date range: 90 days

### 3. Gong Call Transcripts (~150 rows — one transcript per call)
- `call_id`, `account_id`, `account_name`, `call_date`, `call_type` (QBR, check-in, demo, onboarding, renewal), `duration_min`, `transcript_text`, `attendees`
- Transcript text: 3-5 paragraph excerpts (not full calls, but enough for AI to extract themes)
- Themes embedded: competitor mentions, expansion signals, frustration, champion engagement, budget concerns

### Complete Data Model (10 tables)
| Table | Rows | Purpose |
|-------|------|---------|
| accounts | 20 | Account metadata, ARR, health status |
| product_events | ~5,300 | Product telemetry (logins, feature use, exports) |
| support_tickets | ~513 | Customer support tickets with free text |
| gong_transcripts | ~157 | Sales/CS call transcript excerpts |
| employees | 20 | AE/CSM/SE roster with hire/departure dates |
| account_assignments | 44 | Account ownership history with transitions |
| opportunities | 21 | Renewal and expansion pipeline |
| feature_usage | ~7,800 | Granular feature-level adoption per account per week |
| invoices | 80 | Billing history with discounts and payment timing |
| csm_notes | ~55 | Internal CSM risk flags, escalations, meeting notes, check-ins |

### Agent Self-Improvement Loop
After every answer, the agent suggests a specific dbt model or semantic YAML change to make the discovered insight permanent. This turns every conversation into a blueprint for a better data model. The analytics engineer reviews and approves the suggestion — the human stays in the loop, but the agent accelerates the iteration cycle.

## Derived Columns in the Mart

### health_category
Added as a CASE WHEN derivation in MARTS.MART_ACCOUNT_HEALTH so Lab 2's semantic model has a clean dimension:
- **at_risk**: competitor_mentioned OR avg_sentiment < -0.3
- **expansion**: expansion_signal AND usage_trend > 5%
- **healthy**: avg_sentiment >= -0.1 AND usage_trend >= -5%
- **attention**: everything else (mixed signals)

## Key Metrics the Agent Should Compute
- **Account Health Score**: composite of usage trend + support sentiment + Gong signals
- **Usage Trend**: WoW change in active users / events per account
- **Support Sentiment**: avg sentiment of recent tickets
- **Gong Signals**: classified themes from recent calls
- **Days Since Last Login**: per account
- **Seat Utilization**: active users / licensed seats
