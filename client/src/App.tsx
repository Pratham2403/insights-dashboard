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
      {/* Dashboard Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-xl font-semibold text-gray-900">Brand Health Monitor</div>
              <div className="text-sm text-gray-500">Last 30 Days: May 11, 2025 – Jun 09, 2025</div>
            </div>
            
            {/* AI Chat Logo/Button */}
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleChat}
                className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg hover:from-purple-600 hover:to-blue-600 transition-all duration-200 shadow-md hover:shadow-lg"
              >
                <Brain className="w-5 h-5" />
                <span className="font-medium">AI Assistant</span>
                <Sparkles className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Dashboard Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Brand Insights Section */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg">
              <MessageCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Apparel & Fashion Brand Insights</h2>
              <p className="text-gray-600">Visit Brand Insights section to see more details</p>
            </div>
          </div>

          {/* Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <LineChart
              data={dashboardData.sentimentTrend}
              title="Sentiment Trend Over Time"
            />
            <BarChart
              data={dashboardData.topicAnalysis}
              title="Key Topics Discussed"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Apparel & Fashion Customer Experience</h2>
              <p className="text-gray-600">Visit Customer Experience section to see more details</p>
            </div>
          </div>

          {/* Customer Experience Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Pre-Purchase Stage</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Product Discovery</span>
                  <span className="text-sm font-medium text-green-600">+15%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Price Comparison</span>
                  <span className="text-sm font-medium text-yellow-600">-5%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Reviews Reading</span>
                  <span className="text-sm font-medium text-green-600">+22%</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Purchase Stage</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Checkout Process</span>
                  <span className="text-sm font-medium text-green-600">+8%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Payment Options</span>
                  <span className="text-sm font-medium text-green-600">+12%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Order Confirmation</span>
                  <span className="text-sm font-medium text-green-600">+18%</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Post-Purchase Stage</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Delivery Experience</span>
                  <span className="text-sm font-medium text-green-600">+25%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Product Quality</span>
                  <span className="text-sm font-medium text-green-600">+30%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Customer Support</span>
                  <span className="text-sm font-medium text-yellow-600">+5%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Floating Chat Interface */}
      {isChatOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className={`bg-white rounded-xl shadow-2xl border border-gray-200 transition-all duration-300 ${
            isMinimized ? 'w-96 h-16' : 'w-full max-w-6xl h-[80vh]'
          }`}>
            {/* Chat Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50 rounded-t-xl">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">AI Assistant</h3>
                  <p className="text-sm text-gray-600">Integrated reasoning & analysis</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleMinimize}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <Minimize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={toggleChat}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4" />
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
                      <div className="p-6 h-full flex items-center justify-center bg-gray-50">
                        <div className="text-center">
                          <Brain className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                          <h3 className="text-lg font-semibold text-gray-700 mb-2">
                            Reasoning Panel
                          </h3>
                          <p className="text-gray-500 max-w-xs">
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