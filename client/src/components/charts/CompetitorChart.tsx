import React from 'react';

interface CompetitorData {
  brand: string;
  mentions: number;
  sentiment: number;
  share: number;
}

interface CompetitorChartProps {
  data: CompetitorData[];
  title: string;
}

const CompetitorChart: React.FC<CompetitorChartProps> = ({ data, title }) => {
  const maxMentions = Math.max(...data.map(d => d.mentions));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div className="space-y-4">
        {data.map((competitor, index) => (
          <div key={index} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900">{competitor.brand}</span>
              <div className="flex items-center space-x-4 text-sm">
                <span className="text-gray-600">{competitor.mentions} mentions</span>
                <span className={`font-medium ${
                  competitor.sentiment > 0.6 ? 'text-green-600' : 
                  competitor.sentiment > 0.3 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {(competitor.sentiment * 100).toFixed(0)}% sentiment
                </span>
              </div>
            </div>
            
            <div className="relative">
              <div className="bg-gray-200 rounded-full h-3">
                <div
                  className={`h-full rounded-full transition-all duration-500 ease-out ${
                    index === 0 ? 'bg-gradient-to-r from-purple-500 to-blue-500' : 'bg-gray-400'
                  }`}
                  style={{ width: `${competitor.share}%` }}
                />
              </div>
              <div className="absolute right-0 top-0 -mt-6">
                <span className="text-xs text-gray-600">{competitor.share}% market share</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CompetitorChart;