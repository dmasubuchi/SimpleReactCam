"""
Image Processor for AI Housekeeping Advisor Bot.

This module serves as the entry point for the Image Processor Cloud Function.
It receives image data, calls the Cloud Vision API, parses the results,
and returns structured information (JSON).
"""
import base64
import logging
import os
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Housekeeping Advisor - Image Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vision_client = None
try:
    from google.cloud import vision
    vision_client = vision.ImageAnnotatorClient()
    logger.info("Successfully initialized Vision API client")
except Exception as e:
    logger.warning(f"Could not initialize Vision API client: {str(e)}")
    logger.warning("Using mock data for development")
    vision_client = None


class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis."""
    labels: List[Dict[str, Any]]
    objects: List[Dict[str, Any]]
    text: Optional[str] = None
    colors: List[Dict[str, Any]]
    properties: Dict[str, Any]


@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "Image Processor is running"}


@app.post("/process", response_model=ImageAnalysisResponse)
async def process_image(image: UploadFile = File(...)) -> ImageAnalysisResponse:
    """
    Process an uploaded image using Google Cloud Vision API.
    If Vision API is not available, returns mock data for development.
    
    Args:
        image: The uploaded image file
        
    Returns:
        ImageAnalysisResponse: Structured information about the image
    
    Raises:
        HTTPException: If there's an error processing the image
    """
    try:
        logger.info(f"Processing image: {image.filename}, size: {image.size}")
        
        image_content = await image.read()
        
        if vision_client:
            vision_image = vision.Image(content=image_content)
            
            features = [
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION),
                vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION),
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION),
                vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES),
            ]
            
            logger.info("Calling Vision API for image analysis")
            response = vision_client.annotate_image({
                'image': vision_image,
                'features': features,
            })
            
            labels = []
            for label in response.label_annotations:
                labels.append({
                    "description": label.description,
                    "score": label.score,
                    "topicality": label.topicality
                })
            
            objects = []
            for obj in response.localized_object_annotations:
                objects.append({
                    "name": obj.name,
                    "score": obj.score,
                    "bounding_poly": [
                        {"x": vertex.x, "y": vertex.y}
                        for vertex in obj.bounding_poly.normalized_vertices
                    ]
                })
            
            text = None
            if response.text_annotations:
                text = response.text_annotations[0].description
            
            colors = []
            if response.image_properties:
                for color in response.image_properties.dominant_colors.colors:
                    colors.append({
                        "color": {
                            "red": color.color.red,
                            "green": color.color.green,
                            "blue": color.color.blue
                        },
                        "score": color.score,
                        "pixel_fraction": color.pixel_fraction
                    })
        else:
            logger.info("Using mock data for development (Vision API not available)")
            
            labels = [
                {"description": "Kitchen", "score": 0.95, "topicality": 0.95},
                {"description": "Room", "score": 0.92, "topicality": 0.92},
                {"description": "Countertop", "score": 0.88, "topicality": 0.88},
                {"description": "Cabinetry", "score": 0.85, "topicality": 0.85},
                {"description": "Sink", "score": 0.82, "topicality": 0.82},
                {"description": "Appliance", "score": 0.80, "topicality": 0.80},
                {"description": "Clean", "score": 0.75, "topicality": 0.75}
            ]
            
            objects = [
                {
                    "name": "Sink", 
                    "score": 0.92,
                    "bounding_poly": [
                        {"x": 0.2, "y": 0.3}, {"x": 0.4, "y": 0.3},
                        {"x": 0.4, "y": 0.5}, {"x": 0.2, "y": 0.5}
                    ]
                },
                {
                    "name": "Refrigerator", 
                    "score": 0.89,
                    "bounding_poly": [
                        {"x": 0.6, "y": 0.2}, {"x": 0.8, "y": 0.2},
                        {"x": 0.8, "y": 0.7}, {"x": 0.6, "y": 0.7}
                    ]
                },
                {
                    "name": "Oven", 
                    "score": 0.85,
                    "bounding_poly": [
                        {"x": 0.1, "y": 0.6}, {"x": 0.3, "y": 0.6},
                        {"x": 0.3, "y": 0.8}, {"x": 0.1, "y": 0.8}
                    ]
                }
            ]
            
            text = "Kitchen with modern appliances"
            
            colors = [
                {
                    "color": {"red": 255, "green": 255, "blue": 255},
                    "score": 0.4,
                    "pixel_fraction": 0.3
                },
                {
                    "color": {"red": 200, "green": 200, "blue": 200},
                    "score": 0.3,
                    "pixel_fraction": 0.2
                },
                {
                    "color": {"red": 50, "green": 50, "blue": 50},
                    "score": 0.2,
                    "pixel_fraction": 0.1
                }
            ]
        
        properties = {
            "environment_type": "unknown",
            "cleanliness_level": "unknown",
            "organization_level": "unknown"
        }
        
        environment_labels = {"kitchen", "bathroom", "bedroom", "living room", "dining room"}
        for label in labels:
            if label["description"].lower() in environment_labels:
                properties["environment_type"] = label["description"].lower()
                break
        
        cleanliness_indicators = {
            "clean": ["clean", "tidy", "organized", "neat", "spotless"],
            "moderate": ["lived in", "used", "normal"],
            "dirty": ["dirty", "messy", "cluttered", "disorganized", "stained"]
        }
        
        for level, indicators in cleanliness_indicators.items():
            for label in labels:
                if any(indicator in label["description"].lower() for indicator in indicators):
                    properties["cleanliness_level"] = level
                    break
            if properties["cleanliness_level"] != "unknown":
                break
        
        if len(objects) > 10:
            properties["organization_level"] = "cluttered"
        elif len(objects) > 5:
            properties["organization_level"] = "moderate"
        else:
            properties["organization_level"] = "minimal"
        
        logger.info("Image analysis completed successfully")
        
        return ImageAnalysisResponse(
            labels=labels,
            objects=objects,
            text=text,
            colors=colors,
            properties=properties
        )
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error processing image"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
