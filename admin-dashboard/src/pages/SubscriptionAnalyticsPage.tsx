import React, { useState } from 'react';
import { Calendar, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { RevenueCard } from '@/features/subscriptions/components/RevenueCard';
import { useSubscriptionAnalytics } from '@/features/subscriptions/hooks/useSubscriptionManagement';

export const SubscriptionAnalyticsPage: React.FC = () => {
  const [dateRange, setDateRange] = useState({
    startDate: format(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"),
    endDate: format(new Date(), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"),
  });

  const { data, isLoading, isError, refetch } = useSubscriptionAnalytics(
    dateRange.startDate,
    dateRange.endDate
  );

  const handleDateChange = (field: 'startDate' | 'endDate', value: string) => {
    setDateRange(prev => ({ ...prev, [field]: value }));
    // Refetch with new date range
    setTimeout(() => refetch(), 100);
  };

  if (isError) {
    return (
      <div className="p-8 text-center text-red-600 bg-red-50 rounded-lg border border-red-100 m-6">
        Failed to load analytics data. Please check your connection or try again later.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Subscription Analytics
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Track subscription revenue and performance metrics.
          </p>
        </div>
        
        {/* Date Range Picker */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-400" />
            <input
              type="date"
              value={dateRange.startDate.split('T')[0]}
              onChange={(e) => handleDateChange('startDate', new Date(e.target.value).toISOString())}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
            />
          </div>
          <span className="text-slate-400">→</span>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={dateRange.endDate.split('T')[0]}
              onChange={(e) => handleDateChange('endDate', new Date(e.target.value).toISOString())}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Analytics Cards */}
      <RevenueCard analytics={data} isLoading={isLoading} />
    </div>
  );
};