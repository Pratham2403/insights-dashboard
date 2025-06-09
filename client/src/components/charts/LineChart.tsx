import React from 'react';

interface DataPoint {
  date: string;
  positive: number;
  negative: number;
}

interface LineChartProps {
  data: DataPoint[];
  title: string;
}

const LineChart: React.FC<LineChartProps> = ({ data, title }) => {
  const maxValue = Math.max(...data.flatMap(d => [d.positive, d.negative]));
  const chartHeight = 200;
  const chartWidth = 400;
  const padding = 40;

  const getPath = (values: number[], color: string) => {
    const points = values.map((value, index) => {
      const x = padding + (index * (chartWidth - 2 * padding)) / (values.length - 1);
      const y = chartHeight - padding - ((value / maxValue) * (chartHeight - 2 * padding));
      return `${x},${y}`;
    }).join(' L');
    
    return `M${points}`;
  };

  const positiveValues = data.map(d => d.positive);
  const negativeValues = data.map(d => d.negative);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div className="relative">
        <svg width="100%" height={chartHeight} viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="overflow-visible">
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={ratio}
              x1={padding}
              y1={padding + ratio * (chartHeight - 2 * padding)}
              x2={chartWidth - padding}
              y2={padding + ratio * (chartHeight - 2 * padding)}
              stroke="#f3f4f6"
              strokeWidth="1"
            />
          ))}
          
          {/* Positive line */}
          <path
            d={getPath(positiveValues, '#10b981')}
            fill="none"
            stroke="#10b981"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* Negative line */}
          <path
            d={getPath(negativeValues, '#ef4444')}
            fill="none"
            stroke="#ef4444"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* Data points */}
          {positiveValues.map((value, index) => {
            const x = padding + (index * (chartWidth - 2 * padding)) / (positiveValues.length - 1);
            const y = chartHeight - padding - ((value / maxValue) * (chartHeight - 2 * padding));
            return (
              <circle
                key={`positive-${index}`}
                cx={x}
                cy={y}
                r="4"
                fill="#10b981"
                className="hover:r-6 transition-all duration-200"
              />
            );
          })}
          
          {negativeValues.map((value, index) => {
            const x = padding + (index * (chartWidth - 2 * padding)) / (negativeValues.length - 1);
            const y = chartHeight - padding - ((value / maxValue) * (chartHeight - 2 * padding));
            return (
              <circle
                key={`negative-${index}`}
                cx={x}
                cy={y}
                r="4"
                fill="#ef4444"
                className="hover:r-6 transition-all duration-200"
              />
            );
          })}
        </svg>
        
        {/* Legend */}
        <div className="flex items-center justify-center space-x-6 mt-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Positive</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Negative</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LineChart;