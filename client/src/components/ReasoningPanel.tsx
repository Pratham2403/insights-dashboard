import React from 'react';
import { Brain, Database, AlertCircle, CheckCircle, Clock, ArrowRight, Cpu, Settings, Activity } from 'lucide-react';
import { useChatContext } from '../context/ChatContext';

interface ReasoningPanelProps {
  isThinking: boolean;
  onComplete: () => void;
  configId?: string;
}

const ReasoningPanel: React.FC<ReasoningPanelProps> = ({ isThinking }) => {
  const { dashboardState } = useChatContext();

  const renderReasoningField = (key: string, value: any) => {
    if (value === null || value === undefined) return null;

    // Only show reasoning/technical fields
    const reasoningFields = [
      'current_stage',
      'workflow_status', 
      'workflow_started',
      'hitl_step',
      'next_node',
      'reason',
      'thread_id',
      'errors',
      'refined_query',
      'keywords',
      'filters',
      'boolean_query',
      'themes',
      'defaults_applied'
    ];

    if (!reasoningFields.includes(key)) return null;

    const getIcon = (key: string) => {
      switch (key) {
        case 'current_stage':
          return <Activity className="w-4 h-4 text-blue-600" />;
        case 'workflow_status':
          return <Settings className="w-4 h-4 text-green-600" />;
        case 'workflow_started':
          return <Clock className="w-4 h-4 text-purple-600" />;
        case 'thread_id':
          return <Database className="w-4 h-4 text-indigo-600" />;
        case 'errors':
          return <AlertCircle className="w-4 h-4 text-red-600" />;
        case 'next_node':
          return <ArrowRight className="w-4 h-4 text-orange-600" />;
        case 'hitl_step':
          return <Cpu className="w-4 h-4 text-teal-600" />;
        case 'refined_query':
        case 'boolean_query':
          return <Database className="w-4 h-4 text-blue-600" />;
        case 'keywords':
        case 'themes':
          return <CheckCircle className="w-4 h-4 text-green-600" />;
        case 'filters':
        case 'defaults_applied':
          return <Settings className="w-4 h-4 text-gray-600" />;
        default:
          return <CheckCircle className="w-4 h-4 text-gray-600" />;
      }
    };

    const formatKey = (key: string) => {
      return key.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');
    };

    const formatValue = (value: any) => {
      if (Array.isArray(value)) {
        if (value.length === 0) return <span className="text-gray-400 italic">Empty array</span>;
        return (
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {value.map((item, index) => (
              <div key={index} className="bg-gray-100 px-2 py-1 rounded text-xs">
                {typeof item === 'object' ? JSON.stringify(item, null, 2) : String(item)}
              </div>
            ))}
          </div>
        );
      }
      
      if (typeof value === 'object') {
        return (
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-32">
            {JSON.stringify(value, null, 2)}
          </pre>
        );
      }
      
      if (typeof value === 'boolean') {
        return (
          <span className={`px-2 py-1 rounded text-xs ${
            value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {value ? 'True' : 'False'}
          </span>
        );
      }
      
      if (key === 'workflow_started' && typeof value === 'string') {
        try {
          const date = new Date(value);
          return <span className="text-gray-900 text-xs">{date.toLocaleString()}</span>;
        } catch {
          return <span className="text-gray-900">{String(value)}</span>;
        }
      }
      
      return <span className="text-gray-900">{String(value)}</span>;
    };

    const getPriorityLevel = (key: string) => {
      const highPriority = ['current_stage', 'workflow_status', 'next_node', 'errors'];
      const mediumPriority = ['hitl_step', 'reason', 'thread_id'];
      
      if (highPriority.includes(key)) return 'high';
      if (mediumPriority.includes(key)) return 'medium';
      return 'low';
    };

    const priority = getPriorityLevel(key);
    const borderColor = priority === 'high' ? 'border-red-200' : 
                       priority === 'medium' ? 'border-yellow-200' : 'border-gray-200';
    const bgColor = priority === 'high' ? 'hover:bg-red-50' : 
                   priority === 'medium' ? 'hover:bg-yellow-50' : 'hover:bg-gray-50';

    return (
      <div key={key} className={`border ${borderColor} rounded-lg p-3 ${bgColor} transition-colors`}>
        <div className="flex items-center space-x-2 mb-2">
          {getIcon(key)}
          <h4 className="font-medium text-gray-900 text-sm">{formatKey(key)}</h4>
          {priority === 'high' && (
            <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">Critical</span>
          )}
        </div>
        <div className="text-sm">
          {formatValue(value)}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white h-full flex flex-col">
      <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900">
              System State Monitor
            </h2>
            <p className="text-sm text-gray-600">
              Real-time workflow and reasoning state
            </p>
          </div>
          {isThinking && (
            <div className="flex items-center space-x-2 text-purple-600">
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium">Processing...</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {dashboardState ? (
          <div className="space-y-4">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                <Cpu className="w-4 h-4 mr-2" />
                Workflow & Reasoning State
              </h3>
            </div>
            
            {Object.entries(dashboardState)
              .sort(([keyA], [keyB]) => {
                // Sort by priority: high -> medium -> low
                const getPriority = (key: string) => {
                  const highPriority = ['current_stage', 'workflow_status', 'next_node', 'errors'];
                  const mediumPriority = ['hitl_step', 'reason', 'thread_id'];
                  if (highPriority.includes(key)) return 0;
                  if (mediumPriority.includes(key)) return 1;
                  return 2;
                };
                return getPriority(keyA) - getPriority(keyB);
              })
              .map(([key, value]) => renderReasoningField(key, value))
              .filter(Boolean)
            }
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Brain className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                No Active State
              </h3>
              <p className="text-gray-500 max-w-xs">
                Start a conversation to see the AI reasoning process and system state in real-time.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReasoningPanel;