import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot } from 'lucide-react';
import { useChatContext } from '../context/ChatContext';
import { useDashboardContext } from '../context/DashboardContext';
import { useTypingAnimation } from '../hooks/useTypingAnimation';
import { chatApiService } from '../services/chatApi';

interface ChatInterfaceProps {
  onReasoningStart: (configId: string) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onReasoningStart }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { threadId, messages, isLoading, setThreadId, addMessage, setLoading } = useChatContext();
  const { currentDashboard } = useDashboardContext();
  
  const lastMessage = messages[messages.length - 1];
  const shouldAnimate = lastMessage && !lastMessage.isUser;
  
  const { displayText, isTyping } = useTypingAnimation(
    shouldAnimate ? lastMessage.content : '',
    20
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, displayText]);

  // Initialize with welcome message when dashboard changes
  useEffect(() => {
    if (currentDashboard && messages.length === 0) {
      const welcomeMessage = {
        id: Date.now().toString(),
        content: `Hello! I'm your AI assistant for the ${currentDashboard.name} dashboard. I can help analyze your data, provide insights, and show you my reasoning process. 

Try asking me:
- "How to implement React error handling?" for technical guidance
- "Analyze my dashboard data" for insights
- "What are the market trends?" for competitive analysis

What would you like to explore?`,
        isUser: false,
        timestamp: new Date(),
        threadId: threadId || undefined,
      };
      addMessage(welcomeMessage);
    }
  }, [currentDashboard, messages.length, threadId, addMessage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading && currentDashboard) {
      const userMessage = {
        id: Date.now().toString(),
        content: inputValue.trim(),
        isUser: true,
        timestamp: new Date(),
        threadId: threadId || undefined,
      };

      addMessage(userMessage);
      setLoading(true);
      setInputValue('');

      try {
        const response = await chatApiService.sendMessage({
          query: inputValue.trim(),
          thread_id: threadId || undefined,
          dashboard_id: currentDashboard.id,
        });

        // Update thread ID if it's a new conversation
        if (!threadId && response.thread_id) {
          setThreadId(response.thread_id);
        }

        // Start reasoning animation if config is provided
        if (response.reasoning_config) {
          onReasoningStart(response.reasoning_config);
        }

        // Add AI response after a delay to show reasoning
        setTimeout(() => {
          const aiMessage = {
            id: (Date.now() + 1).toString(),
            content: response.response,
            isUser: false,
            timestamp: new Date(),
            threadId: response.thread_id,
          };

          addMessage(aiMessage);
          setLoading(false);
        }, response.reasoning_config ? 4000 : 1500);

      } catch (error) {
        console.error('Error sending message:', error);
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          content: 'Sorry, I encountered an error while processing your request. Please try again.',
          isUser: false,
          timestamp: new Date(),
          threadId: threadId || undefined,
        };
        addMessage(errorMessage);
        setLoading(false);
      }
    }
  };

  if (!currentDashboard) {
    return (
      <div className="bg-white flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gray-500 mb-2">No dashboard selected</p>
          <p className="text-sm text-gray-400">Please select a dashboard from the sidebar to start chatting</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message, index) => {
          const isLastMessage = index === messages.length - 1;
          const shouldShowAnimation = isLastMessage && !message.isUser && shouldAnimate;
          
          return (
            <div
              key={message.id}
              className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-xl p-4 shadow-sm ${
                  message.isUser
                    ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                    : 'bg-gray-50 text-gray-900 border border-gray-200'
                }`}
              >
                <div className="flex items-start space-x-3">
                  {!message.isUser && (
                    <div className="p-1.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex-shrink-0">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}
                  {message.isUser && (
                    <div className="p-1.5 bg-white/20 rounded-lg flex-shrink-0">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div className="flex-1">
                    <div className="prose prose-sm max-w-none">
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {shouldShowAnimation ? displayText : message.content}
                      </p>
                    </div>
                    {shouldShowAnimation && isTyping && (
                      <span className="inline-block w-2 h-4 bg-purple-500 ml-1 animate-pulse rounded" />
                    )}
                    <p className="text-xs opacity-60 mt-2">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 max-w-[80%] shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="p-1.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-6 border-t border-gray-200 bg-gray-50">
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={`Ask me about ${currentDashboard.name}...`}
            disabled={isLoading}
            className="flex-1 bg-white border border-gray-300 rounded-lg px-4 py-3 text-gray-900 placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 disabled:opacity-50 shadow-sm"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        
        {threadId && (
          <p className="text-xs text-gray-500 mt-2">
            Thread ID: {threadId.slice(0, 8)}...
          </p>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;