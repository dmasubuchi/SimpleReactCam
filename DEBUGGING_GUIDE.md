# AI Housekeeping Advisor Bot - Debugging Guide

This document provides a comprehensive guide for debugging issues in the AI Housekeeping Advisor Bot application.

## Common Issues and Troubleshooting Steps

### 1. Frontend Issues

#### 1.1 Image Upload Failures

**Symptoms:**
- "Failed to upload image" error
- No response after clicking upload button
- Console errors related to file handling

**Troubleshooting Steps:**
1. Check browser console for JavaScript errors
2. Verify image format (JPG, PNG, GIF) and size (< 10MB)
3. Check network tab for failed requests
4. Verify CORS headers in API responses

**Potential Solutions:**
- Implement client-side image compression
- Add more detailed error handling in upload component
- Verify CORS configuration in Cloud Functions

#### 1.2 UI Rendering Issues

**Symptoms:**
- Components not displaying correctly
- Missing elements or styles
- Layout breaks on certain screen sizes

**Troubleshooting Steps:**
1. Check browser console for React errors
2. Inspect DOM elements using browser developer tools
3. Test on different browsers and screen sizes
4. Verify CSS imports and styles

**Potential Solutions:**
- Add responsive design breakpoints
- Fix CSS specificity issues
- Implement error boundaries in React components

### 2. Backend Issues

#### 2.1 API Gateway Failures

**Symptoms:**
- 500 Internal Server Error responses
- Timeout errors
- "Failed to get advice" errors

**Troubleshooting Steps:**
1. Check Cloud Logging for api-gateway function errors
2. Verify environment variables (IMAGE_PROCESSOR_URL, MESSAGE_GENERATOR_URL)
3. Test direct API calls using curl or Postman
4. Check IAM permissions for service accounts

**Potential Solutions:**
- Fix environment variable configuration
- Increase function timeout settings
- Implement better error handling and logging
- Grant necessary IAM permissions

#### 2.2 Image Processor Issues

**Symptoms:**
- "Failed to process image" errors
- Vision API errors in logs
- Empty or incomplete analysis results

**Troubleshooting Steps:**
1. Check Cloud Logging for image-processor function errors
2. Verify Vision API credentials and permissions
3. Test with different image types and sizes
4. Check Vision API quotas and limits

**Potential Solutions:**
- Update Vision API credentials
- Optimize image before sending to Vision API
- Implement fallback analysis methods
- Increase Vision API quotas if needed

#### 2.3 Message Generator Issues

**Symptoms:**
- "Failed to generate advice" errors
- Gemini API errors in logs
- Empty or irrelevant advice responses

**Troubleshooting Steps:**
1. Check Cloud Logging for message-generator function errors
2. Verify Gemini API credentials and permissions
3. Inspect the prompts being sent to Gemini API
4. Check for safety blocks or content policy violations

**Potential Solutions:**
- Update Gemini API credentials
- Refine prompts for better responses
- Implement fallback advice generation
- Handle safety blocks gracefully

### 3. Integration Issues

#### 3.1 Cross-Function Communication

**Symptoms:**
- Timeouts between function calls
- Incomplete data passed between functions
- Inconsistent error handling

**Troubleshooting Steps:**
1. Add correlation IDs to track requests across functions
2. Check logs with matching timestamps across functions
3. Verify data formats passed between functions
4. Test each function independently

**Potential Solutions:**
- Standardize error handling across functions
- Implement request tracing with correlation IDs
- Validate data schemas between functions
- Increase timeouts for function-to-function calls

#### 3.2 Authentication Issues

**Symptoms:**
- 403 Forbidden errors
- "Unauthorized" errors in logs
- Functions unable to call each other

**Troubleshooting Steps:**
1. Check IAM roles and permissions
2. Verify service account configurations
3. Test with explicit authentication tokens
4. Check for organization policy constraints

**Potential Solutions:**
- Grant necessary IAM roles to service accounts
- Configure function-to-function authentication
- Implement token-based authentication
- Request organization policy exceptions if needed

## Debugging Tools and Techniques

### 1. Cloud Logging

**How to Use:**
```bash
# View logs for a specific function
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=api-gateway" --project=YOUR_PROJECT_ID --limit=10

# Filter logs by severity
gcloud logging read "resource.type=cloud_function AND severity>=ERROR" --project=YOUR_PROJECT_ID --limit=10

# Search for specific error messages
gcloud logging read "resource.type=cloud_function AND textPayload:\"Failed to call\"" --project=YOUR_PROJECT_ID --limit=10
```

### 2. Cloud Trace

**How to Use:**
1. Enable Cloud Trace API in your GCP project
2. Add trace instrumentation to your functions
3. View traces in the GCP Console
4. Analyze latency and bottlenecks

### 3. Local Testing

**How to Use:**
```bash
# Test image-processor locally
cd backend/image-processor
functions-framework --target=image_processor --debug

# Test message-generator locally
cd backend/message-generator
functions-framework --target=message_generator --debug

# Test api-gateway locally
cd backend/api-gateway
functions-framework --target=api_gateway --debug
```

### 4. Direct API Testing

**How to Use:**
```bash
# Test api-gateway directly
curl -X POST https://YOUR_REGION-YOUR_PROJECT_ID.cloudfunctions.net/api-gateway \
  -H "Content-Type: application/json" \
  -d '{"scenario": "plant", "image_data": "BASE64_ENCODED_IMAGE"}'

# Test with authentication
curl -X POST https://YOUR_REGION-YOUR_PROJECT_ID.cloudfunctions.net/api-gateway \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -d '{"scenario": "plant", "image_data": "BASE64_ENCODED_IMAGE"}'
```

## Root Cause Analysis Template

When encountering issues, use this template to document and analyze the problem:

### Issue Description
- **Error Message:** [Copy exact error message]
- **Component:** [Frontend/API Gateway/Image Processor/Message Generator]
- **Scenario:** [Plant/Closet/Fridge]
- **Steps to Reproduce:** [List exact steps]

### Evidence Collected
- **Frontend Logs:** [Browser console errors]
- **Backend Logs:** [Cloud Logging entries]
- **Network Requests:** [API calls and responses]
- **Environment Variables:** [Relevant configurations]

### Root Cause Analysis
- **Identified Cause:** [Description of the root cause]
- **Affected Components:** [List all affected components]
- **Impact:** [Describe the user impact]

### Resolution
- **Fix Applied:** [Description of the solution]
- **Verification Steps:** [How to verify the fix]
- **Prevention Measures:** [How to prevent similar issues]

## Performance Optimization

For performance-related issues, refer to the [PERFORMANCE_ANALYSIS.md](PERFORMANCE_ANALYSIS.md) document.
