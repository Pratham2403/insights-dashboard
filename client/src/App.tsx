import React, { useState } from 'react';
import { Menu, Brain, Sparkles, X, Minimize2 } from 'lucide-react';
import { DashboardProvider } from './context/DashboardContext';
import { ChatProvider } from './context/ChatContext';
import { useDashboardContext } from './context/DashboardContext';
import { useChatContext } from './context/ChatContext';
import Sidebar from './components/Sidebar';
import DashboardRenderer from './components/DashboardRenderer';
import ChatInterface from './components/ChatInterface';
import ReasoningPanel from './components/ReasoningPanel';
import ResizableLayout from './components/ResizableLayout';

const AppContent: React.FC = () => {
    const { currentDashboard } = useDashboardContext();
    const { setCurrentDashboard } = useChatContext();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [isMinimized, setIsMinimized] = useState(false);
    const [isThinking, setIsThinking] = useState(false);
    const [reasoningConfigId, setReasoningConfigId] = useState(
        'react-error-handling'
    );

    // Update chat context when dashboard changes
    React.useEffect(() => {
        if (currentDashboard) {
            setCurrentDashboard(currentDashboard.id);
        }
    }, [currentDashboard?.id]);

    const handleReasoningStart = (configId: string) => {
        setReasoningConfigId(configId);
        setIsThinking(true);
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
            {/* Header */}
            <header className="bg-white border-b border-gray-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 py-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => setIsSidebarOpen(true)}
                                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <Menu className="w-6 h-6" />
                            </button>

                            <div className="flex items-center space-x-3">
                                <div className="text-xl font-semibold text-gray-900">
                                    {currentDashboard?.name ||
                                        'Analytics Dashboard'}
                                </div>
                                {currentDashboard && (
                                    <div className="text-sm text-gray-500">
                                        Last 30 Days: May 11, 2025 – Jun 09,
                                        2025
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex items-center space-x-4">
                            <button
                                onClick={toggleChat}
                                className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg hover:from-purple-600 hover:to-blue-600 transition-all duration-200 shadow-md hover:shadow-lg"
                            >
                                <Brain className="w-5 h-5" />
                                <span className="font-medium">
                                    AI Assistant
                                </span>
                                <Sparkles className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-6">
                {currentDashboard ? (
                    <DashboardRenderer dataFile={currentDashboard.dataFile} />
                ) : (
                    <div className="flex items-center justify-center h-64">
                        <div className="text-center">
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">
                                Welcome to Analytics Dashboard
                            </h2>
                            <p className="text-gray-600 mb-4">
                                Select a dashboard from the sidebar to get
                                started
                            </p>
                            <button
                                onClick={() => setIsSidebarOpen(true)}
                                className="bg-gradient-to-r from-purple-500 to-blue-500 text-white px-6 py-3 rounded-lg hover:from-purple-600 hover:to-blue-600 transition-all duration-200 shadow-md hover:shadow-lg"
                            >
                                Open Dashboards
                            </button>
                        </div>
                    </div>
                )}
            </main>

            {/* Sidebar */}
            <Sidebar
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            {/* Floating Chat Interface - Moved up */}
            {isChatOpen && (
                <div className="fixed inset-0 z-50 flex items-start justify-center bg-black bg-opacity-50 p-4 pt-8">
                    <div
                        className={`bg-white rounded-xl shadow-2xl border border-gray-200 transition-all duration-300 ${
                            isMinimized
                                ? 'w-96 h-16 mt-8'
                                : 'w-full max-w-[1500px] h-[80vh] mt-8'
                        }`}
                    >
                        {/* Chat Header */}
                        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50 rounded-t-xl">
                            <div className="flex items-center space-x-3">
                                <div className="p-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg">
                                    <Brain className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-gray-900">
                                        AI Assistant
                                    </h3>
                                    <p className="text-sm text-gray-600">
                                        {currentDashboard
                                            ? `Analyzing ${currentDashboard.name}`
                                            : 'Ready to help'}
                                    </p>
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
                                            onReasoningStart={
                                                handleReasoningStart
                                            }
                                        />
                                    }
                                    rightPanel={
                                        <ReasoningPanel
                                            isThinking={isThinking}
                                            onComplete={handleReasoningComplete}
                                            configId={reasoningConfigId}
                                        />
                                    }
                                    minLeftWidth={300}
                                    minRightWidth={300}
                                    defaultLeftWidth={60}
                                />
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

function App() {
    return (
        <DashboardProvider>
            <ChatProvider>
                <AppContent />
            </ChatProvider>
        </DashboardProvider>
    );
}

export default App;
