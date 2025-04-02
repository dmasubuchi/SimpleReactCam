/**
 * API service for AI Housekeeping Advisor Bot
 * 
 * This service handles communication with the backend API Gateway.
 * It can be configured to use either the real API or a mock implementation.
 */
import { getAdvice as mockGetAdvice } from './mockApi';

const API_URL = import.meta.env.VITE_API_URL || '';
const USE_MOCK_API = !API_URL || API_URL.includes('api-gateway-url-from-deployment');

/**
 * Get advice for an image in a specific scenario
 * @param imageData Base64 encoded image data
 * @param scenario The scenario (plant, closet, fridge)
 * @returns Response with advice or error
 */
export const getAdvice = async (imageData: string, scenario: string) => {
  try {
    if (USE_MOCK_API) {
      console.log('Using mock API for getAdvice');
      return await mockGetAdvice(imageData, scenario);
    }

    console.log(`Calling API at ${API_URL}`);
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        scenario,
        image_data: imageData,
      }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || `Failed to get advice: ${response.statusText}`);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching advice:', error);
    return {
      success: false,
      data: null,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
};
