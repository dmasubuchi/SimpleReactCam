# AI Housekeeping Advisor Bot - Deployment Guide

This document provides detailed instructions for deploying the AI Housekeeping Advisor Bot application to Google Cloud Platform (GCP) and Firebase Hosting.

## Prerequisites

- Google Cloud Platform (GCP) account with billing enabled
- Firebase account (for frontend hosting)
- `gcloud` CLI installed and configured
- `firebase` CLI installed and configured
- Required API services enabled in GCP:
  - Cloud Functions API
  - Cloud Build API
  - Cloud Vision API
  - Vertex AI API
  - Secret Manager API

## 1. Backend Deployment (Cloud Functions)

The backend consists of three Python Cloud Functions:
- `api-gateway`: Handles HTTP requests from the frontend
- `image-processor`: Processes images using Cloud Vision API
- `message-generator`: Generates advice using Vertex AI Gemini API

### 1.1 Service Account Setup

Create a service account with the necessary permissions:

```bash
# Create service account
gcloud iam service-accounts create ai-housekeeping-sa \
  --display-name="AI Housekeeping Service Account"

# Assign required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:ai-housekeeping-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:ai-housekeeping-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudfunctions.invoker"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:ai-housekeeping-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:ai-housekeeping-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/vision.user"
```

### 1.2 Secret Manager Setup

Store API keys and credentials in Secret Manager:

```bash
# Store Vision API key
echo -n "YOUR_VISION_API_KEY" | \
  gcloud secrets create vision-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Store Gemini API key
echo -n "YOUR_GEMINI_API_KEY" | \
  gcloud secrets create gemini-api-key \
  --data-file=- \
  --replication-policy="automatic"
```

### 1.3 Deploy Image Processor Function

```bash
cd backend/image-processor

gcloud functions deploy image-processor \
  --gen2 \
  --runtime=python39 \
  --region=us-central1 \
  --source=. \
  --entry-point=image_processor \
  --trigger-http \
  --allow-unauthenticated \
  --service-account=ai-housekeeping-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars=VISION_API_SECRET_NAME=vision-api-key \
  --memory=512MB \
  --timeout=60s
```

After deployment, note the URL of the deployed function:

```bash
IMAGE_PROCESSOR_URL=$(gcloud functions describe image-processor \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)")

echo "Image Processor URL: $IMAGE_PROCESSOR_URL"
```

### 1.4 Deploy Message Generator Function

```bash
cd ../message-generator

gcloud functions deploy message-generator \
  --gen2 \
  --runtime=python39 \
  --region=us-central1 \
  --source=. \
  --entry-point=message_generator \
  --trigger-http \
  --allow-unauthenticated \
  --service-account=ai-housekeeping-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars=GEMINI_API_SECRET_NAME=gemini-api-key \
  --memory=512MB \
  --timeout=120s
```

After deployment, note the URL of the deployed function:

```bash
MESSAGE_GENERATOR_URL=$(gcloud functions describe message-generator \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)")

echo "Message Generator URL: $MESSAGE_GENERATOR_URL"
```

### 1.5 Deploy API Gateway Function

The API Gateway function requires the URLs of the other two functions as environment variables:

```bash
cd ../api-gateway

gcloud functions deploy api-gateway \
  --gen2 \
  --runtime=python39 \
  --region=us-central1 \
  --source=. \
  --entry-point=api_gateway \
  --trigger-http \
  --allow-unauthenticated \
  --service-account=ai-housekeeping-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars=IMAGE_PROCESSOR_URL=$IMAGE_PROCESSOR_URL,MESSAGE_GENERATOR_URL=$MESSAGE_GENERATOR_URL \
  --memory=256MB \
  --timeout=180s
```

After deployment, note the URL of the API Gateway function:

```bash
API_GATEWAY_URL=$(gcloud functions describe api-gateway \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)")

echo "API Gateway URL: $API_GATEWAY_URL"
```

### 1.6 CORS Configuration for API Gateway

The API Gateway function already includes CORS handling in its code. The `handle_cors` function in `src/main.py` adds the necessary CORS headers to responses:

```python
def handle_cors(request: Request, response: Any) -> Any:
    """
    Add CORS headers to the response.
    
    Args:
        request: The HTTP request object.
        response: The response object.
        
    Returns:
        The response object with CORS headers added.
    """
    origin = request.headers.get("Origin", "*")
    
    if isinstance(response, tuple):
        data, status_code = response
        response = make_response(data, status_code)
    else:
        response = make_response(response)
    
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response
```

The function also handles OPTIONS requests for CORS preflight:

```python
if request.method == "OPTIONS":
    logger.info("Handling OPTIONS request (CORS preflight)")
    response = make_response("")
    return handle_cors(request, (response, 204))
```

This approach is recommended over using deployment flags because it provides more flexibility and allows for dynamic origin handling.

To support both local development and production environments, you can modify the CORS handling to explicitly allow both:

```python
def handle_cors(request: Request, response: Any) -> Any:
    """Add CORS headers to the response."""
    origin = request.headers.get("Origin", "")
    
    # Allow specific origins
    allowed_origins = [
        "http://localhost:5173",  # Vite dev server
        "https://your-app-id.web.app"  # Firebase hosting (replace with your actual domain)
    ]
    
    # Set CORS headers based on origin
    if origin in allowed_origins:
        if isinstance(response, tuple):
            data, status_code = response
            response = make_response(data, status_code)
        else:
            response = make_response(response)
        
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response
```

### 1.7 Verify API Gateway Deployment

To verify that the API Gateway function is properly deployed and CORS is configured correctly:

```bash
# Test basic functionality
curl -X POST $API_GATEWAY_URL \
  -H "Content-Type: application/json" \
  -d '{"scenario": "plant", "image_data": "base64_encoded_image_data"}'

# Test CORS preflight
curl -I -X OPTIONS $API_GATEWAY_URL \
  -H "Origin: https://your-app-id.web.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

The OPTIONS request should return a 204 status code with the appropriate CORS headers.

## 2. Frontend Deployment (Firebase Hosting)

### 2.1 Configure Environment Variables

Create a `.env.production` file in the root of your frontend project with the API Gateway URL:

```
VITE_API_URL=https://api-gateway-xxxxxxxxxxxx-uc.a.run.app
```

Replace the URL with the actual API Gateway URL obtained from the backend deployment.

### 2.2 Build the Frontend

```bash
# Install dependencies
npm install

# Build for production
npm run build
```

This will create a `build` directory with the production-ready assets.

### 2.3 Firebase Hosting Setup

If you haven't already set up Firebase Hosting:

```bash
# Login to Firebase
firebase login

# Initialize Firebase Hosting
firebase init hosting
```

During the initialization process:
- Select your Firebase project
- Specify `build` as your public directory (or the appropriate build output directory)
- Configure as a single-page app (answer "yes" to "Configure as a single-page app")
- Don't overwrite `index.html` if asked

This will create a `firebase.json` file. Ensure it has the following configuration:

```json
{
  "hosting": {
    "public": "build",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

### 2.4 Deploy to Firebase Hosting

```bash
firebase deploy --only hosting
```

After deployment, Firebase will provide a URL where your application is hosted (e.g., `https://your-app-id.web.app`).

### 2.5 Verify Frontend Deployment

Open the deployed URL in a browser and test the application by:
1. Uploading an image
2. Selecting a scenario (plant, closet, or fridge)
3. Verifying that advice is generated correctly

## 3. Alternative: Deploy Frontend to Cloud Run

If you prefer to use Cloud Run instead of Firebase Hosting:

### 3.1 Create a Dockerfile

Create a `Dockerfile` in the root of your frontend project:

```dockerfile
# Build stage
FROM node:18 as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
```

Create an `nginx.conf` file:

```
server {
    listen 8080;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

### 3.2 Build and Deploy to Cloud Run

```bash
# Build the container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-housekeeping-frontend

# Deploy to Cloud Run
gcloud run deploy ai-housekeeping-frontend \
  --image gcr.io/YOUR_PROJECT_ID/ai-housekeeping-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 4. Post-Deployment Verification

### 4.1 Verify CORS Configuration

Test that the API Gateway function allows requests from your frontend domain:

```bash
curl -I -X OPTIONS $API_GATEWAY_URL \
  -H "Origin: https://your-app-id.web.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

The response should include:
- `Access-Control-Allow-Origin: https://your-app-id.web.app`
- `Access-Control-Allow-Methods: POST, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, Authorization`

### 4.2 End-to-End Testing

1. Open the deployed frontend URL in a browser
2. Upload an image of a plant, closet, or fridge
3. Select the appropriate scenario
4. Submit the request
5. Verify that advice is generated and displayed correctly

If you encounter any issues:
- Check the browser console for errors
- Check the Cloud Functions logs for backend errors
- Verify that all environment variables are set correctly
- Ensure that the service account has the necessary permissions

## 5. Automated Deployment Script

For convenience, you can use the following script to deploy all three backend functions in one go:

```bash
#!/bin/bash

set -e

if [ -z "$1" ]; then
  echo "Usage: ./deploy.sh PROJECT_ID [REGION]"
  echo "Example: ./deploy.sh my-project-id us-central1"
  exit 1
fi

PROJECT_ID=$1
REGION=${2:-"us-central1"}

echo "Deploying backend services to project: $PROJECT_ID in region: $REGION"

echo "Deploying Image Processor..."
cd image-processor
gcloud functions deploy image-processor \
  --gen2 \
  --runtime=python39 \
  --region=$REGION \
  --source=. \
  --entry-point=image_processor \
  --trigger-http \
  --allow-unauthenticated \
  --project=$PROJECT_ID
IMAGE_PROCESSOR_URL=$(gcloud functions describe image-processor --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
echo "Image Processor deployed at: $IMAGE_PROCESSOR_URL"

echo "Deploying Message Generator..."
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
MESSAGE_GENERATOR_URL=$(gcloud functions describe message-generator --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
echo "Message Generator deployed at: $MESSAGE_GENERATOR_URL"

echo "Deploying API Gateway..."
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
API_GATEWAY_URL=$(gcloud functions describe api-gateway --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
echo "API Gateway deployed at: $API_GATEWAY_URL"

echo "Backend deployment completed successfully!"
echo "API Gateway URL: $API_GATEWAY_URL"
echo ""
echo "Update your frontend .env.production file with:"
echo "VITE_API_URL=$API_GATEWAY_URL"
```

Save this script as `deploy.sh` in the `backend` directory, make it executable with `chmod +x deploy.sh`, and run it with your project ID:

```bash
./deploy.sh YOUR_PROJECT_ID
```

## Conclusion

You have now deployed the AI Housekeeping Advisor Bot application to Google Cloud Platform and Firebase Hosting. The application consists of three Cloud Functions for the backend and a React frontend hosted on Firebase or Cloud Run.

If you encounter any issues during deployment, refer to the verification steps and troubleshooting tips provided in this guide.
