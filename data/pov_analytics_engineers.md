# The Data Layer Is the Last Mile — Why Analytics Engineers Are More Valuable, Not Less

**Audience:** Room full of analytics engineers, some shaken by Block's 40% layoff
**Goal:** Reframe the narrative from "AI is coming for your job" to "you're sitting on the most valuable seat in the building"
**Tone:** Confident, grounded, backed by receipts

---

## The Fear (name it)

Block just cut 4,000 people — 40% of the company. Dorsey said the quiet part loud: AI replaces roles, not just tasks. You've seen the headlines. Boris Cherny, the guy who built Claude Code, says he hasn't written a line of code in months. Roon at OpenAI says the same. "Software engineer" as a title is disappearing. Sal Khan says everyone's a "builder" now.

So what happens to *you*?

---

## The Reframe

Here's what nobody in the AI discourse is talking about: **every agent that replaces a human creates 10x the data footprint that human ever did.**

### Tailwind Facts — Data Is Exploding *Because* of Agents

- **Tomasz Tunguz (2026 Predictions):** "Agents issue at least an order of magnitude more queries to databases and data lakes than people ever have." That's not a projection — it's happening now. Agent data access patterns are *breaking* existing databases.

- **Parag Agrawal (Parallel Web Systems, ex-Twitter CEO):** AI agents will consume the web "several orders of magnitude more than humans ever have." His company is already processing millions of agent queries per day — and they just raised $100M at a $740M valuation to scale the infrastructure.

- **Google Gemini API:** 85 billion requests in Jan 2026, up from 35 billion ten months earlier. 142% growth in under a year. And that's *one* model.

- **Gartner:** 40% of enterprise applications will embed AI agents by end of 2026, up from <5% in 2025. Every one of those agents reads data, writes data, and creates logs, traces, and artifacts that need to be governed.

- **Sherwin Wu (OpenAI):** Engineers on the API platform manage fleets of 10-20 parallel agents. Each agent makes API calls, writes to databases, generates artifacts. Multiply that across every engineer at every company.

**The punchline:** The human-to-data ratio is collapsing. One person used to generate a few queries a day. Now one person orchestrating agents generates thousands. Someone has to make sense of that. Someone has to govern it, model it, serve it, and make it trustworthy.

That someone is you.

---

## Why Analytics Engineers Specifically

### 1. You're closest to discernment

Every AI agent, every coding assistant, every autonomous workflow — they all need to make decisions. Decisions require data. But not just *any* data. They need data that's been modeled, tested, documented, and trusted.

You're the people who build the semantic layer. You're the people who know that `revenue` means something different in finance vs. product vs. sales. You're the people who decide what's a metric vs. what's noise.

In a world of agents, **the person who controls the data contract controls the outcome.** That's you.

### 2. You can now build the whole thing

Here's the part that should excite you: the same AI that scared you is your superpower.

Don't sell Claude Code. **Sell what Claude Code makes you capable of.**

Before: You wrote dbt models and handed a dashboard to a PM who decided what to do with it. Your value ended at the chart.

Now: You can write the dbt model, spin up a Streamlit app on top of it, build an alert system, create an agent that acts on the data — all yourself. You're not just the data layer anymore. You're the **full-stack data product builder.**

The Jeanne DeWitt framework applies here: don't sell the tool, sell the superpower the tool gives you. You're not "an analytics engineer who uses AI." You're "the person who can go from business question to production data product in a day."

### 3. The role convergence benefits you most

Boris Cherny says "software engineer" as a title is going away. Jenny Wen says the design process is dead. Marc Andreessen calls the PM/eng/design convergence a "Mexican standoff" — everyone thinks they can do the others' jobs.

Here's the thing: in a standoff, **the person with the best information wins.**

- Engineers can now PM, but they don't know which metric matters
- PMs can now code, but they don't know where the data lives
- Designers can now ship, but they don't know what users actually do

You know all of it. You sit at the intersection of business logic, data infrastructure, and user behavior. You've been translating between technical and business languages your entire career.

The convergence of roles isn't a threat to you. **It's the market finally catching up to what you've been doing.**

---

## The New Stack for the Analytics Engineer-Builder

| Before | Now |
|---|---|
| Write SQL/dbt → hand off dashboard | Write SQL/dbt → build the app → deploy |
| "Here's the data" | "Here's the data product" |
| Serve stakeholders | Serve users |
| Cost center | Revenue enabler |
| Bottlenecked by eng for deployment | Deploy yourself with Claude Code |
| One domain (data) | Three domains (data + product + app) |

---

## What to Do Monday Morning

1. **Pick one dashboard that should be an app.** Use Claude Code to turn it into a Streamlit/Next.js app. Ship it. Show your team what "analytics engineer as builder" looks like.

2. **Pick one manual workflow your stakeholders do with your data.** Build an agent that does it. You know the data better than anyone — you're the best person to build the agent.

3. **Start framing your work as products, not outputs.** You don't "maintain the revenue model." You "own the revenue intelligence product." Language matters.

4. **Learn prompt engineering for agents, not just for chat.** The difference between a good agent and a hallucinating mess is the data contract underneath it. That's your expertise.

---

## Closing: The Tailwind Is Real

The world doesn't need fewer data people. It needs *different* data people. People who can:
- Model data AND build apps on top of it
- Write a dbt test AND write the business case for why it matters
- Govern an agent's data access AND design the workflow the agent executes

Block cut 40% of its workforce. But Parallel Web Systems just raised $100M because agents need data infrastructure at orders of magnitude beyond what humans required. Lovable hit $200M ARR in one year because builders (not specialists) are winning. Anthropic's engineers are 200% more productive because they orchestrate, not implement.

The tide isn't going out on data. **It's a tsunami coming in.** And you're the surfers who already know how to read the waves.

---

## Source Episodes to Watch

### Must-watch (directly supports the pitch)
1. **Boris Cherny** — "What happens after coding is solved" — [YouTube](https://youtu.be/We7BZVKbCVw)
2. **Sherwin Wu** — "Engineers are becoming sorcerers" — [YouTube](https://youtu.be/B26CwKm5C1k)
3. **Jenny Wen** — "The design process is dead" — [YouTube](https://youtu.be/eh8bcBIAAFo)
4. **Lazar Jovanovic** — "The rise of the professional vibe coder" — [YouTube](https://youtu.be/0XNkUdzxiZI)
5. **Jeanne DeWitt Grosser** — "What world-class GTM looks like in 2026" — [YouTube](https://youtu.be/RmnWHz8HD74)

### Strong supporting context
6. **Oji & Ezinne Udezue** — "How AI is reshaping the product role" — [Spotify](https://open.spotify.com/episode/4Z7LwOwqKtaA1jQ6JXaVYb)
7. **Alexander Embiricos** — "A full software engineering teammate" (OpenAI Codex) — [YouTube](https://youtu.be/xeZDHGjG5zM)
8. **Marc Andreessen** — "The real AI boom hasn't started yet" (Lenny's)
9. **Elena Verna** — "The new AI growth playbook for 2026" (Lovable $200M ARR) — [Spotify](https://open.spotify.com/episode/2tjRRxdTXpTl2vki4HTczP)

### Data-specific
10. **Data Engineering Podcast** — "The Future of Data Engineering: AI, LLMs, and Automation" — [Episode](https://www.dataengineeringpodcast.com/episodepage/the-future-of-data-engineering-ai-llms-and-automation)
11. **Zach Wilson** — "The 2026 AI Data Engineer Roadmap" — [Blog](https://blog.dataexpert.io/p/the-2026-ai-data-engineer-roadmap)

### Key articles (not podcasts but essential)
12. **Anthropic Research** — "How AI Is Transforming Work at Anthropic" — [Link](https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic)
13. **SF Standard** — "'Engineer' is so 2025. In AI land, everyone's a 'builder' now" — [Link](https://sfstandard.com/2026/03/05/engineer-2025-ai-land-everyone-s-builder-now/)
14. **Tomasz Tunguz** — "12 Predictions for 2026" (agents 10x database queries) — [Link](https://tomtunguz.com/2026-predictions/)
15. **Fortune** — "Top engineers at Anthropic, OpenAI say AI now writes 100% of their code" — [Link](https://fortune.com/2026/01/29/100-percent-of-code-at-anthropic-and-openai-is-now-ai-written-boris-cherny-roon/)
