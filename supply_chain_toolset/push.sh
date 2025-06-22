#!/bin/bash

# Exit if any command fails
set -e

# Make sure to install gcloud - 
 
# Build and submit the container to Google Container Registry
echo "📦 Submitting build to Google Cloud Build..."
gcloud builds submit --tag gcr.io/mcpservice-scp/supply-chain-toolset

# Deploy the image to Google Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy supply-chain-toolset \
  --image gcr.io/mcpservice-scp/supply-chain-toolset \
  --region us-central1 \
  --allow-unauthenticated

# If deploying it for the first time, give Neo4j database creds for the agents to connect to the database. 
# This will get stored in Google Cloud Run credentials as env variables
# gcloud run deploy supply-chain-toolset \
#   --image gcr.io/mcpservice-scp/supply-chain-toolset \
#   --region us-central1 \
#   --allow-unauthenticated \
#   --set-env-vars NEO4J_URI=<url here>,NEO4J_USERNAME=<database name>,NEO4J_PASSWORD=<password here

echo "✅ Deployment complete."
