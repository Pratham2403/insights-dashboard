import React, { useState, useEffect } from 'react';
import { Brain, Zap } from 'lucide-react';
import ReasoningStep from './ReasoningStep';
import ProgressIndicator from './ProgressIndicator';
import { sampleReasoningSteps } from '../data/reasoningSteps';
import { ReasoningStep as ReasoningStepType } from '../types';

interface ReasoningPanelProps {
  isThinking: boolean;
  onComplete: () => void;
}

const ReasoningPanel: React.FC<ReasoningPanelProps> = ({ isThinking, onComplete }) => {
  const [steps, setSteps] = useState<ReasoningStepType[]>(sampleReasoningSteps);
  const [selectedStepId, setSelectedStepId] = useState<number | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (!isThinking) return;

    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        const nextStep = prev + 1;
        if (nextStep > steps.length) {
          clearInterval(timer);
          onComplete();
          return prev;
        }

        // Update steps state
        setSteps((prevSteps) =>
          prevSteps.map((step, index) => ({
            ...step,
            isCompleted: index < nextStep - 1,
            isActive: index === nextStep - 1,
          }))
        );

        return nextStep;
      });
    }, 2000);

    return () => clearInterval(timer);
  }, [isThinking, steps.length, onComplete]);

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
          <h2 className="text-lg font-semibold text-gray-900">AI Reasoning Process</h2>
          {isThinking && (
            <div className="flex items-center space-x-2 text-purple-600">
              <Zap className="w-4 h-4 animate-pulse" />
              <span className="text-sm font-medium">Thinking...</span>
            </div>
          )}
        </div>

        <ProgressIndicator currentStep={currentStep} totalSteps={steps.length} />
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {steps.map((step) => (
          <ReasoningStep
            key={step.id}
            step={step}
            isSelected={selectedStepId === step.id}
            onClick={() => handleStepClick(step.id)}
          />
        ))}

        {!isThinking && currentStep > steps.length && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-700 text-sm font-medium">
              ✓ Reasoning complete! Ready to generate response.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReasoningPanel;