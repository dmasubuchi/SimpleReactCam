import React from 'react';
import { ChatMessage } from '../types';

/**
 * Props for the MessageBubble component.
 */
interface MessageBubbleProps {
  /**
   * The chat message to display.
   */
  message: ChatMessage;
}

/**
 * A component that displays a single chat message.
 * Styles the message differently based on the sender (user or bot).
 */
const MessageBubble = ({ message }: MessageBubbleProps) => {
  const bubbleStyle = {
    padding: '10px 15px',
    borderRadius: '18px',
    maxWidth: '70%',
    marginBottom: '10px',
    wordWrap: 'break-word' as const,
    backgroundColor: message.sender === 'user' ? '#e3f2fd' : '#f1f1f1',
    alignSelf: message.sender === 'user' ? 'flex-end' : 'flex-start',
  };

  return (
    <div style={bubbleStyle}>
      {message.content}
    </div>
  );
};

export default MessageBubble;
