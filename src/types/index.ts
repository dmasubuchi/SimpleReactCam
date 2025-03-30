/**
 * Type definitions for the AI Housekeeping Advisor Bot chat interface.
 */

/**
 * Represents a chat message in the application.
 */
export interface ChatMessage {
  /**
   * Unique identifier for each message.
   */
  id: string;
  
  /**
   * Indicates who sent the message.
   */
  sender: 'user' | 'bot';
  
  /**
   * The type of message content.
   * Currently only supports 'text', will add 'image' later.
   */
  type: 'text';
  
  /**
   * The text content of the message.
   */
  content: string;
}
