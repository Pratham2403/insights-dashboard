import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

export interface ChatRequest {
  query: string;
  thread_id?: string;
  dashboard_id?: string;
}

export interface ChatResponse {
  response: string;
  thread_id: string;
  reasoning_config?: string;
  timestamp: string;
}

// Demo API service with timeout simulation
class ChatApiService {
  private baseURL = '/api/chat'; // This would be your actual API endpoint
  private timeout = 3000; // 3 second timeout for demo

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    // Security: Validate thread_id format if provided
    if (request.thread_id && !this.isValidThreadId(request.thread_id)) {
      throw new Error('Invalid thread_id format');
    }

    // Simulate API call with timeout
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        try {
          const response = this.generateMockResponse(request);
          resolve(response);
        } catch (error) {
          reject(error);
        }
      }, this.timeout);
    });
  }

  private isValidThreadId(threadId: string): boolean {
    // UUID v4 format validation
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(threadId);
  }

  private generateMockResponse(request: ChatRequest): ChatResponse {
    const threadId = request.thread_id || uuidv4();
    
    // Generate different responses based on query content
    let response = '';
    let reasoningConfig = '';

    if (request.query.toLowerCase().includes('react error handling')) {
      response = this.getReactErrorHandlingResponse();
      reasoningConfig = 'react-error-handling';
    } else if (request.query.toLowerCase().includes('dashboard') || request.query.toLowerCase().includes('data')) {
      response = this.getDashboardAnalysisResponse(request.dashboard_id);
      reasoningConfig = 'dashboard-analysis';
    } else if (request.query.toLowerCase().includes('market') || request.query.toLowerCase().includes('competitor')) {
      response = this.getMarketIntelligenceResponse();
      reasoningConfig = 'market-intelligence';
    } else {
      response = this.getGenericResponse(request.query);
      reasoningConfig = 'dashboard-analysis';
    }

    return {
      response,
      thread_id: threadId,
      reasoning_config: reasoningConfig,
      timestamp: new Date().toISOString(),
    };
  }

  private getReactErrorHandlingResponse(): string {
    return `Here's a comprehensive guide to implementing React error handling:

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
  }

  private getDashboardAnalysisResponse(dashboardId?: string): string {
    return `Based on your dashboard data analysis, here are the key insights:

## Current Performance Metrics
Your dashboard shows strong performance across multiple indicators:

**Engagement Trends:**
- Significant increase in mentions and reach
- Positive sentiment trending upward
- Geographic expansion showing promising results

**Key Recommendations:**
1. **Capitalize on Positive Momentum**: The current upward trend in sentiment and engagement suggests your recent initiatives are working well.

2. **Geographic Expansion**: Focus on regions showing high engagement rates, particularly North America and Asia Pacific.

3. **Content Strategy**: Topics related to product quality and customer service are driving the most positive sentiment.

**Areas for Attention:**
- Monitor pricing-related discussions as they show mixed sentiment
- Consider expanding customer support in high-growth regions

Would you like me to dive deeper into any specific metric or provide more detailed analysis of a particular aspect?`;
  }

  private getMarketIntelligenceResponse(): string {
    return `Here's your comprehensive market intelligence analysis:

## Market Position Analysis
Based on current data, your market position shows:

**Competitive Landscape:**
- Strong sentiment performance compared to competitors
- Growing market share in key segments
- Innovation topics driving positive discussions

**Strategic Opportunities:**
1. **Market Leadership**: Your sentiment scores outperform major competitors
2. **Innovation Focus**: High positive sentiment around innovation topics
3. **Geographic Expansion**: Untapped potential in emerging markets

**Competitive Threats:**
- Market leader maintains significant share advantage
- Pricing pressure from challenger brands
- Need for continued innovation to maintain differentiation

**Recommendations:**
1. Leverage superior sentiment to capture market share
2. Invest in innovation to maintain competitive advantage
3. Consider strategic partnerships in high-growth regions

Would you like detailed analysis of any specific competitor or market segment?`;
  }

  private getGenericResponse(query: string): string {
    return `I understand you're asking about "${query}". Based on your dashboard data and current context, I can provide insights and analysis.

For the most comprehensive analysis with detailed reasoning, try asking me about:
- "React error handling" for technical implementation guidance
- "Dashboard analysis" for data insights and recommendations  
- "Market intelligence" for competitive analysis

What specific aspect would you like me to focus on? I can analyze your current dashboard metrics, provide technical guidance, or offer strategic recommendations based on your data.`;
  }
}

export const chatApiService = new ChatApiService();