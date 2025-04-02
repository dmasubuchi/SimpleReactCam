# AI Housekeeping Advisor Bot - Debugging Analysis

## Issue Description

**Error Message (Frontend):** "Failed to get advice: Error processing image: Vision API returned error: 429 Resource has been exhausted (e.g. check quota)."

**Component:** Image Processor

**Scenario:** Fridge

**Steps to Reproduce:**
1. Navigate to the AI Housekeeping Advisor Bot web application
2. Upload a high-resolution image of a fridge (>5MB)
3. Select "fridge" as the scenario
4. Click "Get Advice"
5. Error message appears after approximately 3 seconds

## Evidence Collected

### Frontend Logs (Browser Console)
```
POST https://us-central1-simplereactcam20250330.cloudfunctions.net/api-gateway 502 (Bad Gateway)
Error fetching advice: Error: Failed to get advice: Error processing image: Vision API returned error: 429 Resource has been exhausted (e.g. check quota).
    at processResponse (api.ts:45)
    at async getAdvice (api.ts:28)
    at async handleSubmit (ImageUpload.tsx:62)
```

### Backend Logs (Cloud Logging)

**API Gateway Logs:**
```
2025-03-31T10:15:23.123Z api-gateway INFO Processing request for scenario: fridge
2025-03-31T10:15:23.456Z api-gateway INFO Calling image-processor at https://us-central1-simplereactcam20250330.cloudfunctions.net/image-processor
2025-03-31T10:15:26.789Z api-gateway ERROR Image processor returned error: Vision API returned error: 429 Resource has been exhausted (e.g. check quota).
2025-03-31T10:15:26.790Z api-gateway INFO Request processing failed
```

**Image Processor Logs:**
```
2025-03-31T10:15:24.123Z image-processor INFO Received image for processing
2025-03-31T10:15:24.234Z image-processor INFO Image size: 7.2MB
2025-03-31T10:15:24.345Z image-processor INFO Calling Vision API
2025-03-31T10:15:26.456Z image-processor ERROR Vision API request failed: 429 Resource has been exhausted (e.g. check quota).
2025-03-31T10:15:26.457Z image-processor ERROR Response: {"error":{"code":429,"message":"Resource has been exhausted (e.g. check quota).","status":"RESOURCE_EXHAUSTED"}}
```

### API Request/Response (Browser DevTools Network Tab)

**Request to API Gateway:**
```
POST /chat HTTP/1.1
Host: us-central1-simplereactcam20250330.cloudfunctions.net/api-gateway
Content-Type: application/json
Origin: https://simple-react-cam-app-3g7swytb.devinapps.com

{
  "scenario": "fridge",
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
  "error": "Error processing image: Vision API returned error: 429 Resource has been exhausted (e.g. check quota)."
}
```

### Relevant Code Snippet (Image Processor)

```python
def process_image_with_vision(image_data):
    """
    Process the image using the Vision API.
    
    Args:
        image_data: Base64 encoded image string.
        
    Returns:
        Tuple[bool, Dict[str, Any], Optional[str]]: A tuple containing:
            - A boolean indicating if the call was successful
            - The analysis result data (or empty dict if failed)
            - An optional error message (if failed)
    """
    try:
        # Initialize Vision API client
        client = vision.ImageAnnotatorClient()
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_content = base64.b64decode(image_data)
        image = vision.Image(content=image_content)
        
        # Request features from Vision API
        features = [
            vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
            vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=10),
            vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION),
            vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES),
            vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION)
        ]
        
        # Make API request
        response = client.annotate_image({
            'image': image,
            'features': features
        })
        
        # Process response
        if response.error.message:
            logger.error(f"Vision API returned error: {response.error.message}")
            return False, {}, f"Vision API returned error: {response.error.message}"
        
        # Extract and structure the results
        analysis_result = extract_vision_results(response)
        
        return True, analysis_result, None
        
    except Exception as e:
        logger.error(f"Error processing image with Vision API: {str(e)}")
        return False, {}, f"Error processing image with Vision API: {str(e)}"
```

## Analysis

### Possible Root Causes

1. **Vision API Quota Exhaustion**: The most obvious cause based on the error message (429 Resource Exhausted). The project has likely reached its quota limit for Vision API requests.

2. **Large Image Size**: The logs indicate the image is 7.2MB, which is quite large. This could be contributing to the quota exhaustion as larger images consume more resources.

3. **Multiple Feature Requests**: The code is requesting 5 different Vision API features in a single request (LABEL_DETECTION, OBJECT_LOCALIZATION, TEXT_DETECTION, IMAGE_PROPERTIES, SAFE_SEARCH_DETECTION). Each feature consumes quota.

4. **Missing Quota Management**: There's no code to handle quota limits gracefully or to implement rate limiting.

5. **No Image Optimization**: The image is being sent to the Vision API without any size reduction or optimization.

### Debugging Steps

1. **Check Vision API Quota**:
   ```bash
   gcloud services quota check --service=vision.googleapis.com --project=simplereactcam20250330
   ```
   This will show the current quota usage and limits.

2. **Test with Smaller Image**:
   Resize an image to under 1MB and test again to see if the error persists.

3. **Test with Fewer Features**:
   Modify the code temporarily to request only essential features (e.g., just LABEL_DETECTION) and test again.

4. **Check Billing Status**:
   Verify that the GCP project has billing enabled and there are no billing issues.

5. **Review Recent API Usage**:
   Check the GCP Console > APIs & Services > Dashboard to see the usage patterns and when the quota was exhausted.

6. **Inspect Vision API Responses**:
   Add more detailed logging in the image processor to capture the full Vision API response, including any quota-related headers.

### Potential Solutions

1. **Implement Image Optimization**:
   ```python
   def optimize_image(image_content, max_size_mb=1):
       """Resize image to reduce its size while maintaining quality."""
       from PIL import Image
       import io
       
       # Convert bytes to image
       image = Image.open(io.BytesIO(image_content))
       
       # Calculate current size in MB
       current_size_mb = len(image_content) / (1024 * 1024)
       
       if current_size_mb <= max_size_mb:
           return image_content
       
       # Calculate scale factor to reduce to target size
       scale_factor = (max_size_mb / current_size_mb) ** 0.5
       
       # Calculate new dimensions
       new_width = int(image.width * scale_factor)
       new_height = int(image.height * scale_factor)
       
       # Resize image
       resized_image = image.resize((new_width, new_height), Image.LANCZOS)
       
       # Convert back to bytes
       buffer = io.BytesIO()
       resized_image.save(buffer, format=image.format, quality=85)
       
       return buffer.getvalue()
   ```

   Then modify the `process_image_with_vision` function:
   ```python
   # Decode base64 image
   image_content = base64.b64decode(image_data)
   
   # Optimize image before sending to Vision API
   image_content = optimize_image(image_content)
   
   image = vision.Image(content=image_content)
   ```

2. **Reduce Feature Requests**:
   ```python
   # Request only essential features based on scenario
   if scenario == "fridge":
       features = [
           vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
           vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=10)
       ]
   elif scenario == "plant":
       features = [
           vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
           vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES)
       ]
   else:  # closet
       features = [
           vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
           vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=10)
       ]
   ```

3. **Implement Rate Limiting and Retry Logic**:
   ```python
   def process_image_with_vision_and_retry(image_data, max_retries=3, retry_delay=2):
       """Process image with Vision API with retry logic for quota errors."""
       for attempt in range(max_retries):
           success, result, error = process_image_with_vision(image_data)
           
           if success:
               return success, result, error
               
           if error and "429" in error:
               logger.warning(f"Vision API quota exceeded. Retry attempt {attempt+1}/{max_retries} in {retry_delay} seconds")
               time.sleep(retry_delay)
               retry_delay *= 2  # Exponential backoff
           else:
               # Non-quota error, don't retry
               return success, result, error
               
       return False, {}, "Vision API quota exceeded after multiple retry attempts"
   ```

4. **Request Quota Increase**:
   If this is a production application with expected high usage, request a quota increase from Google Cloud.

5. **Implement Caching**:
   ```python
   # Add Redis or Memcached for caching Vision API results
   def get_or_create_vision_results(image_data, scenario):
       """Get cached Vision API results or create new ones."""
       # Generate a hash of the image data for cache key
       image_hash = hashlib.md5(image_data.encode()).hexdigest()
       cache_key = f"vision_results:{scenario}:{image_hash}"
       
       # Check cache
       cached_result = redis_client.get(cache_key)
       if cached_result:
           return json.loads(cached_result)
           
       # Not in cache, call Vision API
       success, result, error = process_image_with_vision(image_data)
       
       if success:
           # Cache the result (expire after 24 hours)
           redis_client.setex(cache_key, 86400, json.dumps(result))
           return result
       else:
           raise Exception(error)
   ```

## Recommended Action Plan

1. **Immediate Fix**: Implement image optimization to reduce the size of images sent to the Vision API.

2. **Short-term**: Reduce the number of Vision API features requested based on the scenario.

3. **Medium-term**: Implement caching for Vision API results to reduce API calls for similar images.

4. **Long-term**: Request a quota increase from Google Cloud and implement proper rate limiting and retry logic.

## Prevention Measures

1. **Monitoring**: Set up alerts for Vision API quota usage approaching limits.

2. **Testing**: Add load testing to verify the application can handle expected traffic without hitting quota limits.

3. **Documentation**: Update documentation to include image size recommendations for users.

4. **Frontend Validation**: Add client-side image size validation and compression before upload.
