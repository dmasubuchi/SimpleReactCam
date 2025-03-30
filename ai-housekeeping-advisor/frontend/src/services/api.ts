import axios from 'axios';
import { AdviceResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

/**
 * API service for communicating with the backend.
 */
const apiService = {
  /**
   * Upload an image and get housekeeping advice.
   * 
   * @param imageFile - The image file to upload
   * @param context - Optional additional context for the advice
   * @returns Promise with the advice response
   */
  async analyzeImage(imageFile: File, context?: string): Promise<AdviceResponse> {
    try {
      const formData = new FormData();
      formData.append('image', imageFile);
      
      if (context) {
        formData.append('context', context);
      }
      
      const response = await axios.post<AdviceResponse>(
        `${API_BASE_URL}/analyze`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error analyzing image:', error);
      throw error;
    }
  },
};

export default apiService;
