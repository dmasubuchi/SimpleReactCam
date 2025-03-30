# AI Housekeeping Advisor Bot - Debugging Example

This document provides a practical example of debugging a specific issue in the AI Housekeeping Advisor Bot application.

## Issue Description

**Error Message (Frontend):** "Failed to get advice: Message generator error: Gemini API returned an error: 400 Bad Request"

**Component:** Message Generator

**Scenario:** Closet

**Steps to Reproduce:**
1. Navigate to the AI Housekeeping Advisor Bot web application
2. Upload an image of a closet
3. Select "closet" as the scenario
4. Click "Get Advice"
5. Error message appears after approximately 5 seconds

## Evidence Collected

### Frontend Logs (Browser Console)

```
POST https://us-central1-simplereactcam20250330.cloudfunctions.net/api-gateway 502 (Bad Gateway)
Error fetching advice: Error: Failed to get advice: Message generator error: Gemini API returned an error: 400 Bad Request
    at processResponse (api.ts:45)
    at async getAdvice (api.ts:28)
    at async handleSubmit (ImageUpload.tsx:62)
```

### Backend Logs (Cloud Logging)

**API Gateway Logs:**
```
2025-03-30T16:45:23.123Z api-gateway INFO Processing request for scenario: closet
2025-03-30T16:45:24.456Z api-gateway INFO Successfully received analysis result from image-processor
2025-03-30T16:45:24.789Z api-gateway INFO Calling message-generator at https://us-central1-simplereactcam20250330.cloudfunctions.net/message-generator
2025-03-30T16:45:28.012Z api-gateway ERROR Message generator returned error: Gemini API returned an error: 400 Bad Request
```

**Message Generator Logs:**
```
2025-03-30T16:45:25.123Z message-generator INFO Received request for scenario: closet
2025-03-30T16:45:25.456Z message-generator INFO Constructing prompt with analysis result
2025-03-30T16:45:25.789Z message-generator INFO Calling Gemini API
2025-03-30T16:45:27.890Z message-generator ERROR Gemini API returned an error: 400 Bad Request
2025-03-30T16:45:27.891Z message-generator ERROR Request payload: {"contents":[{"parts":[{"text":"You are an AI Housekeeping Advisor specializing in closet organization. Based on the following analysis of a closet image, provide practical advice for organizing, cleaning, and maintaining the closet. Analysis: {\"labels\":[\"Closet\",\"Wardrobe\",\"Furniture\",\"Room\",\"Clothes hanger\",\"Shelf\"],\"objects\":[{\"name\":\"Clothes\",\"confidence\":0.92},{\"name\":\"Shelf\",\"confidence\":0.87},{\"name\":\"Hanger\",\"confidence\":0.85},{\"name\":\"Box\",\"confidence\":0.76}],\"colors\":[\"White\",\"Brown\",\"Black\",\"Blue\"],\"text_annotations\":[],\"safe_search\":{\"adult\":\"VERY_UNLIKELY\",\"spoof\":\"VERY_UNLIKELY\",\"medical\":\"VERY_UNLIKELY\",\"violence\":\"VERY_UNLIKELY\",\"racy\":\"VERY_UNLIKELY\"},\"image_properties\":{\"dominant_colors\":[\"White\",\"Brown\"]}}"}]},{"role":"model"}]}
2025-03-30T16:45:27.892Z message-generator ERROR Response: {"error":{"code":400,"message":"Invalid JSON payload received. Unknown name \"role\": Cannot find field.","status":"INVALID_ARGUMENT","details":[{"@type":"type.googleapis.com/google.rpc.BadRequest","fieldViolations":[{"field":"","description":"Invalid JSON payload received. Unknown name \"role\": Cannot find field."}]}]}}
```

### API Request/Response (Browser DevTools Network Tab)

**Request to API Gateway:**
```
POST /chat HTTP/1.1
Host: us-central1-simplereactcam20250330.cloudfunctions.net/api-gateway
Content-Type: application/json
Origin: https://simple-react-cam-app-3g7swytb.devinapps.com

{
  "scenario": "closet",
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/4gIcSUNDX1BST0ZJTEUAAQEAAAIMbGNtcwIQAABtbnRyUkdCIFhZWiAH3..."
}
```

**Response from API Gateway:**
```
HTTP/1.1 502 Bad Gateway
Content-Type: application/json
Access-Control-Allow-Origin: https://simple-react-cam-app-3g7swytb.devinapps.com

{
  "success": false,
  "error": "Message generator error: Gemini API returned an error: 400 Bad Request"
}
```

## Root Cause Analysis

### Identified Cause

The root cause of this issue is an **incorrect format in the Gemini API request payload**. Specifically, the error message indicates:

```
Invalid JSON payload received. Unknown name "role": Cannot find field.
```

Looking at the request payload in the message-generator logs, we can see that the request includes a `"role":"model"` field, which is causing the 400 Bad Request error. This suggests that the code is using an incorrect format for the Gemini API request.

### Affected Components

- `message-generator` Cloud Function
- Specifically, the code that constructs the Gemini API request payload

### Impact

- Users are unable to get advice for any scenario (not just closet)
- The error is consistent and reproducible
- This is a critical issue blocking the core functionality of the application

## Resolution

### Fix Applied

The issue can be fixed by updating the Gemini API request format in the `message-generator` function. The current code appears to be using a format that's incompatible with the Gemini API.

Here's the corrected code for the Gemini API request in `message-generator/src/main.py`:

```python
def generate_advice_with_gemini(scenario, analysis_result):
    """
    Generate advice using the Gemini API based on the scenario and analysis result.
    
    Args:
        scenario: The scenario identifier (plant, closet, or fridge).
        analysis_result: The analysis result from the image-processor.
        
    Returns:
        Tuple[bool, str, Optional[str]]: A tuple containing:
            - A boolean indicating if the call was successful
            - The generated advice (or empty string if failed)
            - An optional error message (if failed)
    """
    try:
        # Construct the prompt based on the scenario
        prompt = construct_prompt(scenario, analysis_result)
        
        # Initialize Gemini API client
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Extract the generated text
        if response.candidates and response.candidates[0].content.parts:
            advice = response.candidates[0].content.parts[0].text
            return True, advice, None
        else:
            return False, "", "Gemini API returned empty response"
    
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        return False, "", f"Gemini API returned an error: {str(e)}"
```

The key change is removing the incorrect format with `"role":"model"` and using the proper Gemini API client methods.

### Verification Steps

1. Deploy the updated `message-generator` function
2. Test with a closet image
3. Verify that advice is generated successfully
4. Check Cloud Logging to confirm no more 400 Bad Request errors

### Prevention Measures

1. Add unit tests for the Gemini API request format
2. Implement better error handling to provide more detailed error messages
3. Add documentation about the correct Gemini API request format
4. Consider implementing a staging environment for testing API changes before production

## Lessons Learned

1. **API Format Changes**: Always verify API request formats against the latest documentation, as they may change over time.
2. **Detailed Error Logging**: The detailed error logs were crucial in identifying the root cause quickly.
3. **Request/Response Inspection**: Logging both the request payload and error response helped pinpoint the exact issue.
4. **Testing Process**: Implement a more thorough testing process for API integrations before deployment.
