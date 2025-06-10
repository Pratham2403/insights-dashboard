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
  setThreadId: (threadId: string | null) => void;
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  clearMessages: () => void;
}