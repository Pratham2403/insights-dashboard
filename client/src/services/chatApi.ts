import axios from 'axios';

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
    status?: string;
    interrupt_data?: any;
    result?: any;
    workflow_state?: any; // Added for workflow state tracking
}

export interface BackendResponse {
    status: string;
    message: string;
    data: {
        status: string;
        result?: any;
        thread_id: string;
        interrupt_data?: any;
    };
    timestamp: string;
}

class ChatApiService {
    private baseURL = 'http://localhost:8000/api'; // Backend API endpoint
    private axiosInstance = axios.create({
        baseURL: this.baseURL,
        headers: {
            'Content-Type': 'application/json',
        },
    });

    async sendMessage(request: ChatRequest): Promise<ChatResponse> {
        // Security: Validate thread_id format if provided
        if (request.thread_id && !this.isValidThreadId(request.thread_id)) {
            throw new Error('Invalid thread_id format');
        }

        try {
            const payload = {
                query: request.query,
                thread_id: request.thread_id || null,
            };

            console.log('📤 Sending request to backend:', payload);

            const response = await this.axiosInstance.post<BackendResponse>(
                '/process',
                payload
            );

            console.log('📥 Backend response:', response.data);

            const backendData = response.data.data;

            // Handle different response types from backend
            if (backendData.status === 'waiting_for_input') {
                // HITL interaction required
                return {
                    response: this.formatHITLResponse(
                        backendData.interrupt_data
                    ),
                    thread_id: backendData.thread_id,
                    reasoning_config: 'dashboard-workflow',
                    timestamp: response.data.timestamp,
                    status: 'waiting_for_input',
                    interrupt_data: backendData.interrupt_data,
                    workflow_state: backendData.result || {}, // Include any available state
                };
            } else if (backendData.status === 'completed') {
                // Workflow completed
                return {
                    response: this.formatCompletedResponse(backendData.result),
                    thread_id: backendData.thread_id,
                    reasoning_config: 'dashboard-workflow',
                    timestamp: response.data.timestamp,
                    status: 'completed',
                    result: backendData.result,
                    workflow_state: backendData.result,
                };
            } else {
                // Default case
                return {
                    response: response.data.message || 'Processing completed',
                    thread_id: backendData.thread_id,
                    reasoning_config: 'dashboard-workflow',
                    timestamp: response.data.timestamp,
                    status: backendData.status,
                    workflow_state: backendData.result || {},
                };
            }
        } catch (error: any) {
            console.error('❌ Error communicating with backend:', error);

            if (error.response) {
                throw new Error(
                    `Backend error: ${
                        error.response.data?.message ||
                        error.response.statusText
                    }`
                );
            } else if (error.request) {
                throw new Error(
                    'Unable to connect to backend service. Please ensure the server is running.'
                );
            } else {
                throw new Error(`Request error: ${error.message}`);
            }
        }
    }

    private isValidThreadId(threadId: string): boolean {
        // UUID v4 format validation
        const uuidRegex =
            /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        return uuidRegex.test(threadId);
    }

    private formatHITLResponse(interruptData: any): string {
        if (!interruptData) {
            return 'Please provide feedback to continue the analysis.';
        }

        const {
            question,
            refined_query,
            keywords,
            filters,
            data_requirements,
            instructions,
        } = interruptData;

        let response = `${question || 'Please review the analysis below:'}\n\n`;

        if (refined_query) {
            response += `**Refined Query:** ${refined_query}\n\n`;
        }

        if (keywords && keywords.length > 0) {
            response += `**Keywords Identified:** ${keywords.join(', ')}\n\n`;
        }

        if (filters && Object.keys(filters).length > 0) {
            response += `**Filters Applied:**\n`;
            Object.entries(filters).forEach(([key, value]) => {
                response += `- ${key}: ${value}\n`;
            });
            response += '\n';
        }

        if (data_requirements && data_requirements.length > 0) {
            response += `**Data Requirements:**\n`;
            data_requirements.forEach((req: string) => {
                response += `- ${req}\n`;
            });
            response += '\n';
        }

        response +=
            instructions ||
            "Reply 'yes' to approve or provide feedback to refine the analysis.";

        return response;
    }

    private formatCompletedResponse(result: any): string {
        if (!result) {
            return 'Analysis completed successfully.';
        }

        // Handle different result structures from the backend
        if (typeof result === 'string') {
            return result;
        }

        if (result.analysis_results) {
            return this.formatAnalysisResults(result.analysis_results);
        }

        if (result.themes && Array.isArray(result.themes)) {
            return this.formatThemesResponse(result.themes);
        }

        if (result.boolean_query) {
            return `Analysis completed with query: ${result.boolean_query}`;
        }

        // Fallback: stringify the result in a readable format
        return (
            'Analysis completed. Here are the key insights from your data:\n\n' +
            JSON.stringify(result, null, 2).slice(0, 1000) +
            '...'
        );
    }

    private formatAnalysisResults(analysisResults: any): string {
        let response = '## Analysis Results\n\n';

        if (analysisResults.insights) {
            response += '### Key Insights\n';
            if (Array.isArray(analysisResults.insights)) {
                analysisResults.insights.forEach(
                    (insight: string, index: number) => {
                        response += `${index + 1}. ${insight}\n`;
                    }
                );
            } else {
                response += `${analysisResults.insights}\n`;
            }
            response += '\n';
        }

        if (analysisResults.recommendations) {
            response += '### Recommendations\n';
            if (Array.isArray(analysisResults.recommendations)) {
                analysisResults.recommendations.forEach(
                    (rec: string, index: number) => {
                        response += `${index + 1}. ${rec}\n`;
                    }
                );
            } else {
                response += `${analysisResults.recommendations}\n`;
            }
            response += '\n';
        }

        if (analysisResults.metrics) {
            response += '### Key Metrics\n';
            Object.entries(analysisResults.metrics).forEach(([key, value]) => {
                response += `- **${key}**: ${value}\n`;
            });
            response += '\n';
        }

        return response;
    }

    private formatThemesResponse(themes: any[]): string {
        let response = '## Dashboard Themes Analysis\n\n';

        themes.forEach((theme, index) => {
            response += `### Theme ${index + 1}: ${
                theme.name || `Theme ${index + 1}`
            }\n`;
            if (theme.description) {
                response += `${theme.description}\n`;
            }
            if (theme.boolean_query) {
                response += `**Query**: ${theme.boolean_query}\n`;
            }
            if (theme.keywords && theme.keywords.length > 0) {
                response += `**Keywords**: ${theme.keywords.join(', ')}\n`;
            }
            response += '\n';
        });

        return response;
    }

    async getHistory(threadId: string): Promise<any> {
        try {
            const response = await this.axiosInstance.get(
                `/history/${threadId}`
            );
            return response.data;
        } catch (error: any) {
            console.error('❌ Error fetching history:', error);
            throw new Error(
                `Failed to fetch conversation history: ${error.message}`
            );
        }
    }
}

export const chatApiService = new ChatApiService();
