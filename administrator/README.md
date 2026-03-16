# Administrator Guide

Set up the workshop environment on a Snowflake account before participants arrive.

## Prerequisites

- Snowflake account with Cortex AI enabled
- `SYSADMIN` role access
- Python 3.10+

## Setup Steps

### 1. Generate the synthetic data

```bash
python workshop/data/generate_data.py
```

Creates 10 CSVs in `workshop/data/seed/` (~14,000 rows across 20 accounts).

### 2. Deploy to Snowflake

```bash
# Create database, schemas, stages, and load seed data
python workshop/sql/deploy.py
```

This creates:
- `DIGITALNATIVECO` database
- `RAW` schema with 10 tables
- `STAGING` schema (empty — Lab 1 builds into it)
- `MARTS` schema (empty — Lab 1 builds into it)

### 3. Verify the deployment

```bash
python workshop/sql/setup_checkpoint.py raw
```

Confirms all 10 RAW tables are loaded with correct row counts.

### 4. (Optional) Pre-build to a checkpoint

If you want participants to skip ahead to Lab 2 or Lab 3:

```bash
# Build everything through Lab 1 (staging + enrichment + mart)
python workshop/sql/setup_checkpoint.py lab1

# Build everything through Lab 2 (Lab 1 + semantic model + search services + agent)
python workshop/sql/setup_checkpoint.py lab2

# Build everything through Lab 3 (Lab 2 + agent configured with sample questions)
python workshop/sql/setup_checkpoint.py lab3
```

### 5. Reset / teardown

```bash
# Remove all lab objects, keep RAW data intact
python workshop/sql/teardown_lab.py --confirm
```

### 6. Run the full test suite

```bash
python workshop/sql/test_full_lab.py
```

Runs 42 tests: staging views, enrichment, mart, semantic model, search services, agent creation, and agent query validation.

## Environment Config

Copy `workshop/app/.env.example` to `workshop/app/.env` and fill in:

```
VITE_SNOWFLAKE_ACCOUNT=your_account
VITE_SNOWFLAKE_USER=WORKSHOP_SVC_USER
VITE_SNOWFLAKE_TOKEN=your_programmatic_access_token
VITE_SNOWFLAKE_DATABASE=DIGITALNATIVECO
VITE_SNOWFLAKE_SCHEMA=MARTS
VITE_SNOWFLAKE_WAREHOUSE=COMPUTE_WH
VITE_SNOWFLAKE_ROLE=WORKSHOP_ROLE
```

## Key Scripts

| Script | Purpose |
|--------|---------|
| `workshop/data/generate_data.py` | Generate synthetic CSVs |
| `workshop/sql/deploy.py` | Deploy database + load data |
| `workshop/sql/setup_checkpoint.py` | Rebuild to any lab checkpoint |
| `workshop/sql/teardown_lab.py` | Clean up lab objects |
| `workshop/sql/test_full_lab.py` | Full validation suite |
| `workshop/sql/run_lab1.py` | Run Lab 1 programmatically |
| `workshop/sql/run_lab2.py` | Run Lab 2 programmatically |
| `workshop/create_slides.py` | Generate Google Slides deck |

## Presenter Materials

- Slide deck script: `data/workshop_slides.md`
- Demo script with expected outputs: `workshop/data/labs/demo_script.md`
- Full lab guides (with answers): `workshop/data/labs/lab1.md`, `lab2.md`, `lab3.md`
