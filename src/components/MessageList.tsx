import React from 'react';
import { ChatMessage } from '../types';
import MessageBubble from './MessageBubble';

/**
 * Props for the MessageList component.
 */
interface MessageListProps {
  /**
   * Array of chat messages to display.
   */
  messages: ChatMessage[];
}

/**
 * A component that displays a list of chat messages.
 * Renders a MessageBubble for each message in the array.
 */
const MessageList = ({ messages }: MessageListProps) => {
  const listStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    height: '100%',
    overflowY: 'auto' as const,
    padding: '10px',
  };

  return (
    <div style={listStyle}>
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </div>
  );
};

export default MessageList;
