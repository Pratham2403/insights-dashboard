import React from 'react';

interface DataPoint {
  topic: string;
  mentions: number;
  sentiment: number;
}

interface BarChartProps {
  data: DataPoint[];
  title: string;
}

const BarChart: React.FC<BarChartProps> = ({ data, title }) => {
  const maxMentions = Math.max(...data.map(d => d.mentions));

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.5) return '#10b981'; // green
    if (sentiment > 0) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div className="space-y-4">
        {data.map((item, index) => (
          <div key={index} className="flex items-center space-x-4">
            <div className="w-24 text-sm text-gray-600 font-medium truncate">
              {item.topic}
            </div>
            
            <div className="flex-1 relative">
              <div className="bg-gray-200 rounded-full h-6 relative overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${(item.mentions / maxMentions) * 100}%`,
                    backgroundColor: getSentimentColor(item.sentiment),
                  }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-medium text-gray-700">
                    {item.mentions}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="w-16 text-right">
              <span
                className="text-sm font-medium"
                style={{ color: getSentimentColor(item.sentiment) }}
              >
                {item.sentiment > 0 ? '+' : ''}{(item.sentiment * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BarChart;