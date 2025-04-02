/**
 * TypeScript definitions for environment variables
 */
interface ImportMetaEnv {
  /**
   * API Gateway URL for the backend
   */
  readonly VITE_API_URL: string;
  
  /**
   * Available scenarios for the AI Housekeeping Advisor Bot
   */
  readonly VITE_AVAILABLE_SCENARIOS?: string;
  
  /**
   * Maximum image size in MB
   */
  readonly VITE_MAX_IMAGE_SIZE_MB?: string;
  
  /**
   * Application name
   */
  readonly VITE_APP_NAME?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
