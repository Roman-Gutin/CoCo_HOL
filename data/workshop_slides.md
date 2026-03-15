# The Data Layer Is the Last Mile — Slide Deck Script

**Duration:** 15 min opening + 15 min closing
**Presenter:** Roman
**Audience:** Analytics engineers ready to build with AI

---

## OPENING (15 minutes)

The opening has four beats: welcome, what's interesting, why now, what we're building.

---

### Slide 1 — Title + Welcome

**On screen:**
- "The Data Layer Is the Last Mile"
- Your name, title, company
- Wi-Fi / setup instructions in small text at bottom

**Speaker notes:**
"Thank you for being here. I'm Roman — [brief intro: who you are, what you do, why you care about this topic]. Before we start, quick show of hands — how many of you have built something with an AI agent? How many have built something with Cortex Code? Great. By the end of today, everyone's hand goes up."

*Keep this warm. Make eye contact. You're a person, not a pitch deck.*

---

### Slide 2 — The Most Interesting Thing Happening in Data Right Now

**On screen:**
- A simple diagram:
  - Left: **Business user** asks a question in English
  - Center: **AI agent** reasons across structured data + unstructured text
  - Right: **Trusted data layer** (your semantic model, your mart, your search indexes)
  - Arrow from right to center: "Without this, the agent hallucinates"
- Tagline: *"Trusted agents that serve business users. That's the new product category."*

**Speaker notes:**
"Here's what I think is the most interesting thing happening in data right now. We're building agents that business users can actually talk to — not chatbots that parrot back documentation, but agents that reason across real company data and give answers with dollar amounts, named accounts, and specific actions. The CRO asks 'how do I increase NRR by 10%?' and the agent pulls from product usage, support tickets, sales calls, and internal notes to give her a real answer. That's a new kind of product. And the thing that makes it work — the thing that separates a useful agent from a hallucinating one — is the data layer underneath it. The semantic model. The enriched mart. The search indexes over unstructured data. That's what you build."

---

### Slide 3 — Why This Is Possible Now

**On screen:**
- Boris Cherny (built Claude Code): *"I haven't written a line of code in months"*
- He doesn't mean coding is dead — he means **coding agents build for him**
- What used to take a team of 5 and a quarter now takes one person and an afternoon:
  - Data pipeline with AI enrichment → **Cortex Code writes the SQL**
  - Semantic model + agent → **one YAML file + one CREATE statement**
  - Production app → **Snowflake Intelligence, zero frontend code**
- *"The bottleneck isn't building anymore. It's knowing what to build."*

**Speaker notes:**
"Boris Cherny built Claude Code at Anthropic. When he says he doesn't write code anymore, he doesn't mean coding is dead — he means coding agents build for him. And that changes everything about scope. What used to require a data engineer, an ML engineer, a frontend developer, and a quarter of roadmap... you can now do in an afternoon. Cortex Code writes the SQL. You review it. You write a 50-line YAML file that teaches the agent your business logic. You deploy it to Snowflake Intelligence and hand it to a business user. One person, one afternoon. The bottleneck isn't building anymore. The bottleneck is knowing what to build — which metrics matter, what 'at risk' actually means, how to model ten messy sources into one trusted table. That's your expertise. And now you have the tools to turn that expertise into a shipped product."

---

### Slide 4 — What's Changing for You

**On screen:**

| Before | Now |
|---|---|
| Write SQL → hand off dashboard | Write SQL → build the agent → ship the product |
| "Here's the data" | "Here's the intelligence product" |
| Serve stakeholders | Serve users directly |
| Bottlenecked by eng for deployment | Deploy yourself |
| One domain (data) | Three domains (data + agent + product) |

- Jeanne DeWitt (Vercel COO, ex-Stripe): *"Sell the transformation, not the feature"*
- ~~"An analytics engineer who uses AI"~~
- **"The person who can go from business question to production intelligence product in a day"**

**Speaker notes:**
"This is the shift. You're not handing off a dashboard and hoping someone acts on it. You're building the product that answers the question directly. Same core skills — modeling data, defining business logic, making it trustworthy — but now you take it all the way to the user. Jeanne DeWitt at Vercel talks about selling the transformation, not the feature. Nobody cares that you use Cortex Code. They care that the CRO can ask a question in English and get a data-backed answer before her next meeting."

---

### Slide 5 — What We're Building Today

**On screen:**
- **The use case: Account Health Intelligence**
- **DigitalNativeCo** — B2B SaaS: Canvas (design), Flow (workflow), Insight (analytics)
- 20 accounts, 10 data sources, $3.5M ARR
- **The CRO's question:** *"What can I do to increase NRR by 10%?"*
- Three labs:
  - **Lab 1 (25 min):** Understand the business — AI-enrich 10 data sources into one account health mart
  - **Lab 2 (25 min):** Build the brain — semantic model + search services + Cortex Agent
  - **Lab 3 (25 min):** Ship the product — configure, use, and share via Snowflake Intelligence
- *"One person. Three labs. 90 minutes."*

**Visual suggestion:** Ten-source diagram flowing into "Account Health Intelligence" node, with the three labs as layers beneath it.

**Speaker notes:**
"Here's what we're building. DigitalNativeCo is a B2B SaaS company — creative tool, workflow automation, analytics. Think Adobe-shaped. They have 20 accounts and a CRO who wants to know how to increase NRR by 10%. The answer is buried across ten data sources that never talk to each other: product analytics, support tickets, Gong call transcripts, employee records, account assignments, pipeline, feature usage, invoices, and internal CSM notes. In Lab 1, you'll use Cortex Code to enrich all of that with AI and build a single mart. In Lab 2, you'll write a semantic model, connect search services, and deploy an agent that can reason across everything. In Lab 3, you'll ship it to the person sitting next to you — and they'll ask the CRO's question and get a real answer. One person. 90 minutes. Let's go."

**[TRANSITION TO LAB 1]**

---

## CLOSING (15 minutes)

---

### Slide 10 — What You Just Did

**On screen:**
- Lab 1: Built a pipeline that ingests 10 data sources — product events, support tickets, Gong transcripts, employee roster, account assignments, opportunities, feature usage, invoices, and CSM notes — and used AI to classify sentiment, extract churn signals, and flag expansion opportunities. In SQL.
- Lab 2: Built a Cortex Agent that can answer "Is Meridian Media at risk?" by reasoning across usage trends, feature adoption patterns, support ticket sentiment, Gong call themes, invoice/discount history, and internal CSM risk flags — powered by your semantic model. After every answer, the agent suggests a dbt model or semantic YAML change to make that insight permanent.
- Lab 3: Shipped a production intelligence product using Snowflake Intelligence — configured sample questions, response instructions, and visualization tools, then shared it with a colleague who used it immediately with zero setup. Saw a React dashboard demo showing what full custom control looks like.
- **"One person. Ten data sources. Three layers. 90 minutes."**

**Speaker notes:**
"Look at what's on your screen. You took ten disconnected data sources — product analytics, support tickets, sales call transcripts, employee records, account ownership history, renewal pipeline, feature-level adoption, billing data, and internal CSM notes — and built a complete intelligence product. The pipeline enriches the data. The agent reasons over it — and then suggests how to improve your data model so the next question is even easier to answer. The app serves it to users. A CS team at DigitalNativeCo could log in right now and see that Meridian Media is at risk because their champion left, usage cratered, the last Gong call mentioned SketchFlow, and the CSM flagged it as an escalation. Or that Atlas Digital is ready for a cross-sell because usage is up 15% month-over-month, feature adoption is accelerating, and they asked about Flow pricing on the last call. You built all of that. As one person. That's not 'analytics engineering.' That's full-stack data product building."

---

### Slide 11 — The New Analytics Engineer

**On screen:**
- You're not a cost center. You're a product builder.
- You don't serve stakeholders. You serve users.
- You don't hand off data. You ship data products.
- Today's proof: you built an Account Health Intelligence product that a CS team can use *right now*.

**Speaker notes:**
"The title might change. 'Analytics engineer' might become 'data product builder' or just 'builder.' But the core skill — understanding business logic, modeling data across messy sources, making it trustworthy — that's now the foundation everything else is built on. Agents, apps, intelligence products — they all start with your work. You just proved you can build the whole stack. That's the new job, and it's a bigger job than the old one."

---

### Slide 12 — What To Do Monday

**On screen:**
1. Pick one question your CS/sales/success team asks every week → build an agent that answers it by triangulating your data sources
2. Pick one dashboard that should be an app → ship it as a React or Streamlit app with a chat interface
3. Frame your work as products, not outputs — "I own Account Health Intelligence," not "I maintain the accounts table"
4. Learn agent orchestration — your semantic layer is the moat between useful agents and hallucinating ones

**Speaker notes:**
"Don't wait for permission. Don't wait for a hackathon. Monday morning, think about the question your success team asks every week — 'which accounts are at risk?' or 'who should we upsell?' You now know how to build the product that answers it. You proved to yourself today that you can take messy, multi-source data and turn it into an intelligence product. Now prove it to your org."

---

### Slide 13 — The Tailwind Is Real

**On screen:**
- "The tide isn't going out on data. It's a tsunami coming in."
- Agents 10x the data footprint → you build the infrastructure they run on
- Everyone's a builder → you're the builder who can triangulate product, support, and sales data into a single intelligence layer
- The question isn't whether data matters. It's how fast you can build the products that run on it.

**Speaker notes:**
"I'll leave you with this. Every agent that goes into production needs a data layer underneath it — modeled, tested, trusted. That's what you build. And now you can build the agent on top of it, and the product on top of that. You just proved it. The opportunity ahead is enormous: every team in every company is going to want what you built today. Go build it for them."

---

### Slide 14 — Resources

**On screen:**
- **Must-watch podcasts:**
  - Boris Cherny — "What happens after coding is solved" — youtu.be/We7BZVKbCVw
  - Sherwin Wu — "Engineers are becoming sorcerers" — youtu.be/B26CwKm5C1k
  - Jeanne DeWitt Grosser — "What world-class GTM looks like in 2026" — youtu.be/RmnWHz8HD74
- **Key reads:**
  - Tomasz Tunguz — "12 Predictions for 2026" — tomtunguz.com/2026-predictions/
  - Anthropic Research — "How AI Is Transforming Work" — anthropic.com/research/how-ai-is-transforming-work-at-anthropic
- **Docs:**
  - Cortex Code (Snowflake docs)
  - Cortex Agents (Snowflake docs)
  - React in Snowflake / Snowflake Native Apps (Snowflake docs)
- **This POV doc:** [share link with the room]

**Speaker notes:**
"I'm sharing the full POV doc and this resource list. The podcast episodes are the best way to internalize this shift. Watch Boris Cherny first — it'll reframe how you think about your role. And if you want to keep building on what we did today — the DigitalNativeCo data is yours to keep. Take the Account Health agent, plug in your own company's data, and show your team what's possible. Thanks for spending two hours with me. Now go build something."

**[Q&A — remaining time]**
