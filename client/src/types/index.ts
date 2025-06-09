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
}