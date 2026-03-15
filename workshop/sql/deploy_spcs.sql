-- =============================================================================
-- Deploy Account Health Dashboard to Snowflake Container Services (SPCS)
-- =============================================================================
-- Account:  RNRIZGX-DEMO_TEMP
-- Database: DIGITALNATIVECO
-- Schema:   MARTS
-- =============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE DIGITALNATIVECO;
USE SCHEMA MARTS;

-- ---------------------------------------------------------------------------
-- 1. Create an image repository to store the Docker image
-- ---------------------------------------------------------------------------
CREATE IMAGE REPOSITORY IF NOT EXISTS DASHBOARD_REPO;

-- Verify and get the repository URL (you need this for docker push)
SHOW IMAGE REPOSITORIES;
-- Look for the 'repository_url' column — it will be something like:
--   rnrizgx-demo_temp.registry.snowflakecomputing.com/digitalnativeco/marts/dashboard_repo

-- ---------------------------------------------------------------------------
-- 2. Create a compute pool (smallest instance, single node)
-- ---------------------------------------------------------------------------
CREATE COMPUTE POOL IF NOT EXISTS DASHBOARD_COMPUTE_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = CPU_X64_XS
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 3600;

-- Wait for compute pool to be ACTIVE/IDLE
DESCRIBE COMPUTE POOL DASHBOARD_COMPUTE_POOL;

-- ---------------------------------------------------------------------------
-- 3. Build and push the Docker image (run these in your terminal, not SQL)
-- ---------------------------------------------------------------------------
-- cd /path/to/workshop/app
-- bash deploy.sh

-- Or manually:
--   snow spcs image-registry login
--   docker build --rm --platform linux/amd64 \
--     -t rnrizgx-demo_temp.registry.snowflakecomputing.com/digitalnativeco/marts/dashboard_repo/account-health-dashboard:latest .
--   docker push rnrizgx-demo_temp.registry.snowflakecomputing.com/digitalnativeco/marts/dashboard_repo/account-health-dashboard:latest

-- Verify the image was pushed
SHOW IMAGES IN IMAGE REPOSITORY DASHBOARD_REPO;

-- ---------------------------------------------------------------------------
-- 4. Create the service with inline YAML specification
-- ---------------------------------------------------------------------------
-- Drop existing service if re-deploying
-- DROP SERVICE IF EXISTS DASHBOARD_SERVICE;

CREATE SERVICE IF NOT EXISTS DASHBOARD_SERVICE
    IN COMPUTE POOL DASHBOARD_COMPUTE_POOL
    FROM SPECIFICATION $$
spec:
  containers:
  - name: dashboard
    image: /DIGITALNATIVECO/MARTS/DASHBOARD_REPO/account-health-dashboard:latest
    readinessProbe:
      port: 8080
      path: /healthcheck
  endpoints:
  - name: dashboard
    port: 8080
    public: true
$$
    MIN_INSTANCES = 1
    MAX_INSTANCES = 1;

-- ---------------------------------------------------------------------------
-- 5. Check service status
-- ---------------------------------------------------------------------------
SHOW SERVICES;
SELECT SYSTEM$GET_SERVICE_STATUS('DIGITALNATIVECO.MARTS.DASHBOARD_SERVICE');
SHOW ENDPOINTS IN SERVICE DASHBOARD_SERVICE;
-- The 'ingress_url' column contains the public URL for the dashboard

-- ---------------------------------------------------------------------------
-- 6. View service logs (useful for debugging)
-- ---------------------------------------------------------------------------
-- SELECT SYSTEM$GET_SERVICE_LOGS('DIGITALNATIVECO.MARTS.DASHBOARD_SERVICE', 0, 'dashboard', 100);

-- ---------------------------------------------------------------------------
-- 7. Grant access to other roles
-- ---------------------------------------------------------------------------
-- Grant usage on the database and schema
GRANT USAGE ON DATABASE DIGITALNATIVECO TO ROLE WORKSHOP_ROLE;
GRANT USAGE ON SCHEMA DIGITALNATIVECO.MARTS TO ROLE WORKSHOP_ROLE;

-- Grant the service role so WORKSHOP_ROLE can access the public endpoint
GRANT SERVICE ROLE DASHBOARD_SERVICE!ALL_ENDPOINTS_USAGE TO ROLE WORKSHOP_ROLE;
GRANT SERVICE ROLE DASHBOARD_SERVICE!ALL_ENDPOINTS_USAGE TO ROLE ACCOUNTADMIN;

-- Grant MONITOR privilege so the role can check service status
GRANT MONITOR ON SERVICE DASHBOARD_SERVICE TO ROLE WORKSHOP_ROLE;

-- ---------------------------------------------------------------------------
-- 8. Teardown (when you want to remove everything)
-- ---------------------------------------------------------------------------
-- DROP SERVICE IF EXISTS DASHBOARD_SERVICE;
-- DROP COMPUTE POOL IF EXISTS DASHBOARD_COMPUTE_POOL;
-- DROP IMAGE REPOSITORY IF EXISTS DASHBOARD_REPO;
