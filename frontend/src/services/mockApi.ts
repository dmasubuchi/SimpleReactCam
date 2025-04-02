/**
 * Mock API service for AI Housekeeping Advisor Bot
 * 
 * This service simulates backend responses for testing without requiring
 * actual backend deployment to GCP.
 */

/**
 * Get advice for an image in a specific scenario
 * @param imageData Base64 encoded image data
 * @param scenario The scenario (plant, closet, fridge)
 * @returns Mock response with advice
 */
export const getAdvice = async (imageData: string, scenario: string) => {
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  switch (scenario) {
    case 'plant':
      return {
        success: true,
        data: {
          advice: "Your plant appears to be a peace lily. It needs indirect light and weekly watering. The leaves look slightly droopy, which suggests it might need more water. Try watering it thoroughly and ensure good drainage.",
          analysis: {
            labels: ["Plant", "Houseplant", "Flower pot", "Leaf", "Indoor plant"],
            objects: [
              { name: "Plant", confidence: 0.98 },
              { name: "Pot", confidence: 0.87 }
            ],
            colors: ["Green", "Brown", "White"],
            text_annotations: []
          }
        },
        error: null
      };
    case 'closet':
      return {
        success: true,
        data: {
          advice: "Your closet could benefit from better organization. Consider using shelf dividers for folded clothes, installing hooks for bags, and using uniform hangers. Group similar items together and consider seasonal rotation to maximize space.",
          analysis: {
            labels: ["Closet", "Wardrobe", "Furniture", "Room", "Clothes hanger", "Shelf"],
            objects: [
              { name: "Clothes", confidence: 0.92 },
              { name: "Shelf", confidence: 0.87 },
              { name: "Hanger", confidence: 0.85 },
              { name: "Box", confidence: 0.76 }
            ],
            colors: ["White", "Brown", "Black", "Blue"],
            text_annotations: []
          }
        },
        error: null
      };
    case 'fridge':
      return {
        success: true,
        data: {
          advice: "Your refrigerator could use some organization. Store dairy on the middle shelf, vegetables in the crisper drawers, and avoid storing milk in the door. Clean out expired items weekly and use clear containers to see leftovers easily.",
          analysis: {
            labels: ["Refrigerator", "Major appliance", "Home appliance", "Food", "Shelf"],
            objects: [
              { name: "Refrigerator", confidence: 0.99 },
              { name: "Food container", confidence: 0.85 },
              { name: "Bottle", confidence: 0.82 },
              { name: "Vegetable", confidence: 0.75 }
            ],
            colors: ["White", "Green", "Red", "Yellow"],
            text_annotations: ["Milk", "Expiry: 04/05"]
          }
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

/**
 * Simulate image processing with mock analysis results
 * @param imageData Base64 encoded image data
 * @returns Mock image analysis results
 */
export const processImage = async (imageData: string) => {
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  return {
    success: true,
    data: {
      labels: ["Person", "Room", "Furniture", "Indoor"],
      objects: [
        { name: "Person", confidence: 0.95 },
        { name: "Chair", confidence: 0.88 },
        { name: "Table", confidence: 0.82 }
      ],
      colors: ["Brown", "White", "Blue", "Black"],
      text_annotations: []
    },
    error: null
  };
};
