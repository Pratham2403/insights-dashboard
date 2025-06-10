import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { ChatMessage, ChatContextType, WorkflowState } from '../types';

interface ChatState {
    threadId: string | null;
    messages: ChatMessage[];
    isLoading: boolean;
    workflowState: WorkflowState | null;
    currentStep: number;
}

type ChatAction =
    | { type: 'SET_THREAD_ID'; payload: string | null }
    | { type: 'ADD_MESSAGE'; payload: ChatMessage }
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'CLEAR_MESSAGES' }
    | { type: 'UPDATE_WORKFLOW_STATE'; payload: Partial<WorkflowState> }
    | { type: 'SET_CURRENT_STEP'; payload: number };

const initialState: ChatState = {
    threadId: null,
    messages: [],
    isLoading: false,
    workflowState: null,
    currentStep: 0,
};

const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
    switch (action.type) {
        case 'SET_THREAD_ID':
            return { ...state, threadId: action.payload };
        case 'ADD_MESSAGE':
            return { ...state, messages: [...state.messages, action.payload] };
        case 'SET_LOADING':
            return { ...state, isLoading: action.payload };
        case 'CLEAR_MESSAGES':
            return {
                ...state,
                messages: [],
                threadId: null,
                workflowState: null,
                currentStep: 0,
            };
        case 'UPDATE_WORKFLOW_STATE':
            return {
                ...state,
                workflowState: { ...state.workflowState, ...action.payload },
            };
        case 'SET_CURRENT_STEP':
            return { ...state, currentStep: action.payload };
        default:
            return state;
    }
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({
    children,
}) => {
    const [state, dispatch] = useReducer(chatReducer, initialState);

    const setThreadId = (threadId: string | null) => {
        dispatch({ type: 'SET_THREAD_ID', payload: threadId });
    };

    const addMessage = (message: ChatMessage) => {
        dispatch({ type: 'ADD_MESSAGE', payload: message });
    };

    const setLoading = (loading: boolean) => {
        dispatch({ type: 'SET_LOADING', payload: loading });
    };

    const clearMessages = () => {
        dispatch({ type: 'CLEAR_MESSAGES' });
    };

    const updateWorkflowState = (workflowState: Partial<WorkflowState>) => {
        dispatch({ type: 'UPDATE_WORKFLOW_STATE', payload: workflowState });
    };

    const setCurrentStep = (step: number) => {
        dispatch({ type: 'SET_CURRENT_STEP', payload: step });
    };

    const value: ChatContextType = {
        threadId: state.threadId,
        messages: state.messages,
        isLoading: state.isLoading,
        workflowState: state.workflowState,
        currentStep: state.currentStep,
        setThreadId,
        addMessage,
        setLoading,
        clearMessages,
        updateWorkflowState,
        setCurrentStep,
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
