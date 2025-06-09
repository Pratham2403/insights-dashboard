import React from 'react';
import { TrendingUp, TrendingDown, Eye, MessageCircle, Users, Heart } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change: string;
  trend: 'up' | 'down';
  icon: 'mentions' | 'reach' | 'engagement' | 'sentiment';
  color?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, trend, icon, color = 'blue' }) => {
  const getIcon = () => {
    const iconClass = "w-6 h-6";
    switch (icon) {
      case 'mentions':
        return <MessageCircle className={iconClass} />;
      case 'reach':
        return <Eye className={iconClass} />;
      case 'engagement':
        return <Heart className={iconClass} />;
      case 'sentiment':
        return <Users className={iconClass} />;
      default:
        return <MessageCircle className={iconClass} />;
    }
  };

  const getColorClasses = () => {
    const colors = {
      blue: 'from-blue-500 to-blue-600',
      green: 'from-green-500 to-green-600',
      purple: 'from-purple-500 to-purple-600',
      orange: 'from-orange-500 to-orange-600',
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg bg-gradient-to-r ${getColorClasses()} text-white`}>
          {getIcon()}
        </div>
        <div className={`flex items-center space-x-1 text-sm font-medium ${
          trend === 'up' ? 'text-green-600' : 'text-red-600'
        }`}>
          {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          <span>{change}</span>
        </div>
      </div>
      
      <div>
        <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
        <p className="text-gray-600 text-sm font-medium">{title}</p>
      </div>
    </div>
  );
};

export default MetricCard;