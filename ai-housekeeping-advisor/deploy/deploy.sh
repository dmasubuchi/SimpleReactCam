#!/bin/bash

# Exit on error
set -e

echo "Deploying AI Housekeeping Advisor Backend to Google Cloud Functions..."

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
  echo "Error: Not authenticated with Google Cloud. Please run 'gcloud auth login' first."
  exit 1
fi

# Deploy API Gateway
echo "Deploying API Gateway..."
cd ../backend/api-gateway/deploy
gcloud functions deploy api-gateway \
  --runtime=python39 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point=app

# Get the API Gateway URL
API_GATEWAY_URL=$(gcloud functions describe api-gateway --format="value(httpsTrigger.url)")
echo "API Gateway deployed at: $API_GATEWAY_URL"

# Deploy Image Processor
echo "Deploying Image Processor..."
cd ../../image-processor/deploy
gcloud functions deploy image-processor \
  --runtime=python39 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point=app

# Get the Image Processor URL
IMAGE_PROCESSOR_URL=$(gcloud functions describe image-processor --format="value(httpsTrigger.url)")
echo "Image Processor deployed at: $IMAGE_PROCESSOR_URL"

# Deploy Message Generator
echo "Deploying Message Generator..."
cd ../../message-generator/deploy
gcloud functions deploy message-generator \
  --runtime=python39 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point=app

# Get the Message Generator URL
MESSAGE_GENERATOR_URL=$(gcloud functions describe message-generator --format="value(httpsTrigger.url)")
echo "Message Generator deployed at: $MESSAGE_GENERATOR_URL"

# Update environment variables for API Gateway
echo "Updating API Gateway environment variables..."
gcloud functions update api-gateway \
  --set-env-vars=IMAGE_PROCESSOR_URL=$IMAGE_PROCESSOR_URL,MESSAGE_GENERATOR_URL=$MESSAGE_GENERATOR_URL

echo "Backend deployment complete!"
echo "Frontend should be configured to use API Gateway URL: $API_GATEWAY_URL"

# Create a .env file for the frontend
cd ../../../frontend
echo "VITE_API_URL=$API_GATEWAY_URL" > .env.production

echo "Frontend environment variables updated. Ready for frontend deployment."
