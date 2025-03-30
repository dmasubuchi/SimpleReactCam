import React from 'react';
import { ChatMessage } from '../types';
import MessageList from './MessageList';

/**
 * Props for the ChatWindow component.
 */
interface ChatWindowProps {
  /**
   * Array of chat messages to display.
   */
  messages: ChatMessage[];
}

/**
 * A component that displays a chat window with messages.
 * Contains the MessageList and a placeholder for future input controls.
 */
const ChatWindow = ({ messages }: ChatWindowProps) => {
  const windowStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    height: '500px',
    width: '100%',
    maxWidth: '600px',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  };

  const messageListContainerStyle = {
    flex: 1,
    overflow: 'hidden',
  };

  const inputPlaceholderStyle = {
    padding: '15px',
    borderTop: '1px solid #e0e0e0',
    backgroundColor: '#f9f9f9',
    textAlign: 'center' as const,
    color: '#888',
  };

  return (
    <div style={windowStyle}>
      <div style={messageListContainerStyle}>
        <MessageList messages={messages} />
      </div>
      <div style={inputPlaceholderStyle}>
        Input controls will be added here in the next step
      </div>
    </div>
  );
};

export default ChatWindow;
