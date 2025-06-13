import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { ChatMessage, ChatContextType, DashboardState } from '../types';
import { chatApiService } from '../services/chatApi';

interface ChatState {
    threadId: string | null;
    messages: ChatMessage[];
    isLoading: boolean;
    dashboardState: DashboardState | null;
    dashboardThreads: { [dashboardId: string]: string }; // Track thread IDs per dashboard
    currentDashboardId: string | null;
    isReopenedDashboard: boolean; // Track if this is a reopened dashboard
}

type ChatAction =
    | {
          type: 'SET_THREAD_ID';
          payload: { threadId: string | null; dashboardId?: string };
      }
    | { type: 'ADD_MESSAGE'; payload: ChatMessage }
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'CLEAR_MESSAGES'; payload?: { dashboardId?: string } }
    | { type: 'SET_DASHBOARD_STATE'; payload: DashboardState | null }
    | {
          type: 'LOAD_DASHBOARD_CONTEXT';
          payload: {
              dashboardId: string;
              threadId: string | null;
              messages: ChatMessage[];
              dashboardState: DashboardState | null;
              isReopenedDashboard: boolean;
          };
      }
    | { type: 'SET_CURRENT_DASHBOARD'; payload: string | null };

const initialState: ChatState = {
    threadId: null,
    messages: [],
    isLoading: false,
    dashboardState: null,
    dashboardThreads: {},
    currentDashboardId: null,
    isReopenedDashboard: false,
};

const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
    switch (action.type) {
        case 'SET_THREAD_ID':
            const newThreads = { ...state.dashboardThreads };
            if (action.payload.dashboardId && action.payload.threadId) {
                newThreads[action.payload.dashboardId] =
                    action.payload.threadId;
            }
            return {
                ...state,
                threadId: action.payload.threadId,
                dashboardThreads: newThreads,
            };
        case 'ADD_MESSAGE':
            return { ...state, messages: [...state.messages, action.payload] };
        case 'SET_LOADING':
            return { ...state, isLoading: action.payload };
        case 'CLEAR_MESSAGES':
            return {
                ...state,
                messages: [],
                threadId: action.payload?.dashboardId ? state.threadId : null,
                dashboardState: null,
            };
        case 'SET_DASHBOARD_STATE':
            return { ...state, dashboardState: action.payload };
        case 'LOAD_DASHBOARD_CONTEXT':
            return {
                ...state,
                threadId: action.payload.threadId,
                messages: action.payload.messages,
                dashboardState: action.payload.dashboardState,
                isReopenedDashboard: action.payload.isReopenedDashboard,
                dashboardThreads: {
                    ...state.dashboardThreads,
                    [action.payload.dashboardId]: action.payload.threadId || '',
                },
                currentDashboardId: action.payload.dashboardId,
            };
        case 'SET_CURRENT_DASHBOARD':
            return {
                ...state,
                currentDashboardId: action.payload,
            };
        default:
            return state;
    }
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({
    children,
}) => {
    const [state, dispatch] = useReducer(chatReducer, initialState);

    const setThreadId = (threadId: string | null, dashboardId?: string) => {
        dispatch({ type: 'SET_THREAD_ID', payload: { threadId, dashboardId } });
    };

    const addMessage = (message: ChatMessage) => {
        dispatch({ type: 'ADD_MESSAGE', payload: message });
    };

    const setLoading = (loading: boolean) => {
        dispatch({ type: 'SET_LOADING', payload: loading });
    };

    const clearMessages = (dashboardId?: string) => {
        dispatch({ type: 'CLEAR_MESSAGES', payload: { dashboardId } });
    };

    const setDashboardState = (dashboardState: DashboardState | null) => {
        dispatch({ type: 'SET_DASHBOARD_STATE', payload: dashboardState });
    };

    const loadDashboardContext = (dashboardId: string) => {
        // Load stored thread, messages, and dashboard state for this dashboard
        const storedThreadId = chatApiService.getStoredThreadId(dashboardId);
        const storedMessages = chatApiService.getStoredMessages(dashboardId);
        const storedDashboardState =
            chatApiService.getStoredDashboardState(dashboardId);

        // Determine if this is a reopened dashboard (has existing thread and messages)
        const isReopenedDashboard = !!(
            storedThreadId && storedMessages.length > 0
        );

        dispatch({
            type: 'LOAD_DASHBOARD_CONTEXT',
            payload: {
                dashboardId,
                threadId: storedThreadId,
                messages: storedMessages,
                dashboardState: storedDashboardState,
                isReopenedDashboard,
            },
        });
    };

    const setCurrentDashboard = (dashboardId: string | null) => {
        dispatch({ type: 'SET_CURRENT_DASHBOARD', payload: dashboardId });

        if (dashboardId) {
            loadDashboardContext(dashboardId);
        }
    };

    // Auto-save messages to localStorage when they change
    React.useEffect(() => {
        if (state.currentDashboardId && state.messages.length > 0) {
            chatApiService.storeMessages(
                state.currentDashboardId,
                state.messages
            );
        }
    }, [state.messages, state.currentDashboardId]);

    // Auto-save threadId to localStorage when it changes
    React.useEffect(() => {
        if (state.currentDashboardId && state.threadId) {
            chatApiService.storeThreadId(
                state.currentDashboardId,
                state.threadId
            );
        }
    }, [state.threadId, state.currentDashboardId]);

    // Auto-save dashboard state to localStorage when it changes
    React.useEffect(() => {
        if (state.currentDashboardId && state.dashboardState) {
            chatApiService.storeDashboardState(
                state.currentDashboardId,
                state.dashboardState
            );
        }
    }, [state.dashboardState, state.currentDashboardId]);

    const value: ChatContextType = {
        threadId: state.threadId,
        messages: state.messages,
        isLoading: state.isLoading,
        dashboardState: state.dashboardState,
        isReopenedDashboard: state.isReopenedDashboard,
        setThreadId,
        addMessage,
        setLoading,
        clearMessages,
        setDashboardState,
        loadDashboardContext,
        setCurrentDashboard,
    };

    return (
        <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
    );
};

export const useChatContext = () => {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error('useChatContext must be used within a ChatProvider');
    }
    return context;
};
