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
    status?: 'waiting_for_input' | 'completed' | 'processing';
    interruptData?: HITLInterruptData;
    workflowState?: WorkflowState;
}

export interface HITLInterruptData {
    question?: string;
    step?: number;
    refined_query?: string;
    keywords?: string[];
    filters?: Record<string, any>;
    data_requirements?: string[];
    instructions?: string;
    reason?: string;
}

export interface WorkflowState {
    query?: string[];
    refined_query?: string;
    keywords?: string[];
    filters?: Record<string, any>;
    boolean_query?: string;
    themes?: Array<{
        name?: string;
        description?: string;
        boolean_query?: string;
        keywords?: string[];
    }>;
    data_requirements?: string[];
    analysis_results?: Record<string, any>;
    hitl_step?: number;
    current_stage?: string;
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
    state_field?: string;
    is_hitl?: boolean;
}

export interface ChatContextType {
    threadId: string | null;
    messages: ChatMessage[];
    isLoading: boolean;
    workflowState: WorkflowState | null;
    currentStep: number;
    setThreadId: (threadId: string | null) => void;
    addMessage: (message: ChatMessage) => void;
    setLoading: (loading: boolean) => void;
    clearMessages: () => void;
    updateWorkflowState: (state: Partial<WorkflowState>) => void;
    setCurrentStep: (step: number) => void;
}
