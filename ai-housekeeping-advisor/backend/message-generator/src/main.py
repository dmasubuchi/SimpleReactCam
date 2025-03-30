"""
Message Generator for AI Housekeeping Advisor Bot.

This module serves as the entry point for the Message Generator Cloud Function.
It receives structured image analysis results, constructs a prompt,
calls the Vertex AI Gemini API, and returns the generated advice text.
"""
import logging
import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Housekeeping Advisor - Message Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gemini_available = False
try:
    from google.cloud import aiplatform
    try:
        from google.cloud.aiplatform.preview.generative_models import GenerativeModel
        gemini_available = True
    except ImportError:
        try:
            from vertexai.generative_models import GenerativeModel
            gemini_available = True
        except ImportError:
            gemini_available = False
    
    if gemini_available:
        aiplatform.init(project=os.getenv("GOOGLE_CLOUD_PROJECT", "ai-housekeeping-advisor"))
        logger.info("Successfully initialized Vertex AI")
except Exception as e:
    logger.warning(f"Could not initialize Vertex AI: {str(e)}")
    logger.warning("Using mock data for development")
    gemini_available = False

GEMINI_MODEL = "gemini-1.0-pro"
GEMINI_TEMPERATURE = 0.2
GEMINI_MAX_OUTPUT_TOKENS = 1024
GEMINI_TOP_P = 0.8
GEMINI_TOP_K = 40


class GenerateRequest(BaseModel):
    """Request model for generating advice."""
    image_analysis: Dict[str, Any]
    context: Optional[str] = None


class GenerateResponse(BaseModel):
    """Response model for generated advice."""
    advice: str


@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "Message Generator is running"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_advice(request: GenerateRequest) -> GenerateResponse:
    """
    Generate housekeeping advice based on image analysis.
    If Vertex AI is not available, returns mock data for development.
    
    Args:
        request: Object containing image analysis and optional context
        
    Returns:
        GenerateResponse: Object containing the generated advice
    
    Raises:
        HTTPException: If there's an error generating the advice
    """
    try:
        logger.info("Generating advice based on image analysis")
        
        labels = request.image_analysis.get("labels", [])
        objects = request.image_analysis.get("objects", [])
        text = request.image_analysis.get("text", "")
        properties = request.image_analysis.get("properties", {})
        
        prompt = _construct_prompt(labels, objects, text, properties, request.context)
        
        use_mock_data = not gemini_available
        
        advice = ""
        if not use_mock_data:
            logger.info(f"Calling Gemini API with model: {GEMINI_MODEL}")
            try:
                model = GenerativeModel(
                    model_name=GEMINI_MODEL,
                    generation_config={
                        "temperature": GEMINI_TEMPERATURE,
                        "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
                        "top_p": GEMINI_TOP_P,
                        "top_k": GEMINI_TOP_K,
                    }
                )
                
                response = model.generate_content(prompt)
                advice = response.text
            except Exception as e:
                logger.error(f"Error using Gemini API: {str(e)}")
                logger.info("Falling back to mock data")
                use_mock_data = True
        
        if use_mock_data:
            logger.info("Using mock data for development (Vertex AI not available)")
            
            environment_type = properties.get("environment_type", "unknown")
            
            if environment_type == "kitchen":
                advice = """
                Based on the image of your kitchen, here are some practical housekeeping tips:

                1. **Counter Organization**: Your countertops appear to have several appliances. Consider using a tiered shelf organizer to maximize vertical space and keep frequently used items accessible.

                2. **Sink Area**: Keep a small dish brush and eco-friendly soap dispenser by the sink for quick cleanup after meal preparation. This prevents buildup of dishes and makes daily maintenance easier.

                3. **Appliance Maintenance**: For stainless steel appliances, use a microfiber cloth with a drop of olive oil to remove fingerprints and add shine. This works better than commercial cleaners and is non-toxic.

                4. **Food Storage**: Implement a "first in, first out" system in your refrigerator and pantry to reduce food waste. Use clear containers to easily see what's inside.

                Quick Tip: Place a bowl of water with lemon and vinegar in the microwave for 2 minutes to easily clean stuck-on food and eliminate odors naturally.
                """
            elif environment_type == "bathroom":
                advice = """
                Looking at your bathroom, here are some targeted housekeeping recommendations:

                1. **Shower Maintenance**: To prevent mildew and soap scum, keep a squeegee in the shower and spend 30 seconds wiping down walls after each use. This simple habit reduces deep cleaning frequency.

                2. **Towel Management**: Your towels appear to be hanging close together. Install additional hooks or a towel bar with more spacing to ensure proper drying and prevent musty odors.

                3. **Counter Organization**: Use small baskets or trays to group similar toiletries together. This not only looks neater but makes cleaning the counter surface much easier.

                4. **Ventilation**: Make sure to run your bathroom fan for 20-30 minutes after showering to reduce humidity and prevent mold growth.

                Quick Tip: A shower curtain liner can be refreshed by washing it with two towels on a gentle cycle with vinegar added to the detergent.
                """
            elif environment_type == "bedroom":
                advice = """
                Based on your bedroom image, here are some practical housekeeping suggestions:

                1. **Bedding Refresh**: Your bedding appears slightly rumpled. Consider using hospital corners when making your bed for a neater appearance, and rotate your mattress every 3-6 months for even wear.

                2. **Nightstand Organization**: Implement the "one in, one out" rule for your nightstand to prevent clutter accumulation. Keep only essentials within reach.

                3. **Clothing Management**: Designate a specific "landing spot" like a decorative basket for clothes that have been worn but aren't ready for washing yet. This prevents them from ending up on chairs or the floor.

                4. **Air Quality**: Dust your ceiling fan blades and air vents regularly to improve air quality while you sleep. A pillowcase works perfectly for catching dust from fan blades.

                Quick Tip: Place a few drops of lavender essential oil on a cotton ball and tuck it inside your pillowcase for better sleep quality and a naturally fresh scent.
                """
            else:
                advice = """
                Based on the image of your home environment, here are some practical housekeeping recommendations:

                1. **Surface Cleaning**: For general surfaces, keep a spray bottle with equal parts water and white vinegar with a few drops of dish soap. This all-purpose cleaner works on most surfaces and is non-toxic.

                2. **Organization Strategy**: Implement the "touch it once" rule - when you pick something up, put it where it belongs immediately rather than setting it down elsewhere temporarily.

                3. **Maintenance Schedule**: Create a simple rotating cleaning schedule where you focus on one area or task each day rather than trying to clean everything at once. This makes housekeeping more manageable.

                4. **Decluttering Method**: Use the four-box method (keep, donate, trash, relocate) when organizing any space. Set a timer for 15 minutes and sort items quickly to avoid decision fatigue.

                Quick Tip: Keep microfiber cloths in multiple rooms for quick cleanups. They trap dust better than paper towels and can be washed and reused hundreds of times.
                """
            
        logger.info("Advice generated successfully")
        
        return GenerateResponse(advice=advice)
    
    except Exception as e:
        logger.error(f"Error generating advice: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error generating advice"
        )


def _construct_prompt(
    labels: list,
    objects: list,
    text: str,
    properties: dict,
    context: Optional[str]
) -> str:
    """
    Construct a prompt for the Gemini API based on image analysis.
    
    Args:
        labels: List of labels detected in the image
        objects: List of objects detected in the image
        text: Text detected in the image
        properties: Properties extracted from the image
        context: Optional additional context
        
    Returns:
        str: Constructed prompt
    """
    environment_type = properties.get("environment_type", "unknown")
    cleanliness_level = properties.get("cleanliness_level", "unknown")
    organization_level = properties.get("organization_level", "unknown")
    
    top_labels = [label["description"] for label in labels[:5]]
    top_objects = [obj["name"] for obj in objects[:10]]
    
    prompt = f"""
    You are an expert housekeeping advisor. Based on the analysis of an image, provide practical, 
    specific housekeeping advice (cleaning, organizing, or cooking tips) for the user.
    
    Image Analysis:
    - Environment Type: {environment_type}
    - Cleanliness Level: {cleanliness_level}
    - Organization Level: {organization_level}
    - Key Items Detected: {', '.join(top_objects)}
    - Key Features: {', '.join(top_labels)}
    """
    
    if text:
        prompt += f"\n- Text Visible in Image: {text}"
    
    if context:
        prompt += f"\n\nAdditional Context from User: {context}"
    
    if environment_type == "kitchen":
        prompt += """
        \nFocus on:
        1. Food safety and hygiene
        2. Efficient organization of kitchen tools and appliances
        3. Cleaning techniques for different surfaces
        4. Meal preparation tips based on visible ingredients
        """
    elif environment_type == "bathroom":
        prompt += """
        \nFocus on:
        1. Hygiene and sanitation
        2. Mold and mildew prevention
        3. Efficient organization of toiletries
        4. Water conservation tips
        """
    elif environment_type == "bedroom":
        prompt += """
        \nFocus on:
        1. Organization and decluttering
        2. Bedding hygiene and maintenance
        3. Creating a restful environment
        4. Storage solutions
        """
    elif environment_type == "living room":
        prompt += """
        \nFocus on:
        1. Dust control and air quality
        2. Furniture arrangement and care
        3. Decluttering common areas
        4. Creating a welcoming space
        """
    
    prompt += """
    \nProvide your advice in a friendly, conversational tone. Include:
    1. A brief assessment of the current state
    2. 3-5 specific, actionable recommendations
    3. Any quick tips or life hacks relevant to the situation
    
    Keep your response concise (250-350 words) and practical.
    """
    
    return prompt


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
