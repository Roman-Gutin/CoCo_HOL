-- =============================================================================
-- Service User Setup for Workshop React App (Programmatic Access Token)
-- =============================================================================
-- Run as ACCOUNTADMIN
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------------
-- 1. Create the service user
-- ---------------------------------------------------------------------------
CREATE USER IF NOT EXISTS WORKSHOP_SVC_USER
    TYPE             = SERVICE
    DEFAULT_ROLE     = WORKSHOP_ROLE
    DEFAULT_WAREHOUSE = COMPUTE_WH
    COMMENT          = 'Service user for workshop React app — Cortex REST API access';

-- ---------------------------------------------------------------------------
-- 2. Grant roles
-- ---------------------------------------------------------------------------
GRANT ROLE WORKSHOP_ROLE TO USER WORKSHOP_SVC_USER;

-- Cortex functions require CORTEX_USER
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE WORKSHOP_ROLE;

-- ---------------------------------------------------------------------------
-- 3. Create and assign network policy (REQUIRED for PATs)
-- ---------------------------------------------------------------------------
CREATE NETWORK POLICY IF NOT EXISTS WORKSHOP_APP_POLICY
    ALLOWED_IP_LIST = ('0.0.0.0/0')  -- allows all IPs; restrict in production
    COMMENT = 'Network policy for workshop service user';

ALTER USER WORKSHOP_SVC_USER SET NETWORK_POLICY = WORKSHOP_APP_POLICY;

-- ---------------------------------------------------------------------------
-- 4. Generate Programmatic Access Token
-- ---------------------------------------------------------------------------
-- PATs are created via system function. The token is shown ONCE — save it.

ALTER USER WORKSHOP_SVC_USER
    ADD PROGRAMMATIC_ACCESS_TOKEN
    TOKEN_NAME = 'workshop_app_token'
    COMMENT    = 'Token for React app Cortex REST API calls';

-- Copy the token from the output ^^^
-- It will look like: ver:1-hint:xxx-xxx:xxxxxxxxxxxxxxxx

-- ---------------------------------------------------------------------------
-- 5. Verify
-- ---------------------------------------------------------------------------

-- Confirm user exists and has correct role
SHOW USERS LIKE 'WORKSHOP_SVC_USER';

-- Confirm token exists
SELECT SYSTEM$LIST_PROGRAMMATIC_ACCESS_TOKENS('WORKSHOP_SVC_USER');

-- ---------------------------------------------------------------------------
-- 6. Use in React app (.env)
-- ---------------------------------------------------------------------------
-- VITE_SNOWFLAKE_ACCOUNT=your_account.region
-- VITE_SNOWFLAKE_TOKEN=ver:1-hint:xxx-xxx:xxxxxxxxxxxxxxxx
-- VITE_SNOWFLAKE_DATABASE=DIGITALNATIVECO
-- VITE_SNOWFLAKE_SCHEMA=MARTS
-- VITE_SNOWFLAKE_WAREHOUSE=COMPUTE_WH

-- ---------------------------------------------------------------------------
-- Cleanup (after workshop)
-- ---------------------------------------------------------------------------
-- ALTER USER WORKSHOP_SVC_USER DROP PROGRAMMATIC_ACCESS_TOKEN TOKEN_NAME = 'workshop_app_token';
-- DROP USER WORKSHOP_SVC_USER;
