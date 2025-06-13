export interface ReasoningStep {
    id: number;
    heading: string;
    content: string;
    isCompleted: boolean;
    isActive: boolean;
}

export interface ChatMessage {
    id: string;
    content: string;
    isUser: boolean;
    timestamp: Date;
    threadId?: string;
}

export interface Dashboard {
    id: string;
    name: string;
    type: string;
    description: string;
    icon: string;
    color: string;
    dataFile: string;
    createdAt: Date;
    lastAccessed: Date;
}

export interface DashboardData {
    id: string;
    name: string;
    type: string;
    brandMetrics: {
        mentions: MetricData;
        sentiment: SentimentData;
        reach: MetricData;
        engagement: MetricData;
    };
    sentimentTrend: TrendData[];
    topicAnalysis: TopicData[];
    competitorComparison: CompetitorData[];
    geographicData: GeographicData[];
    timeSeriesData: TimeSeriesData[];
}

export interface MetricData {
    current: string | number;
    previous: string | number;
    change: string;
    trend: 'up' | 'down';
}

export interface SentimentData {
    positive: number;
    negative: number;
    neutral: number;
}

export interface TrendData {
    date: string;
    positive: number;
    negative: number;
}

export interface TopicData {
    topic: string;
    mentions: number;
    sentiment: number;
}

export interface CompetitorData {
    brand: string;
    mentions: number;
    sentiment: number;
    share: number;
}

export interface GeographicData {
    region: string;
    mentions: number;
    sentiment: number;
}

export interface TimeSeriesData {
    date: string;
    mentions: number;
    reach: number;
    engagement: number;
}

export interface ReasoningConfig {
    id: string;
    name: string;
    description: string;
    steps: ReasoningStepConfig[];
}

export interface ReasoningStepConfig {
    id: number;
    heading: string;
    content: string;
    duration: number;
}

export interface ChatContextType {
    threadId: string | null;
    messages: ChatMessage[];
    isLoading: boolean;
    dashboardState: DashboardState | null;
    isReopenedDashboard: boolean;
    setThreadId: (threadId: string | null, dashboardId?: string) => void;
    addMessage: (message: ChatMessage) => void;
    setLoading: (loading: boolean) => void;
    clearMessages: (dashboardId?: string) => void;
    setDashboardState: (state: DashboardState | null) => void;
    loadDashboardContext: (dashboardId: string) => void;
    setCurrentDashboard: (dashboardId: string | null) => void;
}

// Backend State Interface - Updated to match states.py exactly
export interface DashboardState {
    // Core fields as per PROMPT.md and states.py
    query: string[]; // List of queries for conversation
    refined_query?: string; // Refined query string
    keywords?: string[]; // Extracted keywords list
    filters?: Record<string, any>; // Filter mappings
    boolean_query?: string; // Generated boolean query
    themes?: Array<Record<string, any>>; // Generated themes with boolean queries

    // LangGraph compatibility (required)
    messages: any[]; // BaseMessage sequence

    // Additional tracking fields
    thread_id?: string;
    current_stage?: string;
    workflow_status?: string;
    workflow_started?: string;
    data_requirements?: string[];

    hitl_step?: number; // tracks HITL step progression
    user_input?: string; // current user input
    next_node?: string; // next node to route to
    reason?: string; // reason for HITL trigger (e.g., "clarification_needed")

    // Processing metadata
    entities?: string[];
    industry?: string;
    sub_vertical?: string;
    use_case?: string;
    defaults_applied?: Record<string, any>; // Applied defaults for the query (changed from string[] to Record)
    conversation_summary?: string; // Summary of the conversation

    // HITL verification
    human_feedback?: string;

    // Workflow tracking
    errors?: string[];
}
