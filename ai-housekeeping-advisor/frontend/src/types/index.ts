/**
 * TypeScript type definitions for the AI Housekeeping Advisor frontend.
 */

/**
 * Response from the API Gateway after analyzing an image.
 */
export interface AdviceResponse {
  advice: string;
  image_analysis: ImageAnalysis;
}

/**
 * Image analysis data from the Vision API.
 */
export interface ImageAnalysis {
  labels: Label[];
  objects: DetectedObject[];
  text?: string;
  colors: Color[];
  properties: EnvironmentProperties;
}

/**
 * Label detected in an image.
 */
export interface Label {
  description: string;
  score: number;
  topicality: number;
}

/**
 * Object detected in an image.
 */
export interface DetectedObject {
  name: string;
  score: number;
  bounding_poly: BoundingPolyVertex[];
}

/**
 * Vertex of a bounding polygon for an object.
 */
export interface BoundingPolyVertex {
  x: number;
  y: number;
}

/**
 * Color information from the image.
 */
export interface Color {
  color: {
    red: number;
    green: number;
    blue: number;
  };
  score: number;
  pixel_fraction: number;
}

/**
 * Properties extracted from the environment in the image.
 */
export interface EnvironmentProperties {
  environment_type: string;
  cleanliness_level: string;
  organization_level: string;
}
