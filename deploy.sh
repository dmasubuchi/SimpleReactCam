#!/bin/bash

set -e

# Default values
PROJECT_ID=${1:-"simplereactcam20250330"}
REGION=${2:-"us-central1"}

echo "Deploying AI Housekeeping Advisor Bot to GCP project: $PROJECT_ID in region: $REGION"

# Deploy image-processor function
echo "Deploying image-processor Cloud Function..."
cd backend/image-processor
gcloud functions deploy image-processor \
  --gen2 \
  --runtime=python39 \
  --region=$REGION \
  --source=. \
  --entry-point=image_processor \
  --trigger-http \
  --allow-unauthenticated \
  --project=$PROJECT_ID

# Get the image-processor URL
IMAGE_PROCESSOR_URL=$(gcloud functions describe image-processor --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
echo "Image Processor URL: $IMAGE_PROCESSOR_URL"

# Deploy message-generator function
echo "Deploying message-generator Cloud Function..."
cd ../message-generator
gcloud functions deploy message-generator \
  --gen2 \
  --runtime=python39 \
  --region=$REGION \
  --source=. \
  --entry-point=message_generator \
  --trigger-http \
  --allow-unauthenticated \
  --project=$PROJECT_ID

# Get the message-generator URL
MESSAGE_GENERATOR_URL=$(gcloud functions describe message-generator --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
echo "Message Generator URL: $MESSAGE_GENERATOR_URL"

# Deploy api-gateway function
echo "Deploying api-gateway Cloud Function..."
cd ../api-gateway
gcloud functions deploy api-gateway \
  --gen2 \
  --runtime=python39 \
  --region=$REGION \
  --source=. \
  --entry-point=api_gateway \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars=IMAGE_PROCESSOR_URL=$IMAGE_PROCESSOR_URL,MESSAGE_GENERATOR_URL=$MESSAGE_GENERATOR_URL \
  --project=$PROJECT_ID

# Get the api-gateway URL
API_GATEWAY_URL=$(gcloud functions describe api-gateway --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
echo "API Gateway URL: $API_GATEWAY_URL"

echo "Backend deployment completed successfully!"
echo ""
echo "To deploy the frontend, update the .env.production file with:"
echo "VITE_API_URL=$API_GATEWAY_URL"
echo ""
echo "Then run:"
echo "cd frontend"
echo "npm install"
echo "npm run build"
echo "firebase deploy --only hosting"
