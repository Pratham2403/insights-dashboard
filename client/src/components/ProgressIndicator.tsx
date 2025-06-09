import React from 'react';
import { Check, Circle } from 'lucide-react';

interface ProgressIndicatorProps {
  currentStep: number;
  totalSteps: number;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ currentStep, totalSteps }) => {
  return (
    <div className="flex items-center space-x-2">
      {Array.from({ length: totalSteps }, (_, index) => {
        const stepNumber = index + 1;
        const isCompleted = stepNumber < currentStep;
        const isActive = stepNumber === currentStep;
        
        return (
          <div key={stepNumber} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                isCompleted
                  ? 'bg-green-500 border-green-500 text-white'
                  : isActive
                  ? 'border-purple-500 bg-purple-500 text-white'
                  : 'border-gray-300 text-gray-400'
              }`}
            >
              {isCompleted ? (
                <Check size={16} />
              ) : (
                <Circle size={12} fill={isActive ? 'currentColor' : 'none'} />
              )}
            </div>
            {stepNumber < totalSteps && (
              <div
                className={`w-8 h-0.5 mx-1 transition-all duration-300 ${
                  isCompleted ? 'bg-green-500' : 'bg-gray-300'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ProgressIndicator;