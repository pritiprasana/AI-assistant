import { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatContainer from './components/ChatContainer';
import InputArea from './components/InputArea';
import type { Message, Mode } from './types';
import { chatAPI } from './services/api';
import { messageStorage } from './services/storage';
import './index.css';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [mode, setMode] = useState<Mode>('flair');
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Load messages from localStorage on mount
  useEffect(() => {
    const savedMessages = messageStorage.load();
    setMessages(savedMessages);
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      messageStorage.save(messages);
    }
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call API
      const response = await chatAPI.sendMessage({
        message: content,
        use_rag: mode === 'flair',
      });

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: Date.now(),
        sources: response.sources,  // Include RAG sources
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Sorry, there was an error communicating with the API. Make sure the server is running on http://localhost:8000',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setMessages([]);
    messageStorage.clear();
    setShowSettings(false);
  };

  return (
    <div className="flex flex-col h-screen bg-dark">
      <Header
        mode={mode}
        onModeChange={setMode}
        onSettingsClick={() => setShowSettings(!showSettings)}
      />

      {showSettings && (
        <div className="bg-dark-lighter border-b border-gray-700 px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <h3 className="text-lg font-semibold mb-3">Settings</h3>
            <button
              onClick={handleClearHistory}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded transition-colors"
            >
              Clear Conversation History
            </button>
          </div>
        </div>
      )}

      <ChatContainer messages={messages} isLoading={isLoading} />
      <InputArea onSendMessage={handleSendMessage} disabled={isLoading} mode={mode} />
    </div>
  );
}

export default App;
