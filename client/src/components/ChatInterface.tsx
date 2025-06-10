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
    const {
        threadId,
        messages,
        isLoading,
        workflowState,
        currentStep,
        setThreadId,
        addMessage,
        setLoading,
        updateWorkflowState,
        setCurrentStep,
    } = useChatContext();
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

                // Update thread ID from response (always use the latest from backend)
                if (response.thread_id) {
                    setThreadId(response.thread_id);
                }

                // Update workflow state if provided
                if (response.workflow_state) {
                    updateWorkflowState(response.workflow_state);

                    // Update current step based on workflow progress
                    let step = 1;
                    if (response.workflow_state.refined_query)
                        step = Math.max(step, 2);
                    if (response.workflow_state.keywords?.length > 0)
                        step = Math.max(step, 3);
                    if (response.workflow_state.hitl_step)
                        step = Math.max(
                            step,
                            response.workflow_state.hitl_step
                        );
                    if (response.workflow_state.data_requirements?.length > 0)
                        step = Math.max(step, 4);
                    if (response.workflow_state.themes?.length > 0)
                        step = Math.max(step, 5);
                    if (response.workflow_state.analysis_results)
                        step = Math.max(step, 6);

                    setCurrentStep(step);
                }

                // Handle HITL interactions
                if (
                    response.status === 'waiting_for_input' &&
                    response.interrupt_data
                ) {
                    // Update current step for reasoning panel
                    if (response.interrupt_data.step) {
                        setCurrentStep(response.interrupt_data.step);
                    }

                    const hitlMessage = {
                        id: (Date.now() + 1).toString(),
                        content: response.response,
                        isUser: false,
                        timestamp: new Date(),
                        threadId: response.thread_id,
                        status: 'waiting_for_input' as const,
                        interruptData: response.interrupt_data,
                    };

                    addMessage(hitlMessage);

                    // Start reasoning animation if config is provided
                    if (response.reasoning_config) {
                        onReasoningStart(response.reasoning_config);
                    }

                    // Enable input for HITL response
                    setLoading(false);
                } else {
                    // Start reasoning animation if config is provided
                    if (response.reasoning_config) {
                        onReasoningStart(response.reasoning_config);
                    }

                    // Add AI response after a delay to show reasoning
                    setTimeout(
                        () => {
                            const aiMessage = {
                                id: (Date.now() + 1).toString(),
                                content: response.response,
                                isUser: false,
                                timestamp: new Date(),
                                threadId: response.thread_id,
                                status: response.status as any,
                                workflowState: response.result,
                            };

                            addMessage(aiMessage);
                            setLoading(false);
                        },
                        response.reasoning_config ? 4000 : 1500
                    );
                }
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
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((message, index) => {
                    const isLastMessage = index === messages.length - 1;
                    const shouldShowAnimation =
                        isLastMessage && !message.isUser && shouldAnimate;
                    const isHITL = message.status === 'waiting_for_input';

                    return (
                        <div
                            key={message.id}
                            className={`flex ${
                                message.isUser ? 'justify-end' : 'justify-start'
                            }`}
                        >
                            <div
                                className={`max-w-[80%] rounded-xl p-4 shadow-sm ${
                                    message.isUser
                                        ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                                        : isHITL
                                        ? 'bg-gradient-to-r from-amber-50 to-orange-50 text-gray-900 border-2 border-amber-200'
                                        : 'bg-gray-50 text-gray-900 border border-gray-200'
                                }`}
                            >
                                <div className="flex items-start space-x-3">
                                    {!message.isUser && (
                                        <div
                                            className={`p-1.5 rounded-lg flex-shrink-0 ${
                                                isHITL
                                                    ? 'bg-gradient-to-r from-amber-500 to-orange-500'
                                                    : 'bg-gradient-to-r from-purple-500 to-blue-500'
                                            }`}
                                        >
                                            <Bot className="w-4 h-4 text-white" />
                                        </div>
                                    )}
                                    {message.isUser && (
                                        <div className="p-1.5 bg-white/20 rounded-lg flex-shrink-0">
                                            <User className="w-4 h-4 text-white" />
                                        </div>
                                    )}
                                    <div className="flex-1">
                                        {isHITL && (
                                            <div className="mb-3 p-3 bg-white rounded-lg border border-amber-200">
                                                <div className="text-sm font-medium text-amber-800 mb-2">
                                                    🔍 Human Verification
                                                    Required
                                                </div>
                                                {message.interruptData && (
                                                    <div className="space-y-2 text-sm">
                                                        {message.interruptData
                                                            .refined_query && (
                                                            <div>
                                                                <span className="font-medium">
                                                                    Refined
                                                                    Query:
                                                                </span>{' '}
                                                                {
                                                                    message
                                                                        .interruptData
                                                                        .refined_query
                                                                }
                                                            </div>
                                                        )}
                                                        {message.interruptData
                                                            .keywords &&
                                                            message
                                                                .interruptData
                                                                .keywords
                                                                .length > 0 && (
                                                                <div>
                                                                    <span className="font-medium">
                                                                        Keywords:
                                                                    </span>{' '}
                                                                    {message.interruptData.keywords.join(
                                                                        ', '
                                                                    )}
                                                                </div>
                                                            )}
                                                        {message.interruptData
                                                            .filters &&
                                                            Object.keys(
                                                                message
                                                                    .interruptData
                                                                    .filters
                                                            ).length > 0 && (
                                                                <div>
                                                                    <span className="font-medium">
                                                                        Filters:
                                                                    </span>{' '}
                                                                    {JSON.stringify(
                                                                        message
                                                                            .interruptData
                                                                            .filters,
                                                                        null,
                                                                        2
                                                                    )}
                                                                </div>
                                                            )}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                        <div className="prose prose-sm max-w-none">
                                            <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                                {shouldShowAnimation
                                                    ? displayText
                                                    : message.content}
                                            </p>
                                        </div>
                                        {shouldShowAnimation && isTyping && (
                                            <span className="inline-block w-2 h-4 bg-purple-500 ml-1 animate-pulse rounded" />
                                        )}
                                        <p
                                            className={`text-xs mt-2 ${
                                                message.isUser
                                                    ? 'opacity-60'
                                                    : isHITL
                                                    ? 'text-amber-600'
                                                    : 'opacity-60'
                                            }`}
                                        >
                                            {message.timestamp.toLocaleTimeString()}
                                            {isHITL &&
                                                ' • Waiting for approval'}
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
