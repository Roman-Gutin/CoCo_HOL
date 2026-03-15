-- =============================================================================
-- DigitalNativeCo Workshop — Snowflake Setup Script
-- =============================================================================
--
-- WHAT THIS SCRIPT DOES:
--   1. Creates the DIGITALNATIVECO database with RAW, STAGING, and MARTS schemas
--   2. Creates tables in RAW matching the seven seed CSV files
--   3. Creates a CSV file format and an internal stage for uploading data
--   4. Loads data from the stage into tables using COPY INTO
--   5. Creates a WORKSHOP_ROLE with the necessary grants
--   6. Runs verification queries so you can confirm everything loaded
--
-- PREREQUISITES:
--   - You need ACCOUNTADMIN (or a role with CREATE DATABASE / CREATE ROLE)
--   - A warehouse must exist. This script uses COMPUTE_WH — change if yours differs.
--   - After running the DDL sections, upload the four CSV files to the stage:
--
--       PUT file://path/to/accounts.csv @DIGITALNATIVECO.RAW.SEED_STAGE;
--       PUT file://path/to/product_events.csv @DIGITALNATIVECO.RAW.SEED_STAGE;
--       PUT file://path/to/support_tickets.csv @DIGITALNATIVECO.RAW.SEED_STAGE;
--       PUT file://path/to/gong_transcripts.csv @DIGITALNATIVECO.RAW.SEED_STAGE;
--
--     Then run the COPY INTO section to load the data.
--
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 0. CONTEXT — set role and warehouse
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_WH;


-- ---------------------------------------------------------------------------
-- 1. DATABASE & SCHEMAS
-- ---------------------------------------------------------------------------

-- Create the main database for the workshop
CREATE DATABASE IF NOT EXISTS DIGITALNATIVECO;

USE DATABASE DIGITALNATIVECO;

-- RAW: landing zone for CSV data, untransformed
CREATE SCHEMA IF NOT EXISTS RAW;

-- STAGING: cleaned / typed / deduplicated data
CREATE SCHEMA IF NOT EXISTS STAGING;

-- MARTS: business-level tables & views consumed by Cortex / dashboards
CREATE SCHEMA IF NOT EXISTS MARTS;


-- ---------------------------------------------------------------------------
-- 2. RAW TABLES — one per CSV, columns match the files exactly
-- ---------------------------------------------------------------------------
USE SCHEMA RAW;

-- Accounts: 20 customer accounts with firmographic + contract info
CREATE OR REPLACE TABLE ACCOUNTS (
    ACCOUNT_ID          VARCHAR(10)     NOT NULL,   -- e.g. ACC-001
    ACCOUNT_NAME        VARCHAR(100)    NOT NULL,
    INDUSTRY            VARCHAR(100),
    ARR                 NUMBER(12,2),               -- annual recurring revenue ($)
    LICENSED_SEATS      INTEGER,
    PRODUCTS            VARCHAR(200),               -- comma-separated list: Canvas, Flow, Insight
    CONTRACT_RENEWAL_DATE DATE,
    CSM_NAME            VARCHAR(100),               -- Customer Success Manager
    PRIMARY_AE          VARCHAR(100),               -- Current Account Executive
    HEALTH_STATUS       VARCHAR(20),                -- at_risk, expansion, healthy, attention
    NPS_SCORE           INTEGER                     -- 1-10
);

-- Product Events: ~5,300 rows of telemetry (logins, feature use, exports, etc.)
CREATE OR REPLACE TABLE PRODUCT_EVENTS (
    EVENT_ID            VARCHAR(20)     NOT NULL,   -- e.g. EVT-000001
    ACCOUNT_ID          VARCHAR(10)     NOT NULL,
    ACCOUNT_NAME        VARCHAR(100),
    USER_ID             VARCHAR(20),                -- e.g. ACC-001-U045
    PRODUCT             VARCHAR(20),                -- Canvas | Flow | Insight
    EVENT_TYPE          VARCHAR(30),                -- login, feature_use, export, api_call, invite_sent
    EVENT_DATE          TIMESTAMP_NTZ,
    SESSION_DURATION_MIN NUMBER(8,2)
);

-- Support Tickets: ~513 rows with free-text ticket descriptions
CREATE OR REPLACE TABLE SUPPORT_TICKETS (
    TICKET_ID           VARCHAR(20)     NOT NULL,   -- e.g. TKT-0001
    ACCOUNT_ID          VARCHAR(10)     NOT NULL,
    ACCOUNT_NAME        VARCHAR(100),
    PRODUCT             VARCHAR(20),
    TICKET_TEXT         VARCHAR(5000),               -- free-text description (used for sentiment analysis)
    PRIORITY            VARCHAR(5),                  -- P1, P2, P3, P4
    STATUS              VARCHAR(20),                 -- open, resolved, escalated
    CREATED_AT          TIMESTAMP_NTZ
);

-- Gong Call Transcripts: ~150 calls with multi-paragraph transcript excerpts
CREATE OR REPLACE TABLE GONG_TRANSCRIPTS (
    CALL_ID             VARCHAR(20)     NOT NULL,   -- e.g. CALL-0001
    ACCOUNT_ID          VARCHAR(10)     NOT NULL,
    ACCOUNT_NAME        VARCHAR(100),
    CALL_DATE           TIMESTAMP_NTZ,
    CALL_TYPE           VARCHAR(30),                -- QBR, check-in, demo, onboarding, renewal
    DURATION_MIN        INTEGER,
    TRANSCRIPT_EXCERPT  VARCHAR(16777216),           -- large text — transcript excerpts can be long
    ATTENDEES           VARCHAR(2000)
);

-- Employees: ~20 rows — AEs, CSMs, SEs, managers (includes departed/on-leave)
CREATE OR REPLACE TABLE EMPLOYEES (
    EMPLOYEE_ID         VARCHAR(10)     NOT NULL,   -- e.g. EMP-001
    NAME                VARCHAR(100)    NOT NULL,
    TITLE               VARCHAR(100),
    ROLE                VARCHAR(20),                -- AE, CSM, SE, Manager
    DEPARTMENT          VARCHAR(50),
    HIRE_DATE           DATE,
    DEPARTURE_DATE      DATE,                       -- NULL if active
    DEPARTURE_REASON    VARCHAR(50),                 -- NULL, resigned, parental_leave, terminated
    STATUS              VARCHAR(20)                  -- active, departed, on_leave
);

-- Account Assignments: ~44 rows — who owns which account, historical transitions
CREATE OR REPLACE TABLE ACCOUNT_ASSIGNMENTS (
    ASSIGNMENT_ID       VARCHAR(20)     NOT NULL,   -- e.g. ASSIGN-001
    ACCOUNT_ID          VARCHAR(10)     NOT NULL,
    ACCOUNT_NAME        VARCHAR(100),
    EMPLOYEE_ID         VARCHAR(10)     NOT NULL,
    EMPLOYEE_NAME       VARCHAR(100),
    ROLE                VARCHAR(20),                -- AE or CSM
    ASSIGNED_DATE       DATE,
    UNASSIGNED_DATE     DATE,                       -- NULL if current
    IS_CURRENT          BOOLEAN                     -- TRUE if active assignment
);

-- Opportunities: ~21 rows — renewals, expansions, pipeline data
CREATE OR REPLACE TABLE OPPORTUNITIES (
    OPPORTUNITY_ID      VARCHAR(10)     NOT NULL,   -- e.g. OPP-001
    ACCOUNT_ID          VARCHAR(10)     NOT NULL,
    ACCOUNT_NAME        VARCHAR(100),
    OPP_TYPE            VARCHAR(30),                -- new_business, expansion, renewal
    OPP_NAME            VARCHAR(200),
    AMOUNT              NUMBER(12,2),
    STAGE               VARCHAR(30),                -- prospect, qualified, proposal, negotiation, closed_won, closed_lost
    CLOSE_DATE          DATE,
    OWNER_ID            VARCHAR(10),
    OWNER_NAME          VARCHAR(100),
    CREATED_DATE        DATE,
    NOTES               VARCHAR(5000)               -- free-text context about the deal
);

-- Feature Usage: ~7,800 rows — granular feature-level adoption per account per week
CREATE OR REPLACE TABLE FEATURE_USAGE (
    FEATURE_USAGE_ID    VARCHAR(20)     NOT NULL,
    ACCOUNT_ID          VARCHAR(10)     NOT NULL,
    ACCOUNT_NAME        VARCHAR(100),
    USER_ID             VARCHAR(20),
    FEATURE_NAME        VARCHAR(50),                -- e.g. canvas_collab_edit, flow_approvals
    USAGE_COUNT         INTEGER,
    USAGE_WEEK          DATE                        -- week start date
);

-- Invoices: ~80 rows — billing history with discounts and payment timing
CREATE OR REPLACE TABLE INVOICES (
    INVOICE_ID          VARCHAR(20)     NOT NULL,
    ACCOUNT_ID          VARCHAR(10)     NOT NULL,
    ACCOUNT_NAME        VARCHAR(100),
    INVOICE_DATE        DATE,
    QUARTER             VARCHAR(20),
    GROSS_AMOUNT        NUMBER(12,2),
    DISCOUNT_PCT        NUMBER(5,2),
    NET_AMOUNT          NUMBER(12,2),
    PAYMENT_STATUS      VARCHAR(20),                -- paid, overdue
    DAYS_TO_PAY         INTEGER                     -- NULL if overdue
);

-- CSM Notes: ~18 rows — internal risk flags, escalations, meeting notes
CREATE OR REPLACE TABLE CSM_NOTES (
    NOTE_ID             VARCHAR(20)     NOT NULL,
    ACCOUNT_ID          VARCHAR(10)     NOT NULL,
    ACCOUNT_NAME        VARCHAR(100),
    AUTHOR              VARCHAR(100),               -- CSM or AE name
    CREATED_DATE        DATE,
    NOTE_TYPE           VARCHAR(30),                -- risk_flag, escalation, meeting_summary, win
    NOTE_TEXT           VARCHAR(10000)               -- free-text internal notes
);


-- ---------------------------------------------------------------------------
-- 3. FILE FORMAT & INTERNAL STAGE
-- ---------------------------------------------------------------------------

-- CSV file format: headers in row 1, fields optionally enclosed in double quotes
-- FIELD_OPTIONALLY_ENCLOSED_BY handles the quoted commas inside PRODUCTS and TRANSCRIPT_EXCERPT
CREATE OR REPLACE FILE FORMAT CSV_FORMAT
    TYPE                    = 'CSV'
    FIELD_DELIMITER         = ','
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER             = 1
    TRIM_SPACE              = TRUE
    NULL_IF                 = ('', 'NULL', 'null')
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

-- Internal named stage — participants will PUT files here
CREATE OR REPLACE STAGE SEED_STAGE
    FILE_FORMAT = CSV_FORMAT;

-- *** UPLOAD STEP ***
-- After creating the stage, upload the four CSV files. Run these from SnowSQL
-- or use the Snowsight UI (Data > Databases > ... > Stage > Upload):
--
--   PUT file://accounts.csv @DIGITALNATIVECO.RAW.SEED_STAGE AUTO_COMPRESS=FALSE;
--   PUT file://product_events.csv @DIGITALNATIVECO.RAW.SEED_STAGE AUTO_COMPRESS=FALSE;
--   PUT file://support_tickets.csv @DIGITALNATIVECO.RAW.SEED_STAGE AUTO_COMPRESS=FALSE;
--   PUT file://gong_transcripts.csv @DIGITALNATIVECO.RAW.SEED_STAGE AUTO_COMPRESS=FALSE;
--   PUT file://employees.csv @DIGITALNATIVECO.RAW.SEED_STAGE AUTO_COMPRESS=FALSE;
--   PUT file://account_assignments.csv @DIGITALNATIVECO.RAW.SEED_STAGE AUTO_COMPRESS=FALSE;
--   PUT file://opportunities.csv @DIGITALNATIVECO.RAW.SEED_STAGE AUTO_COMPRESS=FALSE;
--
-- Verify uploads:
--   LIST @DIGITALNATIVECO.RAW.SEED_STAGE;


-- ---------------------------------------------------------------------------
-- 4. COPY INTO — load CSVs from stage into RAW tables
-- ---------------------------------------------------------------------------

-- Accounts (20 rows expected)
COPY INTO ACCOUNTS
    FROM @SEED_STAGE/accounts.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';

-- Product Events (~5,301 rows expected)
COPY INTO PRODUCT_EVENTS
    FROM @SEED_STAGE/product_events.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';

-- Support Tickets (~486 rows expected)
COPY INTO SUPPORT_TICKETS
    FROM @SEED_STAGE/support_tickets.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';

-- Gong Transcripts (~157 rows expected; file has multi-line quoted fields)
COPY INTO GONG_TRANSCRIPTS
    FROM @SEED_STAGE/gong_transcripts.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';

-- Employees (~20 rows)
COPY INTO EMPLOYEES
    FROM @SEED_STAGE/employees.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';

-- Account Assignments (~44 rows)
COPY INTO ACCOUNT_ASSIGNMENTS
    FROM @SEED_STAGE/account_assignments.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';

-- Opportunities (~21 rows)
COPY INTO OPPORTUNITIES
    FROM @SEED_STAGE/opportunities.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';

-- Feature Usage (~7,800 rows)
COPY INTO FEATURE_USAGE
    FROM @SEED_STAGE/feature_usage.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';

-- Invoices (~80 rows)
COPY INTO INVOICES
    FROM @SEED_STAGE/invoices.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';

-- CSM Notes (~18 rows)
COPY INTO CSM_NOTES
    FROM @SEED_STAGE/csm_notes.csv
    FILE_FORMAT = CSV_FORMAT
    ON_ERROR    = 'ABORT_STATEMENT';


-- ---------------------------------------------------------------------------
-- 5. ROLES & GRANTS
-- ---------------------------------------------------------------------------

-- Create a dedicated workshop role so participants don't need ACCOUNTADMIN
CREATE ROLE IF NOT EXISTS WORKSHOP_ROLE;

-- Grant Cortex user privileges (required for Cortex LLM functions like COMPLETE, SENTIMENT, etc.)
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE WORKSHOP_ROLE;

-- Warehouse access
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE WORKSHOP_ROLE;

-- Database-level access
GRANT USAGE ON DATABASE DIGITALNATIVECO TO ROLE WORKSHOP_ROLE;

-- Schema-level access (all three schemas)
GRANT USAGE ON SCHEMA DIGITALNATIVECO.RAW       TO ROLE WORKSHOP_ROLE;
GRANT USAGE ON SCHEMA DIGITALNATIVECO.STAGING    TO ROLE WORKSHOP_ROLE;
GRANT USAGE ON SCHEMA DIGITALNATIVECO.MARTS      TO ROLE WORKSHOP_ROLE;

-- Table reads in RAW
GRANT SELECT ON ALL TABLES IN SCHEMA DIGITALNATIVECO.RAW TO ROLE WORKSHOP_ROLE;

-- Let workshop participants create objects in STAGING and MARTS
GRANT CREATE TABLE ON SCHEMA DIGITALNATIVECO.STAGING TO ROLE WORKSHOP_ROLE;
GRANT CREATE VIEW  ON SCHEMA DIGITALNATIVECO.STAGING TO ROLE WORKSHOP_ROLE;
GRANT CREATE TABLE ON SCHEMA DIGITALNATIVECO.MARTS   TO ROLE WORKSHOP_ROLE;
GRANT CREATE VIEW  ON SCHEMA DIGITALNATIVECO.MARTS   TO ROLE WORKSHOP_ROLE;

-- Allow read on any future tables participants create in STAGING / MARTS
GRANT SELECT ON FUTURE TABLES IN SCHEMA DIGITALNATIVECO.STAGING TO ROLE WORKSHOP_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA DIGITALNATIVECO.MARTS   TO ROLE WORKSHOP_ROLE;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA DIGITALNATIVECO.STAGING TO ROLE WORKSHOP_ROLE;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA DIGITALNATIVECO.MARTS   TO ROLE WORKSHOP_ROLE;

-- Grant the workshop role to your user (replace YOUR_USERNAME or run separately)
-- GRANT ROLE WORKSHOP_ROLE TO USER YOUR_USERNAME;


-- ---------------------------------------------------------------------------
-- 6. VERIFICATION — confirm everything loaded correctly
-- ---------------------------------------------------------------------------
USE SCHEMA RAW;

-- Row counts — these should match the seed file sizes
SELECT 'ACCOUNTS'            AS table_name, COUNT(*) AS row_count FROM ACCOUNTS
UNION ALL
SELECT 'PRODUCT_EVENTS',                  COUNT(*)              FROM PRODUCT_EVENTS
UNION ALL
SELECT 'SUPPORT_TICKETS',                 COUNT(*)              FROM SUPPORT_TICKETS
UNION ALL
SELECT 'GONG_TRANSCRIPTS',                COUNT(*)              FROM GONG_TRANSCRIPTS
UNION ALL
SELECT 'EMPLOYEES',                       COUNT(*)              FROM EMPLOYEES
UNION ALL
SELECT 'ACCOUNT_ASSIGNMENTS',             COUNT(*)              FROM ACCOUNT_ASSIGNMENTS
UNION ALL
SELECT 'OPPORTUNITIES',                   COUNT(*)              FROM OPPORTUNITIES
UNION ALL
SELECT 'FEATURE_USAGE',                   COUNT(*)              FROM FEATURE_USAGE
UNION ALL
SELECT 'INVOICES',                        COUNT(*)              FROM INVOICES
UNION ALL
SELECT 'CSM_NOTES',                       COUNT(*)              FROM CSM_NOTES
ORDER BY table_name;

-- Expected counts:
--   ACCOUNTS             →    20
--   ACCOUNT_ASSIGNMENTS  →   ~44
--   EMPLOYEES            →   ~20
--   GONG_TRANSCRIPTS     →  ~157
--   OPPORTUNITIES        →   ~21
--   PRODUCT_EVENTS       → ~5,301
--   SUPPORT_TICKETS      →  ~513

-- Sample data: peek at a few rows from each table
SELECT * FROM ACCOUNTS            LIMIT 5;
SELECT * FROM PRODUCT_EVENTS      LIMIT 5;
SELECT * FROM SUPPORT_TICKETS     LIMIT 5;
SELECT * FROM GONG_TRANSCRIPTS    LIMIT 3;
SELECT * FROM EMPLOYEES           LIMIT 5;
SELECT * FROM ACCOUNT_ASSIGNMENTS LIMIT 5;
SELECT * FROM OPPORTUNITIES       LIMIT 5;

-- Quick data quality check: make sure every event/ticket/call references a valid account
SELECT 'orphan_events'  AS check_name, COUNT(*) AS orphan_count
FROM PRODUCT_EVENTS e
LEFT JOIN ACCOUNTS a ON e.ACCOUNT_ID = a.ACCOUNT_ID
WHERE a.ACCOUNT_ID IS NULL
UNION ALL
SELECT 'orphan_tickets', COUNT(*)
FROM SUPPORT_TICKETS t
LEFT JOIN ACCOUNTS a ON t.ACCOUNT_ID = a.ACCOUNT_ID
WHERE a.ACCOUNT_ID IS NULL
UNION ALL
SELECT 'orphan_calls', COUNT(*)
FROM GONG_TRANSCRIPTS g
LEFT JOIN ACCOUNTS a ON g.ACCOUNT_ID = a.ACCOUNT_ID
WHERE a.ACCOUNT_ID IS NULL;
-- All three should return 0


-- =============================================================================
-- SETUP COMPLETE
-- You now have 10 tables:
--   DIGITALNATIVECO.RAW.ACCOUNTS              — 20 customer accounts
--   DIGITALNATIVECO.RAW.PRODUCT_EVENTS        — product telemetry events
--   DIGITALNATIVECO.RAW.SUPPORT_TICKETS       — support ticket text
--   DIGITALNATIVECO.RAW.GONG_TRANSCRIPTS      — call transcript excerpts
--   DIGITALNATIVECO.RAW.EMPLOYEES             — 20 employees (AEs, CSMs, SEs, managers)
--   DIGITALNATIVECO.RAW.ACCOUNT_ASSIGNMENTS   — account ownership history
--   DIGITALNATIVECO.RAW.OPPORTUNITIES         — renewal/expansion pipeline
--   DIGITALNATIVECO.RAW.FEATURE_USAGE         — granular feature adoption per account/week
--   DIGITALNATIVECO.RAW.INVOICES              — billing history with discounts/payment timing
--   DIGITALNATIVECO.RAW.CSM_NOTES             — internal risk flags and meeting notes
--   WORKSHOP_ROLE                              — role with Cortex + read/write access
-- =============================================================================
