import React from 'react';
import { Users, Store, DollarSign, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useDashboardStats } from '../features/dashboard/hooks/useDashboardStats';
import { StatCard } from '../features/dashboard/components/StatCard';
import { DashboardCharts } from '../features/dashboard/components/DashboardCharts';

export const DashboardPage: React.FC = () => {
  const { data: stats, isLoading, isError } = useDashboardStats();

  if (isError) {
    return (
      <div className="p-8 text-center text-red-600 bg-red-50 rounded-lg border border-red-100 m-6">
        Failed to load dashboard statistics. Please check your connection or try again later.
      </div>
    );
  }

  // Helper to format currency
  const formatCurrency = (amount: number = 0) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard 
          title="Total Users" 
          value={stats?.total_users ?? 0} 
          icon={Users} 
          isLoading={isLoading} 
        />
        <StatCard 
          title="Total Merchants" 
          value={stats?.total_merchants ?? 0} 
          icon={Store} 
          isLoading={isLoading} 
        />
        <StatCard 
          title="Total Revenue" 
          value={formatCurrency(stats?.total_revenue)} 
          icon={DollarSign} 
          isLoading={isLoading} 
          trend={{ value: 12.5, isPositive: true }}
        />
        <StatCard 
          title="Successful Verifications" 
          value={stats?.successful_verifications ?? 0} 
          icon={CheckCircle} 
          isLoading={isLoading} 
        />
        <StatCard 
          title="Failed Verifications" 
          value={stats?.failed_verifications ?? 0} 
          icon={XCircle} 
          isLoading={isLoading} 
        />
        <StatCard 
          title="Pending Callbacks" 
          value={stats?.pending_callbacks ?? 0} 
          icon={Clock} 
          isLoading={isLoading} 
        />
      </div>

      {/* Charts Panel */}
      <DashboardCharts />

      {/* Recent Activity Panel Shell */}
      <div className="mt-6 bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="flex items-center justify-center h-32 text-gray-400 bg-gray-50 rounded-lg border border-dashed border-gray-200">
          Activity log stream will be implemented in subsequent phases.
        </div>
      </div>
    </div>
  );
};