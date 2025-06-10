import React, { useState, useEffect } from 'react';
import { DashboardData } from '../types';
import MetricCard from './charts/MetricCard';
import LineChart from './charts/LineChart';
import BarChart from './charts/BarChart';
import DonutChart from './charts/DonutChart';
import CompetitorChart from './charts/CompetitorChart';

interface DashboardRendererProps {
  dataFile: string;
}

const DashboardRenderer: React.FC<DashboardRendererProps> = ({ dataFile }) => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Dynamic import based on dataFile
        let data;
        switch (dataFile) {
          case 'brandHealthData.json':
            data = await import('../data/brandHealthData.json');
            break;
          case 'customerExperienceData.json':
            data = await import('../data/customerExperienceData.json');
            break;
          case 'marketIntelligenceData.json':
            data = await import('../data/marketIntelligenceData.json');
            break;
          default:
            data = await import('../data/brandHealthData.json');
        }
        
        setDashboardData(data.default);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error('Error loading dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [dataFile]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-2">{error || 'No data available'}</p>
          <p className="text-gray-500 text-sm">Please try refreshing the page</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Mentions"
          value={dashboardData.brandMetrics.mentions.current}
          change={dashboardData.brandMetrics.mentions.change}
          trend={dashboardData.brandMetrics.mentions.trend}
          icon="mentions"
          color="blue"
        />
        <MetricCard
          title="Reach"
          value={dashboardData.brandMetrics.reach.current}
          change={dashboardData.brandMetrics.reach.change}
          trend={dashboardData.brandMetrics.reach.trend}
          icon="reach"
          color="green"
        />
        <MetricCard
          title="Engagement"
          value={dashboardData.brandMetrics.engagement.current}
          change={dashboardData.brandMetrics.engagement.change}
          trend={dashboardData.brandMetrics.engagement.trend}
          icon="engagement"
          color="purple"
        />
        <MetricCard
          title="Positive Sentiment"
          value={`${dashboardData.brandMetrics.sentiment.positive}%`}
          change="+12%"
          trend="up"
          icon="sentiment"
          color="orange"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LineChart
          data={dashboardData.sentimentTrend}
          title="Sentiment Trend Over Time"
        />
        <BarChart
          data={dashboardData.topicAnalysis}
          title="Key Topics Discussed"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DonutChart
          data={dashboardData.geographicData}
          title="Geographic Distribution"
        />
        <CompetitorChart
          data={dashboardData.competitorComparison}
          title="Competitor Analysis"
        />
      </div>

      {/* Additional sections based on dashboard type */}
      {dashboardData.type === 'customer-analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Pre-Purchase Stage</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Product Discovery</span>
                <span className="text-sm font-medium text-green-600">+15%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Price Comparison</span>
                <span className="text-sm font-medium text-yellow-600">-5%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Reviews Reading</span>
                <span className="text-sm font-medium text-green-600">+22%</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Purchase Stage</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Checkout Process</span>
                <span className="text-sm font-medium text-green-600">+8%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Payment Options</span>
                <span className="text-sm font-medium text-green-600">+12%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Order Confirmation</span>
                <span className="text-sm font-medium text-green-600">+18%</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Post-Purchase Stage</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Delivery Experience</span>
                <span className="text-sm font-medium text-green-600">+25%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Product Quality</span>
                <span className="text-sm font-medium text-green-600">+30%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Customer Support</span>
                <span className="text-sm font-medium text-yellow-600">+5%</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardRenderer;