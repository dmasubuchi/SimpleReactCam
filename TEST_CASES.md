# AI Housekeeping Advisor Bot - Test Cases

This document provides a comprehensive list of test cases for the AI Housekeeping Advisor Bot application.

## Core Functionality Tests

| Test ID | Scenario | Description | Expected Result | Priority |
|---------|----------|-------------|----------------|----------|
| CF-01 | Plant | Upload a clear image of a healthy plant | Receive relevant plant care advice | High |
| CF-02 | Plant | Upload an image of a plant with visible issues (yellowing leaves, etc.) | Receive advice addressing the visible plant issues | High |
| CF-03 | Closet | Upload an image of an organized closet | Receive positive feedback and minor improvement suggestions | High |
| CF-04 | Closet | Upload an image of a disorganized closet | Receive specific organization advice | High |
| CF-05 | Fridge | Upload an image of a well-stocked fridge | Receive food storage and meal planning advice | High |
| CF-06 | Fridge | Upload an image of an empty or poorly stocked fridge | Receive shopping suggestions and food storage advice | High |

## Input Validation Tests

| Test ID | Scenario | Description | Expected Result | Priority |
|---------|----------|-------------|----------------|----------|
| IV-01 | Any | Upload a non-image file (e.g., PDF, text file) | Receive clear error message about invalid file type | High |
| IV-02 | Any | Upload an image larger than 10MB | Receive clear error message about file size limit | Medium |
| IV-03 | Any | Upload a corrupted image file | Receive clear error message about invalid image | Medium |
| IV-04 | Any | Send request without 'scenario' parameter | Receive clear error message about missing scenario | High |
| IV-05 | Any | Send request without 'image_data' parameter | Receive clear error message about missing image data | High |
| IV-06 | Any | Send request with invalid 'scenario' value | Receive clear error message about invalid scenario | Medium |

## Error Handling Tests

| Test ID | Scenario | Description | Expected Result | Priority |
|---------|----------|-------------|----------------|----------|
| EH-01 | Any | Simulate Vision API failure | Receive user-friendly error message; detailed logs in Cloud Logging | High |
| EH-02 | Any | Simulate Gemini API failure | Receive user-friendly error message; detailed logs in Cloud Logging | High |
| EH-03 | Any | Simulate Gemini API safety block/refusal | Receive appropriate message about content policy; logs in Cloud Logging | Medium |
| EH-04 | Any | Simulate backend function timeout | Receive timeout error message; detailed logs in Cloud Logging | Medium |
| EH-05 | Any | Simulate network error between frontend and backend | Display connection error message to user | Medium |
| EH-06 | Any | Simulate network error between backend functions | Receive error message; detailed logs in Cloud Logging | Medium |

## Edge Case Tests

| Test ID | Scenario | Description | Expected Result | Priority |
|---------|----------|-------------|----------------|----------|
| EC-01 | Any | Upload a completely blank white image | Receive message about insufficient image content | Medium |
| EC-02 | Any | Upload an extremely cluttered/complex image | Process image and provide relevant advice | Medium |
| EC-03 | Plant | Upload an image unrelated to plants (e.g., car) | Receive message indicating no plants detected | Medium |
| EC-04 | Closet | Upload an image unrelated to closets (e.g., kitchen) | Receive message indicating no closet detected | Medium |
| EC-05 | Fridge | Upload an image unrelated to fridges (e.g., living room) | Receive message indicating no fridge detected | Medium |
| EC-06 | Any | Upload an image with text in a foreign language | Process image and provide relevant advice based on visual content | Low |

## UI/UX Tests

| Test ID | Scenario | Description | Expected Result | Priority |
|---------|----------|-------------|----------------|----------|
| UX-01 | Any | Verify loading indicator during image processing | Loading indicator displays correctly during processing | High |
| UX-02 | Any | Test application responsiveness during loading | UI remains responsive while processing image | Medium |
| UX-03 | Any | Verify error message clarity and helpfulness | Error messages are clear, helpful, and actionable | High |
| UX-04 | Any | Test layout on different browser window sizes | Layout adjusts appropriately to different screen sizes | Medium |
| UX-05 | Any | Test chat message scrolling with many messages | Messages scroll properly and newest messages are visible | Medium |

## Concurrency Tests

| Test ID | Scenario | Description | Expected Result | Priority |
|---------|----------|-------------|----------------|----------|
| CC-01 | Any | Send multiple image requests in quick succession | All requests processed correctly without errors | Low |
| CC-02 | Mixed | Send different scenario requests simultaneously | Each request processed correctly with appropriate response | Low |

## Performance Tests

| Test ID | Scenario | Description | Expected Result | Priority |
|---------|----------|-------------|----------------|----------|
| PF-01 | Any | Measure end-to-end response time | Response time within acceptable limits (< 10 seconds) | Medium |
| PF-02 | Any | Measure Vision API response time | Vision API response time within acceptable limits (< 3 seconds) | Medium |
| PF-03 | Any | Measure Gemini API response time | Gemini API response time within acceptable limits (< 5 seconds) | Medium |

## Security Tests

| Test ID | Scenario | Description | Expected Result | Priority |
|---------|----------|-------------|----------------|----------|
| SC-01 | Any | Verify CORS configuration | Only allowed origins can access the API | High |
| SC-02 | Any | Test API access without proper authentication | Unauthorized access is blocked | High |
| SC-03 | Any | Verify secure handling of API keys | API keys are not exposed in frontend or logs | High |

## Debugging Support

For debugging issues, follow these steps:

1. Check frontend console logs for client-side errors
2. Examine network requests in browser DevTools
3. Check Cloud Logging for backend function logs
4. Verify environment variables are set correctly
5. Test API endpoints directly using curl or Postman
6. Verify IAM permissions for service accounts
7. Check for cold start delays in Cloud Functions

