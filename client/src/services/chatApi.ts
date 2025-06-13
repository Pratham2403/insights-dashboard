import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import { DashboardState } from '../types';

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
    dashboard_state?: DashboardState | null;
    status?: string;
    interrupt_data?: any;
    result?: any;
    message?: string;
}

// Backend API service for Sprinklr Dashboard
class ChatApiService {
    private baseURL = 'http://localhost:8000'; // Backend API endpoint

    async sendMessage(request: ChatRequest): Promise<ChatResponse> {
        try {
            // Call the actual backend API
            const response = await axios.post(
                `${this.baseURL}/api/process`,
                {
                    query: request.query,
                    thread_id: request.thread_id || undefined,
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            );

            const data = response.data;

            if (data.status === 'success' && data.data) {
                const resultData = data.data;

                // Handle different response types from backend
                if (resultData.status === 'waiting_for_input') {
                    // HITL (Human-in-the-Loop) response
                    return {
                        response: this.formatHITLResponse(resultData),
                        thread_id: resultData.thread_id,
                        reasoning_config: 'hitl-verification',
                        timestamp: new Date().toISOString(),
                        dashboard_state:
                            this.convertToClientDashboardState(resultData),
                        status: 'waiting_for_input',
                        interrupt_data: resultData.interrupt_data,
                        message: resultData.message,
                    };
                } else if (
                    resultData.status === 'completed' ||
                    resultData.status === 'completed-explicitly'
                ) {
                    // Workflow completed response
                    return {
                        response: this.formatCompletedResponse(
                            resultData.result
                        ),
                        thread_id: resultData.thread_id,
                        reasoning_config: 'analysis-complete',
                        timestamp: new Date().toISOString(),
                        dashboard_state: this.convertToClientDashboardState(
                            resultData.result
                        ),
                        status: 'completed',
                        result: resultData.result,
                    };
                } else {
                    // Default processing response
                    return {
                        response: 'Processing your request...',
                        thread_id: resultData.thread_id || uuidv4(),
                        reasoning_config: 'processing',
                        timestamp: new Date().toISOString(),
                        dashboard_state:
                            this.convertToClientDashboardState(resultData),
                    };
                }
            } else {
                throw new Error('Invalid response from backend');
            }
        } catch (error) {
            console.error('Backend API error:', error);

            // Fallback response on error
            return {
                response: `I encountered an error while processing your request: ${
                    error instanceof Error ? error.message : 'Unknown error'
                }. Please try again.`,
                thread_id: request.thread_id || uuidv4(),
                timestamp: new Date().toISOString(),
                dashboard_state: null,
            };
        }
    }

    private formatHITLResponse(data: any): string {
        const interruptData = data.interrupt_data || {};

        let response = `## Review Required\n\n`;

        // Show only Review Analysis, Data Requirements, Refined Query, Conversation Summary, Instructions

        // 1. Review Analysis (if available)

        // 3. Refined Query
        if (interruptData.refined_query) {
            response += `**Refined Query:** ${interruptData.refined_query}\n\n`;
        }

        // 4. Conversation Summary
        if (interruptData.conversation_summary) {
            response += `**Conversation Summary:** ${interruptData.conversation_summary}\n\n`;
        }

        // 2. Data Requirements
        if (
            interruptData.data_requirements &&
            interruptData.data_requirements.length > 0
        ) {
            response += `**Data Requirements:**\n${interruptData.data_requirements
                .map((req: string) => `- ${req}`)
                .join('\n')}\n\n`;
        }

        // 5. Instructions (always last)
        response += `**Instructions:** ${
            interruptData.instructions ||
            "Reply 'yes' to approve or provide feedback to refine"
        }`;

        return response;
    }

    private formatCompletedResponse(result: any): string {
        let response = `## Analysis Complete! 🎉\n\n`;

        // Show only a summary message since themes will be displayed beautifully in the UI
        if (result.themes && result.themes.length > 0) {
            response += `**Discovered ${result.themes.length} Key Themes**\n\n`;
            response += `I've analyzed your data and identified ${result.themes.length} significant themes. Each theme includes detailed insights, confidence metrics, and optimized boolean queries for further exploration.\n\n`;
        }

        // 2. Boolean Query Generated
        if (result.boolean_query) {
            response += `**Main Analysis Query:** \`${result.boolean_query}\`\n\n`;
        }

        // Final message
        response += `Your comprehensive analysis is now complete and ready for exploration! 🚀`;

        return response;
    }

    private convertToClientDashboardState(data: any): DashboardState | null {
        if (!data) return null;

        // Handle interrupt data structure
        const sourceData = data.interrupt_data || data;

        return {
            query: Array.isArray(sourceData.query)
                ? sourceData.query
                : sourceData.query
                ? [sourceData.query]
                : [data.message || ''],
            refined_query: sourceData.refined_query || '',
            keywords: Array.isArray(sourceData.keywords)
                ? sourceData.keywords
                : [],
            filters: sourceData.filters || {},
            boolean_query: sourceData.boolean_query || '',
            themes: Array.isArray(sourceData.themes) ? sourceData.themes : [],
            messages: [],
            thread_id: data.thread_id,
            current_stage: sourceData.current_stage || 'processing',
            workflow_status: sourceData.workflow_status || 'active',
            workflow_started:
                sourceData.workflow_started || new Date().toISOString(),
            data_requirements: Array.isArray(sourceData.data_requirements)
                ? sourceData.data_requirements
                : [],
            hitl_step: sourceData.step || sourceData.hitl_step || 1,
            user_input: sourceData.user_input || '',
            next_node: sourceData.next_node || 'analysis',
            reason: sourceData.reason || 'processing_query',
            entities: Array.isArray(sourceData.entities)
                ? sourceData.entities
                : [],
            industry: sourceData.industry || '',
            sub_vertical: sourceData.sub_vertical || '',
            use_case: sourceData.use_case || '',
            defaults_applied: sourceData.defaults_applied || {},
            conversation_summary: sourceData.conversation_summary || '',
            human_feedback: sourceData.human_feedback,
            errors: Array.isArray(sourceData.errors) ? sourceData.errors : [],
        };
    }

    // Thread management utilities
    getStoredThreadId(dashboardId: string): string | null {
        try {
            return localStorage.getItem(`chat_thread_${dashboardId}`);
        } catch (error) {
            console.error('Error accessing localStorage:', error);
            return null;
        }
    }

    storeThreadId(dashboardId: string, threadId: string): void {
        try {
            localStorage.setItem(`chat_thread_${dashboardId}`, threadId);
        } catch (error) {
            console.error('Error storing thread ID:', error);
        }
    }

    clearStoredThreadId(dashboardId: string): void {
        try {
            localStorage.removeItem(`chat_thread_${dashboardId}`);
        } catch (error) {
            console.error('Error clearing thread ID:', error);
        }
    }

    getStoredMessages(dashboardId: string): any[] {
        try {
            const stored = localStorage.getItem(`chat_messages_${dashboardId}`);
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('Error accessing stored messages:', error);
            return [];
        }
    }

    storeMessages(dashboardId: string, messages: any[]): void {
        try {
            localStorage.setItem(
                `chat_messages_${dashboardId}`,
                JSON.stringify(messages)
            );
        } catch (error) {
            console.error('Error storing messages:', error);
        }
    }

    clearStoredMessages(dashboardId: string): void {
        try {
            localStorage.removeItem(`chat_messages_${dashboardId}`);
        } catch (error) {
            console.error('Error clearing messages:', error);
        }
    }

    // Dashboard state management utilities
    getStoredDashboardState(dashboardId: string): DashboardState | null {
        try {
            const stored = localStorage.getItem(
                `chat_dashboard_state_${dashboardId}`
            );
            return stored ? JSON.parse(stored) : null;
        } catch (error) {
            console.error('Error accessing stored dashboard state:', error);
            return null;
        }
    }

    storeDashboardState(
        dashboardId: string,
        dashboardState: DashboardState
    ): void {
        try {
            localStorage.setItem(
                `chat_dashboard_state_${dashboardId}`,
                JSON.stringify(dashboardState)
            );
        } catch (error) {
            console.error('Error storing dashboard state:', error);
        }
    }

    clearStoredDashboardState(dashboardId: string): void {
        try {
            localStorage.removeItem(`chat_dashboard_state_${dashboardId}`);
        } catch (error) {
            console.error('Error clearing dashboard state:', error);
        }
    }
}

export const chatApiService = new ChatApiService();
