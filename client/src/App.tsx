import React, { useState } from 'react';
import { MessageCircle, Brain, Sparkles, X, Minimize2 } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import ReasoningPanel from './components/ReasoningPanel';
import ResizableLayout from './components/ResizableLayout';
import MetricCard from './components/charts/MetricCard';
import LineChart from './components/charts/LineChart';
import BarChart from './components/charts/BarChart';
import DonutChart from './components/charts/DonutChart';
import CompetitorChart from './components/charts/CompetitorChart';
import { ChatMessage } from './types';
import dashboardData from './data/dashboardData.json';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      content: 'Hello! I\'m your AI assistant integrated with your dashboard. I can help analyze your data, provide insights, and show you my reasoning process. Try asking me "How to implement React error handling?" to see a demo!',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  const handleSendMessage = async (messageContent: string) => {
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: messageContent,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Check if this is the demo query
    const isDemoQuery = messageContent.toLowerCase().includes('react error handling');
    
    if (isDemoQuery) {
      setShowReasoning(true);
      setIsThinking(true);
    }

    // Simulate AI response delay
    setTimeout(() => {
      let responseContent = '';
      
      if (isDemoQuery) {
        responseContent = `Here's a comprehensive guide to implementing React error handling:

## Error Boundaries
Error boundaries are React components that catch JavaScript errors anywhere in their child component tree and display a fallback UI.

\`\`\`jsx
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}
\`\`\`

## Async Error Handling
For async operations, use try-catch blocks:

\`\`\`jsx
const fetchData = async () => {
  try {
    const response = await api.getData();
    setData(response);
  } catch (error) {
    setError(error.message);
  }
};
\`\`\`

## Best Practices
1. Use error boundaries for component-level errors
2. Implement global error handling for unhandled promises
3. Provide meaningful error messages to users
4. Log errors for debugging in development
5. Use error reporting services in production

This approach ensures robust error handling throughout your React application!`;
      } else {
        responseContent = `I understand you're asking about "${messageContent}". I'd be happy to help you with that! 

For the best experience with detailed reasoning, try asking me "How to implement React error handling?" to see my full reasoning process in action.

What specific aspect would you like me to focus on?`;
      }

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: responseContent,
        isUser: false,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);
      setIsLoading(false);
    }, isDemoQuery ? 4000 : 1500);
  };

  const handleReasoningComplete = () => {
    setIsThinking(false);
  };

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
    if (!isChatOpen) {
      setIsMinimized(false);
    }
  };

  const toggleMinimize = () => {
    setIsMinimized(!isMinimized);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sprinklr Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="text-2xl font-bold text-gray-900">Brand Health Monitor</div>
              <div className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                Last 30 Days: May 11, 2025 – Jun 09, 2025
              </div>
            </div>
            
            {/* AI Assistant Button */}
            <button
              onClick={toggleChat}
              className="flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl font-medium"
            >
              <Brain className="w-5 h-5" />
              <span>AI Assistant</span>
              <Sparkles className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Dashboard Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Brand Insights Section */}
        <div className="mb-12">
          {/* Section Header */}
          <div className="flex items-center space-x-4 mb-8">
            <div className="w-12 h-12 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
              <MessageCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Apparel & Fashion Brand Insights</h2>
              <p className="text-gray-600 mt-1">Visit Brand Insights section to see more details</p>
            </div>
          </div>

          {/* Metrics Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
            <MetricCard
              title="Mentions"
              value={dashboardData.brandMetrics.mentions.current}
              change={dashboardData.brandMetrics.mentions.change}
              trend="up"
              icon="mentions"
              color="blue"
            />
            <MetricCard
              title="Reach"
              value={dashboardData.brandMetrics.reach.current}
              change={dashboardData.brandMetrics.reach.change}
              trend="up"
              icon="reach"
              color="green"
            />
            <MetricCard
              title="Engagement"
              value={dashboardData.brandMetrics.engagement.current}
              change={dashboardData.brandMetrics.engagement.change}
              trend="up"
              icon="engagement"
              color="purple"
            />
            <MetricCard
              title="Positive Sentiment"
              value={`${dashboardData.brandMetrics.sentiment.positive}%`}
              change="+12%"
              trend="up"
              icon="sentiment"
              color="orange"
            />
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
            <LineChart
              data={dashboardData.sentimentTrend}
              title="Sentiment Trend Over Time"
            />
            <BarChart
              data={dashboardData.topicAnalysis}
              title="Key Topics Discussed"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <DonutChart
              data={dashboardData.geographicData}
              title="Geographic Distribution"
            />
            <CompetitorChart
              data={dashboardData.competitorComparison}
              title="Competitor Analysis"
            />
          </div>
        </div>

        {/* Customer Experience Section */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-8">
            <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Apparel & Fashion Customer Experience</h2>
              <p className="text-gray-600 mt-1">Visit Customer Experience section to see more details</p>
            </div>
          </div>

          {/* Customer Experience Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 hover:shadow-md transition-shadow duration-200">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Pre-Purchase Stage</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-700 font-medium">Product Discovery</span>
                  <span className="text-green-600 font-bold text-sm bg-green-50 px-3 py-1 rounded-full">+15%</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-700 font-medium">Price Comparison</span>
                  <span className="text-yellow-600 font-bold text-sm bg-yellow-50 px-3 py-1 rounded-full">-5%</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-700 font-medium">Reviews Reading</span>
                  <span className="text-green-600 font-bold text-sm bg-green-50 px-3 py-1 rounded-full">+22%</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 hover:shadow-md transition-shadow duration-200">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Purchase Stage</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-700 font-medium">Checkout Process</span>
                  <span className="text-green-600 font-bold text-sm bg-green-50 px-3 py-1 rounded-full">+8%</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-700 font-medium">Payment Options</span>
                  <span className="text-green-600 font-bold text-sm bg-green-50 px-3 py-1 rounded-full">+12%</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-700 font-medium">Order Confirmation</span>
                  <span className="text-green-600 font-bold text-sm bg-green-50 px-3 py-1 rounded-full">+18%</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 hover:shadow-md transition-shadow duration-200">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Post-Purchase Stage</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-700 font-medium">Delivery Experience</span>
                  <span className="text-green-600 font-bold text-sm bg-green-50 px-3 py-1 rounded-full">+25%</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-700 font-medium">Product Quality</span>
                  <span className="text-green-600 font-bold text-sm bg-green-50 px-3 py-1 rounded-full">+30%</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-700 font-medium">Customer Support</span>
                  <span className="text-yellow-600 font-bold text-sm bg-yellow-50 px-3 py-1 rounded-full">+5%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Floating Chat Interface */}
      {isChatOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className={`bg-white rounded-2xl shadow-2xl border border-gray-200 transition-all duration-300 ${
            isMinimized ? 'w-96 h-16' : 'w-full max-w-6xl h-[85vh]'
          }`}>
            {/* Chat Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-t-2xl">
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-lg">AI Assistant</h3>
                  <p className="text-sm text-gray-600">Integrated reasoning & analysis</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleMinimize}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <Minimize2 className="w-5 h-5" />
                </button>
                <button
                  onClick={toggleChat}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Chat Content with Resizable Layout */}
            {!isMinimized && (
              <div className="h-full">
                <ResizableLayout
                  leftPanel={
                    <ChatInterface
                      messages={messages}
                      onSendMessage={handleSendMessage}
                      isLoading={isLoading}
                    />
                  }
                  rightPanel={
                    showReasoning ? (
                      <ReasoningPanel 
                        isThinking={isThinking} 
                        onComplete={handleReasoningComplete}
                      />
                    ) : (
                      <div className="p-8 h-full flex items-center justify-center bg-gray-50">
                        <div className="text-center">
                          <Brain className="w-20 h-20 text-gray-400 mx-auto mb-6" />
                          <h3 className="text-xl font-bold text-gray-700 mb-3">
                            Reasoning Panel
                          </h3>
                          <p className="text-gray-500 max-w-sm">
                            Ask me "How to implement React error handling?" to see my step-by-step reasoning process!
                          </p>
                        </div>
                      </div>
                    )
                  }
                  minLeftWidth={300}
                  minRightWidth={300}
                  defaultLeftWidth={50}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;