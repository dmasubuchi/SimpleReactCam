# Deployment Guide for AI Housekeeping Advisor

This guide explains how to deploy the AI Housekeeping Advisor application to Google Cloud.

## Prerequisites

1. Google Cloud SDK installed and configured
2. Google Cloud project with the following APIs enabled:
   - Cloud Functions API
   - Cloud Build API
   - Vision API
   - Vertex AI API
3. Authentication set up for Google Cloud

## Backend Deployment

The backend consists of three separate Cloud Functions:
1. `api-gateway`: Handles HTTP requests from the frontend
2. `image-processor`: Processes images using Vision API
3. `message-generator`: Generates advice using Vertex AI

### Automated Deployment

1. Authenticate with Google Cloud:
   ```bash
   gcloud auth login
   ```

2. Run the deployment script:
   ```bash
   cd deploy
   ./deploy.sh
   ```

3. The script will:
   - Deploy all three Cloud Functions
   - Configure environment variables for communication between functions
   - Update the frontend configuration with the deployed API URL

### Manual Deployment

If you prefer to deploy manually:

1. Deploy the API Gateway:
   ```bash
   cd backend/api-gateway/deploy
   gcloud functions deploy api-gateway \
     --runtime=python39 \
     --trigger-http \
     --allow-unauthenticated \
     --entry-point=app
   ```

2. Deploy the Image Processor:
   ```bash
   cd ../../image-processor/deploy
   gcloud functions deploy image-processor \
     --runtime=python39 \
     --trigger-http \
     --allow-unauthenticated \
     --entry-point=app
   ```

3. Deploy the Message Generator:
   ```bash
   cd ../../message-generator/deploy
   gcloud functions deploy message-generator \
     --runtime=python39 \
     --trigger-http \
     --allow-unauthenticated \
     --entry-point=app
   ```

4. Update the API Gateway environment variables:
   ```bash
   IMAGE_PROCESSOR_URL=$(gcloud functions describe image-processor --format="value(httpsTrigger.url)")
   MESSAGE_GENERATOR_URL=$(gcloud functions describe message-generator --format="value(httpsTrigger.url)")
   
   gcloud functions update api-gateway \
     --set-env-vars=IMAGE_PROCESSOR_URL=$IMAGE_PROCESSOR_URL,MESSAGE_GENERATOR_URL=$MESSAGE_GENERATOR_URL
   ```

5. Update the frontend configuration:
   ```bash
   API_GATEWAY_URL=$(gcloud functions describe api-gateway --format="value(httpsTrigger.url)")
   echo "VITE_API_URL=$API_GATEWAY_URL" > frontend/.env.production
   ```

## Frontend Deployment

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Deploy to Firebase Hosting (or your preferred hosting service):
   ```bash
   firebase deploy
   ```

## Troubleshooting

- If you encounter authentication issues, ensure you've run `gcloud auth login`
- If Cloud Functions fail to deploy, check that the required APIs are enabled
- If functions can't communicate with each other, verify the environment variables are set correctly
