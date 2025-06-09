import React from 'react';
import { ReasoningStep as ReasoningStepType } from '../types';
import { useTypingAnimation } from '../hooks/useTypingAnimation';

interface ReasoningStepProps {
  step: ReasoningStepType;
  isSelected: boolean;
  onClick: () => void;
}

const ReasoningStep: React.FC<ReasoningStepProps> = ({ step, isSelected, onClick }) => {
  const { displayText, isTyping } = useTypingAnimation(
    isSelected ? step.content : '',
    30
  );

  return (
    <div className="space-y-3">
      {/* Step Heading */}
      <div
        className={`cursor-pointer p-4 rounded-lg border transition-all duration-300 hover:shadow-md ${
          isSelected
            ? 'border-purple-300 bg-purple-50 shadow-sm'
            : step.isCompleted
            ? 'border-green-300 bg-green-50'
            : step.isActive
            ? 'border-yellow-300 bg-yellow-50'
            : 'border-gray-200 bg-gray-50 hover:bg-gray-100'
        }`}
        onClick={onClick}
      >
        <div className="flex items-center space-x-3">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
              step.isCompleted
                ? 'bg-green-500 text-white'
                : step.isActive
                ? 'bg-yellow-500 text-yellow-900'
                : 'bg-gray-300 text-gray-600'
            }`}
          >
            {step.id}
          </div>
          <h3 className={`font-medium ${
            isSelected ? 'text-purple-900' : 
            step.isCompleted ? 'text-green-900' : 
            step.isActive ? 'text-yellow-900' : 'text-gray-700'
          }`}>
            {step.heading}
          </h3>
        </div>
      </div>

      {/* Step Content */}
      {isSelected && (
        <div className="p-4 rounded-lg border border-purple-200 bg-purple-50/50">
          <div className="text-gray-700">
            <p>{displayText}</p>
            {isTyping && (
              <span className="inline-block w-2 h-5 bg-purple-500 ml-1 animate-pulse rounded" />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReasoningStep;