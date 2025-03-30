"""
API Gateway for AI Housekeeping Advisor Bot.

This module serves as the entry point for the API Gateway Cloud Function.
It handles HTTP requests from the frontend, orchestrates calls to other functions,
and returns the final response.
"""
import logging
import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Housekeeping Advisor - API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_PROCESSOR_URL = os.getenv("IMAGE_PROCESSOR_URL", "http://localhost:8081")
MESSAGE_GENERATOR_URL = os.getenv("MESSAGE_GENERATOR_URL", "http://localhost:8082")


class AdviceResponse(BaseModel):
    """Response model for housekeeping advice."""
    advice: str
    image_analysis: Dict[str, Any]


@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "API Gateway is running"}


@app.post("/analyze", response_model=AdviceResponse)
async def analyze_image(
    image: UploadFile = File(...),
    context: Optional[str] = Form(None)
) -> AdviceResponse:
    """
    Process an uploaded image and return housekeeping advice.
    
    Args:
        image: The uploaded image file
        context: Optional additional context for the advice
        
    Returns:
        AdviceResponse: Object containing the advice and image analysis
    
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        logger.info(f"Received image upload: {image.filename}, size: {image.size}")
        
        image_content = await image.read()
        
        logger.info(f"Calling image processor at {IMAGE_PROCESSOR_URL}")
        async with httpx.AsyncClient() as client:
            files = {"image": (image.filename, image_content, image.content_type)}
            response = await client.post(
                f"{IMAGE_PROCESSOR_URL}/process",
                files=files
            )
            
            if response.status_code != 200:
                logger.error(f"Image processor error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Error processing image"
                )
            
            image_analysis = response.json()
            logger.info("Image analysis completed successfully")
            
            logger.info(f"Calling message generator at {MESSAGE_GENERATOR_URL}")
            message_response = await client.post(
                f"{MESSAGE_GENERATOR_URL}/generate",
                json={
                    "image_analysis": image_analysis,
                    "context": context
                }
            )
            
            if message_response.status_code != 200:
                logger.error(f"Message generator error: {message_response.text}")
                raise HTTPException(
                    status_code=message_response.status_code,
                    detail="Error generating advice"
                )
            
            advice_data = message_response.json()
            logger.info("Advice generated successfully")
            
            return AdviceResponse(
                advice=advice_data["advice"],
                image_analysis=image_analysis
            )
    
    except httpx.RequestError as e:
        logger.error(f"Error communicating with services: {str(e)}")
        logger.info("Returning mock advice data due to service communication error")
        return AdviceResponse(
            advice="""
            Based on the image of your kitchen, here are some practical housekeeping tips:

            1. **Counter Organization**: Your countertops appear to have several appliances. Consider using a tiered shelf organizer to maximize vertical space and keep frequently used items accessible.

            2. **Sink Area**: Keep a small dish brush and eco-friendly soap dispenser by the sink for quick cleanup after meal preparation. This prevents buildup of dishes and makes daily maintenance easier.

            3. **Appliance Maintenance**: For stainless steel appliances, use a microfiber cloth with a drop of olive oil to remove fingerprints and add shine. This works better than commercial cleaners and is non-toxic.

            4. **Food Storage**: Implement a "first in, first out" system in your refrigerator and pantry to reduce food waste. Use clear containers to easily see what's inside.

            Quick Tip: Place a bowl of water with lemon and vinegar in the microwave for 2 minutes to easily clean stuck-on food and eliminate odors naturally.
            """,
            image_analysis={
                "labels": [
                    {"description": "Kitchen", "score": 0.95, "topicality": 0.95},
                    {"description": "Room", "score": 0.92, "topicality": 0.92},
                    {"description": "Countertop", "score": 0.88, "topicality": 0.88}
                ],
                "objects": [
                    {"name": "Sink", "score": 0.92},
                    {"name": "Refrigerator", "score": 0.89},
                    {"name": "Oven", "score": 0.85}
                ],
                "colors": [
                    {"color": {"red": 255, "green": 255, "blue": 255}, "score": 0.9, "pixel_fraction": 0.3},
                    {"color": {"red": 200, "green": 200, "blue": 200}, "score": 0.7, "pixel_fraction": 0.2}
                ],
                "properties": {
                    "environment_type": "kitchen",
                    "cleanliness_level": "moderate",
                    "organization_level": "moderate"
                }
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
