"""Create the workshop Google Slides presentation."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.auth import authenticate
from googleapiclient.discovery import build

creds = authenticate()
slides = build("slides", "v1", credentials=creds)

# ── Create or reuse presentation ─────────────────────────────────────
EXISTING_ID = "1DtOEiU0c8V6wnDLM9GUAWatVAmb2Jxq0dQd2XHpZU9I"
try:
    pres = slides.presentations().get(presentationId=EXISTING_ID).execute()
    pres_id = EXISTING_ID
    print(f"Reusing: https://docs.google.com/presentation/d/{pres_id}/edit")
except Exception:
    pres = slides.presentations().create(
        body={"title": "The Data Layer Is the Last Mile"}
    ).execute()
    pres_id = pres["presentationId"]
    print(f"Created: https://docs.google.com/presentation/d/{pres_id}/edit")

# Delete any existing slides beyond the first
existing_slides = pres.get("slides", [])
if len(existing_slides) > 1:
    del_reqs = [{"deleteObject": {"objectId": s["objectId"]}} for s in existing_slides[1:]]
    slides.presentations().batchUpdate(presentationId=pres_id, body={"requests": del_reqs}).execute()

default_slide = pres["slides"][0]
title_ph = subtitle_ph = None
for el in default_slide.get("pageElements", []):
    ph = el.get("shape", {}).get("placeholder", {})
    if ph.get("type") in ("CENTERED_TITLE", "TITLE"):
        title_ph = el["objectId"]
    elif ph.get("type") == "SUBTITLE":
        subtitle_ph = el["objectId"]

# ── Slide content ────────────────────────────────────────────────────
SLIDES = [
    {
        "title": "The Most Interesting Thing\nHappening in Data Right Now",
        "body": "\n".join([
            "Business users have questions that span multiple data sources",
            "AI agents can now reason across all of them — and give actionable answers",
            "But the agent only works if the data layer underneath is trusted",
            "",
            "The agent is the interface.",
            "Your data layer is what makes it intelligent.",
        ]),
    },
    {
        "title": "Why One Person Can Build This Now",
        "body": "\n".join([
            '"I haven\'t written a line of code in months"',
            "— Boris Cherny, built Claude Code at Anthropic",
            "",
            "Coding agents collapsed the build time",
            "What took a team and a quarter → one person, one afternoon",
            "",
            "The bottleneck moved: building → knowing what to build",
            "Which metrics matter. What 'at risk' means.",
            "How to model 10 messy sources into one trusted table.",
            "That's your expertise.",
        ]),
    },
    {
        "title": "What's Changing for You",
        "body": "\n".join([
            "Before: Write SQL → hand off a dashboard",
            "Now: Write SQL → build the agent → ship the product",
            "",
            'Before: "Here\'s the data"',
            'Now: "Here\'s the intelligence product — ask it anything"',
            "",
            "Before: Bottlenecked by eng for deployment",
            "Now: Deploy yourself. No frontend code. No waiting.",
            "",
            "Same core skills. Massively expanded scope.",
        ]),
    },
    {
        "title": "What We're Building Today",
        "body": "\n".join([
            "DigitalNativeCo — B2B SaaS: Canvas, Flow, Insight",
            "20 accounts · $3.5M ARR · 10 data sources",
            "",
            'The CRO\'s question: "What can I do to increase NRR by 10%?"',
            "",
            "Lab 1 (25 min): Understand the Business",
            "    AI-enrich 10 sources → one account health mart",
            "",
            "Lab 2 (25 min): Build the Brain",
            "    Semantic model + search services + Cortex Agent",
            "",
            "Lab 3 (25 min): Ship the Product",
            "    Configure, use, and share via Snowflake Intelligence",
            "",
            "One person. Three labs. 90 minutes.",
        ]),
    },
    {
        "title": "What You Just Did",
        "body": "\n".join([
            "Pipeline → Semantic Layer → Agent → Product",
            "",
            "Lab 1: AI-enriched 10 data sources into one trusted mart",
            "Lab 2: Semantic model + search services + agent",
            "         that discovers insights you didn't ask about",
            "Lab 3: Shipped it — your neighbor used it immediately",
            "",
            "One person. Ten data sources. 90 minutes.",
        ]),
    },
    {
        "title": "What To Do Monday",
        "body": "\n".join([
            "1. Pick one question your team asks every week",
            "   → build the product that answers it",
            "",
            '2. Frame your work as products, not outputs',
            '   "I own Account Health Intelligence"',
            '   not "I maintain the accounts table"',
            "",
            "3. Your semantic layer is what makes agents useful",
            "   Without it: hallucination. With it: intelligence product.",
        ]),
    },
    {
        "title": "The Opportunity",
        "body": "\n".join([
            "Every agent that goes into production",
            "needs a data layer underneath it —",
            "modeled, tested, trusted.",
            "",
            "You build that layer.",
            "And now you build the product on top of it.",
            "",
            "Go build it.",
        ]),
    },
    {
        "title": "Resources",
        "body": "\n".join([
            "Podcasts:",
            "  Boris Cherny — What happens after coding is solved",
            "  Sherwin Wu — Engineers are becoming sorcerers",
            "  Jeanne DeWitt — World-class GTM in 2026",
            "",
            "Reads:",
            "  Tomasz Tunguz — 12 Predictions for 2026",
            "  Anthropic — How AI Is Transforming Work",
            "",
            "Docs: Cortex Code · Cortex Agents · Snowflake Intelligence",
            "",
            "The DigitalNativeCo data is yours to keep.",
        ]),
    },
]

# ── Build requests ───────────────────────────────────────────────────
reqs = []

# Title slide text
if title_ph:
    reqs.append({"insertText": {"objectId": title_ph, "text": "The Data Layer Is the Last Mile"}})
if subtitle_ph:
    reqs.append({"insertText": {"objectId": subtitle_ph, "text": "How analytics engineers build the products AI agents run on"}})

# Content slides
for i, s in enumerate(SLIDES):
    sid, tid, bid = f"slide{i}", f"title{i}", f"body_{i}"
    reqs.append({
        "createSlide": {
            "objectId": sid,
            "insertionIndex": i + 1,
            "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
            "placeholderIdMappings": [
                {"layoutPlaceholder": {"type": "TITLE", "index": 0}, "objectId": tid},
                {"layoutPlaceholder": {"type": "BODY", "index": 0}, "objectId": bid},
            ],
        }
    })
    reqs.append({"insertText": {"objectId": tid, "text": s["title"]}})
    reqs.append({"insertText": {"objectId": bid, "text": s["body"]}})

# Execute
slides.presentations().batchUpdate(
    presentationId=pres_id, body={"requests": reqs}
).execute()

url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
print(f"Done! Open: {url}")
