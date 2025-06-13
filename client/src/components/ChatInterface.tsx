import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
    Send,
    User,
    Bot,
    Filter,
    Target,
    Building,
    Layers,
    Lightbulb,
    ArrowRight,
    CheckCircle,
    AlertCircle,
    Clock,
    MessageSquare,
} from 'lucide-react';
import { useChatContext } from '../context/ChatContext';
import { useDashboardContext } from '../context/DashboardContext';
import { useTypingAnimation } from '../hooks/useTypingAnimation';
import { chatApiService } from '../services/chatApi';
import ThemeDisplay from './ThemeDisplay';

interface ChatInterfaceProps {
    onReasoningStart: (configId: string) => void;
}

// Custom Markdown Renderer Component
const MarkdownRenderer: React.FC<{
    content: string;
    isAnimated?: boolean;
    displayText?: string;
}> = ({ content, isAnimated = false, displayText = '' }) => {
    const textToRender = isAnimated ? displayText : content;

    return (
        <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-headings:font-semibold prose-h2:text-lg prose-h2:mt-6 prose-h2:mb-4 prose-h3:text-base prose-h3:mt-4 prose-h3:mb-3 prose-p:text-gray-700 prose-p:leading-relaxed prose-strong:text-gray-900 prose-strong:font-semibold prose-ul:my-3 prose-li:my-1 prose-code:bg-gray-100 prose-code:px-2 prose-code:py-1 prose-code:rounded prose-code:text-sm prose-code:font-mono">
            <ReactMarkdown
                components={{
                    h2: ({ children }) => (
                        <div className="flex items-center space-x-2 mt-6 mb-4 pb-2 border-b border-gray-200">
                            <MessageSquare className="w-5 h-5 text-purple-600" />
                            <h2 className="text-lg font-semibold text-gray-900 m-0">
                                {children}
                            </h2>
                        </div>
                    ),
                    h3: ({ children }) => (
                        <div className="flex items-center space-x-2 mt-4 mb-3">
                            <ArrowRight className="w-4 h-4 text-blue-600" />
                            <h3 className="text-base font-semibold text-gray-900 m-0">
                                {children}
                            </h3>
                        </div>
                    ),
                    strong: ({ children }) => (
                        <span className="font-semibold text-gray-900 bg-yellow-50 px-1 py-0.5 rounded">
                            {children}
                        </span>
                    ),
                    ul: ({ children }) => (
                        <ul className="space-y-2 my-3 pl-4">{children}</ul>
                    ),
                    li: ({ children }) => (
                        <li className="flex items-start space-x-2 text-gray-700">
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span>{children}</span>
                        </li>
                    ),
                    p: ({ children }) => (
                        <p className="text-gray-700 leading-relaxed mb-3 last:mb-0">
                            {children}
                        </p>
                    ),
                    code: ({ children }) => (
                        <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono text-gray-800">
                            {children}
                        </code>
                    ),
                }}
            >
                {textToRender}
            </ReactMarkdown>
        </div>
    );
};

// Enhanced Structured Response Renderer for Review Requirements
const StructuredResponseRenderer: React.FC<{
    content: string;
    isAnimated?: boolean;
    displayText?: string;
}> = ({ content, isAnimated = false, displayText = '' }) => {
    const textToRender = isAnimated ? displayText : content;

    // Check if this is a review/HITL response format
    const isReviewFormat =
        textToRender.includes('Review analysis:') ||
        textToRender.includes('Review Required') ||
        textToRender.includes('**Review Analysis:**') ||
        textToRender.includes('**Data Requirements:**') ||
        textToRender.includes('**Instructions:**');

    if (isReviewFormat) {
        return (
            <div className="space-y-4">
                <ReactMarkdown
                    components={{
                        h2: ({ children }) => (
                            <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 mb-4">
                                <div className="flex items-center space-x-3">
                                    <div className="p-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg">
                                        <AlertCircle className="w-5 h-5 text-white" />
                                    </div>
                                    <h2 className="text-xl font-semibold text-purple-900 m-0">
                                        {children}
                                    </h2>
                                </div>
                            </div>
                        ),
                        strong: ({ children }) => {
                            const text = children?.toString() || '';

                            // Review Analysis section
                            if (text.includes('Review Analysis:')) {
                                return (
                                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-4">
                                        <div className="flex items-center space-x-2 mb-3">
                                            <Clock className="w-5 h-5 text-blue-600" />
                                            <span className="font-semibold text-blue-900 text-lg">
                                                Review Analysis
                                            </span>
                                        </div>
                                    </div>
                                );
                            }

                            // Data Requirements section
                            if (text.includes('Data Requirements:')) {
                                return (
                                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 my-4">
                                        <div className="flex items-center space-x-2 mb-3">
                                            <Target className="w-5 h-5 text-yellow-600" />
                                            <span className="font-semibold text-yellow-900 text-lg">
                                                Data Requirements
                                            </span>
                                        </div>
                                    </div>
                                );
                            }

                            // Refined Query section
                            if (text.includes('Refined Query:')) {
                                return (
                                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 my-4">
                                        <div className="flex items-center space-x-2 mb-3">
                                            <CheckCircle className="w-5 h-5 text-green-600" />
                                            <span className="font-semibold text-green-900 text-lg">
                                                Refined Query
                                            </span>
                                        </div>
                                    </div>
                                );
                            }

                            // Conversation Summary section
                            if (text.includes('Conversation Summary:')) {
                                return (
                                    <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 my-4">
                                        <div className="flex items-center space-x-2 mb-3">
                                            <MessageSquare className="w-5 h-5 text-indigo-600" />
                                            <span className="font-semibold text-indigo-900 text-lg">
                                                Conversation Summary
                                            </span>
                                        </div>
                                    </div>
                                );
                            }

                            // Instructions section
                            if (text.includes('Instructions:')) {
                                return (
                                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 my-4">
                                        <div className="flex items-center space-x-2 mb-3">
                                            <ArrowRight className="w-5 h-5 text-purple-600" />
                                            <span className="font-semibold text-purple-900 text-lg">
                                                Instructions
                                            </span>
                                        </div>
                                    </div>
                                );
                            }

                            return (
                                <span className="font-semibold text-gray-900">
                                    {children}
                                </span>
                            );
                        },
                        ul: ({ children }) => (
                            <ul className="space-y-2 my-3 pl-4">{children}</ul>
                        ),
                        li: ({ children }) => (
                            <li className="flex items-start space-x-2 text-gray-700 bg-gray-50 p-3 rounded-lg border border-gray-200">
                                <AlertCircle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                                <span>{children}</span>
                            </li>
                        ),
                        p: ({ children }) => {
                            const text = children?.toString() || '';

                            // Style content that comes after section headers
                            if (text.length > 0) {
                                return (
                                    <div className="bg-white border border-gray-200 rounded-lg p-4 my-3">
                                        <p className="text-gray-700 leading-relaxed m-0">
                                            {children}
                                        </p>
                                    </div>
                                );
                            }

                            return (
                                <p className="text-gray-700 leading-relaxed mb-3 last:mb-0">
                                    {children}
                                </p>
                            );
                        },
                    }}
                >
                    {textToRender}
                </ReactMarkdown>
            </div>
        );
    }

    // Fall back to regular markdown renderer
    return (
        <MarkdownRenderer
            content={content}
            isAnimated={isAnimated}
            displayText={displayText}
        />
    );
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onReasoningStart }) => {
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const {
        threadId,
        messages,
        isLoading,
        dashboardState,
        isReopenedDashboard,
        setThreadId,
        addMessage,
        setLoading,
        setDashboardState,
    } = useChatContext();
    const { currentDashboard } = useDashboardContext();

    const lastMessage = messages[messages.length - 1];
    const shouldAnimate = lastMessage && !lastMessage.isUser;

    const { displayText, isTyping } = useTypingAnimation(
        shouldAnimate ? lastMessage.content : '',
        0
    );

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, displayText]);

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
                    setThreadId(response.thread_id, currentDashboard.id);
                }

                // Update dashboard state
                if (response.dashboard_state) {
                    setDashboardState(response.dashboard_state);
                }

                // Start reasoning animation if config is provided
                if (response.reasoning_config) {
                    onReasoningStart(response.reasoning_config);
                }

                // Determine delay based on response type
                let delay = 1500; // Default delay
                if (response.status === 'waiting_for_input') {
                    delay = 2000; // HITL needs more processing time
                } else if (response.reasoning_config) {
                    delay = 4000; // Complex reasoning needs more time
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
                }, delay);
            } catch (error) {
                console.error('Error sending message:', error);
                const errorMessage = {
                    id: (Date.now() + 1).toString(),
                    content:
                        'Sorry, I encountered an error while processing your request. Please try again.',
                    isUser: false,
                    timestamp: new Date(),
                    threadId: threadId || undefined,
                };
                addMessage(errorMessage);
                setLoading(false);
            }
        }
    };

    const renderUserInsightCard = (
        title: string,
        value: any,
        icon: React.ReactNode,
        color: string = 'blue'
    ) => {
        if (
            !value ||
            (Array.isArray(value) && value.length === 0) ||
            (typeof value === 'object' && Object.keys(value).length === 0)
        )
            return null;

        return (
            <div
                className={`bg-gradient-to-r from-${color}-50 to-${color}-100 border border-${color}-200 rounded-lg p-3 mb-3`}
            >
                <div className="flex items-center space-x-2 mb-2">
                    {icon}
                    <h4 className={`font-medium text-${color}-900 text-sm`}>
                        {title}
                    </h4>
                </div>
                <div className="text-sm text-gray-700">
                    {Array.isArray(value) ? (
                        <div className="flex flex-wrap gap-1">
                            {value.slice(0, 4).map((item, index) => (
                                <span
                                    key={index}
                                    className="bg-white px-2 py-1 rounded border text-xs font-medium"
                                >
                                    {typeof item === 'object'
                                        ? item.name || Object.keys(item)[0]
                                        : String(item)}
                                </span>
                            ))}
                            {value.length > 4 && (
                                <span className="text-gray-500 text-xs">
                                    +{value.length - 4} more
                                </span>
                            )}
                        </div>
                    ) : typeof value === 'object' ? (
                        <div className="bg-white p-2 rounded border text-xs">
                            {Object.entries(value)
                                .slice(0, 3)
                                .map(([k, v]) => (
                                    <div
                                        key={k}
                                        className="flex justify-between"
                                    >
                                        <span className="font-medium">
                                            {k}:
                                        </span>
                                        <span>{String(v)}</span>
                                    </div>
                                ))}
                        </div>
                    ) : (
                        <p className="bg-white p-2 rounded border text-sm font-medium">
                            {String(value)}
                        </p>
                    )}
                </div>
            </div>
        );
    };

    if (!currentDashboard) {
        return (
            <div className="bg-white flex items-center justify-center h-full">
                <div className="text-center">
                    <p className="text-gray-500 mb-2">No dashboard selected</p>
                    <p className="text-sm text-gray-400">
                        Please select a dashboard from the sidebar to start
                        chatting
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white flex flex-col h-full">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((message, index) => {
                    const isLastMessage = index === messages.length - 1;
                    const shouldShowAnimation =
                        isLastMessage && !message.isUser && shouldAnimate;

                    return (
                        <div
                            key={message.id}
                            className={`flex ${
                                message.isUser ? 'justify-end' : 'justify-start'
                            }`}
                        >
                            <div
                                className={`max-w-[90%] rounded-xl shadow-sm transition-all duration-200 hover:shadow-md ${
                                    message.isUser
                                        ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white p-4'
                                        : 'bg-gray-50 text-gray-900 border border-gray-200 hover:bg-gray-100'
                                }`}
                            >
                                <div className="flex items-start space-x-3">
                                    {!message.isUser && (
                                        <div className="p-1.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex-shrink-0 mt-1">
                                            <Bot className="w-4 h-4 text-white" />
                                        </div>
                                    )}
                                    {message.isUser && (
                                        <div className="p-1.5 bg-white/20 rounded-lg flex-shrink-0 mt-1">
                                            <User className="w-4 h-4 text-white" />
                                        </div>
                                    )}
                                    <div className="flex-1 min-w-0">
                                        {/* AI Message with Enhanced User Insights */}
                                        {!message.isUser && (
                                            <div className="p-4">
                                                {/* User-Relevant Insights - Only show if this is the latest AI message and we have state and NOT a reopened dashboard */}
                                                {isLastMessage &&
                                                    dashboardState &&
                                                    !isReopenedDashboard && (
                                                        <div className="mb-4 border-b border-gray-200 pb-4">
                                                            <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                                                                <Lightbulb className="w-4 h-4 mr-2 text-yellow-600" />
                                                                Analysis
                                                                Insights
                                                                {dashboardState.hitl_step && (
                                                                    <span className="ml-2 px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                                                                        HITL
                                                                        Step{' '}
                                                                        {
                                                                            dashboardState.hitl_step
                                                                        }
                                                                    </span>
                                                                )}
                                                            </h3>
                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                                {renderUserInsightCard(
                                                                    'Industry',
                                                                    dashboardState.industry,
                                                                    <Building className="w-4 h-4 text-purple-600" />,
                                                                    'purple'
                                                                )}
                                                                {renderUserInsightCard(
                                                                    'Sub-Vertical',
                                                                    dashboardState.sub_vertical,
                                                                    <Layers className="w-4 h-4 text-blue-600" />,
                                                                    'blue'
                                                                )}
                                                                {renderUserInsightCard(
                                                                    'Entities',
                                                                    dashboardState.entities,
                                                                    <Target className="w-4 h-4 text-green-600" />,
                                                                    'green'
                                                                )}
                                                                {renderUserInsightCard(
                                                                    'Filters',
                                                                    dashboardState.filters,
                                                                    <Filter className="w-4 h-4 text-indigo-600" />,
                                                                    'indigo'
                                                                )}
                                                                {renderUserInsightCard(
                                                                    'Use Case',
                                                                    dashboardState.use_case,
                                                                    <Layers className="w-4 h-4 text-orange-600" />,
                                                                    'orange'
                                                                )}
                                                                {dashboardState.defaults_applied &&
                                                                    renderUserInsightCard(
                                                                        'Applied Defaults',
                                                                        dashboardState.defaults_applied,
                                                                        <ArrowRight className="w-4 h-4 text-teal-600" />,
                                                                        'teal'
                                                                    )}
                                                            </div>
                                                        </div>
                                                    )}

                                                {/* Themes Display */}
                                                {isLastMessage &&
                                                    dashboardState &&
                                                    dashboardState.themes &&
                                                    dashboardState.themes
                                                        .length > 0 && (
                                                        <div className="mb-6">
                                                            <ThemeDisplay
                                                                themes={
                                                                    dashboardState.themes as any[]
                                                                }
                                                                title="Discovered Insights"
                                                            />
                                                        </div>
                                                    )}

                                                {/* AI Response Text */}
                                                <div className="mt-4">
                                                    <StructuredResponseRenderer
                                                        content={
                                                            message.content
                                                        }
                                                        isAnimated={
                                                            shouldShowAnimation
                                                        }
                                                        displayText={
                                                            displayText
                                                        }
                                                    />
                                                    {shouldShowAnimation &&
                                                        isTyping && (
                                                            <span className="inline-block w-2 h-4 bg-purple-500 ml-1 animate-pulse rounded" />
                                                        )}
                                                </div>
                                            </div>
                                        )}

                                        {/* User Message */}
                                        {message.isUser && (
                                            <div className="prose prose-sm max-w-none">
                                                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                                                    {message.content}
                                                </p>
                                            </div>
                                        )}

                                        <p className="text-xs opacity-60 mt-2 px-4">
                                            {message.timestamp instanceof Date
                                                ? message.timestamp.toDateString()
                                                : new Date(
                                                      message.timestamp
                                                  ).toDateString()}{' '}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 max-w-[90%] shadow-sm">
                            <div className="flex items-center space-x-3">
                                <div className="p-1.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg">
                                    <Bot className="w-4 h-4 text-white" />
                                </div>
                                <div className="flex space-x-1">
                                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" />
                                    <div
                                        className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"
                                        style={{ animationDelay: '0.1s' }}
                                    />
                                    <div
                                        className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"
                                        style={{ animationDelay: '0.2s' }}
                                    />
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
                        className="flex-1 bg-white border border-gray-300 rounded-lg px-4 py-3 text-gray-900 placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 disabled:opacity-50 shadow-sm transition-all duration-200"
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
