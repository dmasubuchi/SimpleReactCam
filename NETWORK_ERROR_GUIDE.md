# Network Error Troubleshooting Guide for AI Housekeeping Advisor Bot

This guide addresses the "Network Error" issue that occurs when using the AI Housekeeping Advisor Bot application.

## Problem Description

When attempting to get advice from the AI Housekeeping Advisor Bot, a "Network Error" message appears at the bottom of the screen after clicking the "Get Advice" button.

![Network Error Screenshot](https://app.devin.ai/attachments/e73e7e7c-9be9-41dd-b4d2-f85b98b8d85d/image.png)

## Root Cause Analysis

The network error occurs because the frontend application is trying to communicate with backend Cloud Functions that have not been properly deployed or configured. Specifically:

1. The frontend is deployed at: `https://simple-react-cam-app-3g7swytb.devinapps.com/`
2. The frontend is configured to call an API Gateway URL that is not valid
3. In the `.env.production` file, the `VITE_API_URL` is set to a placeholder value: `https://api-gateway-url-from-deployment`
4. The backend Cloud Functions have not been successfully deployed due to GCP organization policy restrictions

## Solution Steps

### 1. Deploy Backend Cloud Functions

The backend consists of three Cloud Functions that need to be deployed:
- `image-processor`: Processes images using Google Cloud Vision API
- `message-generator`: Generates advice using Google Vertex AI Gemini API
- `api-gateway`: Coordinates between the frontend and the other two functions

To deploy the backend:

```bash
# Navigate to the backend directory
cd ~/repos/SimpleReactCam/backend

# Make the deployment script executable
chmod +x deploy_secure.sh

# Deploy with your GCP project ID
./deploy_secure.sh YOUR_PROJECT_ID us-central1
```

**Note:** The deployment script is designed to work with GCP organization policies that require authentication for Cloud Functions. If you encounter permission issues, you may need to:

1. Ensure you're authenticated with gcloud: `gcloud auth login`
2. Verify you have the necessary IAM roles: `roles/cloudfunctions.developer`, `roles/iam.serviceAccountUser`
3. Request exceptions to organization policies if needed

### 2. Update Frontend Configuration

After successful backend deployment, you need to update the frontend configuration with the actual API Gateway URL:

```bash
# Get the API Gateway URL from the deployment output
API_GATEWAY_URL=$(gcloud functions describe api-gateway --gen2 --region=us-central1 --project=YOUR_PROJECT_ID --format="value(serviceConfig.uri)")

# Update the frontend .env.production file
cd ~/repos/SimpleReactCam/frontend
echo "VITE_API_URL=$API_GATEWAY_URL" > .env.production

# Rebuild and redeploy the frontend
npm install
npm run build
# Deploy the build directory to your hosting service
```

### 3. Configure Authentication (If Required)

Since the Cloud Functions are deployed without the `--allow-unauthenticated` flag, you need to set up authentication:

```bash
# Grant invoker role to your account
gcloud functions add-iam-policy-binding api-gateway \
  --region=us-central1 \
  --member=user:YOUR_EMAIL@example.com \
  --role=roles/cloudfunctions.invoker \
  --project=YOUR_PROJECT_ID
```

For frontend-to-backend authentication, implement a token-based approach:

1. Set up Firebase Authentication or similar service
2. Generate and include authentication tokens in API requests
3. Verify tokens in the Cloud Functions

## Alternative Solutions

If you cannot deploy the backend due to organization policies, consider these alternatives:

### Option 1: Local Backend Development

Run the backend locally for testing:

```bash
# Navigate to the backend directory
cd ~/repos/SimpleReactCam/backend

# Install dependencies for each function
cd api-gateway && pip install -r requirements.txt
cd ../image-processor && pip install -r requirements.txt
cd ../message-generator && pip install -r requirements.txt

# Run the functions locally
cd ../api-gateway
functions-framework --target=api_gateway --debug
```

Then update the frontend to use the local backend URL:

```bash
# Create a .env.development file
cd ~/repos/SimpleReactCam/frontend
echo "VITE_API_URL=http://localhost:8080" > .env.development

# Run the frontend in development mode
npm start
```

### Option 2: Mock Backend

Implement a mock backend in the frontend code that returns predefined responses:

```typescript
// Create a mock API service
// src/services/mockApi.ts

export const getAdvice = async (imageData: string, scenario: string) => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  // Return mock response based on scenario
  switch (scenario) {
    case 'plant':
      return {
        success: true,
        data: {
          advice: "Your plant appears to be a peace lily. It needs indirect light and weekly watering. The leaves look slightly droopy, which suggests it might need more water. Try watering it thoroughly and ensure good drainage."
        },
        error: null
      };
    case 'closet':
      return {
        success: true,
        data: {
          advice: "Your closet could benefit from better organization. Consider using shelf dividers for folded clothes, installing hooks for bags, and using uniform hangers. Group similar items together and consider seasonal rotation to maximize space."
        },
        error: null
      };
    case 'fridge':
      return {
        success: true,
        data: {
          advice: "Your refrigerator could use some organization. Store dairy on the middle shelf, vegetables in the crisper drawers, and avoid storing milk in the door. Clean out expired items weekly and use clear containers to see leftovers easily."
        },
        error: null
      };
    default:
      return {
        success: false,
        data: null,
        error: "Unknown scenario"
      };
  }
};
```

Then update the frontend to use the mock API instead of the real one.

## Debugging Tips

If you continue to experience network errors after following these steps:

1. Check browser console for specific error messages
2. Verify CORS configuration in the API Gateway function
3. Test the API Gateway directly using curl or Postman
4. Check Cloud Function logs for errors:
   ```bash
   gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=api-gateway" --project=YOUR_PROJECT_ID --limit=10
   ```

## Conclusion

The "Network Error" is primarily caused by missing or misconfigured backend services. By properly deploying the Cloud Functions and updating the frontend configuration, you should be able to resolve this issue and get the AI Housekeeping Advisor Bot working correctly.
