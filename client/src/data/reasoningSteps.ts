import { ReasoningStep } from '../types';

export const sampleReasoningSteps: ReasoningStep[] = [
    {
        id: 1,
        heading: 'Query Refinement Agent',
        content:
            'Processing user query to extract intent, refine language, and identify key requirements for dashboard analysis. Creating refined_query from original query.',
        isCompleted: false,
        isActive: false,
    },
    {
        id: 2,
        heading: 'Query Generator Agent',
        content:
            'Generating boolean queries based on refined query, extracting keywords, and applying appropriate filters. Creating keywords list and filters object.',
        isCompleted: false,
        isActive: false,
    },
    {
        id: 3,
        heading: 'Human-in-the-Loop Verification',
        content:
            'Waiting for human review and approval of extracted keywords, filters, and boolean queries before proceeding. User can approve or provide feedback.',
        isCompleted: false,
        isActive: false,
    },
    {
        id: 4,
        heading: 'Data Collector Agent',
        content:
            'Collecting relevant data based on approved queries and filters, organizing information for analysis. Gathering data_requirements.',
        isCompleted: false,
        isActive: false,
    },
    {
        id: 5,
        heading: 'Data Analyzer Agent',
        content:
            'Analyzing collected data, generating themes, insights, and recommendations for dashboard visualization. Creating themes with boolean queries.',
        isCompleted: false,
        isActive: false,
    },
    {
        id: 6,
        heading: 'Final Processing',
        content:
            'Synthesizing analysis results, formatting output, and preparing final response with actionable insights.',
        isCompleted: false,
        isActive: false,
    },
];
