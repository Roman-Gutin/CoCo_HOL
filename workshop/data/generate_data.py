"""
Generate synthetic data for DigitalNativeCo workshop demo.

Outputs ten CSVs to workshop/data/seed/:
  - accounts.csv            (20 rows)
  - product_events.csv      (~5000 rows)
  - support_tickets.csv     (~500 rows)
  - gong_transcripts.csv    (~150 rows)
  - employees.csv           (20 rows)
  - account_assignments.csv (~44 rows)
  - opportunities.csv       (~21 rows)
  - feature_usage.csv       (~7800 rows)
  - invoices.csv            (~80 rows)
  - csm_notes.csv           (~55 rows)

Usage:
    python workshop/data/generate_data.py
"""

import csv
import os
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(SCRIPT_DIR, "seed")
os.makedirs(SEED_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------
START_DATE = datetime(2025, 12, 15)
END_DATE = datetime(2026, 3, 14)
NUM_DAYS = (END_DATE - START_DATE).days + 1  # 90 days

def random_date(start=START_DATE, end=END_DATE):
    return start + timedelta(days=random.randint(0, (end - start).days))

def date_str(dt):
    return dt.strftime("%Y-%m-%d")

def datetime_str(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def day_index(dt):
    """0-based index from START_DATE."""
    return (dt - START_DATE).days

# ---------------------------------------------------------------------------
# CSM names
# ---------------------------------------------------------------------------
CSM_NAMES = [
    "Sarah Chen", "Marcus Rivera", "Emily Thornton",
    "James Okafor", "Rachel Goldstein",
]

# ---------------------------------------------------------------------------
# Account definitions
# ---------------------------------------------------------------------------
# category: churn_risk | expansion | healthy | attention
ACCOUNTS = [
    # CHURN RISK
    dict(account_id="ACC-001", account_name="Meridian Media Group", industry="Media & Advertising",
         arr=186000, licensed_seats=45, products=["Canvas", "Flow"],
         contract_renewal_date="2026-06-15", csm="Sarah Chen", category="churn_risk",
         story="usage_crater"),
    dict(account_id="ACC-002", account_name="Cascade Financial", industry="Financial Services",
         arr=312000, licensed_seats=80, products=["Canvas", "Flow", "Insight"],
         contract_renewal_date=date_str(END_DATE + timedelta(days=48)), csm="Marcus Rivera", category="churn_risk",
         story="partial_adoption"),
    dict(account_id="ACC-003", account_name="Beacon Logistics", industry="Logistics & Supply Chain",
         arr=97000, licensed_seats=30, products=["Canvas", "Insight"],
         contract_renewal_date="2026-07-20", csm="Emily Thornton", category="churn_risk",
         story="sudden_cliff"),
    dict(account_id="ACC-004", account_name="Prism Retail", industry="Retail",
         arr=54000, licensed_seats=15, products=["Canvas"],
         contract_renewal_date=date_str(END_DATE + timedelta(days=27)), csm="James Okafor", category="churn_risk",
         story="silent_decline"),
    # EXPANSION
    dict(account_id="ACC-005", account_name="Atlas Digital", industry="Digital Marketing",
         arr=228000, licensed_seats=60, products=["Canvas"],
         contract_renewal_date="2026-09-30", csm="Rachel Goldstein", category="expansion",
         story="growing_fast"),
    dict(account_id="ACC-006", account_name="Summit Healthcare", industry="Healthcare",
         arr=145000, licensed_seats=40, products=["Canvas", "Flow"],
         contract_renewal_date="2026-11-15", csm="Sarah Chen", category="expansion",
         story="fast_ramp"),
    dict(account_id="ACC-007", account_name="Voyager Entertainment", industry="Entertainment",
         arr=480000, licensed_seats=120, products=["Canvas", "Flow", "Insight"],
         contract_renewal_date="2026-08-01", csm="Marcus Rivera", category="expansion",
         story="stable_high"),
    dict(account_id="ACC-008", account_name="Ironclad Manufacturing", industry="Manufacturing",
         arr=110000, licensed_seats=35, products=["Canvas"],
         contract_renewal_date="2026-10-20", csm="Emily Thornton", category="expansion",
         story="moderate_growth"),
    # HEALTHY
    dict(account_id="ACC-009", account_name="Northstar Consulting", industry="Management Consulting",
         arr=165000, licensed_seats=50, products=["Canvas", "Flow"],
         contract_renewal_date="2026-12-01", csm="James Okafor", category="healthy",
         story="steady"),
    dict(account_id="ACC-010", account_name="Ridgeline Media", industry="Media & Publishing",
         arr=138000, licensed_seats=42, products=["Flow"],
         contract_renewal_date="2026-07-15", csm="Rachel Goldstein", category="healthy",
         story="steady"),
    dict(account_id="ACC-011", account_name="Clearwater Tech", industry="Technology",
         arr=275000, licensed_seats=70, products=["Canvas", "Flow", "Insight"],
         contract_renewal_date="2026-09-01", csm="Sarah Chen", category="healthy",
         story="steady"),
    dict(account_id="ACC-012", account_name="Horizon Pharma", industry="Pharmaceuticals",
         arr=198000, licensed_seats=55, products=["Canvas"],
         contract_renewal_date="2026-06-30", csm="Marcus Rivera", category="healthy",
         story="seasonal"),
    dict(account_id="ACC-013", account_name="Sterling Partners", industry="Private Equity",
         arr=62000, licensed_seats=18, products=["Canvas", "Insight"],
         contract_renewal_date="2026-08-15", csm="Emily Thornton", category="healthy",
         story="steady"),
    dict(account_id="ACC-014", account_name="Apex Marketing", industry="Marketing Agency",
         arr=124000, licensed_seats=38, products=["Canvas", "Flow"],
         contract_renewal_date="2026-11-01", csm="James Okafor", category="healthy",
         story="slow_growth"),
    # NEEDS ATTENTION
    dict(account_id="ACC-015", account_name="Cobalt Aerospace", industry="Aerospace & Defense",
         arr=210000, licensed_seats=55, products=["Canvas", "Flow", "Insight"],
         contract_renewal_date="2026-10-01", csm="Rachel Goldstein", category="attention",
         story="onboarding_stalled"),
    dict(account_id="ACC-016", account_name="Driftwood Media", industry="Media & Entertainment",
         arr=88000, licensed_seats=25, products=["Canvas", "Flow"],
         contract_renewal_date="2026-07-01", csm="Sarah Chen", category="attention",
         story="admin_change"),
    dict(account_id="ACC-017", account_name="Evergreen Education", industry="Education",
         arr=73000, licensed_seats=22, products=["Canvas", "Insight"],
         contract_renewal_date="2026-05-15", csm="Marcus Rivera", category="attention",
         story="budget_pressure"),
    dict(account_id="ACC-018", account_name="Flux Dynamics", industry="Engineering Services",
         arr=156000, licensed_seats=48, products=["Canvas", "Flow", "Insight"],
         contract_renewal_date="2026-09-15", csm="Emily Thornton", category="attention",
         story="rate_limits"),
]

# Pad to 20 with 2 more healthy accounts
ACCOUNTS.extend([
    dict(account_id="ACC-019", account_name="Pinnacle Sports", industry="Sports & Recreation",
         arr=92000, licensed_seats=28, products=["Canvas", "Flow"],
         contract_renewal_date="2026-08-30", csm="James Okafor", category="healthy",
         story="steady"),
    dict(account_id="ACC-020", account_name="Crestline Analytics", industry="Data & Analytics",
         arr=172000, licensed_seats=46, products=["Flow", "Insight"],
         contract_renewal_date="2026-10-15", csm="Rachel Goldstein", category="healthy",
         story="steady"),
])

# ---------------------------------------------------------------------------
# User ID pools per account
# ---------------------------------------------------------------------------
def build_user_pool(account):
    seats = account["licensed_seats"]
    aid = account["account_id"]
    return [f"{aid}-U{str(i+1).zfill(3)}" for i in range(seats)]

USER_POOLS = {a["account_id"]: build_user_pool(a) for a in ACCOUNTS}

# ---------------------------------------------------------------------------
# Usage multiplier curves  (index 0 = day 0 = Dec 15; index 89 = Mar 14)
# Returns a multiplier 0..N for a given day index.
# ---------------------------------------------------------------------------
def _linear(start, end, n=NUM_DAYS):
    return [start + (end - start) * i / (n - 1) for i in range(n)]

def _cliff(normal, cliff_day, post_cliff):
    """Normal level until cliff_day, then drops."""
    return [normal if i < cliff_day else post_cliff for i in range(NUM_DAYS)]

def usage_curve(story):
    if story == "usage_crater":
        # High first 30 days, then cratering over 8 weeks
        return [1.0 if i < 30 else max(0.08, 1.0 - (i - 30) * 0.015) for i in range(NUM_DAYS)]
    elif story == "partial_adoption":
        # Low overall, mostly Flow; Canvas/Insight very low
        return _linear(0.4, 0.3)
    elif story == "sudden_cliff":
        return _cliff(0.8, NUM_DAYS - 21, 0.12)
    elif story == "silent_decline":
        return _linear(0.5, 0.15)
    elif story == "growing_fast":
        # 15% MoM => roughly 0.5% per day compound
        return [0.6 * (1.005 ** i) for i in range(NUM_DAYS)]
    elif story == "fast_ramp":
        return _linear(0.15, 0.95)
    elif story == "stable_high":
        return [random.uniform(0.85, 1.0) for _ in range(NUM_DAYS)]
    elif story == "moderate_growth":
        return _linear(0.5, 0.75)
    elif story == "steady":
        return [random.uniform(0.55, 0.75) for _ in range(NUM_DAYS)]
    elif story == "seasonal":
        # Spike around Jan (campaign season)
        return [0.6 + 0.3 * max(0, 1 - abs(i - 45) / 30) for i in range(NUM_DAYS)]
    elif story == "slow_growth":
        return _linear(0.55, 0.68)
    elif story == "onboarding_stalled":
        return [0.15 + 0.05 * random.random() for _ in range(NUM_DAYS)]
    elif story == "admin_change":
        # Dip around day 50, recover
        return [0.65 if i < 45 else (0.3 if i < 60 else 0.55) for i in range(NUM_DAYS)]
    elif story == "budget_pressure":
        return [random.uniform(0.55, 0.70) for _ in range(NUM_DAYS)]
    elif story == "rate_limits":
        return [random.uniform(0.75, 0.95) for _ in range(NUM_DAYS)]
    else:
        return [0.6] * NUM_DAYS

EVENT_TYPES = ["login", "feature_use", "export", "api_call", "invite_sent"]
EVENT_TYPE_WEIGHTS = [30, 35, 15, 15, 5]

# ---------------------------------------------------------------------------
# Product events generation
# ---------------------------------------------------------------------------
def generate_product_events():
    events = []
    eid = 1
    for acct in ACCOUNTS:
        curve = usage_curve(acct["story"])
        pool = USER_POOLS[acct["account_id"]]
        seats = acct["licensed_seats"]
        products = acct["products"]

        # Partial adoption: Cascade Financial mostly uses Flow
        product_weights = None
        if acct["story"] == "partial_adoption":
            product_weights = []
            for p in products:
                product_weights.append(1 if p == "Flow" else 0.08)

        # Base events per day at multiplier=1.0
        base_daily = max(2, int(seats * 0.15))

        for d in range(NUM_DAYS):
            dt = START_DATE + timedelta(days=d)
            # Weekend damping
            weekend = dt.weekday() >= 5
            mult = curve[d] * (0.25 if weekend else 1.0)
            n_events = max(0, int(base_daily * mult + random.gauss(0, 1)))

            # Choose active users for the day (subset)
            active_pct = min(1.0, mult * 0.7 + 0.05)
            n_active = max(1, int(len(pool) * active_pct))
            active_users = random.sample(pool, min(n_active, len(pool)))

            for _ in range(n_events):
                user = random.choice(active_users)
                if product_weights:
                    product = random.choices(products, weights=product_weights, k=1)[0]
                else:
                    product = random.choice(products)
                etype = random.choices(EVENT_TYPES, weights=EVENT_TYPE_WEIGHTS, k=1)[0]
                # Session duration varies by event type
                if etype == "login":
                    dur = round(random.uniform(1, 45), 1)
                elif etype == "feature_use":
                    dur = round(random.uniform(3, 60), 1)
                elif etype == "export":
                    dur = round(random.uniform(1, 10), 1)
                elif etype == "api_call":
                    dur = round(random.uniform(0.1, 2), 1)
                else:
                    dur = round(random.uniform(0.5, 5), 1)

                hour = random.choices(range(6, 22), weights=[1,2,4,8,10,10,9,8,7,8,9,8,6,4,2,1], k=1)[0]
                minute = random.randint(0, 59)
                event_dt = dt.replace(hour=hour, minute=minute)

                events.append({
                    "event_id": f"EVT-{eid:06d}",
                    "account_id": acct["account_id"],
                    "account_name": acct["account_name"],
                    "user_id": user,
                    "product": product,
                    "event_type": etype,
                    "event_date": datetime_str(event_dt),
                    "session_duration_min": dur,
                })
                eid += 1
    return events


# ---------------------------------------------------------------------------
# Support ticket text templates — MANY per category for variety
# ---------------------------------------------------------------------------

CHURN_RISK_TICKETS_MERIDIAN = [
    ("Canvas", "P2", "Our design team is really struggling with the new Canvas interface. The toolbar layout changed and nobody can find the asset library anymore. We've lost at least two days of productivity this week. Can someone walk us through this?"),
    ("Canvas", "P1", "This is the third time this month Canvas has frozen mid-export. We had a client deadline today and had to recreate everything in SketchFlow. This is unacceptable for what we're paying."),
    ("Canvas", "P2", "We need to export our entire asset library out of Canvas ASAP. Our creative director wants everything in a portable format. Can you provide a bulk export tool or API endpoint?"),
    ("Flow", "P2", "Our team lead Jennifer left last month and she was the only one who understood how our Flow automations were set up. Nobody knows how to modify the approval chains. Is there documentation for inheriting admin workflows?"),
    ("Canvas", "P1", "Canvas performance has degraded badly. Pages with more than 20 layers take 10+ seconds to render. We're a media company — we work with complex layouts daily. Several team members are asking if we can switch to SketchFlow."),
    ("Canvas", "P3", "Is there a way to migrate our Canvas templates to another platform? Asking for planning purposes. We need to understand what our options are before our next internal review."),
    ("Flow", "P2", "The Flow integration with our DAM system broke after your last update. Our creative workflow depends on this. We've been manually transferring files for two weeks and it's killing our velocity."),
    ("Canvas", "P2", "Honestly, I'm frustrated. We've filed three tickets this month and the responses have been slow and unhelpful. Our contract is up in June and leadership is already questioning whether to renew."),
    ("Canvas", "P2", "We've been trying to reach our account executive Jake Torres for three weeks about renewal pricing. His emails are bouncing and he's not responding on Slack. Is he still with the company? We need to discuss pricing options before our budget review."),
    ("Canvas", "P1", "URGENT: Our VP of Marketing David Leung has requested a full asset export from Canvas. He wants to evaluate migration costs to SketchFlow. We need the bulk export API documentation and estimated data transfer timelines. We are a $186K account and haven't had a working AE relationship in weeks."),
    ("Flow", "P2", "We tested our approval workflow in both Canvas and SketchFlow last week. What takes 45 minutes in Canvas took 5 minutes in SketchFlow. The performance gap is becoming impossible to justify internally. Our SketchFlow pilot cost us $2K — our Canvas contract is $186K. The ROI math is not in your favor."),
]

CHURN_RISK_TICKETS_CASCADE = [
    ("Canvas", "P2", "We purchased Canvas six months ago but adoption is still near zero. The onboarding materials don't match our version and the team found it confusing. Can we get a dedicated training session?"),
    ("Canvas", "P3", "Our team has tried Canvas three times now and keeps going back to their old tools. The learning curve is too steep for what we need. Is there a simplified mode or a quick-start guide for financial services use cases?"),
    ("Insight", "P2", "Insight dashboards are not loading for half our team. We get a spinner that never resolves. This has been happening intermittently for weeks. We're paying for a product nobody can use."),
    ("Insight", "P3", "The Insight data connectors don't support our core data warehouse (Teradata). Without this, the product is essentially useless to us. Are there plans to add Teradata support?"),
    ("Canvas", "P2", "We were told Canvas would integrate with our compliance review system during the sales process. Six months in, this integration doesn't exist. Our legal team is asking why we're paying for shelfware."),
    ("Flow", "P3", "Flow works fine for our team but we're only using maybe 30% of what we're paying for. Is there a way to downgrade our plan to match our actual usage?"),
    ("Canvas", "P1", "Multiple users are locked out of Canvas after the last SSO update. Our IT team says the SAML configuration changed on your end without notice. This is affecting our entire New York office."),
    ("Insight", "P2", "We need to understand our actual ROI on Insight. Can you pull usage stats for our account? Our CFO is reviewing all SaaS spend and tools with low adoption are first on the chopping block."),
]

CHURN_RISK_TICKETS_BEACON = [
    ("Insight", "P1", "URGENT: The Insight API has been returning 500 errors for the past 4 hours. Our logistics dashboard is completely down. This feeds real-time data to our dispatch team. Hundreds of shipments are affected."),
    ("Insight", "P1", "The API outage from yesterday is happening again. We were told it was resolved but we're seeing the same 500 errors. Our ops team is furious. We need a root cause analysis immediately."),
    ("Canvas", "P1", "API calls to Canvas are timing out consistently since last Tuesday. Our automated report generation pipeline depends on this. We're manually generating reports for 30+ clients right now."),
    ("Insight", "P1", "Third major API outage in three weeks. We signed up for 99.9% uptime SLA and we're nowhere close. Our VP of Operations wants to discuss SLA credits and is cc'ing our legal team."),
    ("Insight", "P2", "Following up on the API reliability issues. We've calculated approximately 47 hours of cumulative downtime this month. Per our contract, we believe we're owed significant SLA credits. Please escalate."),
    ("Canvas", "P2", "After the recent API issues, our engineering team doesn't trust the platform stability. They're building redundancy around your APIs which is costing us engineering time. Can we get on a call about your infrastructure roadmap?"),
    ("Insight", "P1", "I was told Jake Torres was our account executive but apparently he left the company? We now have Kevin McBride who seems very junior and doesn't know our architecture. The API outages cost us approximately $12K in operational overhead and we still haven't received the SLA credit calculation. Who is actually owning this account?"),
    ("Insight", "P2", "Escalation request: Our VP of Operations wants to speak with your VP of Sales about the ongoing API reliability issues AND the account management transition. We've had 3 major outages and 2 AE changes in 3 months. This is not enterprise-grade service for a company paying $97K annually."),
]

CHURN_RISK_TICKETS_PRISM = [
    # Silent churn — very few tickets
    ("Canvas", "P4", "Minor UI issue — the color picker dropdown clips on smaller screens. Not urgent."),
    ("Canvas", "P3", "How do we update our billing contact? The admin who set this up left the company."),
]

EXPANSION_TICKETS_ATLAS = [
    ("Canvas", "P3", "Feature request: Can Canvas support real-time co-editing like Google Docs? Our team of 12 designers frequently needs to collaborate simultaneously on campaign assets."),
    ("Canvas", "P3", "We'd love to see a version history feature with branching — similar to Git but for design files. Our team is growing and we need better collaboration controls."),
    ("Canvas", "P4", "Suggestion: It would be great if Canvas had native Pantone color library support. We do a lot of print work and need precise color matching."),
    ("Canvas", "P3", "Is there an API endpoint to programmatically create Canvas projects? We want to auto-generate templated designs for our 200+ SMB clients."),
    ("Canvas", "P4", "Love the new batch export feature! One suggestion — could you add PDF/X-4 as an export format? It's the standard our print vendors require."),
    ("Canvas", "P3", "Feature request: Can we get an integration with Brandwatch or Sprout Social? We want to publish directly from Canvas to social media. Would save our team hours every week."),
    ("Canvas", "P4", "Small UX suggestion: the keyboard shortcut for 'group layers' conflicts with our OS shortcut. Any way to customize keyboard bindings?"),
]

EXPANSION_TICKETS_SUMMIT = [
    ("Canvas", "P3", "Quick question — how do we set up role-based access so our compliance team can view but not edit designs? We're rolling this out to our regulatory affairs department next week."),
    ("Flow", "P3", "How do we configure Flow to route approvals based on document type? We need clinical materials to go through a different review chain than marketing collateral."),
    ("Canvas", "P4", "Is there a way to create a shared template library that all departments can access? We have 6 teams now and want to standardize our visual identity."),
    ("Flow", "P3", "We're onboarding 15 new users next week. Is there a bulk invite feature or should we do them one by one? Also, can we pre-assign them to specific workspaces?"),
    ("Canvas", "P3", "Can Canvas handle HIPAA-compliant document workflows? We want to use it for patient-facing materials but need to ensure PHI is protected."),
    ("Flow", "P4", "Our team lead wants to know if Flow can integrate with Epic (our EHR system) for automated report distribution. Even a webhook would work."),
    ("Canvas", "P3", "How do we set up an approval workflow where the legal team has final sign-off on all external-facing materials? This is a compliance requirement for us."),
]

EXPANSION_TICKETS_VOYAGER = [
    # Self-sufficient, very few tickets
    ("Flow", "P4", "Minor: The Flow webhook retry logic seems to cap at 3 attempts. Can this be configurable? We'd like 5 retries with exponential backoff for our media pipeline."),
]

EXPANSION_TICKETS_IRONCLAD = [
    ("Canvas", "P3", "Can Canvas generate automated spec sheets from our design templates? We're creating 50+ product spec documents a month and want to templatize the process."),
    ("Canvas", "P4", "Feature request: support for DXF or STEP file preview within Canvas. Our engineering team shares CAD drawings and it would be nice to preview them inline."),
    ("Canvas", "P3", "Our manufacturing team is asking about Insight. Can we get a demo? We want to track how often each product template is used and by which team."),
    ("Canvas", "P4", "Is there a plugin or extension marketplace for Canvas? We'd like to build a custom integration with our ERP system (SAP)."),
]

HEALTHY_TICKETS = [
    ("Canvas", "P3", "Minor rendering glitch on the Canvas dashboard when using Firefox. Text overlaps the sidebar on the project list page. Chrome works fine."),
    ("Flow", "P3", "One of our Flow automations stopped triggering after we changed our email domain. Looks like the email validation is too strict. Can you whitelist our new domain?"),
    ("Canvas", "P4", "Suggestion: Would be nice if Canvas remembered my last-used workspace when I log in instead of defaulting to the home screen every time."),
    ("Flow", "P2", "A Flow automation that was working fine for months suddenly started sending duplicate notifications. Nothing changed on our end. Can you check the trigger logic?"),
    ("Insight", "P3", "The Insight export to Excel is truncating column headers longer than 30 characters. Our report names are descriptive and this is causing confusion downstream."),
    ("Canvas", "P3", "Can we increase our storage quota? We're at 89% capacity and have a big campaign launching next month. We don't want to archive anything right now."),
    ("Flow", "P4", "Quick question — is there a way to add conditional branching in Flow based on file size? We want large assets to route to a different approval path."),
    ("Canvas", "P2", "Our SSO integration broke after an IdP certificate rotation on our side. Can you provide the steps to update the SAML certificate in Canvas? The docs are out of date."),
    ("Insight", "P3", "Dashboard loading times have gotten slower over the past month. Not critical but noticeable. We have about 18 months of historical data loaded."),
    ("Flow", "P3", "Is there a way to set up recurring scheduled exports in Flow? We manually trigger a weekly report export and would like to automate it."),
    ("Canvas", "P4", "Feature idea: dark mode for Canvas would be amazing. Our designers work late hours and the bright interface causes eye strain."),
    ("Insight", "P3", "The date range picker in Insight defaults to the current month. Can it remember the last-used date range? We almost always look at trailing 90 days."),
    ("Canvas", "P3", "We accidentally deleted a shared template folder. Is there an undo or recycle bin feature? We need to recover about 15 templates."),
    ("Flow", "P2", "Flow webhook deliveries to our Slack channel stopped working yesterday. The webhook URL hasn't changed. Can you check if there's an outage on your webhook service?"),
    ("Insight", "P4", "Minor: The Insight PDF export puts the footer text on top of the chart legend on page 3. Probably a layout calculation bug."),
    ("Canvas", "P3", "How do we configure Canvas to use our company fonts? We uploaded them to the asset library but they only show up for the admin account."),
    ("Flow", "P3", "Is it possible to trigger a Flow automation from an external webhook? We want Jira ticket creation to automatically spawn a Canvas project."),
    ("Canvas", "P4", "The image compression on Canvas export is a bit aggressive. Can we get a quality slider or a lossless export option for PNG?"),
    ("Insight", "P3", "We'd like to embed an Insight dashboard in our internal wiki (Confluence). Is there an iframe embed option or public link feature?"),
    ("Flow", "P4", "Small bug: when a Flow step fails, the error message just says 'Step failed.' No details. Would be helpful to see the actual error for debugging."),
]

ATTENTION_TICKETS_COBALT = [
    ("Canvas", "P2", "We're four weeks into onboarding and our team still can't figure out the workspace structure. The hierarchy of Organizations > Teams > Projects > Files is confusing. Can we get a walkthrough?"),
    ("Flow", "P2", "Our team tried to set up their first Flow automation and got lost immediately. The UI doesn't make it clear where to start. Three people gave up and went back to email approvals."),
    ("Insight", "P3", "We connected Insight to our data source but the dashboard is empty. No errors, just blank charts. We followed the setup guide step by step. What are we missing?"),
    ("Canvas", "P2", "The permissions model is very confusing. We have 55 licensed seats but only 8 people can access the shared workspace. The rest see 'You don't have access.' We've spent two hours on this."),
    ("Canvas", "P3", "Is there a getting-started video series? The documentation is very text-heavy and our team prefers visual learning. We're an aerospace engineering company, not a design agency — we need simpler onboarding."),
    ("Flow", "P3", "We can't figure out how to connect Flow to Canvas. The integration page lists dozens of connectors but the Canvas one says 'Coming soon.' Wasn't this supposed to be included?"),
    ("Insight", "P2", "Our Insight dashboards show data from a test environment we used during setup. How do we switch to production data? We can't find the data source settings anywhere."),
    ("Canvas", "P3", "Honest feedback: we bought three products and the onboarding experience has been rough. Each product has a different UI pattern and login flow. It doesn't feel like an integrated suite."),
]

ATTENTION_TICKETS_DRIFTWOOD = [
    ("Canvas", "P3", "Hi, I'm the new admin for our Canvas account. The previous admin (Mark Torres) left the company. How do I transfer ownership? I can't access the admin console."),
    ("Canvas", "P2", "Following up — I still can't access admin settings. Our team needs me to add 3 new users but I'm locked out of user management. This is blocking our project."),
    ("Flow", "P3", "Where do I find the API keys for our Flow integrations? Mark set these up and I don't know where they're stored. Our automated workflows are running but I can't modify them."),
    ("Canvas", "P3", "Basic question — how do we reset the SSO configuration? Mark set up SSO with our old identity provider and we've since switched to Okta."),
    ("Flow", "P3", "Is there a way to audit what automations are active on our account? I inherited this and have no idea what's running. I found one that sends emails to Mark's personal address."),
    ("Canvas", "P4", "Can you send me the onboarding documentation? I need to get up to speed on admin features. I'm essentially starting from scratch."),
    ("Canvas", "P3", "Also — I was told our account executive Diana is on leave and someone named Tom Westfield is covering. I've emailed Tom twice and haven't heard back. We need help with our SSO migration and there's no one to talk to. Feeling a bit abandoned here."),
]

ATTENTION_TICKETS_EVERGREEN = [
    ("Canvas", "P3", "We love Canvas and our teachers use it daily. However, we're a public school district and our budget is being cut by 15% next year. We need to understand our renewal pricing options."),
    ("Insight", "P3", "Is there an education discount or nonprofit pricing tier? We're evaluating whether we can keep Insight in our budget. The product is great but we have to make tough choices."),
    ("Canvas", "P3", "Can we reduce our seat count from 22 to 12 at renewal? Some departments are being consolidated and we won't need as many licenses. We want to keep using the product."),
    ("Canvas", "P4", "The new quiz template in Canvas is fantastic for our curriculum designers. Any chance you could add more education-specific templates? Would really help justify the cost internally."),
    ("Insight", "P3", "Our superintendent asked for a report on how much we actually use Insight. Can you pull our usage metrics for the past 6 months? We need ammunition to keep it in the budget."),
    ("Canvas", "P3", "Our AE Diana Osei was fantastic — she understood education pricing and always fought for us on renewals. We heard she's on leave and Tom Westfield is covering. No disrespect to Tom but he doesn't know our account. Our renewal is in May and nobody has started the conversation. We're a $73K account with budget pressure — we need proactive help, not radio silence."),
]

ATTENTION_TICKETS_FLUX = [
    ("Flow", "P1", "We're hitting API rate limits every day between 2-4 PM when our automated pipelines run. We're getting HTTP 429 errors and jobs are failing. We need the rate limit increased urgently."),
    ("Flow", "P2", "The 1000 requests/minute rate limit is far too low for our use case. We process engineering simulation data in batches and need at least 5000 req/min. What are our options?"),
    ("Insight", "P2", "The Insight API returned corrupted JSON payloads three times this week. Our data pipeline crashed each time. We need reliable API responses — this is feeding production systems."),
    ("Flow", "P1", "CRITICAL: Our nightly ETL job failed because the Flow API started rejecting requests with a new 'request body too large' error. Nothing changed on our end. Max payload size went from 10MB to 5MB?"),
    ("Canvas", "P3", "Is there a bulk operations API for Canvas? We're making thousands of individual API calls to update templates and it's extremely slow. A batch endpoint would solve our rate limit issues."),
    ("Flow", "P2", "We need webhook delivery guarantees. We've noticed Flow drops webhooks when our endpoint is temporarily unavailable. There's no retry queue and we lose data. For an enterprise product, this is unacceptable."),
    ("Insight", "P2", "The API documentation is incomplete — several endpoints return fields that aren't documented. We're building integrations and keep discovering undocumented breaking changes."),
    ("Flow", "P3", "Feature request: can we get API usage analytics? We want to see our own rate limit consumption over time so we can optimize our batch scheduling."),
]

# ---------------------------------------------------------------------------
# Ticket pool builder — maps account_id to a list of (product, priority, text) tuples
# ---------------------------------------------------------------------------
def _make_ticket_pool():
    pool = {}
    # Churn
    pool["ACC-001"] = [(p, pr, t) for p, pr, t in CHURN_RISK_TICKETS_MERIDIAN]
    pool["ACC-002"] = [(p, pr, t) for p, pr, t in CHURN_RISK_TICKETS_CASCADE]
    pool["ACC-003"] = [(p, pr, t) for p, pr, t in CHURN_RISK_TICKETS_BEACON]
    pool["ACC-004"] = [(p, pr, t) for p, pr, t in CHURN_RISK_TICKETS_PRISM]
    # Expansion
    pool["ACC-005"] = [(p, pr, t) for p, pr, t in EXPANSION_TICKETS_ATLAS]
    pool["ACC-006"] = [(p, pr, t) for p, pr, t in EXPANSION_TICKETS_SUMMIT]
    pool["ACC-007"] = [(p, pr, t) for p, pr, t in EXPANSION_TICKETS_VOYAGER]
    pool["ACC-008"] = [(p, pr, t) for p, pr, t in EXPANSION_TICKETS_IRONCLAD]
    # Attention
    pool["ACC-015"] = [(p, pr, t) for p, pr, t in ATTENTION_TICKETS_COBALT]
    pool["ACC-016"] = [(p, pr, t) for p, pr, t in ATTENTION_TICKETS_DRIFTWOOD]
    pool["ACC-017"] = [(p, pr, t) for p, pr, t in ATTENTION_TICKETS_EVERGREEN]
    pool["ACC-018"] = [(p, pr, t) for p, pr, t in ATTENTION_TICKETS_FLUX]
    return pool

TICKET_POOL = _make_ticket_pool()

# How many tickets each account should generate (approx)
TICKET_COUNTS = {
    "ACC-001": 50,   # Meridian — lots of frustrated tickets + AE gap
    "ACC-002": 45,   # Cascade — onboarding/adoption complaints
    "ACC-003": 42,   # Beacon — concentrated P1s + AE transition
    "ACC-004": 3,    # Prism — silent churn, almost nothing
    "ACC-005": 35,   # Atlas — feature requests
    "ACC-006": 35,   # Summit — how-to questions
    "ACC-007": 3,    # Voyager — self-sufficient
    "ACC-008": 18,   # Ironclad
    "ACC-009": 22, "ACC-010": 20, "ACC-011": 24, "ACC-012": 20,
    "ACC-013": 14, "ACC-014": 18,
    "ACC-015": 35,   # Cobalt — onboarding confusion
    "ACC-016": 32,   # Driftwood — admin change + AE gap
    "ACC-017": 28,   # Evergreen — budget + AE transition
    "ACC-018": 35,   # Flux — rate limits
    "ACC-019": 16, "ACC-020": 18,
}


def generate_support_tickets():
    tickets = []
    tid = 1

    for acct in ACCOUNTS:
        aid = acct["account_id"]
        n = TICKET_COUNTS.get(aid, 15)

        # For Beacon, cluster P1s in last 3 weeks
        if acct["story"] == "sudden_cliff":
            cluster_start = END_DATE - timedelta(days=21)
            # First generate the P1 cluster
            beacon_pool = TICKET_POOL[aid]
            p1_tickets = [t for t in beacon_pool if t[1] == "P1"]
            other_tickets = [t for t in beacon_pool if t[1] != "P1"]
            for tmpl in p1_tickets:
                dt = random_date(cluster_start, END_DATE)
                hour = random.randint(6, 20)
                ts = dt.replace(hour=hour, minute=random.randint(0, 59))
                status = random.choice(["open", "escalated"])
                tickets.append({
                    "ticket_id": f"TKT-{tid:04d}",
                    "account_id": aid,
                    "account_name": acct["account_name"],
                    "product": tmpl[0],
                    "ticket_text": tmpl[2],
                    "priority": tmpl[1],
                    "status": status,
                    "created_at": datetime_str(ts),
                })
                tid += 1
            # Then fill remaining with other templates
            for _ in range(n - len(p1_tickets)):
                tmpl = random.choice(other_tickets if other_tickets else beacon_pool)
                dt = random_date()
                hour = random.randint(6, 20)
                ts = dt.replace(hour=hour, minute=random.randint(0, 59))
                status = random.choices(["open", "resolved", "escalated"], weights=[30, 40, 30], k=1)[0]
                tickets.append({
                    "ticket_id": f"TKT-{tid:04d}",
                    "account_id": aid,
                    "account_name": acct["account_name"],
                    "product": tmpl[0],
                    "ticket_text": tmpl[2],
                    "priority": tmpl[1],
                    "status": status,
                    "created_at": datetime_str(ts),
                })
                tid += 1
            continue

        # For accounts with custom ticket pools
        if aid in TICKET_POOL:
            pool = TICKET_POOL[aid]
            for i in range(n):
                tmpl = pool[i % len(pool)]
                dt = random_date()
                # Churn risk: more tickets toward the end
                if acct["category"] == "churn_risk" and random.random() < 0.6:
                    dt = random_date(START_DATE + timedelta(days=45), END_DATE)
                hour = random.randint(6, 20)
                ts = dt.replace(hour=hour, minute=random.randint(0, 59))
                if acct["category"] == "churn_risk":
                    status = random.choices(["open", "resolved", "escalated"], weights=[40, 30, 30], k=1)[0]
                elif acct["category"] == "expansion":
                    status = random.choices(["open", "resolved", "escalated"], weights=[30, 60, 10], k=1)[0]
                elif acct["category"] == "attention":
                    status = random.choices(["open", "resolved", "escalated"], weights=[45, 35, 20], k=1)[0]
                else:
                    status = random.choices(["open", "resolved", "escalated"], weights=[20, 70, 10], k=1)[0]
                tickets.append({
                    "ticket_id": f"TKT-{tid:04d}",
                    "account_id": aid,
                    "account_name": acct["account_name"],
                    "product": tmpl[0],
                    "ticket_text": tmpl[2],
                    "priority": tmpl[1],
                    "status": status,
                    "created_at": datetime_str(ts),
                })
                tid += 1
        else:
            # Healthy accounts use generic pool
            for _ in range(n):
                tmpl = random.choice(HEALTHY_TICKETS)
                # Only use products the account actually has
                product = tmpl[0] if tmpl[0] in acct["products"] else random.choice(acct["products"])
                dt = random_date()
                hour = random.randint(6, 20)
                ts = dt.replace(hour=hour, minute=random.randint(0, 59))
                status = random.choices(["open", "resolved", "escalated"], weights=[15, 75, 10], k=1)[0]
                tickets.append({
                    "ticket_id": f"TKT-{tid:04d}",
                    "account_id": aid,
                    "account_name": acct["account_name"],
                    "product": product,
                    "ticket_text": tmpl[2],
                    "priority": tmpl[1],
                    "status": status,
                    "created_at": datetime_str(ts),
                })
                tid += 1

    return tickets


# ---------------------------------------------------------------------------
# Gong transcript templates
# ---------------------------------------------------------------------------
# Each entry: (call_type, duration_range, transcript, attendees_template)
# attendees_template uses {csm} placeholder

GONG_TRANSCRIPTS_MERIDIAN = [
    ("check-in", (20, 35),
     """{csm}: Thanks for taking the time today, Derek. I noticed Canvas usage across your team has dropped quite a bit over the past month. Is everything okay?

Derek Huang (Account Manager): Yeah, honestly, things have been tough since Jennifer left. She was our power user — she built all our templates, trained the team, the whole nine yards. Without her, people just kind of stopped using Canvas.

{csm}: I'm sorry to hear that. Jennifer was great to work with. Have you been able to assign someone to pick up her workflows?

Derek Huang: Not really. We've been slammed with client work. A few people on the team started using SketchFlow because they already knew it from previous jobs. It's kind of taken on a life of its own.

{csm}: I see. That's concerning — I'd love to help you get back on track. Would it help if we ran a re-onboarding session for your team? We have new templates specifically for media companies that might help reduce the learning curve.

Derek Huang: Maybe. I'll be honest though — my VP is already asking questions about the renewal. She's seen the SketchFlow usage and is wondering why we're paying for both. I need to show her clear value before June.""",
     "Derek Huang (Account Manager), {csm}"),

    ("QBR", (40, 55),
     """{csm}: Let's look at your Q1 usage metrics. I want to be transparent — active users dropped from 38 to 14 over the past eight weeks.

Laura Singh (VP Creative): Fourteen? That's worse than I thought. {csm}, I'm going to be direct. We're paying $186K annually and only a third of our team is using the product. That math doesn't work.

{csm}: I completely understand, Laura. Let me share some context on what we've been seeing and a recovery plan I've put together.

Laura Singh: Before you do — I should tell you that our design leads have been demoing SketchFlow Enterprise. The team likes it. The collaborative features are strong and the pricing is more straightforward. I haven't made a decision yet, but I need DigitalNativeCo to give me a reason to stay.

{csm}: I appreciate the honesty. Let me walk you through three things: first, the new Canvas collaboration features we shipped last month that directly address what SketchFlow offers; second, a custom onboarding track for your team; and third, a flexible pricing conversation with our account executive. I don't want to lose your business and I think there's a path here.

Laura Singh: Okay, show me what you've got. But I need to see real movement in the next 30 days. Our budget review is in April.""",
     "Laura Singh (VP Creative), Derek Huang (Account Manager), {csm}"),

    ("check-in", (15, 25),
     """{csm}: Hi Derek, just checking in after our QBR last week. Have you had a chance to look at the Canvas collaboration features I demoed?

Derek Huang (Account Manager): I did, briefly. Look, I want to be straight with you — Laura is leaning toward SketchFlow. She asked me to get an export of all our assets from Canvas so we can evaluate the migration path.

{csm}: I hear you. Before you start that process, can I get 30 minutes with Laura directly? I have a revised proposal from our leadership that includes dedicated onboarding support and a pricing adjustment. I think it could change the conversation.

Derek Huang: I can ask, but don't get your hopes up. She's pretty set. The SketchFlow demo went well and their sales team has been very responsive.""",
     "Derek Huang (Account Manager), {csm}"),

    ("check-in", (20, 30),
     """{csm}: Derek, I wanted to check in on how things are going with the transition to your new account executive. Lisa Patel took over from Jake Torres — have you connected with her?

Derek Huang (Account Manager): Wait, Jake left? When did that happen? Nobody told us. We've been trying to reach him for three weeks about the renewal pricing discussion. Emails bouncing, no responses on Slack. We thought he was just ignoring us.

{csm}: I'm so sorry about the communication gap. Jake left the company in mid-January and there was a delay in reassigning accounts. Lisa just came on board for your account last week. She's excellent and I'd love to get her on a call with you and Laura this week.

Derek Huang: {csm}, this is exactly the kind of thing that makes leadership question the relationship. We're a $186K account — one of your bigger ones — and nobody thought to tell us our AE left? Laura is going to hear about this and it's going to reinforce her SketchFlow argument. SketchFlow's sales team responds to us within hours. We went three weeks without even knowing who our rep was.

{csm}: You're absolutely right and I take full responsibility for the gap. Let me set up an introduction with Lisa this week, and I'll make sure she comes prepared with the pricing options Jake was working on. We have not dropped the ball on the renewal — I want to fight for this.

Derek Huang: I'll give Lisa a chance, but the clock is ticking. June is three months away and Laura is already getting SketchFlow contract terms. You're behind.""",
     "Derek Huang (Account Manager), {csm}"),

    ("check-in", (25, 35),
     """Lisa Patel (Account Executive): Hi Derek, Laura — thank you for making time. I'm Lisa, your new account executive. I know the transition from Jake wasn't smooth and I want to acknowledge that upfront.

Laura Singh (VP Creative): Lisa, I appreciate the directness. Let me be equally direct — we've been evaluating SketchFlow Enterprise for the past month. Their team license for our 45 seats would cost us about $40K annually. We're paying you $186K. That's a $146K gap I need to justify to my CEO.

Lisa Patel: I understand the math. Let me address that in two ways. First, the pricing — I have authorization to restructure your contract to better align with your actual usage. We can move to a flex-seat model that would bring your effective cost closer to $120K. Second, the value — Canvas offers enterprise features that SketchFlow doesn't match yet: SOC2 compliance, advanced role-based permissions, and the Flow integration for automated approvals.

Laura Singh: The SOC2 point is relevant — our legal team does care about that. But Lisa, I have to be honest. The fact that Jake left and we went three weeks without anyone reaching out... that tells me something about how important we are to DigitalNativeCo. We're supposed to be a strategic account.

Lisa Patel: You are a strategic account, and the gap in coverage was unacceptable. Here's what I'm proposing: a 60-day renewal plan with dedicated weekly check-ins from me, a re-onboarding for your team led by our solutions engineer Alex Kim, and the revised pricing I mentioned. If at the end of 60 days you don't see the value, I'll personally help you with the migration plan. I'd rather earn your trust than hold you hostage.

Laura Singh: That's a reasonable offer. Let me talk to David Leung, our VP of Marketing, and get back to you by Friday. Derek, can you set up time for Lisa to meet David?

Derek Huang (Account Manager): I'll send the calendar invite today.""",
     "Lisa Patel (Account Executive), Laura Singh (VP Creative), Derek Huang (Account Manager), {csm}"),
]

GONG_TRANSCRIPTS_CASCADE = [
    ("QBR", (35, 50),
     """{csm}: Let's go through your product adoption across the three tools. Flow is looking great — 72 active users out of 80 seats, strong daily engagement. Canvas and Insight are a different story though.

Michael Chen (Director of Operations): Yeah, Flow has been a home run for us. The approval workflows saved our compliance team 20 hours a week. But Canvas — I don't even know what to tell you. We tried rolling it out twice and both times the team bounced off it.

{csm}: What specifically is blocking adoption? Is it the onboarding, the feature set, or something else?

Michael Chen: Honestly, it's the onboarding. The tutorials assume you're a designer. We're a financial services company — our people make pitch decks and regulatory documents, not creative assets. The whole visual language of Canvas feels alien to them.

{csm}: That's really helpful feedback. We actually just launched an industry-specific onboarding track for financial services. Can I set up a pilot with a small group?

Michael Chen: You can try, but I need to be upfront — we're probably not going to renew Canvas and Insight. Those two products are costing us $180K combined and the usage doesn't justify it. Flow is staying no matter what, but the rest is on the chopping block.

{csm}: I understand. Let me pull together some usage data and a targeted adoption plan. If we can move the needle in 60 days, would that change the conversation?

Michael Chen: Possibly. But 60 days is all I can give you. Our procurement team starts renewal reviews in May.""",
     "Michael Chen (Director of Operations), {csm}"),

    ("check-in", (20, 30),
     """{csm}: Hi Michael, following up on the Canvas onboarding pilot. How did the first session go?

Michael Chen (Director of Operations): Five people attended out of the 15 I invited. The three who stayed for the full session said it was better than the original onboarding, but they still don't see why they'd switch from PowerPoint for their daily work.

{csm}: Did they get a chance to try the template library? We built those financial services templates specifically for pitch decks and compliance documents.

Michael Chen: They did. The templates were good but the editing experience is too different from what they know. I think this is a fundamental fit issue, not a training issue. I've told my VP we should consolidate to just Flow at renewal. I'm sorry — I know that's not what you want to hear.""",
     "Michael Chen (Director of Operations), {csm}"),
]

GONG_TRANSCRIPTS_BEACON = [
    ("check-in", (25, 40),
     """{csm}: Robert, I wanted to address the API issues your team has been experiencing. I know it's been a rough few weeks.

Robert Kimball (VP Engineering): Rough is an understatement. We've had three major outages in three weeks. Our dispatch dashboard went down during peak hours. Do you know what happens when a logistics company can't see its shipments? People start making phone calls. Hundreds of phone calls.

{csm}: I completely understand the severity. I've escalated this to our engineering leadership and they've identified the root cause — it was a database connection pooling issue that was triggered by a recent scaling event.

Robert Kimball: That's great, but it doesn't help me with the 47 hours of downtime we've already eaten. Our SLA says 99.9% uptime. We're at about 97% this month. My CFO is going to ask for credits and honestly, I think we deserve them.

{csm}: You absolutely deserve a conversation about that. I've already flagged it with our finance team. Can we schedule a call with our VP of Engineering to walk through the remediation plan and discuss the SLA credit?

Robert Kimball: Fine. But {csm}, I need you to understand — if this happens again, we're going to start evaluating alternatives. We can't afford unreliable infrastructure in our line of work. Lives don't depend on it, but livelihoods do.""",
     "Robert Kimball (VP Engineering), {csm}"),

    ("check-in", (15, 25),
     """{csm}: Robert, I have an update on the SLA remediation. Our engineering team has deployed three fixes: connection pool scaling, automated failover, and enhanced monitoring with PagerDuty integration. We've also provisioned dedicated infrastructure for your account.

Robert Kimball (VP Engineering): Dedicated infrastructure? That's a step in the right direction. What about the SLA credits?

{csm}: I've gotten approval for a 15% credit on your next quarter's invoice, which comes to about $3,600. I know that doesn't fully cover the operational impact, but I wanted to show good faith while we finalize the full credit calculation.

Robert Kimball: I appreciate that. But 15% isn't going to satisfy my CFO when I show him the incident report. We calculated about $12K in operational costs from the outages — overtime for manual dispatching, customer complaints, and SLA penalties from our own clients.

{csm}: Let me take that number back to my leadership. I want to make this right. In the meantime, can you confirm the new dedicated infrastructure is performing as expected?

Robert Kimball: It's been stable for four days. If it stays that way for a month, we can have a different conversation.""",
     "Robert Kimball (VP Engineering), {csm}"),

    ("check-in", (20, 30),
     """{csm}: Robert, I wanted to introduce you to Kevin McBride, your new account executive. He took over from Jake Torres in January.

Robert Kimball (VP Engineering): Another change. Fine. Kevin, no offense, but Jake understood our infrastructure. He knew our architecture, our pain points, our SLA requirements. Are you up to speed on our API issues?

Kevin McBride (Account Executive): I've reviewed the incident reports and the SLA credit discussions. I know you've had three major outages and we owe you a resolution on the full credit calculation.

Robert Kimball: That's the minimum. Here's what I need from you: first, the final SLA credit number — not the 15% partial, the real number based on our $12K operational impact. Second, a written guarantee on uptime or a contractual clause that triggers automatic credits. Third, a technical architecture review with your engineering team so I can trust the platform again.

Kevin McBride: I'll work with our VP of Sales and finance team on the credit calculation. For the contractual clause, I'll need to loop in legal but I think we can make that work.

Robert Kimball: Kevin, I'll give you the same advice I gave Jake before he left — don't make promises you can't keep. Jake was great at the relationship side but our API kept going down anyway. I need results, not reassurance.

{csm}: Robert, I'll make sure Kevin has all the context he needs. And I want to acknowledge — the combination of the API issues and the AE transition hasn't been ideal. You've been incredibly patient and I don't want that patience to run out.

Robert Kimball: It's running thin. Get me the credit number by Friday.""",
     "Robert Kimball (VP Engineering), Kevin McBride (Account Executive), {csm}"),
]

GONG_TRANSCRIPTS_PRISM = [
    ("check-in", (10, 18),
     """{csm}: Hi Patricia, thanks for making time. I wanted to check in on how things are going with Canvas. It's been a while since we last spoke.

Patricia Lowe (Marketing Manager): Oh, hi {csm}. Yeah, things are fine. We've been busy with other stuff. Canvas is fine.

{csm}: Great. I noticed usage has been trending down a bit over the past couple months. Is your team finding everything they need?

Patricia Lowe: Yeah, I think so. We just haven't had as many projects recently. Things should pick up. Listen, I have another meeting in a few minutes — can we circle back on this later?

{csm}: Of course. I'll send you some resources on the new Canvas features we launched this quarter. Maybe we can do a deeper check-in next month?

Patricia Lowe: Sure, sounds good. I'll look at my calendar. Thanks {csm}.""",
     "Patricia Lowe (Marketing Manager), {csm}"),

    ("renewal", (12, 20),
     """{csm}: Patricia, your renewal is coming up in April. I wanted to touch base early to make sure everything is in order.

Patricia Lowe (Marketing Manager): Right, April. I need to check with my boss on that. We've had some budget shifts and I'm not sure what the plan is yet.

{csm}: Understood. Is there anything I can help with to make the case internally? Usage reports, ROI analysis, anything like that?

Patricia Lowe: Maybe. Let me talk to my team first and I'll get back to you. We'll circle back.

{csm}: Sounds good. I'll follow up next week. If there's anything specific you need in the meantime, don't hesitate to reach out.

Patricia Lowe: Will do. Thanks.""",
     "Patricia Lowe (Marketing Manager), {csm}"),
]

GONG_TRANSCRIPTS_ATLAS = [
    ("check-in", (25, 35),
     """{csm}: Great to see you, Nina. Your Canvas metrics are incredible — 15% month-over-month growth, 92% seat utilization. Your team is really getting value out of the platform.

Nina Alvarez (Head of Design): Thank you! Honestly, Canvas has become the backbone of our design workflow. We went from spending half our time on file management to actually designing. The template system alone saves us probably 10 hours a week across the team.

{csm}: That's fantastic to hear. You mentioned last time you were interested in automating some of your design-to-publish workflows. Is that still on your radar?

Nina Alvarez: Absolutely. That's actually why I wanted to talk today. We're doing a lot of manual handoffs between design in Canvas and our marketing ops team. Someone told me Flow can automate that entire pipeline — route designs for approval, resize for different channels, schedule publishing. Is that right?

{csm}: That's exactly what Flow does. I'd love to set up a demo with your marketing ops team. Flow integrates natively with Canvas, so the assets flow through automatically.

Nina Alvarez: That would be great. What does the pricing look like for Flow? We'd probably need about 20 seats to start — the design team plus marketing ops.

{csm}: I'll put together a proposal this week. Given your Canvas usage, there are bundling options that could make this very cost-effective. Would next Thursday work for a demo with the marketing ops team?

Nina Alvarez: Let me check with Jordan, our marketing ops lead. I'll confirm by tomorrow.""",
     "Nina Alvarez (Head of Design), {csm}"),

    ("demo", (35, 50),
     """{csm}: Thanks for joining, Jordan. Nina's been telling me great things about your team's workflow. Today I want to show you how Flow can automate the handoffs between design and marketing ops.

Jordan Reeves (Marketing Ops Manager): Yeah, Nina won't stop talking about Canvas, so I'm curious. Right now we have this clunky process — designers export from Canvas, upload to a shared drive, I get an email, I resize everything manually, then push to our marketing platforms. It takes two days for what should take two hours.

{csm}: Let me show you the Flow automation template for exactly that workflow. [Screen share] Here's a Canvas-to-publish pipeline. When a designer marks a project as 'Ready for Review,' Flow automatically triggers: first, it routes to the approval chain you define. Then once approved, it auto-generates all the size variants you need — social, email, web, print. Finally, it pushes to your connected platforms.

Jordan Reeves: Wait, it does the resizing automatically? That's literally 60% of my team's work.

{csm}: Yes, and it maintains brand guidelines while resizing — so fonts, spacing, and safe zones are all preserved. Let me show you the rules engine.

Jordan Reeves: Nina, why didn't we get this sooner? Okay, {csm}, I'm sold in concept. What do we need to get a pilot going?

Nina Alvarez (Head of Design): I told you! {csm}, let's move fast on this. Send us the proposal and we can probably get procurement started this quarter.""",
     "Nina Alvarez (Head of Design), Jordan Reeves (Marketing Ops Manager), {csm}"),

    ("check-in", (20, 30),
     """{csm}: Nina, I'm sending over the Flow proposal today. Quick question — you mentioned your team is growing. Are you going to need additional Canvas seats as well?

Nina Alvarez (Head of Design): Oh, definitely. We're hiring 8 more designers over the next two quarters. I'll need at least 10 more Canvas seats to account for contractors too.

{csm}: Perfect. I'll include a seat expansion quote alongside the Flow proposal so you can bundle the procurement.

Nina Alvarez: Smart. Also — I've been meaning to ask — do you have anything on the Insight side? Our CEO has been asking for analytics on which campaign assets perform best. If we could tie Canvas usage data to marketing performance metrics, that would be a game-changer.

{csm}: That's exactly what Insight does. Let me add an Insight overview to our next call. I think the combination of Canvas, Flow, and Insight would give you a complete creative operations platform.

Nina Alvarez: I love it. Let's move on all three fronts.""",
     "Nina Alvarez (Head of Design), {csm}"),
]

GONG_TRANSCRIPTS_SUMMIT = [
    ("onboarding", (30, 45),
     """{csm}: Welcome aboard, Dr. Patel. I'm thrilled to have Summit Healthcare on the platform. Let's talk about your rollout plan.

Dr. Aisha Patel (Chief Marketing Officer): Thank you. We're really excited. We've been looking for a unified creative platform that can handle both patient-facing materials and internal communications. Canvas checked every box.

{csm}: Your team ramped up faster than any healthcare client I've worked with. You're at 36 active users out of 40 seats in just six weeks. That's remarkable.

Dr. Aisha Patel: I credit our department leads. Marcus in regulatory affairs actually volunteered to be our Canvas champion. He's been running weekly training sessions on his own time. The man is obsessed.

{csm}: That's incredible. Champions like Marcus are gold. Have you thought about expanding to Flow for your regulatory approval workflows? I know healthcare companies often have complex review chains.

Dr. Aisha Patel: Marcus actually brought that up last week. He wants to automate the medical-legal-regulatory review process. Right now it takes 3 weeks to get a patient brochure approved. He thinks Flow could cut that in half.

{csm}: He's right — we have healthcare clients who've reduced approval cycles from weeks to days. Let me set up a dedicated session with Marcus and your regulatory team.""",
     "Dr. Aisha Patel (CMO), {csm}"),

    ("check-in", (25, 35),
     """{csm}: Great news on the usage front — you're now at 90% seat utilization, and your team's average session duration has doubled since onboarding. The engagement is really strong.

Dr. Aisha Patel (CMO): My team loves this tool. I'm not exaggerating — the patient education materials we're producing now are in a completely different league. Our patient satisfaction scores for communication materials went up 23%.

{csm}: That's an incredible metric. Would you be comfortable sharing that as a case study? Our marketing team would love to feature Summit Healthcare.

Dr. Aisha Patel: Absolutely. In fact, I just presented our Canvas workflow to the hospital system's national marketing council. Three other hospitals in our network asked me for the vendor details. I may have accidentally become your biggest evangelist.

{csm}: I love hearing that. Let me connect you with our enterprise team — if there's an opportunity to expand across the hospital network, we can put together a system-wide proposal.

Dr. Aisha Patel: Yes, let's do that. Also, Marcus wants a demo of Flow before our next call. He's already mapped out the regulatory workflow on a whiteboard. The man doesn't sleep.""",
     "Dr. Aisha Patel (CMO), {csm}"),

    ("demo", (30, 40),
     """Marcus Williams (Regulatory Affairs Director): I've been looking forward to this demo. I mapped out our current approval process — it has 14 steps, 6 reviewers, and takes an average of 18 business days. I want to cut it to 5 days.

{csm}: That's ambitious but achievable. Let me show you the healthcare compliance template in Flow. [Screen share] This workflow mirrors the MLR review process. You can configure conditional routing based on content type — patient-facing materials go through the full medical-legal-regulatory chain, while internal communications skip the medical review.

Marcus Williams: Oh, that's smart. Can I set up parallel reviews instead of sequential? Our medical reviewer and legal reviewer don't actually need to wait for each other.

{csm}: Absolutely. Here's the parallel gate feature. You define which reviews can happen simultaneously and which are dependencies. You also get real-time dashboards showing where each asset is in the pipeline.

Marcus Williams: This is going to change everything. Dr. Patel is going to want to roll this out to all six departments. Can we start with a pilot in my team and then expand?

{csm}: That's exactly what I'd recommend. We can have your team live on Flow within two weeks, prove the value, and then roll out organization-wide.

Marcus Williams: Let's do it. I'll talk to Dr. Patel today. She's going to be thrilled.""",
     "Marcus Williams (Regulatory Affairs Director), {csm}"),
]

GONG_TRANSCRIPTS_VOYAGER = [
    ("QBR", (40, 55),
     """{csm}: Let's review your Q1 metrics. Across all three products, Voyager is one of our most engaged enterprise accounts. 108 active users out of 120 seats, average session duration of 42 minutes, and your team created over 3,200 assets in Canvas last quarter.

Diana Okonkwo (SVP Digital Production): Those numbers track with what we're seeing internally. Our entire post-production pipeline runs on DigitalNativeCo now. Canvas for creative, Flow for approvals and handoffs, Insight for tracking campaign performance. It's become mission-critical.

{csm}: That's great to hear. Anything on the roadmap we should discuss?

Diana Okonkwo: Actually, yes. We're launching a new streaming division — Voyager Plus. It's a whole new content vertical with its own marketing team, about 50 people. They'll need the full suite.

{csm}: Fifty additional seats across all three products? That's exciting. When is the division going live?

Diana Okonkwo: We're hiring now, first team members start in April. I'd like to have everything provisioned and workspaces set up by June at the latest. Can we talk about volume pricing? At 170 total seats, I'm hoping we can negotiate a better per-seat rate.

{csm}: Absolutely. Let me put together an enterprise expansion proposal. Given the volume, there's definitely room for a tiered pricing conversation. I'll have something for you by end of week.

Diana Okonkwo: Perfect. Also, Thomas from our data team wants to talk about Insight API access for the new division. They want to build custom analytics dashboards on top of your data.

{csm}: I'll set up a technical call with Thomas and our solutions engineering team. This is exciting — congratulations on the expansion, Diana.""",
     "Diana Okonkwo (SVP Digital Production), {csm}"),

    ("check-in", (20, 30),
     """{csm}: Diana, the expansion proposal is ready. I have a few pricing options depending on how you want to structure the seat allocation.

Diana Okonkwo (SVP Digital Production): Great, send it over. I have a procurement meeting on Friday and I want to include this. Quick question — can we set up separate workspaces for Voyager Plus so their content doesn't mix with our main library?

{csm}: Yes, absolutely. We can create a separate organization within your enterprise account. They'll have their own workspace, templates, and permissions while still sharing the enterprise-level settings and SSO.

Diana Okonkwo: Perfect. The other thing — Thomas met with your solutions engineering team and he's very impressed. He wants to build an internal dashboard that combines Insight data with our proprietary viewership metrics. He asked about the Insight Enterprise API tier.

{csm}: The Enterprise API includes higher rate limits, custom webhook endpoints, and raw data export. I'll include it in the proposal. It's typically a $2K/month add-on but given the overall expansion, I think we can bundle it in.

Diana Okonkwo: You're speaking my language. Let's get this done.""",
     "Diana Okonkwo (SVP Digital Production), {csm}"),
]

GONG_TRANSCRIPTS_IRONCLAD = [
    ("check-in", (20, 30),
     """{csm}: Jason, good to see you. Canvas usage continues to climb — you're up 12% from last month. What's driving the increase?

Jason Miller (Engineering Manager): We've been using Canvas for all our product documentation now — spec sheets, assembly guides, safety documentation. The template system is a lifesaver. We used to spend days formatting these documents in InDesign.

{csm}: That's a great use case. I remember you mentioned wanting to connect your design data to analytics. Is that still of interest?

Jason Miller: Huge interest. Our VP of Operations keeps asking me which product templates get used most, which ones are outdated, and how long each document takes to produce. Right now I'm tracking all of that in a spreadsheet. Can Insight do that?

{csm}: Absolutely. Insight can pull in Canvas usage data and give you dashboards on template usage, creation time, revision frequency — all the metrics your VP is asking about. Plus, you mentioned your Snowflake data warehouse — Insight has a native Snowflake connector.

Jason Miller: Wait, it connects directly to Snowflake? Our data engineering team would love that. They could join our product manufacturing data with Canvas usage data and build some really powerful analytics.

{csm}: Let me set up a demo with your data engineering team. I think Insight could be a natural extension of what you're already doing with Canvas.

Jason Miller: Let's do it. If the Snowflake connector works well, getting budget approval should be easy.""",
     "Jason Miller (Engineering Manager), {csm}"),
]

GONG_TRANSCRIPTS_COBALT = [
    ("onboarding", (30, 45),
     """{csm}: Let's check in on the onboarding progress. You're at week four — how is the team feeling?

Richard Torres (IT Director): I'm going to be honest — it's been rough. We have 55 licensed seats and only about 8 people are actively using the platform. The rest have either tried it once or haven't logged in at all.

{csm}: That's lower than we'd like to see at this stage. What do you think is causing the low adoption?

Richard Torres: A few things. First, the workspace structure is confusing. Our engineers don't think in terms of 'organizations' and 'teams' and 'projects' — they think in terms of programs and contracts. The mental model doesn't match. Second, the onboarding emails your system sends assume we're a creative agency. We're an aerospace company. The tone is all wrong.

{csm}: Those are both valid concerns. We've been working on industry-specific onboarding tracks and I can switch yours to the engineering/manufacturing template. It maps our workspace hierarchy to program/contract language.

Richard Torres: That would help. The third issue is permissions. I've spent 6 hours trying to set up role-based access and I still can't figure out why 47 people see 'access denied' on the shared workspace. Your documentation doesn't cover our SSO configuration (Azure AD with nested groups).

{csm}: That's a known gap in our docs. Let me schedule a co-working session with our solutions engineer — we'll get your Azure AD groups mapped correctly. Can we do tomorrow morning?

Richard Torres: Sure. But {csm}, I need to set expectations — if we can't get meaningful adoption by week 8, my VP is going to start asking uncomfortable questions about this purchase.""",
     "Richard Torres (IT Director), {csm}"),

    ("check-in", (20, 30),
     """{csm}: Richard, how did the co-working session go? Were you able to get the permissions sorted out?

Richard Torres (IT Director): The solutions engineer was very helpful — the Azure AD mapping works now and all 55 users can access the workspace. That part is fixed. But adoption is still slow. I sent out the new onboarding emails and only 12 people completed the getting-started tutorial.

{csm}: Progress, but I hear the frustration. What if we ran an internal launch event? I could join a team all-hands and do a live demo tailored to your aerospace use cases — showing how Canvas can be used for technical documentation, safety manuals, and program review presentations.

Richard Torres: That's not a bad idea. Our engineers respond better to seeing real-world examples than reading tutorials. Can you build a sample workspace that looks like one of our actual programs? I can send you some sanitized examples.

{csm}: Absolutely. Send me the examples and I'll build out a demo workspace. Let's target next Thursday for the all-hands demo.

Richard Torres: Deal. If this doesn't move the needle, we need to have a different conversation about our deployment strategy.""",
     "Richard Torres (IT Director), {csm}"),
]

GONG_TRANSCRIPTS_DRIFTWOOD = [
    ("check-in", (20, 30),
     """{csm}: Welcome, Yuki. I understand you recently took over as the admin for Driftwood Media's account from Mark Torres.

Yuki Tanaka (New Admin): Yes, about three weeks ago. Mark left the company kind of suddenly and I got handed the keys to everything, including DigitalNativeCo. I'm a project manager by background, not an IT admin, so I'm learning as I go.

{csm}: Totally understandable. Let me help you get up to speed. What are your most pressing concerns right now?

Yuki Tanaka: First, I need full admin access. I can see the dashboard but I can't manage users or change settings. Second, I need to understand what automations Mark set up in Flow — there are things running that I don't fully understand and one of them is sending emails to his personal Gmail.

{csm}: Okay, let's tackle these one at a time. I can initiate an admin transfer right now — it just requires your company's domain verification. For the Flow automations, I'll do a full audit of your active workflows and document them for you.

Yuki Tanaka: That would be incredibly helpful. I also need to add three new team members and remove Mark's access. Can we do that today?

{csm}: Absolutely. Let me walk you through the user management panel.""",
     "Yuki Tanaka (New Admin), {csm}"),

    ("check-in", (20, 30),
     """{csm}: Yuki, how's the admin transition going? Did the Flow audit help?

Yuki Tanaka (New Admin): The audit was great — thank you. I found four automations Mark set up, killed the one emailing his Gmail, and documented the rest. I'm feeling more in control now. But I have a different concern.

{csm}: What's on your mind?

Yuki Tanaka: Our AE Diana was great — she checked in every two weeks and helped Mark with anything we needed. Now I hear she's on parental leave and Tom Westfield is covering. I emailed Tom twice last week about updating our billing contact and haven't heard back. I also emailed him about potentially adding 3 seats for new hires and no response.

{csm}: I'm sorry about that. Tom is covering several accounts right now and may be stretched thin. Let me follow up with him directly and make sure your requests get handled today.

Yuki Tanaka: {csm}, I'm new to this admin role and I don't know your company well. When my AE doesn't respond and my admin predecessor left no documentation, it feels like we're on our own. The product works fine — the people side is what's broken right now.

{csm}: That's fair feedback and I hear you. I'll make sure Tom responds by end of day and I'll be your backup point of contact for anything urgent. You're not on your own.""",
     "Yuki Tanaka (New Admin), {csm}"),
]

GONG_TRANSCRIPTS_EVERGREEN = [
    ("check-in", (25, 35),
     """{csm}: Sandra, I wanted to check in on how things are going at Evergreen Education. Your usage metrics look solid — 18 active users out of 22 seats. How's the team feeling about the platform?

Sandra Brooks (Curriculum Director): The team loves it, honestly. Canvas has transformed how we create curriculum materials. Our teachers used to spend entire weekends formatting worksheets and presentations. Now they have templates and it takes a fraction of the time.

{csm}: That's wonderful. So why the worried tone in your email last week?

Sandra Brooks: Budget. Our district superintendent announced a 15% across-the-board cut for next fiscal year. Every department has to justify every dollar. I love Canvas and Insight, but when you're choosing between software licenses and a teaching assistant, the TA wins.

{csm}: I completely understand. Let me help you build the ROI case. You mentioned Canvas saves teachers time — can we quantify that? If 18 teachers save 3 hours a week, that's 54 hours, which at an average teacher hourly rate is significant.

Sandra Brooks: That's a good angle. I do think the time savings are real. But our business office looks at the invoice amount, not the soft savings. Is there an education pricing tier? We're a public school district — we can't pay enterprise rates.

{csm}: Let me look into our education pricing. We do have special rates for K-12 and higher ed. I'll put together a proposal that shows the per-teacher cost alongside the time savings. Would that help?

Sandra Brooks: That would help a lot. If you can get the number below $40 per seat per month, I think I can make it work. But I need that proposal before our April budget hearing.""",
     "Sandra Brooks (Curriculum Director), {csm}"),

    ("check-in", (15, 25),
     """{csm}: Sandra, I have good news. I spoke with our education team and we can offer Evergreen Education a 35% discount under our K-12 program. That brings your per-seat cost to $36/month.

Sandra Brooks (Curriculum Director): Oh, that's under my threshold! Can you send me a formal quote? I need to present it to the business office by March 20th.

{csm}: I'll have it to you by end of day tomorrow. I'm also including a one-page impact summary showing the usage metrics and estimated time savings. You can present both to the business office.

Sandra Brooks: Perfect. You know, if we keep the seats, I might actually want to add a few more next year. Our elementary school teachers have been asking about Canvas after seeing what the middle school team is doing.

{csm}: That's great to hear. Let's get through the renewal first and then we can plan for expansion. One step at a time.""",
     "Sandra Brooks (Curriculum Director), {csm}"),

    ("check-in", (20, 30),
     """{csm}: Sandra, I wanted to introduce Tom Westfield — he's covering as your account executive while Diana Osei is on parental leave.

Sandra Brooks (Curriculum Director): Oh, Diana's on leave? She didn't mention it on our last call. Congratulations to her, of course. Tom, nice to meet you — are you up to speed on our budget situation?

Tom Westfield (Account Executive): I've been briefed on the education discount proposal. I know your renewal is coming up in May and there's budget pressure.

Sandra Brooks: That's the basics, yes. But Diana knew our account inside and out. She knew our superintendent by name, she knew which board members were supportive and which were skeptical. She fought for our education pricing when your standard team wanted to charge us enterprise rates. I hope she documented all that.

Tom Westfield: I'll review her notes thoroughly. I should be transparent — I'm covering several of Diana's accounts right now so I may not be as responsive as she was, but I'll make sure your renewal doesn't fall through the cracks.

Sandra Brooks: Tom, I appreciate the honesty. But our budget hearing is April 15 and I need that formal quote before then. If the renewal falls through the cracks, we lose Canvas for 400 teachers. That's not something that gets fixed later.

{csm}: Sandra, I'm personally tracking this to make sure nothing gets dropped. You'll have the quote this week.""",
     "Sandra Brooks (Curriculum Director), Tom Westfield (Account Executive), {csm}"),
]

GONG_TRANSCRIPTS_FLUX = [
    ("check-in", (25, 40),
     """{csm}: Raj, I know the rate limiting issues have been a pain point. I wanted to give you an update.

Raj Kapoor (CTO): {csm}, we like your product. The functionality is exactly what we need. But the rate limits are killing us. Our engineering simulation pipeline processes 50,000 API calls between 2 and 4 PM every day. Your current limit of 1,000 per minute means our batch jobs take 8x longer than they should.

{csm}: I hear you. I've been working with our infrastructure team on this. We have two options: first, we can move you to a dedicated API tier with 5,000 requests per minute. Second, we're launching a batch API endpoint next month that lets you submit bulk operations in a single call.

Raj Kapoor: What's the cost for the dedicated tier?

{csm}: It's an add-on to your current plan — $800/month. But given your usage patterns, the batch API might be a better long-term solution at no extra cost.

Raj Kapoor: I want the dedicated tier now and the batch API when it's ready. We can't wait a month for our pipelines to run properly. This is impacting our delivery schedules.

{csm}: Done. I'll get the dedicated tier provisioned today. You should see the increased limits within 24 hours. And I'll make sure you're in the beta for the batch API.

Raj Kapoor: Good. One more thing — the Insight API returned malformed JSON three times this week. Our data pipeline crashed each time. We need reliable API responses, not just faster ones.

{csm}: I'm aware of that bug — it's related to a serialization issue with nested arrays. The fix is in QA now and should ship this week. I'll make sure your account is prioritized for the update.""",
     "Raj Kapoor (CTO), {csm}"),
]

# Healthy/stable accounts — generic positive calls
GONG_TRANSCRIPTS_HEALTHY = [
    ("check-in", (15, 25),
     """{csm}: Hi {contact}, just our regular monthly check-in. How's everything going with {product}?

{contact_full}: Going well! The team is humming along. We had a minor hiccup last week with the export function timing out on large files, but your support team resolved it the same day. No complaints.

{csm}: Happy to hear the support experience was good. Any upcoming needs or changes I should know about?

{contact_full}: Nothing major. We might add a couple of seats next quarter as we bring on summer interns, but I'll let you know. Everything is steady.

{csm}: Perfect. I'll send you the release notes for the update coming next week — there are some nice performance improvements that should help with those large exports.""",
     "{contact_full}, {csm}"),

    ("check-in", (15, 25),
     """{csm}: {contact}, good to connect. I wanted to share some metrics from your account — your team's usage has been very consistent, which is a great sign.

{contact_full}: Yeah, {product} has become part of our daily workflow. The team barely notices it anymore, which I mean as a compliment — it just works.

{csm}: That's the best feedback we can get. Anything on your wish list for the platform?

{contact_full}: Honestly, I'd love to see better integrations with Slack. We use Slack for everything and having notifications from {product} go directly to our project channels would save us from checking two places.

{csm}: Great news — our Slack integration actually launched last month. Let me send you the setup guide. It does exactly what you're describing — project notifications, approval requests, and export completions all go to a Slack channel of your choice.

{contact_full}: Oh perfect, I missed that announcement. I'll get it set up this week. Thanks!""",
     "{contact_full}, {csm}"),

    ("QBR", (30, 45),
     """{csm}: Let's go through your quarterly review. Overall, your account looks very healthy — solid usage, low support volume, and your team is using most of the features available in your plan.

{contact_full}: Good to hear. We're happy with the platform. My only note is that onboarding new team members takes longer than it should. Is there a way to create a custom onboarding track with just the features we use?

{csm}: Actually, yes. We launched custom learning paths last quarter. You can select which modules to include and skip the ones that aren't relevant to your team. I'll send you the admin guide.

{contact_full}: That would be great. We're hiring two people next month and I'd love to get them productive faster. Other than that, everything is good. Same time next quarter?

{csm}: Sounds good. And don't hesitate to reach out before then if anything comes up.""",
     "{contact_full}, {csm}"),

    ("check-in", (15, 25),
     """{csm}: Hi {contact}, how's the team adapting to the UI refresh we rolled out last week?

{contact_full}: A few people grumbled for the first day or two, but everyone has adapted now. The new navigation is actually faster once you get used to it. The quick search bar is a huge improvement.

{csm}: Glad to hear the adjustment was smooth. We put a lot of effort into the search functionality. Any other feedback from the team?

{contact_full}: Just one thing — the mobile app is still pretty limited compared to the desktop version. A couple of our people work remotely and check things on their phones. If you could beef up the mobile experience, that would be great.

{csm}: Mobile improvements are on our H2 roadmap. I'll flag your feedback to the product team. In the meantime, the responsive web version works pretty well on tablets if that helps.

{contact_full}: Good to know. Thanks for the update!""",
     "{contact_full}, {csm}"),

    ("renewal", (20, 30),
     """{csm}: {contact}, your renewal is coming up in a few months. I wanted to touch base early. How are you feeling about the platform?

{contact_full}: Positive. Renewing is a no-brainer for us. The team relies on it daily and we've gotten great value. The only question is whether we want to add any seats or products.

{csm}: Happy to hear that. Let me pull together your usage summary and any product recommendations. If there are areas where you're underutilizing, I can help you get more value from your current plan before we talk about adding anything.

{contact_full}: Sounds good. I trust your judgment — you've always been straightforward with us. Let me know what you find.

{csm}: Will do. I'll have a summary for you by next week.""",
     "{contact_full}, {csm}"),
]

# Healthy account contacts
HEALTHY_CONTACTS = {
    "ACC-009": ("Sarah", "Sarah Kim (Operations Lead)"),
    "ACC-010": ("David", "David Park (Content Director)"),
    "ACC-011": ("Emily", "Emily Watson (VP Technology)"),
    "ACC-012": ("James", "James Cooper (Marketing Director)"),
    "ACC-013": ("Lisa", "Lisa Nakamura (Managing Director)"),
    "ACC-014": ("Carlos", "Carlos Ruiz (Creative Director)"),
    "ACC-019": ("Michelle", "Michelle Torres (Marketing Manager)"),
    "ACC-020": ("Brian", "Brian Foster (Data Team Lead)"),
}


def _fill_healthy_transcript(template_tuple, acct):
    call_type, dur_range, transcript, attendees = template_tuple
    csm = acct["csm"]
    contact_short, contact_full = HEALTHY_CONTACTS.get(acct["account_id"], ("Contact", "Contact Person (Manager)"))
    product = random.choice(acct["products"])
    t = transcript.replace("{csm}", csm).replace("{contact_full}", contact_full).replace("{contact}", contact_short).replace("{product}", product)
    a = attendees.replace("{csm}", csm).replace("{contact_full}", contact_full)
    return call_type, dur_range, t, a


# Map account_id -> list of transcript tuples
GONG_POOLS = {
    "ACC-001": GONG_TRANSCRIPTS_MERIDIAN,
    "ACC-002": GONG_TRANSCRIPTS_CASCADE,
    "ACC-003": GONG_TRANSCRIPTS_BEACON,
    "ACC-004": GONG_TRANSCRIPTS_PRISM,
    "ACC-005": GONG_TRANSCRIPTS_ATLAS,
    "ACC-006": GONG_TRANSCRIPTS_SUMMIT,
    "ACC-007": GONG_TRANSCRIPTS_VOYAGER,
    "ACC-008": GONG_TRANSCRIPTS_IRONCLAD,
    "ACC-015": GONG_TRANSCRIPTS_COBALT,
    "ACC-016": GONG_TRANSCRIPTS_DRIFTWOOD,
    "ACC-017": GONG_TRANSCRIPTS_EVERGREEN,
    "ACC-018": GONG_TRANSCRIPTS_FLUX,
}

# Desired call counts per account
GONG_COUNTS = {
    "ACC-001": 12, "ACC-002": 10, "ACC-003": 10, "ACC-004": 5,
    "ACC-005": 12, "ACC-006": 12, "ACC-007": 8, "ACC-008": 8,
    "ACC-009": 7, "ACC-010": 6, "ACC-011": 7, "ACC-012": 6,
    "ACC-013": 5, "ACC-014": 6,
    "ACC-015": 10, "ACC-016": 7, "ACC-017": 8, "ACC-018": 8,
    "ACC-019": 5, "ACC-020": 5,
}


def generate_gong_transcripts():
    calls = []
    cid = 1

    for acct in ACCOUNTS:
        aid = acct["account_id"]
        n = GONG_COUNTS.get(aid, 5)
        csm = acct["csm"]

        # Get transcript pool
        if aid in GONG_POOLS:
            pool = GONG_POOLS[aid]
        else:
            pool = None  # use healthy pool

        for i in range(n):
            dt = random_date()
            hour = random.choice([9, 10, 11, 13, 14, 15, 16])
            call_dt = dt.replace(hour=hour, minute=random.choice([0, 15, 30]))

            if pool:
                tmpl = pool[i % len(pool)]
                call_type, dur_range, transcript, attendees = tmpl
                transcript = transcript.replace("{csm}", csm)
                attendees = attendees.replace("{csm}", csm)
            else:
                tmpl = GONG_TRANSCRIPTS_HEALTHY[i % len(GONG_TRANSCRIPTS_HEALTHY)]
                call_type, dur_range, transcript, attendees = _fill_healthy_transcript(tmpl, acct)

            duration = random.randint(dur_range[0], dur_range[1])

            calls.append({
                "call_id": f"CALL-{cid:04d}",
                "account_id": aid,
                "account_name": acct["account_name"],
                "call_date": datetime_str(call_dt),
                "call_type": call_type,
                "duration_min": duration,
                "transcript_excerpt": transcript.strip(),
                "attendees": attendees.strip(),
            })
            cid += 1

    return calls


# ---------------------------------------------------------------------------
# Write accounts CSV
# ---------------------------------------------------------------------------
NPS_SCORES = {
    "churn_risk": [2, 3, 4, 3],
    "expansion": [9, 10, 9, 8],
    "healthy": [7, 8, 7, 8, 9, 7, 8, 7],
    "attention": [5, 4, 6, 5],
}
HEALTH_STATUS_MAP = {"churn_risk": "at_risk", "expansion": "expansion", "healthy": "healthy", "attention": "attention"}

def _get_current_ae(account_id):
    assignments = ACCOUNT_ASSIGNMENT_HISTORY.get(account_id, [])
    for emp_id, emp_name, role, assigned, unassigned in reversed(assignments):
        if role == "AE" and unassigned == "":
            return emp_name
    return ""

def write_accounts_csv():
    path = os.path.join(SEED_DIR, "accounts.csv")
    fields = ["account_id", "account_name", "industry", "arr", "licensed_seats",
              "products", "contract_renewal_date", "csm_name", "primary_ae",
              "health_status", "nps_score"]
    rows = []
    cat_idx = {}
    for a in ACCOUNTS:
        cat = a["category"]
        idx = cat_idx.get(cat, 0)
        nps_list = NPS_SCORES[cat]
        nps = nps_list[idx % len(nps_list)]
        cat_idx[cat] = idx + 1
        rows.append({
            "account_id": a["account_id"],
            "account_name": a["account_name"],
            "industry": a["industry"],
            "arr": a["arr"],
            "licensed_seats": a["licensed_seats"],
            "products": ", ".join(a["products"]),
            "contract_renewal_date": a["contract_renewal_date"],
            "csm_name": a["csm"],
            "primary_ae": _get_current_ae(a["account_id"]),
            "health_status": HEALTH_STATUS_MAP[a["category"]],
            "nps_score": nps,
        })
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return len(rows), path


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------
EMPLOYEES = [
    # CSMs
    dict(employee_id="EMP-001", name="Sarah Chen", title="Senior Customer Success Manager", role="CSM", department="Customer Success", hire_date="2023-03-15", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-002", name="Marcus Rivera", title="Customer Success Manager", role="CSM", department="Customer Success", hire_date="2023-08-01", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-003", name="Emily Thornton", title="Senior Customer Success Manager", role="CSM", department="Customer Success", hire_date="2022-11-10", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-004", name="James Okafor", title="Customer Success Manager", role="CSM", department="Customer Success", hire_date="2024-02-20", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-005", name="Rachel Goldstein", title="Customer Success Manager", role="CSM", department="Customer Success", hire_date="2024-06-01", departure_date="", departure_reason="", status="active"),
    # AEs
    dict(employee_id="EMP-006", name="Jake Torres", title="Senior Account Executive", role="AE", department="Sales", hire_date="2022-05-01", departure_date="2026-01-15", departure_reason="resigned", status="departed"),
    dict(employee_id="EMP-007", name="Lisa Patel", title="Account Executive", role="AE", department="Sales", hire_date="2024-01-10", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-008", name="Ryan Nakamura", title="Senior Account Executive", role="AE", department="Sales", hire_date="2023-04-15", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-009", name="Diana Osei", title="Account Executive", role="AE", department="Sales", hire_date="2023-09-01", departure_date="2026-02-01", departure_reason="parental_leave", status="on_leave"),
    dict(employee_id="EMP-010", name="Kevin McBride", title="Account Executive", role="AE", department="Sales", hire_date="2025-11-03", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-011", name="Priya Sharma", title="Senior Account Executive", role="AE", department="Sales", hire_date="2022-08-15", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-012", name="Tom Westfield", title="Account Executive", role="AE", department="Sales", hire_date="2024-03-20", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-013", name="Maria Santos", title="Account Executive", role="AE", department="Sales", hire_date="2024-07-01", departure_date="", departure_reason="", status="active"),
    # SEs
    dict(employee_id="EMP-014", name="Alex Kim", title="Solutions Engineer", role="SE", department="Solutions Engineering", hire_date="2023-06-01", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-015", name="Jordan Blake", title="Senior Solutions Engineer", role="SE", department="Solutions Engineering", hire_date="2022-09-15", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-016", name="Nina Vasquez", title="Solutions Engineer", role="SE", department="Solutions Engineering", hire_date="2024-04-10", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-017", name="Chris Langford", title="Solutions Engineer", role="SE", department="Solutions Engineering", hire_date="2024-09-01", departure_date="", departure_reason="", status="active"),
    # Managers
    dict(employee_id="EMP-018", name="Patricia Huang", title="VP of Customer Success", role="Manager", department="Customer Success", hire_date="2021-06-01", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-019", name="Michael Reeves", title="VP of Sales", role="Manager", department="Sales", hire_date="2021-03-15", departure_date="", departure_reason="", status="active"),
    dict(employee_id="EMP-020", name="Sandra Liu", title="Director of Solutions Engineering", role="Manager", department="Solutions Engineering", hire_date="2022-01-10", departure_date="", departure_reason="", status="active"),
]

# AE assignments per account (current AE employee_id)
# Maps account_id -> list of (employee_id, employee_name, role, assigned_date, unassigned_date)
ACCOUNT_ASSIGNMENT_HISTORY = {
    # CHURN RISK
    "ACC-001": [  # Meridian — Jake left Jan 15, 3-week gap, Lisa assigned Feb 5
        ("EMP-006", "Jake Torres", "AE", "2025-06-01", "2026-01-15"),
        ("EMP-007", "Lisa Patel", "AE", "2026-02-05", ""),
        ("EMP-001", "Sarah Chen", "CSM", "2025-06-01", ""),
    ],
    "ACC-002": [  # Cascade — stable AE (Ryan), CSM (Marcus)
        ("EMP-008", "Ryan Nakamura", "AE", "2025-04-01", ""),
        ("EMP-002", "Marcus Rivera", "CSM", "2025-04-01", ""),
    ],
    "ACC-003": [  # Beacon — Jake left Jan 15, Kevin (junior) assigned immediately
        ("EMP-006", "Jake Torres", "AE", "2025-03-15", "2026-01-15"),
        ("EMP-010", "Kevin McBride", "AE", "2026-01-16", ""),
        ("EMP-003", "Emily Thornton", "CSM", "2025-03-15", ""),
    ],
    "ACC-004": [  # Prism — stable but neglected (Maria Santos, junior)
        ("EMP-013", "Maria Santos", "AE", "2025-07-01", ""),
        ("EMP-004", "James Okafor", "CSM", "2025-07-01", ""),
    ],
    # EXPANSION
    "ACC-005": [  # Atlas — stable, senior AE (Priya)
        ("EMP-011", "Priya Sharma", "AE", "2025-01-15", ""),
        ("EMP-005", "Rachel Goldstein", "CSM", "2025-01-15", ""),
    ],
    "ACC-006": [  # Summit — stable (Ryan)
        ("EMP-008", "Ryan Nakamura", "AE", "2025-09-01", ""),
        ("EMP-001", "Sarah Chen", "CSM", "2025-09-01", ""),
    ],
    "ACC-007": [  # Voyager — stable, senior AE (Priya)
        ("EMP-011", "Priya Sharma", "AE", "2024-06-01", ""),
        ("EMP-002", "Marcus Rivera", "CSM", "2024-06-01", ""),
    ],
    "ACC-008": [  # Ironclad — stable (Lisa)
        ("EMP-007", "Lisa Patel", "AE", "2025-05-01", ""),
        ("EMP-003", "Emily Thornton", "CSM", "2025-05-01", ""),
    ],
    # HEALTHY
    "ACC-009": [("EMP-008", "Ryan Nakamura", "AE", "2025-02-01", ""), ("EMP-004", "James Okafor", "CSM", "2025-02-01", "")],
    "ACC-010": [("EMP-011", "Priya Sharma", "AE", "2025-03-01", ""), ("EMP-005", "Rachel Goldstein", "CSM", "2025-03-01", "")],
    "ACC-011": [("EMP-013", "Maria Santos", "AE", "2025-01-15", ""), ("EMP-001", "Sarah Chen", "CSM", "2025-01-15", "")],
    "ACC-012": [("EMP-007", "Lisa Patel", "AE", "2025-06-01", ""), ("EMP-002", "Marcus Rivera", "CSM", "2025-06-01", "")],
    "ACC-013": [("EMP-012", "Tom Westfield", "AE", "2025-04-01", ""), ("EMP-003", "Emily Thornton", "CSM", "2025-04-01", "")],
    "ACC-014": [("EMP-008", "Ryan Nakamura", "AE", "2025-05-01", ""), ("EMP-004", "James Okafor", "CSM", "2025-05-01", "")],
    "ACC-019": [("EMP-013", "Maria Santos", "AE", "2025-07-01", ""), ("EMP-004", "James Okafor", "CSM", "2025-07-01", "")],
    "ACC-020": [("EMP-011", "Priya Sharma", "AE", "2025-08-01", ""), ("EMP-005", "Rachel Goldstein", "CSM", "2025-08-01", "")],
    # ATTENTION
    "ACC-015": [  # Cobalt — stable (Lisa)
        ("EMP-007", "Lisa Patel", "AE", "2025-08-01", ""),
        ("EMP-005", "Rachel Goldstein", "CSM", "2025-08-01", ""),
    ],
    "ACC-016": [  # Driftwood — Diana went on leave, Tom took over (overloaded)
        ("EMP-009", "Diana Osei", "AE", "2025-04-01", "2026-02-01"),
        ("EMP-012", "Tom Westfield", "AE", "2026-02-01", ""),
        ("EMP-001", "Sarah Chen", "CSM", "2025-04-01", ""),
    ],
    "ACC-017": [  # Evergreen — Diana went on leave, Tom took over
        ("EMP-009", "Diana Osei", "AE", "2025-05-01", "2026-02-01"),
        ("EMP-012", "Tom Westfield", "AE", "2026-02-01", ""),
        ("EMP-002", "Marcus Rivera", "CSM", "2025-05-01", ""),
    ],
    "ACC-018": [  # Flux — stable (Priya)
        ("EMP-011", "Priya Sharma", "AE", "2025-02-01", ""),
        ("EMP-003", "Emily Thornton", "CSM", "2025-02-01", ""),
    ],
}

def generate_employees():
    return EMPLOYEES

def generate_account_assignments():
    rows = []
    aid = 1
    for acct_id, assignments in ACCOUNT_ASSIGNMENT_HISTORY.items():
        acct = next(a for a in ACCOUNTS if a["account_id"] == acct_id)
        for emp_id, emp_name, role, assigned, unassigned in assignments:
            rows.append({
                "assignment_id": f"ASSIGN-{aid:03d}",
                "account_id": acct_id,
                "account_name": acct["account_name"],
                "employee_id": emp_id,
                "employee_name": emp_name,
                "role": role,
                "assigned_date": assigned,
                "unassigned_date": unassigned,
                "is_current": "TRUE" if unassigned == "" else "FALSE",
            })
            aid += 1
    return rows

# ---------------------------------------------------------------------------
# Opportunities
# ---------------------------------------------------------------------------
OPPORTUNITIES = [
    # CHURN RISK — renewals at risk
    dict(opportunity_id="OPP-001", account_id="ACC-001", account_name="Meridian Media Group",
         opp_type="renewal", opp_name="Meridian Media FY26 Renewal",
         amount=186000, stage="negotiation", close_date="2026-06-15",
         owner_id="EMP-007", owner_name="Lisa Patel", created_date="2026-01-20",
         notes="Customer requested competitive pricing after champion Jennifer Park left. New AE Lisa Patel assigned Feb 5 after 3-week gap following Jake Torres departure. VP of Marketing David Leung evaluating SketchFlow. Usage down 40%."),
    dict(opportunity_id="OPP-002", account_id="ACC-002", account_name="Cascade Financial",
         opp_type="renewal", opp_name="Cascade Financial FY26 Renewal",
         amount=312000, stage="qualified", close_date="2026-05-01",
         owner_id="EMP-008", owner_name="Ryan Nakamura", created_date="2025-12-01",
         notes="CFO Margaret Chen reviewing all SaaS spend. Canvas and Insight adoption critically low — only Flow is used. Risk of partial churn (downgrade to Flow-only). $312K at stake but likely $200K+ at risk."),
    dict(opportunity_id="OPP-003", account_id="ACC-003", account_name="Beacon Logistics",
         opp_type="renewal", opp_name="Beacon Logistics FY26 Renewal",
         amount=97000, stage="qualified", close_date="2026-07-20",
         owner_id="EMP-010", owner_name="Kevin McBride", created_date="2026-02-01",
         notes="API reliability issues damaged trust. VP of Operations demanding SLA credits. Junior AE Kevin McBride (2 months tenure) handling — may need senior support. Legal team CC'd on last escalation."),
    dict(opportunity_id="OPP-004", account_id="ACC-004", account_name="Prism Retail",
         opp_type="renewal", opp_name="Prism Retail FY26 Renewal",
         amount=54000, stage="negotiation", close_date="2026-04-10",
         owner_id="EMP-013", owner_name="Maria Santos", created_date="2025-11-15",
         notes="Silent churn risk. Usage declining steadily for 3 months. No support tickets filed. Last Gong call was short and disengaged. Admin who set up account has left. Renewal in 4 weeks — may not renew."),
    # EXPANSION
    dict(opportunity_id="OPP-005", account_id="ACC-005", account_name="Atlas Digital",
         opp_type="expansion", opp_name="Atlas Digital — Flow Add-on",
         amount=95000, stage="proposal", close_date="2026-06-30",
         owner_id="EMP-011", owner_name="Priya Sharma", created_date="2026-02-15",
         notes="Strong champion Raj Patel (Head of Creative) asked about Flow pricing in last QBR. Team growing 15% MoM. $95K proposal for Flow licenses + onboarding. Demo went well — VP of Marketing was in the room and asked good questions."),
    dict(opportunity_id="OPP-006", account_id="ACC-006", account_name="Summit Healthcare",
         opp_type="expansion", opp_name="Summit Healthcare — 20 Seat Expansion",
         amount=72000, stage="prospect", close_date="2026-08-01",
         owner_id="EMP-008", owner_name="Ryan Nakamura", created_date="2026-03-01",
         notes="Org growing rapidly. Champion Dr. Amanda Foster evangelizing internally — brought in 3 new departments. 90% seat utilization at week 6. Regulatory affairs and clinical ops want access. Likely 20 additional seats."),
    dict(opportunity_id="OPP-007", account_id="ACC-007", account_name="Voyager Entertainment",
         opp_type="expansion", opp_name="Voyager Entertainment — New Division (50 seats)",
         amount=180000, stage="qualified", close_date="2026-07-01",
         owner_id="EMP-011", owner_name="Priya Sharma", created_date="2026-02-01",
         notes="VP of Marketing Christina Wells discussed adding 50 seats for new streaming division launching April. Currently at 120 seats, 95%+ utilization. Self-sufficient account — zero support tickets. $180K expansion."),
    dict(opportunity_id="OPP-008", account_id="ACC-008", account_name="Ironclad Manufacturing",
         opp_type="expansion", opp_name="Ironclad Manufacturing — Insight Add-on",
         amount=55000, stage="prospect", close_date="2026-09-01",
         owner_id="EMP-007", owner_name="Lisa Patel", created_date="2026-03-05",
         notes="Manufacturing team asked if Insight can connect to their Snowflake warehouse for template usage analytics. Canvas usage growing steadily. Clear cross-sell opportunity for Insight. Engineering team building SAP integration — high engagement."),
    # HEALTHY — renewals on track
    dict(opportunity_id="OPP-009", account_id="ACC-009", account_name="Northstar Consulting",
         opp_type="renewal", opp_name="Northstar Consulting FY27 Renewal",
         amount=165000, stage="closed_won", close_date="2025-12-01",
         owner_id="EMP-008", owner_name="Ryan Nakamura", created_date="2025-09-01",
         notes="Smooth renewal. Multi-year deal signed. Stable usage, satisfied customer."),
    dict(opportunity_id="OPP-010", account_id="ACC-010", account_name="Ridgeline Media",
         opp_type="renewal", opp_name="Ridgeline Media FY26 Renewal",
         amount=138000, stage="negotiation", close_date="2026-07-15",
         owner_id="EMP-011", owner_name="Priya Sharma", created_date="2026-03-01",
         notes="Standard renewal. Flow power user. No concerns."),
    dict(opportunity_id="OPP-011", account_id="ACC-011", account_name="Clearwater Tech",
         opp_type="renewal", opp_name="Clearwater Tech FY26 Renewal",
         amount=275000, stage="negotiation", close_date="2026-09-01",
         owner_id="EMP-013", owner_name="Maria Santos", created_date="2026-05-01",
         notes="Large account, all 3 products. Moderate but consistent usage. Expect smooth renewal."),
    dict(opportunity_id="OPP-012", account_id="ACC-012", account_name="Horizon Pharma",
         opp_type="renewal", opp_name="Horizon Pharma FY26 Renewal",
         amount=198000, stage="qualified", close_date="2026-06-30",
         owner_id="EMP-007", owner_name="Lisa Patel", created_date="2026-02-15",
         notes="Seasonal usage patterns but overall healthy. Campaign season Jan-Feb drove high engagement."),
    dict(opportunity_id="OPP-013", account_id="ACC-013", account_name="Sterling Partners",
         opp_type="renewal", opp_name="Sterling Partners FY26 Renewal",
         amount=62000, stage="closed_won", close_date="2026-02-15",
         owner_id="EMP-012", owner_name="Tom Westfield", created_date="2025-11-01",
         notes="Small but loyal. Renewed early. High NPS."),
    dict(opportunity_id="OPP-014", account_id="ACC-014", account_name="Apex Marketing",
         opp_type="renewal", opp_name="Apex Marketing FY26 Renewal",
         amount=124000, stage="negotiation", close_date="2026-11-01",
         owner_id="EMP-008", owner_name="Ryan Nakamura", created_date="2026-07-01",
         notes="Slowly growing. No concerns. Possible upsell conversation later in year."),
    # ATTENTION
    dict(opportunity_id="OPP-015", account_id="ACC-015", account_name="Cobalt Aerospace",
         opp_type="renewal", opp_name="Cobalt Aerospace FY26 Renewal",
         amount=210000, stage="qualified", close_date="2026-10-01",
         owner_id="EMP-007", owner_name="Lisa Patel", created_date="2026-06-01",
         notes="Onboarding stalled at week 4. Low adoption despite large seat count. IT Director Richard Torres frustrated. Need solutions engineer engagement."),
    dict(opportunity_id="OPP-016", account_id="ACC-016", account_name="Driftwood Media",
         opp_type="renewal", opp_name="Driftwood Media FY26 Renewal",
         amount=88000, stage="qualified", close_date="2026-07-01",
         owner_id="EMP-012", owner_name="Tom Westfield", created_date="2026-03-01",
         notes="Admin change (Mark Torres left). New admin Yuki Tanaka ramping up. AE change too (Diana on leave, Tom covering). Usage dipped but recovering. Monitor."),
    dict(opportunity_id="OPP-017", account_id="ACC-017", account_name="Evergreen Education",
         opp_type="renewal", opp_name="Evergreen Education FY26 Renewal",
         amount=73000, stage="qualified", close_date="2026-05-15",
         owner_id="EMP-012", owner_name="Tom Westfield", created_date="2026-01-15",
         notes="Budget pressure from board. CFO cutting tools below 70% utilization. Usage is actually fine but renewal conversation will be cost-focused. AE change (Diana on leave, Tom covering) adds risk."),
    dict(opportunity_id="OPP-018", account_id="ACC-018", account_name="Flux Dynamics",
         opp_type="renewal", opp_name="Flux Dynamics FY26 Renewal",
         amount=156000, stage="negotiation", close_date="2026-09-15",
         owner_id="EMP-011", owner_name="Priya Sharma", created_date="2026-05-01",
         notes="Heavy API user hit rate limits. Filed angry tickets but usage is still very high. Technical resolution needed, not a churn risk. Engineering team engaged."),
    # Remaining healthy
    dict(opportunity_id="OPP-019", account_id="ACC-019", account_name="Pinnacle Sports",
         opp_type="renewal", opp_name="Pinnacle Sports FY26 Renewal",
         amount=92000, stage="qualified", close_date="2026-08-30",
         owner_id="EMP-013", owner_name="Maria Santos", created_date="2026-05-01",
         notes="Stable account. Steady usage. No issues."),
    dict(opportunity_id="OPP-020", account_id="ACC-020", account_name="Crestline Analytics",
         opp_type="renewal", opp_name="Crestline Analytics FY26 Renewal",
         amount=172000, stage="negotiation", close_date="2026-10-15",
         owner_id="EMP-011", owner_name="Priya Sharma", created_date="2026-06-01",
         notes="Flow + Insight user. Steady engagement. Standard renewal expected."),
    # Historical closed_lost — churned account from 6 months ago
    dict(opportunity_id="OPP-021", account_id="ACC-999", account_name="TerraFirm Industries",
         opp_type="renewal", opp_name="TerraFirm Industries FY25 Renewal",
         amount=134000, stage="closed_lost", close_date="2025-09-15",
         owner_id="EMP-006", owner_name="Jake Torres", created_date="2025-06-01",
         notes="Lost to SketchFlow. Champion left, replacement chose competitor. Usage declined over 3 months before renewal. Pattern similar to current Meridian situation. Jake Torres was AE — second account lost under similar circumstances before his resignation."),
]

def generate_opportunities():
    return OPPORTUNITIES


# ---------------------------------------------------------------------------
# Feature Usage — granular feature-level adoption per account
# ---------------------------------------------------------------------------
FEATURES = {
    "Canvas": ["canvas_export", "canvas_collab_edit", "canvas_templates", "canvas_layers",
               "canvas_asset_library", "canvas_brand_kit", "canvas_comments", "canvas_version_history"],
    "Flow": ["flow_approvals", "flow_webhooks", "flow_conditional_routing", "flow_scheduled_tasks",
             "flow_integrations", "flow_audit_trail"],
    "Insight": ["insight_dashboards", "insight_api", "insight_scheduled_reports",
                "insight_data_connectors", "insight_embedded_analytics"],
}

# Feature adoption profiles per account story
# (features_used_fraction, power_features) — power features are sticky features that correlate with retention
FEATURE_PROFILES = {
    # Churn risk — low feature breadth, dropped power features
    "ACC-001": {"breadth": 0.3, "power_features": ["canvas_export"], "declining": True},  # Meridian: was broad, narrowed
    "ACC-002": {"breadth": 0.15, "power_features": [], "declining": False},  # Cascade: only Flow features used
    "ACC-003": {"breadth": 0.4, "power_features": ["insight_api"], "declining": True},  # Beacon: API heavy, dropped other features
    "ACC-004": {"breadth": 0.15, "power_features": [], "declining": True},  # Prism: barely using anything
    # Expansion — broad feature adoption, using power features
    "ACC-005": {"breadth": 0.85, "power_features": ["canvas_collab_edit", "canvas_templates", "canvas_brand_kit"], "declining": False},
    "ACC-006": {"breadth": 0.75, "power_features": ["canvas_templates", "flow_approvals", "flow_conditional_routing"], "declining": False},
    "ACC-007": {"breadth": 0.95, "power_features": ["canvas_collab_edit", "canvas_templates", "flow_approvals", "insight_dashboards", "insight_api"], "declining": False},
    "ACC-008": {"breadth": 0.6, "power_features": ["canvas_templates", "canvas_export"], "declining": False},
    # Healthy — moderate breadth, stable
    "ACC-009": {"breadth": 0.6, "power_features": ["canvas_templates", "flow_approvals"], "declining": False},
    "ACC-010": {"breadth": 0.5, "power_features": ["flow_approvals", "flow_webhooks"], "declining": False},
    "ACC-011": {"breadth": 0.7, "power_features": ["canvas_collab_edit", "flow_approvals", "insight_dashboards"], "declining": False},
    "ACC-012": {"breadth": 0.55, "power_features": ["canvas_templates"], "declining": False},
    "ACC-013": {"breadth": 0.45, "power_features": ["canvas_export", "insight_dashboards"], "declining": False},
    "ACC-014": {"breadth": 0.6, "power_features": ["canvas_templates", "flow_approvals"], "declining": False},
    # Attention — mixed
    "ACC-015": {"breadth": 0.2, "power_features": [], "declining": False},  # Cobalt: onboarding stalled, barely exploring
    "ACC-016": {"breadth": 0.45, "power_features": ["canvas_templates"], "declining": False},
    "ACC-017": {"breadth": 0.55, "power_features": ["canvas_templates"], "declining": False},  # Evergreen: good feature use despite budget pressure
    "ACC-018": {"breadth": 0.7, "power_features": ["flow_webhooks", "flow_integrations", "insight_api"], "declining": False},
    "ACC-019": {"breadth": 0.5, "power_features": ["canvas_templates", "flow_approvals"], "declining": False},
    "ACC-020": {"breadth": 0.6, "power_features": ["flow_approvals", "insight_dashboards"], "declining": False},
}

def generate_feature_usage():
    rows = []
    fid = 1
    for acct in ACCOUNTS:
        aid = acct["account_id"]
        profile = FEATURE_PROFILES.get(aid, {"breadth": 0.5, "power_features": [], "declining": False})
        products = acct["products"]
        pool = USER_POOLS[aid]

        # Build feature list for this account's products
        available_features = []
        for p in products:
            available_features.extend(FEATURES.get(p, []))

        # Select features based on breadth
        n_features = max(1, int(len(available_features) * profile["breadth"]))
        # Always include power features
        used_features = list(set(profile["power_features"]) & set(available_features))
        remaining = [f for f in available_features if f not in used_features]
        random.shuffle(remaining)
        used_features.extend(remaining[:n_features - len(used_features)])

        for feature in used_features:
            # Generate weekly usage over 13 weeks
            for week in range(13):
                week_start = START_DATE + timedelta(weeks=week)
                # Usage count varies by feature and account health
                base_count = random.randint(3, 25)
                if feature in profile["power_features"]:
                    base_count = int(base_count * 1.8)

                # Apply declining trend for churn accounts
                if profile["declining"] and week > 5:
                    base_count = max(0, int(base_count * (1 - (week - 5) * 0.12)))

                if base_count == 0:
                    continue

                n_users = max(1, min(len(pool), int(base_count * 0.3)))
                active_users = random.sample(pool, n_users)

                for user in active_users:
                    usage_count = max(1, int(base_count / n_users + random.gauss(0, 2)))
                    rows.append({
                        "feature_usage_id": f"FU-{fid:06d}",
                        "account_id": aid,
                        "account_name": acct["account_name"],
                        "user_id": user,
                        "feature_name": feature,
                        "usage_count": usage_count,
                        "usage_week": date_str(week_start),
                    })
                    fid += 1
    return rows


# ---------------------------------------------------------------------------
# Invoices / Discount History
# ---------------------------------------------------------------------------
INVOICES = []
_inv_id = 1
for acct in ACCOUNTS:
    aid = acct["account_id"]
    arr = acct["arr"]
    quarterly_amount = arr / 4

    # Discount and payment patterns per account story
    if acct["story"] == "usage_crater":  # Meridian — got 30% discount, now churning
        discounts = [30, 30, 30, 30]
        days_to_pay = [15, 18, 35, None]  # Last invoice overdue
        statuses = ["paid", "paid", "paid", "overdue"]
    elif acct["story"] == "partial_adoption":  # Cascade — pays late
        discounts = [15, 15, 15, 15]
        days_to_pay = [42, 38, 45, 51]
        statuses = ["paid", "paid", "paid", "paid"]
    elif acct["story"] == "sudden_cliff":  # Beacon — standard terms
        discounts = [10, 10, 10, 10]
        days_to_pay = [20, 22, 18, None]
        statuses = ["paid", "paid", "paid", "overdue"]
    elif acct["story"] == "silent_decline":  # Prism — last invoice 45 days overdue
        discounts = [0, 0, 0, 0]
        days_to_pay = [25, 30, None, None]
        statuses = ["paid", "paid", "overdue", "overdue"]
    elif acct["story"] == "growing_fast":  # Atlas — perfect payer, no discount
        discounts = [0, 0, 0, 0]
        days_to_pay = [8, 7, 10, 9]
        statuses = ["paid", "paid", "paid", "paid"]
    elif acct["story"] == "fast_ramp":  # Summit — small discount, good payer
        discounts = [5, 5, 5, 5]
        days_to_pay = [12, 10, 14, 11]
        statuses = ["paid", "paid", "paid", "paid"]
    elif acct["story"] == "stable_high":  # Voyager — volume discount, perfect payer
        discounts = [20, 20, 20, 20]
        days_to_pay = [5, 7, 6, 8]
        statuses = ["paid", "paid", "paid", "paid"]
    elif acct["story"] == "budget_pressure":  # Evergreen — discount, slowing payment
        discounts = [35, 35, 35, 35]
        days_to_pay = [20, 28, 35, 42]
        statuses = ["paid", "paid", "paid", "paid"]
    else:  # Healthy/attention defaults
        discounts = [random.choice([0, 5, 10])] * 4
        days_to_pay = [random.randint(10, 30) for _ in range(4)]
        statuses = ["paid"] * 4

    quarters = [
        ("2025-07-01", "Q3 2025"), ("2025-10-01", "Q4 2025"),
        ("2026-01-01", "Q1 2026"), ("2026-03-15", "Q2 2026"),
    ]
    for i, (inv_date, quarter) in enumerate(quarters):
        disc = discounts[i] if i < len(discounts) else 0
        amount = round(quarterly_amount * (1 - disc / 100), 2)
        dtp = days_to_pay[i] if i < len(days_to_pay) else random.randint(15, 30)
        status = statuses[i] if i < len(statuses) else "paid"
        INVOICES.append({
            "invoice_id": f"INV-{_inv_id:04d}",
            "account_id": aid,
            "account_name": acct["account_name"],
            "invoice_date": inv_date,
            "quarter": quarter,
            "gross_amount": round(quarterly_amount, 2),
            "discount_pct": disc,
            "net_amount": amount,
            "payment_status": status,
            "days_to_pay": dtp if status == "paid" else "",
        })
        _inv_id += 1

def generate_invoices():
    return INVOICES


# ---------------------------------------------------------------------------
# CSM Internal Notes — early warning flags, meeting notes, escalations
# ---------------------------------------------------------------------------
CSM_NOTES = [
    # =========================================================================
    # CHURN RISK — Meridian Media Group (ACC-001) — 7 notes
    # =========================================================================
    dict(note_id="NOTE-001", account_id="ACC-001", account_name="Meridian Media Group",
         author="Sarah Chen", created_date="2026-01-05", note_type="risk_flag",
         note_text="Early warning on Meridian. Jennifer Park (our primary champion and the person who drove the original Canvas rollout) just gave notice. She's leaving for a competitor. Derek Huang will take over day-to-day but he doesn't have Jennifer's internal influence. Usage is still strong right now but I'm worried about what happens when she's gone. We should proactively identify a new executive sponsor."),
    dict(note_id="NOTE-002", account_id="ACC-001", account_name="Meridian Media Group",
         author="Sarah Chen", created_date="2026-01-18", note_type="risk_flag",
         note_text="Flagging Meridian as at-risk. Jennifer Park left the company two weeks ago. Usage has already started to drop — from 38 active users to 28 in two weeks. Derek Huang is trying to hold things together but he doesn't have Jennifer's influence. We need to identify a new champion ASAP or this account is in trouble. ARR: $186K, renewal June 15."),
    dict(note_id="NOTE-003", account_id="ACC-001", account_name="Meridian Media Group",
         author="Sarah Chen", created_date="2026-02-03", note_type="escalation",
         note_text="Escalation: Meridian has been without an AE for 3 weeks since Jake Torres left. I've raised this twice and it keeps falling through the cracks. Meanwhile, Derek told me the team is piloting SketchFlow. We are losing this account in slow motion. Requesting immediate AE assignment and executive sponsor engagement."),
    dict(note_id="NOTE-004", account_id="ACC-001", account_name="Meridian Media Group",
         author="Sarah Chen", created_date="2026-02-12", note_type="check_in",
         note_text="Spoke with Derek informally. He mentioned that Laura Singh (VP Creative) has been asking pointed questions about Canvas ROI in their weekly leadership meetings. Derek said Laura pulled up the SketchFlow pricing page during one of those meetings and shared it on screen. This feels like the beginning of a formal evaluation. We have maybe 30 days to change the narrative."),
    dict(note_id="NOTE-005", account_id="ACC-001", account_name="Meridian Media Group",
         author="Sarah Chen", created_date="2026-02-20", note_type="meeting_summary",
         note_text="Met with Derek and Laura Singh (VP Creative). Lisa Patel joined as new AE. Laura was direct — they're comparing us to SketchFlow on price ($186K vs ~$40K) and considering migrating. I presented the collaboration features and Lisa offered a pricing restructure. Laura agreed to give us 60 days. This is saveable but we need to execute flawlessly."),
    dict(note_id="NOTE-006", account_id="ACC-001", account_name="Meridian Media Group",
         author="Lisa Patel", created_date="2026-03-05", note_type="risk_flag",
         note_text="Update on Meridian: Usage still declining despite re-onboarding efforts. Only 5 active users this week, down from 14 at the start of the 60-day window. Derek says the SketchFlow pilot is going well. I think we have 30 days left before Laura makes a final decision. Recommending executive-level intervention — our VP of Sales should reach out to their VP of Marketing directly."),
    dict(note_id="NOTE-007", account_id="ACC-001", account_name="Meridian Media Group",
         author="Sarah Chen", created_date="2026-03-10", note_type="escalation",
         note_text="Final escalation on Meridian. David Leung (VP Marketing) has requested a full asset export from Canvas — this is usually the last step before migration. Lisa Patel is trying to get an executive meeting but David isn't responding. I've asked our VP of Sales to reach out peer-to-peer. If we don't get a meeting in the next 2 weeks, this account is lost. $186K ARR at stake."),

    # =========================================================================
    # CHURN RISK — Cascade Financial (ACC-002) — 5 notes
    # =========================================================================
    dict(note_id="NOTE-008", account_id="ACC-002", account_name="Cascade Financial",
         author="Marcus Rivera", created_date="2025-12-20", note_type="check_in",
         note_text="Routine check-in with Cascade Financial. Michael Chen mentioned that their team tried Canvas again after the Q4 onboarding push. Three designers spent a day with it and went back to PowerPoint. The issue isn't feature gaps — it's that the onboarding assumes creative agency workflows. Financial services teams make pitch decks and regulatory docs, not design assets. We need industry-specific templates."),
    dict(note_id="NOTE-009", account_id="ACC-002", account_name="Cascade Financial",
         author="Marcus Rivera", created_date="2026-01-15", note_type="risk_flag",
         note_text="Cascade Financial is a split story. Flow adoption is excellent (72 of 80 seats). Canvas and Insight are shelfware. Michael Chen (Dir of Ops) told me directly they're considering dropping Canvas and Insight at renewal, keeping only Flow. That would take them from $312K to ~$110K ARR. We need a Canvas-specific rescue plan for financial services use cases."),
    dict(note_id="NOTE-010", account_id="ACC-002", account_name="Cascade Financial",
         author="Marcus Rivera", created_date="2026-02-05", note_type="risk_flag",
         note_text="Cascade update: CFO Margaret Chen has started a formal SaaS spend review. Every tool under 50% utilization is on the chopping block. Canvas is at roughly 8% utilization (6 of 80 seats). Insight is at 12%. Flow is safe at 90%. Michael Chen asked me for a usage report he can present to Margaret — I think he's trying to help us, but the numbers are bad. Renewal is May 1."),
    dict(note_id="NOTE-011", account_id="ACC-002", account_name="Cascade Financial",
         author="Marcus Rivera", created_date="2026-02-28", note_type="meeting_summary",
         note_text="Canvas rescue attempt at Cascade: ran an industry-specific onboarding session with 15 invitees. 5 attended. 3 stayed for the full session. The financial services templates were well-received but the fundamental objection remains — 'why would I leave PowerPoint for this?' I'm beginning to think this is a product-market fit issue for financial services, not a training issue."),
    dict(note_id="NOTE-012", account_id="ACC-002", account_name="Cascade Financial",
         author="Ryan Nakamura", created_date="2026-03-10", note_type="risk_flag",
         note_text="Cascade renewal strategy: I'm recommending we proactively offer a downgrade to Flow-only before they ask. Better to retain $110K than lose $312K when they walk. Michael Chen has been a good partner and I don't want to damage the relationship by pretending Canvas adoption will improve. If we offer the downgrade with a path to re-expand later, we keep the relationship intact."),

    # =========================================================================
    # CHURN RISK — Beacon Logistics (ACC-003) — 5 notes
    # =========================================================================
    dict(note_id="NOTE-013", account_id="ACC-003", account_name="Beacon Logistics",
         author="Emily Thornton", created_date="2026-01-05", note_type="check_in",
         note_text="Routine check-in with Beacon. Robert Kimball mentioned intermittent API slowdowns over the past week. Not outages, but noticeable latency spikes during peak hours (2-4 PM). Their dispatch dashboard pulls real-time data via our Insight API. I flagged it to engineering. Robert was calm about it — 'just keep an eye on it.' I'll monitor."),
    dict(note_id="NOTE-014", account_id="ACC-003", account_name="Beacon Logistics",
         author="Emily Thornton", created_date="2026-01-20", note_type="risk_flag",
         note_text="Beacon Logistics has had 3 major API outages in 3 weeks. VP of Engineering Robert Kimball is furious. He's calculated $12K in operational costs from the outages. On top of this, Jake Torres just left and Kevin McBride is covering — but Kevin is 2 months into the job and doesn't know the account. I'm concerned about the combination of technical issues + relationship gap. ARR: $97K, renewal July."),
    dict(note_id="NOTE-015", account_id="ACC-003", account_name="Beacon Logistics",
         author="Emily Thornton", created_date="2026-02-01", note_type="meeting_summary",
         note_text="Introduced Kevin McBride to Robert Kimball. It did not go well. Robert immediately asked Kevin about the SLA credit calculation and Kevin didn't have the numbers. Robert said 'Jake would have had this ready.' Kevin tried to pivot to the infrastructure improvements and Robert cut him off — 'I don't care about your roadmap, I care about my $12K.' We need a senior person on this account."),
    dict(note_id="NOTE-016", account_id="ACC-003", account_name="Beacon Logistics",
         author="Emily Thornton", created_date="2026-02-10", note_type="escalation",
         note_text="Escalation: Beacon's VP of Operations is now CC'ing their legal team on the SLA credit discussion. We offered 15% credit (~$3,600) but they're claiming $12K in damages. Kevin McBride doesn't have the experience to handle this negotiation. Requesting senior AE or VP of Sales involvement before this becomes a formal dispute."),
    dict(note_id="NOTE-017", account_id="ACC-003", account_name="Beacon Logistics",
         author="Emily Thornton", created_date="2026-03-01", note_type="risk_flag",
         note_text="Beacon stability update: the dedicated infrastructure we provisioned has been stable for 3 weeks. Robert acknowledged the improvement but said 'trust takes longer to rebuild than it does to break.' He wants a contractual uptime guarantee before renewal. Kevin is drafting something but I'm not confident he can close this without senior support. The combination of API issues + AE transition hasn't been ideal."),

    # =========================================================================
    # CHURN RISK — Prism Retail (ACC-004) — 4 notes
    # =========================================================================
    dict(note_id="NOTE-018", account_id="ACC-004", account_name="Prism Retail",
         author="James Okafor", created_date="2026-01-10", note_type="check_in",
         note_text="Tried reaching out to Prism Retail for a routine check-in. The original admin (Tom Nguyen) is listed as the primary contact but his email bounced. Called the main office — receptionist said Tom left the company 'a while ago.' Nobody seems to know who owns the Canvas account now. This is a small account ($54K) but the lack of a point of contact is a red flag."),
    dict(note_id="NOTE-019", account_id="ACC-004", account_name="Prism Retail",
         author="James Okafor", created_date="2026-01-28", note_type="risk_flag",
         note_text="Prism Retail is going dark. No support tickets filed in 6 weeks. Usage declining gradually. Last Gong call was short and the customer seemed disengaged. The admin who originally set up the account has left and I don't think anyone is managing it internally. Renewal is soon — only about 10 weeks away. Small account ($54K) but the pattern is concerning."),
    dict(note_id="NOTE-020", account_id="ACC-004", account_name="Prism Retail",
         author="James Okafor", created_date="2026-02-25", note_type="risk_flag",
         note_text="Follow-up on Prism: Tried to schedule a check-in call three times. First two went unanswered. Third time the new contact said they'd 'circle back' — classic churn language. I believe this account will not renew. Maria Santos (AE) hasn't been able to get a meeting either. Flagging for pipeline adjustment."),
    dict(note_id="NOTE-021", account_id="ACC-004", account_name="Prism Retail",
         author="Maria Santos", created_date="2026-03-08", note_type="risk_flag",
         note_text="Prism renewal is 3 weeks out and we still don't have a meeting scheduled. Patricia Lowe (Marketing Manager) is the only contact who picks up but she keeps deferring to 'leadership decisions.' I think the decision has already been made and they just haven't told us. Adjusting pipeline forecast to 20% probability. This one is essentially lost."),

    # =========================================================================
    # EXPANSION — Atlas Digital (ACC-005) — 4 notes
    # =========================================================================
    dict(note_id="NOTE-022", account_id="ACC-005", account_name="Atlas Digital",
         author="Rachel Goldstein", created_date="2026-01-20", note_type="check_in",
         note_text="Quarterly check-in with Atlas Digital. Nina Alvarez mentioned they're hiring 8 more designers over the next two quarters and will need additional Canvas seats. She also dropped a hint about wanting to automate their design-to-publish workflows — classic Flow use case. I'm going to nurture the Flow conversation and bring Priya in when the timing is right."),
    dict(note_id="NOTE-023", account_id="ACC-005", account_name="Atlas Digital",
         author="Rachel Goldstein", created_date="2026-02-10", note_type="win",
         note_text="Big win potential at Atlas Digital. Raj Patel (Head of Creative) asked about Flow pricing unprompted during our check-in. Their team is growing 15% month-over-month and they're hitting limits with manual workflows. I've scheduled a Flow demo with Priya Sharma for next week. If the demo goes well, we're looking at a $95K expansion. Raj is a true champion — he's already evangelizing Canvas internally."),
    dict(note_id="NOTE-024", account_id="ACC-005", account_name="Atlas Digital",
         author="Priya Sharma", created_date="2026-02-22", note_type="meeting_summary",
         note_text="Flow demo with Atlas went exceptionally well. Raj brought his VP of Marketing into the room — she asked detailed questions about ROI and integration with their existing stack. She said she could get $95K approved if we can show time savings in the first 30 days. Sending a formal proposal this week. This is our strongest expansion opportunity right now."),
    dict(note_id="NOTE-025", account_id="ACC-005", account_name="Atlas Digital",
         author="Rachel Goldstein", created_date="2026-03-08", note_type="win",
         note_text="Atlas update: Nina also asked about Insight — wants to tie Canvas usage data to marketing campaign performance. Their CEO is asking for analytics on which campaign assets perform best. If we land Flow + Insight on top of Canvas, Atlas becomes a full-suite customer at ~$350K ARR. This is the model account for our expansion playbook."),

    # =========================================================================
    # EXPANSION — Summit Healthcare (ACC-006) — 3 notes
    # =========================================================================
    dict(note_id="NOTE-026", account_id="ACC-006", account_name="Summit Healthcare",
         author="Sarah Chen", created_date="2026-01-25", note_type="check_in",
         note_text="Summit Healthcare onboarding update: 36 of 40 seats active in just 4 weeks. Dr. Aisha Patel (CMO) is personally reviewing the Canvas templates her team creates. Marcus Williams in regulatory affairs has been running voluntary training sessions. I've never seen this level of organic adoption. This account is going to be a case study."),
    dict(note_id="NOTE-027", account_id="ACC-006", account_name="Summit Healthcare",
         author="Sarah Chen", created_date="2026-02-15", note_type="win",
         note_text="Summit Healthcare is a retention dream. Dr. Aisha Patel (CMO) presented our Canvas workflow to their hospital network's national marketing council. Three other hospitals in the network asked for vendor details. She's essentially doing our sales for us. Usage at 90% seat utilization in just 6 weeks. This account could become a case study."),
    dict(note_id="NOTE-028", account_id="ACC-006", account_name="Summit Healthcare",
         author="Sarah Chen", created_date="2026-03-05", note_type="win",
         note_text="Marcus Williams wants to pilot Flow for regulatory approval workflows. He's already mapped the current 14-step process on a whiteboard and identified where parallel reviews could cut cycle time from 18 days to 5. Dr. Patel gave him the green light. This will be a 20-seat Flow expansion (~$72K). Setting up a demo with Ryan Nakamura."),

    # =========================================================================
    # EXPANSION — Voyager Entertainment (ACC-007) — 3 notes
    # =========================================================================
    dict(note_id="NOTE-029", account_id="ACC-007", account_name="Voyager Entertainment",
         author="Marcus Rivera", created_date="2026-01-15", note_type="check_in",
         note_text="Voyager Q4 review: 108 active users out of 120 seats, 42-minute average session duration, 3,200+ Canvas assets created last quarter. Diana Okonkwo mentioned they're planning something big for Q2. She was vague but said 'you'll want to be ready for a conversation about scaling.' I think there's an expansion coming."),
    dict(note_id="NOTE-030", account_id="ACC-007", account_name="Voyager Entertainment",
         author="Marcus Rivera", created_date="2026-02-05", note_type="win",
         note_text="Voyager expansion is real. Diana Okonkwo (SVP Digital Production) confirmed they're launching Voyager Plus — a new streaming division with 50 people who need the full suite. At our current per-seat pricing, that's $180K in new ARR. She wants everything provisioned by June. This is our largest expansion opportunity this quarter. Zero risk — they're self-sufficient with zero support tickets."),
    dict(note_id="NOTE-031", account_id="ACC-007", account_name="Voyager Entertainment",
         author="Marcus Rivera", created_date="2026-03-01", note_type="meeting_summary",
         note_text="Sent expansion proposal to Voyager. Diana is reviewing with procurement. She also connected me with Thomas from their data team — he wants Insight Enterprise API access for custom analytics dashboards. Including it as a bundle add-on ($2K/month). This deal could close by end of Q2. Total expansion: $180K seats + $24K API = $204K."),

    # =========================================================================
    # EXPANSION — Ironclad Manufacturing (ACC-008) — 3 notes
    # =========================================================================
    dict(note_id="NOTE-032", account_id="ACC-008", account_name="Ironclad Manufacturing",
         author="Emily Thornton", created_date="2026-01-20", note_type="check_in",
         note_text="Ironclad check-in: Jason Miller's team has fully adopted Canvas for product documentation — spec sheets, assembly guides, safety docs. He's tracking template usage in a spreadsheet and asked if there's a better way. I mentioned Insight and his eyes lit up. 'Can it connect to our Snowflake warehouse?' This is a natural cross-sell opportunity."),
    dict(note_id="NOTE-033", account_id="ACC-008", account_name="Ironclad Manufacturing",
         author="Emily Thornton", created_date="2026-02-15", note_type="win",
         note_text="Ironclad is a strong Insight upsell candidate. Jason Miller's VP of Operations has been asking for analytics on which product templates are used most, revision frequency, and production time per document. Jason is currently doing this manually in Excel. An Insight demo with the Snowflake connector would be compelling. Scheduling for next week."),
    dict(note_id="NOTE-034", account_id="ACC-008", account_name="Ironclad Manufacturing",
         author="Lisa Patel", created_date="2026-03-05", note_type="meeting_summary",
         note_text="Insight demo at Ironclad went well. The Snowflake connector was the selling point — their data engineering team can join manufacturing data with Canvas usage data. Jason said getting budget approval for Insight ($55K) should be straightforward if the Snowflake integration works in pilot. Setting up a 2-week proof of concept."),

    # =========================================================================
    # HEALTHY — routine check-ins (1 note each, 8 accounts)
    # =========================================================================
    dict(note_id="NOTE-035", account_id="ACC-009", account_name="Northstar Consulting",
         author="James Okafor", created_date="2026-02-10", note_type="check_in",
         note_text="Northstar quarterly check-in. Sarah Kim (Operations Lead) says the team is happy with Canvas and Flow. Steady usage, no complaints. They might add 2-3 seats for summer interns but nothing material. Renewal is December — no concerns. This is a 'set it and forget it' account in the best way."),
    dict(note_id="NOTE-036", account_id="ACC-010", account_name="Ridgeline Media",
         author="Rachel Goldstein", created_date="2026-02-20", note_type="check_in",
         note_text="Ridgeline Media check-in. David Park (Content Director) loves Flow — says it's saved his team 15+ hours per week on approval workflows. Stable usage, low ticket volume. Asked about Slack integration; pointed him to the new connector we shipped last month. Renewal is July, no concerns."),
    dict(note_id="NOTE-037", account_id="ACC-011", account_name="Clearwater Tech",
         author="Sarah Chen", created_date="2026-01-30", note_type="check_in",
         note_text="Clearwater Tech QBR. Emily Watson (VP Technology) gave us a clean bill of health. All 3 products in active use, moderate but consistent engagement. She asked about our AI features roadmap — interested in how Cortex could enhance their analytics workflows. Renewal is September, expect smooth process."),
    dict(note_id="NOTE-038", account_id="ACC-012", account_name="Horizon Pharma",
         author="Marcus Rivera", created_date="2026-02-15", note_type="check_in",
         note_text="Horizon Pharma seasonal check-in. James Cooper (Marketing Director) says Canvas usage spikes during Jan-Feb campaign season, which matches what we see in the data. They're heavy Canvas users during campaigns and quiet otherwise. This is normal for pharma marketing. Renewal is June, no concerns."),
    dict(note_id="NOTE-039", account_id="ACC-013", account_name="Sterling Partners",
         author="Emily Thornton", created_date="2026-01-10", note_type="check_in",
         note_text="Sterling Partners check-in. Lisa Nakamura (Managing Director) renewed early — signed a 2-year deal. Small account ($62K) but high NPS and zero drama. She mentioned a new fund launch in Q3 that might drive additional Canvas usage. Low-touch account, high satisfaction."),
    dict(note_id="NOTE-040", account_id="ACC-014", account_name="Apex Marketing",
         author="James Okafor", created_date="2026-02-05", note_type="check_in",
         note_text="Apex Marketing check-in. Carlos Ruiz (Creative Director) says the team is slowly growing into the platform. Usage up slightly month-over-month. No urgent needs, no complaints. Mentioned wanting to explore Flow for campaign approval workflows — planting the seed for a future expansion conversation. Renewal is November."),
    dict(note_id="NOTE-041", account_id="ACC-019", account_name="Pinnacle Sports",
         author="James Okafor", created_date="2026-02-25", note_type="check_in",
         note_text="Pinnacle Sports routine check-in. Michelle Torres (Marketing Manager) says Canvas and Flow are working well for their game-day marketing materials. Stable usage, no issues. She asked about custom fonts — walked her through the asset library upload. Straightforward account, no concerns."),
    dict(note_id="NOTE-042", account_id="ACC-020", account_name="Crestline Analytics",
         author="Rachel Goldstein", created_date="2026-02-18", note_type="check_in",
         note_text="Crestline Analytics check-in. Brian Foster (Data Team Lead) is happy with Flow and Insight. They're using Insight's scheduled reports feature heavily — 12 recurring reports running weekly. Good feature adoption. Mentioned interest in the Insight API for custom integrations. Steady account, renewal October."),

    # =========================================================================
    # ATTENTION — Cobalt Aerospace (ACC-015) — 4 notes
    # =========================================================================
    dict(note_id="NOTE-043", account_id="ACC-015", account_name="Cobalt Aerospace",
         author="Rachel Goldstein", created_date="2026-01-15", note_type="check_in",
         note_text="Cobalt Aerospace week 2 check-in. Richard Torres (IT Director) says the team is confused by the workspace structure. His engineers think in terms of 'programs' and 'contracts,' not 'organizations' and 'teams.' The default onboarding emails reference creative agency workflows — completely wrong for aerospace. I need to switch their onboarding track immediately."),
    dict(note_id="NOTE-044", account_id="ACC-015", account_name="Cobalt Aerospace",
         author="Rachel Goldstein", created_date="2026-02-05", note_type="risk_flag",
         note_text="Cobalt Aerospace onboarding is stalling. Week 4, only 8 of 55 users active. IT Director Richard Torres is frustrated — the onboarding materials don't match their use case (aerospace, not creative agency). We need industry-specific onboarding or we'll lose this $210K account before it ever gets started. Scheduling a co-working session with our SE team."),
    dict(note_id="NOTE-045", account_id="ACC-015", account_name="Cobalt Aerospace",
         author="Rachel Goldstein", created_date="2026-02-28", note_type="meeting_summary",
         note_text="SE co-working session with Cobalt went well. Fixed the Azure AD permissions issue — all 55 users can now access the platform. But Richard warned: if we don't see meaningful adoption by week 8, his VP will question the purchase. Planning an internal launch event with industry-specific demo. This is still recoverable but the window is closing."),
    dict(note_id="NOTE-046", account_id="ACC-015", account_name="Cobalt Aerospace",
         author="Rachel Goldstein", created_date="2026-03-12", note_type="check_in",
         note_text="Cobalt internal launch event happened yesterday. I did a live demo tailored to aerospace use cases — technical documentation, safety manuals, program review presentations. 30 people attended (out of 55). Engagement was noticeably better. Richard seemed cautiously optimistic. We need to see adoption numbers climb in the next 2 weeks to be out of the woods."),

    # =========================================================================
    # ATTENTION — Driftwood Media (ACC-016) — 3 notes
    # =========================================================================
    dict(note_id="NOTE-047", account_id="ACC-016", account_name="Driftwood Media",
         author="Sarah Chen", created_date="2026-01-28", note_type="risk_flag",
         note_text="Driftwood Media: Mark Torres (original admin) left the company without warning. His replacement Yuki Tanaka has no admin experience — she's a project manager who got handed the keys to everything. On top of this, Diana Osei (AE) is going on parental leave next week and Tom Westfield will cover. Two transitions at once is risky for an $88K account."),
    dict(note_id="NOTE-048", account_id="ACC-016", account_name="Driftwood Media",
         author="Sarah Chen", created_date="2026-02-15", note_type="meeting_summary",
         note_text="Met with Yuki Tanaka, Driftwood's new admin. She inherited the account when Mark Torres left suddenly. She's a project manager, not an IT admin — needs significant hand-holding. Did a full Flow automation audit and found 4 active workflows including one sending to Mark's personal Gmail. Cleaned that up. Yuki is willing to learn but needs more support than Tom Westfield (covering for Diana) can provide right now."),
    dict(note_id="NOTE-049", account_id="ACC-016", account_name="Driftwood Media",
         author="Sarah Chen", created_date="2026-03-05", note_type="check_in",
         note_text="Driftwood follow-up: Yuki is ramping up nicely. She figured out user management and added the 3 new team members on her own. Usage has recovered to about 85% of pre-transition levels. Tom Westfield finally responded to her billing contact change request — took 10 days. Not great, but the product side is stabilizing. I think Driftwood is going to be fine if Tom stays responsive."),

    # =========================================================================
    # ATTENTION — Evergreen Education (ACC-017) — 3 notes
    # =========================================================================
    dict(note_id="NOTE-050", account_id="ACC-017", account_name="Evergreen Education",
         author="Marcus Rivera", created_date="2026-01-20", note_type="check_in",
         note_text="Evergreen Education check-in. Sandra Brooks (Curriculum Director) mentioned budget pressures for the first time. The school district superintendent announced a 15% across-the-board cut. Sandra loves Canvas — her teachers use it daily — but she's worried about justifying the cost. I should proactively look into our education pricing tier."),
    dict(note_id="NOTE-051", account_id="ACC-017", account_name="Evergreen Education",
         author="Marcus Rivera", created_date="2026-02-12", note_type="risk_flag",
         note_text="Evergreen Education is a tough one. Usage is actually solid — teachers love Canvas. But the district is cutting budgets 15% across the board. Sandra Brooks (Curriculum Director) says she needs us below $40/seat/month or she can't justify it to the board. Our education discount gets them to $36/seat. I think we save this one but the AE transition (Diana to Tom) adds friction. Tom hasn't responded to Sandra's emails. I'm escalating."),
    dict(note_id="NOTE-052", account_id="ACC-017", account_name="Evergreen Education",
         author="Marcus Rivera", created_date="2026-03-02", note_type="meeting_summary",
         note_text="Good news on Evergreen: got approval for the K-12 education discount (35% off, brings per-seat cost to $36/month). Sandra was relieved — says this is under her threshold and she can present it to the business office. Tom Westfield finally engaged on the formal quote. Budget hearing is April 15. Sandra mentioned that if they keep the seats, elementary school teachers are asking about Canvas too — possible expansion later."),

    # =========================================================================
    # ATTENTION — Flux Dynamics (ACC-018) — 3 notes
    # =========================================================================
    dict(note_id="NOTE-053", account_id="ACC-018", account_name="Flux Dynamics",
         author="Emily Thornton", created_date="2026-01-25", note_type="check_in",
         note_text="Flux Dynamics check-in. Raj Kapoor (CTO) is frustrated about API rate limits but very engaged with the product. His team processes 50,000 API calls daily between 2-4 PM and they're hitting the 1,000/minute cap constantly. This isn't a churn signal — it's a power user who needs enterprise-tier service. If we can solve the rate limit issue, this account is rock solid."),
    dict(note_id="NOTE-054", account_id="ACC-018", account_name="Flux Dynamics",
         author="Emily Thornton", created_date="2026-02-20", note_type="meeting_summary",
         note_text="Flux Dynamics is an unusual case — very high usage but very angry. They're heavy API users hitting rate limits daily. Their engineering team has filed multiple P1 tickets. The frustration is 100% technical, not product-fit. If we can solve the rate limit issue (they need 5000 req/min, we cap at 1000), this account stabilizes immediately. They even want to expand if we fix this. Priya Sharma is working on an enterprise API tier proposal."),
    dict(note_id="NOTE-055", account_id="ACC-018", account_name="Flux Dynamics",
         author="Emily Thornton", created_date="2026-03-10", note_type="win",
         note_text="Flux resolution: provisioned dedicated API tier (5,000 req/min) for $800/month. Raj Kapoor confirmed it's working — batch jobs that took 8 hours now complete in 1 hour. He's happy. Also told me about the upcoming batch API endpoint (next month) which would eliminate the rate limit issue entirely. Raj asked about expanding to 60 seats. This went from our angriest account to a potential expansion. Technical resolution works."),
]

def generate_csm_notes():
    return CSM_NOTES


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------
def write_csv(filename, rows, fieldnames):
    path = os.path.join(SEED_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Generating DigitalNativeCo synthetic data...")
    print(f"  Date range: {date_str(START_DATE)} to {date_str(END_DATE)} ({NUM_DAYS} days)")
    print(f"  Output directory: {SEED_DIR}")
    print()

    # Accounts
    n_accounts, accounts_path = write_accounts_csv()
    print(f"  accounts.csv: {n_accounts} accounts")

    # Product events
    events = generate_product_events()
    events_path = write_csv("product_events.csv", events,
                            ["event_id", "account_id", "account_name", "user_id",
                             "product", "event_type", "event_date", "session_duration_min"])
    print(f"  product_events.csv: {len(events)} events")

    # Support tickets
    tickets = generate_support_tickets()
    tickets_path = write_csv("support_tickets.csv", tickets,
                             ["ticket_id", "account_id", "account_name", "product",
                              "ticket_text", "priority", "status", "created_at"])
    print(f"  support_tickets.csv: {len(tickets)} tickets")

    # Gong transcripts
    transcripts = generate_gong_transcripts()
    transcripts_path = write_csv("gong_transcripts.csv", transcripts,
                                 ["call_id", "account_id", "account_name", "call_date",
                                  "call_type", "duration_min", "transcript_excerpt", "attendees"])
    print(f"  gong_transcripts.csv: {len(transcripts)} calls")

    # Employees
    employees = generate_employees()
    write_csv("employees.csv", employees,
              ["employee_id", "name", "title", "role", "department",
               "hire_date", "departure_date", "departure_reason", "status"])
    print(f"  employees.csv: {len(employees)} employees")

    # Account assignments
    assignments = generate_account_assignments()
    write_csv("account_assignments.csv", assignments,
              ["assignment_id", "account_id", "account_name", "employee_id",
               "employee_name", "role", "assigned_date", "unassigned_date", "is_current"])
    print(f"  account_assignments.csv: {len(assignments)} assignments")

    # Opportunities
    opps = generate_opportunities()
    write_csv("opportunities.csv", opps,
              ["opportunity_id", "account_id", "account_name", "opp_type", "opp_name",
               "amount", "stage", "close_date", "owner_id", "owner_name", "created_date", "notes"])
    print(f"  opportunities.csv: {len(opps)} opportunities")

    # Feature usage
    features = generate_feature_usage()
    write_csv("feature_usage.csv", features,
              ["feature_usage_id", "account_id", "account_name", "user_id",
               "feature_name", "usage_count", "usage_week"])
    print(f"  feature_usage.csv: {len(features)} feature usage rows")

    # Invoices
    invoices = generate_invoices()
    write_csv("invoices.csv", invoices,
              ["invoice_id", "account_id", "account_name", "invoice_date", "quarter",
               "gross_amount", "discount_pct", "net_amount", "payment_status", "days_to_pay"])
    print(f"  invoices.csv: {len(invoices)} invoices")

    # CSM notes
    csm_notes = generate_csm_notes()
    write_csv("csm_notes.csv", csm_notes,
              ["note_id", "account_id", "account_name", "author", "created_date",
               "note_type", "note_text"])
    print(f"  csm_notes.csv: {len(csm_notes)} notes")

    print()
    print("Summary by account category:")
    for cat in ["churn_risk", "expansion", "healthy", "attention"]:
        accts = [a for a in ACCOUNTS if a["category"] == cat]
        aids = {a["account_id"] for a in accts}
        n_events = sum(1 for e in events if e["account_id"] in aids)
        n_tickets = sum(1 for t in tickets if t["account_id"] in aids)
        n_calls = sum(1 for c in transcripts if c["account_id"] in aids)
        print(f"  {cat}: {len(accts)} accounts, {n_events} events, {n_tickets} tickets, {n_calls} calls")

    print()
    print("Done!")


if __name__ == "__main__":
    main()
