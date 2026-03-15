#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Deploy Account Health Dashboard to Snowflake Container Services (SPCS)
# ---------------------------------------------------------------------------
# Prerequisites:
#   - Docker installed and running
#   - Snowflake CLI (snow) installed and configured
#   - Image repository already created (see sql/deploy_spcs.sql)
# ---------------------------------------------------------------------------

# Configuration — update these to match your environment
SNOWFLAKE_ACCOUNT="rnrizgx-demo_temp"
DATABASE="DIGITALNATIVECO"
SCHEMA="MARTS"
REPO_NAME="DASHBOARD_REPO"
IMAGE_NAME="account-health-dashboard"
IMAGE_TAG="latest"

# Snowflake registry hostname: replace underscores with hyphens in account name
REGISTRY_HOST="${SNOWFLAKE_ACCOUNT//_/-}.registry.snowflakecomputing.com"
REPO_URL="${REGISTRY_HOST}/${DATABASE}/${SCHEMA}/${REPO_NAME}"
FULL_IMAGE="${REPO_URL}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "============================================"
echo "SPCS Deployment: ${IMAGE_NAME}"
echo "============================================"
echo ""
echo "Registry:  ${REGISTRY_HOST}"
echo "Repo URL:  ${REPO_URL}"
echo "Image:     ${FULL_IMAGE}"
echo ""

# Step 1: Authenticate Docker with Snowflake registry
echo "[1/4] Authenticating with Snowflake image registry..."
snow spcs image-registry login
echo ""

# Step 2: Build the Docker image (linux/amd64 required for SPCS)
echo "[2/4] Building Docker image for linux/amd64..."
docker build --rm --platform linux/amd64 -t "${FULL_IMAGE}" .
echo ""

# Step 3: Push to Snowflake image registry
echo "[3/4] Pushing image to Snowflake registry..."
docker push "${FULL_IMAGE}"
echo ""

# Step 4: Done
echo "[4/4] Image pushed successfully!"
echo ""
echo "============================================"
echo "NEXT STEPS"
echo "============================================"
echo ""
echo "1. Open a Snowflake worksheet"
echo "2. Run the SQL in sql/deploy_spcs.sql"
echo "3. Wait for the service to reach READY status:"
echo "   SELECT SYSTEM\$GET_SERVICE_STATUS('${DATABASE}.${SCHEMA}.DASHBOARD_SERVICE');"
echo "4. Get the public URL:"
echo "   SHOW ENDPOINTS IN SERVICE ${DATABASE}.${SCHEMA}.DASHBOARD_SERVICE;"
echo ""
