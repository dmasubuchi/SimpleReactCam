import React, { useState } from 'react';
import { ChatMessage } from './types';
import ChatWindow from './components/ChatWindow';

/**
 * Main application component for the AI Housekeeping Advisor Bot.
 */
const App = () => {
  const [messages, setMessages] = useState([
    {
      id: '1',
      sender: 'bot',
      type: 'text',
      content: 'Welcome to the AI Housekeeping Advisor Bot! Upload an image of your home environment to get advice.'
    },
    {
      id: '2',
      sender: 'user',
      type: 'text',
      content: 'Hello! I need some advice about my kitchen.'
    },
    {
      id: '3',
      sender: 'bot',
      type: 'text',
      content: 'I\'d be happy to help with your kitchen! Please upload a photo of your kitchen, and select "kitchen" as the scenario.'
    }
  ]);

  const appStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    padding: '20px',
    backgroundColor: '#f5f5f5',
  };

  return (
    <div style={appStyle}>
      <h1>AI Housekeeping Advisor Bot</h1>
      <ChatWindow messages={messages} />
    </div>
  );
};

export default App;
