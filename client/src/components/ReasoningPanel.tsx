import React, { useState, useEffect } from 'react';
import { Brain, Zap, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import ReasoningStep from './ReasoningStep';
import ProgressIndicator from './ProgressIndicator';
import { useChatContext } from '../context/ChatContext';
import { ReasoningStep as ReasoningStepType, ReasoningConfig } from '../types';

interface ReasoningPanelProps {
    isThinking: boolean;
    onComplete: () => void;
    configId?: string;
}

const ReasoningPanel: React.FC<ReasoningPanelProps> = ({
    isThinking,
    onComplete,
    configId = 'dashboard-workflow',
}) => {
    const [steps, setSteps] = useState<ReasoningStepType[]>([]);
    const [selectedStepId, setSelectedStepId] = useState<number | null>(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [reasoningConfig, setReasoningConfig] =
        useState<ReasoningConfig | null>(null);

    // Get workflow state from chat context
    const { workflowState, currentStep: chatCurrentStep } = useChatContext();

    // Load reasoning configuration from JSON
    useEffect(() => {
        const loadReasoningConfig = async () => {
            try {
                const configData = await import(
                    '../data/reasoningConfigs.json'
                );
                const config = configData.default.find(
                    (c: ReasoningConfig) => c.id === configId
                );

                if (config) {
                    setReasoningConfig(config);
                    const initialSteps = config.steps.map((step) => ({
                        id: step.id,
                        heading: step.heading,
                        content: step.content,
                        isCompleted: false,
                        isActive: false,
                    }));
                    setSteps(initialSteps);
                }
            } catch (error) {
                console.error('Error loading reasoning config:', error);
                // Fallback to default steps
                setSteps([
                    {
                        id: 1,
                        heading: 'Processing request',
                        content:
                            'Analyzing your query and determining the best approach to provide a comprehensive response.',
                        isCompleted: false,
                        isActive: false,
                    },
                ]);
            }
        };

        loadReasoningConfig();
    }, [configId]);

    // Update current step when chat context changes
    useEffect(() => {
        if (chatCurrentStep > 0) {
            setCurrentStep(chatCurrentStep);
        }
    }, [chatCurrentStep]);

    // Update step completion based on workflow state
    useEffect(() => {
        if (workflowState && reasoningConfig) {
            setSteps((prevSteps) =>
                prevSteps.map((step) => {
                    const stepConfig = reasoningConfig.steps.find(
                        (s) => s.id === step.id
                    );
                    if (
                        stepConfig?.state_field &&
                        workflowState[
                            stepConfig.state_field as keyof typeof workflowState
                        ]
                    ) {
                        return { ...step, isCompleted: true };
                    }

                    // Handle HITL step specifically
                    if (
                        stepConfig?.is_hitl &&
                        workflowState.hitl_step &&
                        workflowState.hitl_step >= step.id
                    ) {
                        return { ...step, isActive: true, isCompleted: false };
                    }

                    return step;
                })
            );
        }
    }, [workflowState, reasoningConfig]);

    // Traditional step processing for animation (fallback when no backend state)
    useEffect(() => {
        if (!isThinking || steps.length === 0 || workflowState) return; // Skip if we have backend state

        let stepIndex = 0;
        const processNextStep = () => {
            if (stepIndex >= steps.length) {
                onComplete();
                return;
            }

            // Update steps state
            setSteps((prevSteps) =>
                prevSteps.map((step, index) => ({
                    ...step,
                    isCompleted: index < stepIndex,
                    isActive: index === stepIndex,
                }))
            );

            setCurrentStep(stepIndex + 1);

            // Get duration from config or use default
            const duration =
                reasoningConfig?.steps[stepIndex]?.duration || 2000;

            setTimeout(() => {
                stepIndex++;
                processNextStep();
            }, duration);
        };

        processNextStep();
    }, [isThinking, steps.length, reasoningConfig, onComplete, workflowState]);

    const handleStepClick = (stepId: number) => {
        setSelectedStepId(selectedStepId === stepId ? null : stepId);
    };

    return (
        <div className="bg-white h-full flex flex-col">
            <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
                <div className="flex items-center space-x-3 mb-4">
                    <div className="p-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg">
                        <Brain className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                        <h2 className="text-lg font-semibold text-gray-900">
                            {reasoningConfig?.name || 'AI Reasoning Process'}
                        </h2>
                        {reasoningConfig?.description && (
                            <p className="text-sm text-gray-600">
                                {reasoningConfig.description}
                            </p>
                        )}
                    </div>
                    {isThinking && (
                        <div className="flex items-center space-x-2 text-purple-600">
                            <Zap className="w-4 h-4 animate-pulse" />
                            <span className="text-sm font-medium">
                                Thinking...
                            </span>
                        </div>
                    )}
                </div>
            </div>

            {/* Workflow State Display */}
            {workflowState && (
                <div className="px-6 py-3 bg-blue-50 border-b border-blue-200">
                    <div className="text-sm font-medium text-blue-800 mb-2">
                        Current Workflow State
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                        {workflowState.refined_query && (
                            <div className="flex items-center space-x-2">
                                <CheckCircle className="w-3 h-3 text-green-500" />
                                <span>Query Refined</span>
                            </div>
                        )}
                        {workflowState.keywords &&
                            workflowState.keywords.length > 0 && (
                                <div className="flex items-center space-x-2">
                                    <CheckCircle className="w-3 h-3 text-green-500" />
                                    <span>
                                        Keywords (
                                        {workflowState.keywords.length})
                                    </span>
                                </div>
                            )}
                        {workflowState.filters &&
                            Object.keys(workflowState.filters).length > 0 && (
                                <div className="flex items-center space-x-2">
                                    <CheckCircle className="w-3 h-3 text-green-500" />
                                    <span>Filters Applied</span>
                                </div>
                            )}
                        {workflowState.hitl_step && (
                            <div className="flex items-center space-x-2">
                                <AlertCircle className="w-3 h-3 text-amber-500" />
                                <span>HITL Step {workflowState.hitl_step}</span>
                            </div>
                        )}
                        {workflowState.themes &&
                            workflowState.themes.length > 0 && (
                                <div className="flex items-center space-x-2">
                                    <CheckCircle className="w-3 h-3 text-green-500" />
                                    <span>
                                        Themes ({workflowState.themes.length})
                                    </span>
                                </div>
                            )}
                        {workflowState.data_requirements &&
                            workflowState.data_requirements.length > 0 && (
                                <div className="flex items-center space-x-2">
                                    <CheckCircle className="w-3 h-3 text-green-500" />
                                    <span>Data Requirements</span>
                                </div>
                            )}
                    </div>
                </div>
            )}

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {steps.length === 0 ? (
                    <div className="flex items-center justify-center h-32">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
                    </div>
                ) : (
                    steps.map((step) => (
                        <ReasoningStep
                            key={step.id}
                            step={step}
                            isSelected={selectedStepId === step.id}
                            onClick={() => handleStepClick(step.id)}
                        />
                    ))
                )}

                {!isThinking &&
                    currentStep > steps.length &&
                    steps.length > 0 && (
                        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                            <p className="text-green-700 text-sm font-medium">
                                ✓ Reasoning complete! Ready to generate
                                response.
                            </p>
                        </div>
                    )}
            </div>
        </div>
    );
};

export default ReasoningPanel;
