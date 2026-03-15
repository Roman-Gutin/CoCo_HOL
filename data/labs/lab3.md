# Lab 3: Build & Deploy a Streamlit App

**Duration:** 25 min
**Theme:** "Ship the data product, not just the data"

> **POV connection:** You can now go from model → app → deployed without an eng team. The dashboard is dead. The data app is born. You just went from "here's the data" to "here's the data product."

---

## Prerequisites

- Completed Lab 1 and Lab 2
- `workshop_db.lab1.mart_enriched_tickets` table exists
- `workshop_db.lab1.support_agent` Cortex Agent exists
- Streamlit in Snowflake enabled on your account

---

## Setup (2 min)

Navigate to **Snowsight → Projects → Streamlit** and click **+ Streamlit App**.

Configure:
- **App name:** `support_ticket_analytics`
- **Database:** `workshop_db`
- **Schema:** `lab1`
- **Warehouse:** `COMPUTE_WH`

This opens the Streamlit editor. You'll see a starter template — delete it. We're building from scratch (with AI help).

---

## Step 1: Use Cortex Code to Generate the App (8 min)

Open **Cortex Code** and give it this prompt:

> "Build a Streamlit in Snowflake app for support ticket analytics. The data is in `workshop_db.lab1.mart_enriched_tickets` with columns: ticket_id, ticket_text, ticket_date, product, customer_id, sentiment_score, category, urgency, action_requested. Include: (1) a sidebar with date range and category filters, (2) a metrics row showing total tickets, average sentiment, and top category, (3) a bar chart of ticket volume by category over time, (4) a sentiment heatmap by category and urgency."

Review the generated code. It should produce something like this structure (adjust as needed):

```python
import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session

session = get_active_session()

# --- Page Config ---
st.set_page_config(page_title="Support Ticket Analytics", layout="wide")
st.title("Support Ticket Analytics")

# --- Load Data ---
@st.cache_data(ttl=600)
def load_data():
    df = session.sql("""
        SELECT ticket_id, ticket_text, ticket_date, product,
               sentiment_score, category, urgency, action_requested
        FROM workshop_db.lab1.mart_enriched_tickets
    """).to_pandas()
    df['TICKET_DATE'] = pd.to_datetime(df['TICKET_DATE'])
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['TICKET_DATE'].min(), df['TICKET_DATE'].max())
)

categories = st.sidebar.multiselect(
    "Category",
    options=df['CATEGORY'].unique(),
    default=df['CATEGORY'].unique()
)

urgency_filter = st.sidebar.multiselect(
    "Urgency",
    options=df['URGENCY'].dropna().unique(),
    default=df['URGENCY'].dropna().unique()
)

# --- Apply Filters ---
mask = (
    (df['TICKET_DATE'] >= pd.Timestamp(date_range[0])) &
    (df['TICKET_DATE'] <= pd.Timestamp(date_range[1])) &
    (df['CATEGORY'].isin(categories)) &
    (df['URGENCY'].isin(urgency_filter))
)
filtered = df[mask]

# --- Metrics Row ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tickets", len(filtered))
col2.metric("Avg Sentiment", f"{filtered['SENTIMENT_SCORE'].mean():.2f}")
col3.metric("Top Category", filtered['CATEGORY'].mode().iloc[0] if len(filtered) > 0 else "N/A")
col4.metric("High Urgency", len(filtered[filtered['URGENCY'] == 'high']))

# --- Ticket Volume Chart ---
st.subheader("Ticket Volume by Category Over Time")

volume = (
    filtered.groupby([pd.Grouper(key='TICKET_DATE', freq='W'), 'CATEGORY'])
    .size()
    .reset_index(name='count')
)

chart = alt.Chart(volume).mark_bar().encode(
    x=alt.X('TICKET_DATE:T', title='Week'),
    y=alt.Y('count:Q', title='Tickets'),
    color='CATEGORY:N',
    tooltip=['TICKET_DATE:T', 'CATEGORY:N', 'count:Q']
).properties(height=400)

st.altair_chart(chart, use_container_width=True)

# --- Sentiment Heatmap ---
st.subheader("Sentiment Heatmap: Category × Urgency")

heatmap_data = (
    filtered.groupby(['CATEGORY', 'URGENCY'])['SENTIMENT_SCORE']
    .mean()
    .reset_index()
)

heatmap = alt.Chart(heatmap_data).mark_rect().encode(
    x=alt.X('URGENCY:N', title='Urgency'),
    y=alt.Y('CATEGORY:N', title='Category'),
    color=alt.Color('SENTIMENT_SCORE:Q',
                     scale=alt.Scale(scheme='redyellowgreen', domain=[-1, 1]),
                     title='Avg Sentiment'),
    tooltip=['CATEGORY:N', 'URGENCY:N',
             alt.Tooltip('SENTIMENT_SCORE:Q', format='.2f')]
).properties(height=300)

st.altair_chart(heatmap, use_container_width=True)
```

Paste the code into the Streamlit editor and click **Run**. You should see the app render immediately.

---

## Step 2: Add the AI Chat Interface (8 min)

Now add a chat interface that talks to the Cortex Agent you built in Lab 2.

Add this below the heatmap:

```python
# --- AI Chat Interface ---
st.subheader("Ask the AI Agent")
st.caption("Powered by your semantic model from Lab 2")

user_question = st.text_input(
    "Ask a question about support tickets:",
    placeholder="e.g., What's our most common complaint this month?"
)

if user_question:
    with st.spinner("Agent is thinking..."):
        response = session.sql(f"""
            SELECT * FROM TABLE(
                workshop_db.lab1.support_agent!COMPLETE(
                    '{user_question.replace("'", "''")}'
                )
            )
        """).to_pandas()

        st.markdown("**Agent Response:**")
        st.write(response.iloc[0]['CONTENT'] if 'CONTENT' in response.columns else response.iloc[0][0])
```

Click **Run** again. Type a question like:
- "What's the average sentiment for billing issues?"
- "How many high-urgency tickets did we get this week?"
- "Find tickets where customers mentioned a competitor"

Watch the agent respond in your app.

---

## Step 3: Deploy the App (3 min)

Your app is already running in Snowflake. To share it:

1. Click the **Share** button in the top right of the Streamlit editor
2. Grant access to your workshop role or specific users
3. Copy the app URL

**Share the URL with someone sitting near you.** They can open it in their browser and see your app immediately — no deployment pipeline, no credentials to configure, governed by Snowflake RBAC.

---

## Step 4: Polish with Cortex Code (4 min)

Use the remaining time to improve the app. Try these prompts in Cortex Code:

**Add a data table with search:**
> "Add an expandable section below the charts that shows the raw ticket data in a searchable, sortable table"

```python
with st.expander("View Raw Tickets"):
    st.dataframe(
        filtered[['TICKET_DATE', 'CATEGORY', 'URGENCY', 'SENTIMENT_SCORE',
                   'ACTION_REQUESTED', 'TICKET_TEXT']].sort_values('TICKET_DATE', ascending=False),
        use_container_width=True,
        height=400
    )
```

**Add a product filter:**
> "Add a product multiselect filter to the sidebar"

Each change is a few seconds of prompting + review + apply.

---

## Stretch Goals (if time permits)

### Weekly executive summary tab

```python
tab1, tab2 = st.tabs(["Dashboard", "Executive Summary"])

with tab2:
    if st.button("Generate Weekly Summary"):
        with st.spinner("Generating..."):
            summary = session.sql("""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'claude-3-7-sonnet',
                    'Write a concise executive summary of support ticket trends based on this data: ' ||
                    (SELECT OBJECT_AGG(category, ticket_count::VARIANT)::STRING
                     FROM (SELECT category, COUNT(*) as ticket_count
                           FROM workshop_db.lab1.mart_enriched_tickets
                           WHERE ticket_date >= DATEADD('day', -7, CURRENT_DATE())
                           GROUP BY category))
                ) AS summary
            """).to_pandas()
            st.markdown(summary.iloc[0]['SUMMARY'])
```

### CSV export

```python
csv = filtered.to_csv(index=False)
st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="support_tickets_export.csv",
    mime="text/csv"
)
```

---

## What You Just Did

- Used **Cortex Code** to generate a Streamlit app from natural language
- Built a **filter sidebar**, **metrics row**, **volume chart**, and **sentiment heatmap**
- Added an **AI chat interface** powered by the Cortex Agent from Lab 2
- **Deployed** the app in Snowflake — shareable via URL, governed by RBAC
- Iterated on the app using Cortex Code in real time

You built and deployed a production data app. With a chat interface. Powered by an AI agent. On top of your semantic layer. As one person. In 25 minutes.

**This is what "full-stack data product builder" looks like.**

The dashboard is dead. The data app is born. And you just built one.

---

*Head back to the main room for the closing — we'll talk about what to do Monday.*
