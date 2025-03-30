# AI Housekeeping Advisor Bot - GCP Resources

This document provides an overview of the Google Cloud Platform (GCP) resources used in the AI Housekeeping Advisor Bot project.

## Cloud Functions

| Function Name | Purpose | Environment Variables | APIs Used |
|---------------|---------|----------------------|-----------|
| api-gateway | Handles HTTP requests from the frontend, orchestrates calls to other functions | IMAGE_PROCESSOR_URL, MESSAGE_GENERATOR_URL | None directly |
| image-processor | Processes uploaded images using Google Cloud Vision API | None | Google Cloud Vision API |
| message-generator | Generates housekeeping advice using Google Vertex AI Gemini API | None | Google Vertex AI Gemini API |

## Frontend Hosting

| Resource | Purpose | URL |
|----------|---------|-----|
| Firebase Hosting | Hosts the React frontend application | https://simple-react-cam-app-3g7swytb.devinapps.com/ |

## Required IAM Roles

| Service Account | Required Roles |
|-----------------|----------------|
| Cloud Functions Service Account | Cloud Functions Invoker, Secret Manager Secret Accessor |
| Vision API Service Account | Cloud Vision API User |
| Vertex AI Service Account | Vertex AI User |

## Secret Manager Secrets

| Secret Name | Purpose |
|-------------|---------|
| vision-api-key | API key for Google Cloud Vision API |
| gemini-service-account-key | Service account key for Google Vertex AI Gemini API |

## Deployment Commands

See the [deployment script](./deploy.sh) for the complete deployment process.

## Verification Steps

After deployment, verify the resources using:

```bash
# Verify Cloud Functions
gcloud functions describe api-gateway --gen2 --region=us-central1 --project=simplereactcam20250330

# Test CORS configuration
curl -I -X OPTIONS API_GATEWAY_URL \
  -H "Origin: https://simple-react-cam-app-3g7swytb.devinapps.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

## Resource Diagram

```
Frontend (Firebase Hosting)
        |
        v
    api-gateway
    /         \
   v           v
image-processor  message-generator
   |               |
   v               v
Vision API      Vertex AI Gemini API
```
