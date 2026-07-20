import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, Clock, Users } from 'lucide-react';
import type { SubscriptionAnalytics } from '@/types/subscription';

interface RevenueCardProps {
  analytics: SubscriptionAnalytics | undefined;
  isLoading?: boolean;
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(amount);
};

export const RevenueCard: React.FC<RevenueCardProps> = ({ analytics, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm animate-pulse dark:border-slate-800 dark:bg-slate-900">
            <div className="h-4 w-24 bg-slate-200 rounded dark:bg-slate-700 mb-3"></div>
            <div className="h-8 w-32 bg-slate-200 rounded dark:bg-slate-700"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-500 dark:border-slate-800 dark:bg-slate-900">
        No analytics data available for the selected period.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Total Revenue</span>
            <div className="rounded-lg bg-green-50 p-2 text-green-600 dark:bg-green-900/30">
              <DollarSign className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {formatCurrency(analytics.total_revenue)}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {analytics.conversion_rate}% conversion rate
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Active Subscriptions</span>
            <div className="rounded-lg bg-blue-50 p-2 text-blue-600 dark:bg-blue-900/30">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {analytics.total_active}
          </p>
          <div className="mt-1 flex items-center gap-1 text-xs">
            <span className="text-slate-500">+{analytics.new_this_period} new this period</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Pending</span>
            <div className="rounded-lg bg-amber-50 p-2 text-amber-600 dark:bg-amber-900/30">
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {analytics.total_pending}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Awaiting payment verification
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Expired / Cancelled</span>
            <div className="rounded-lg bg-red-50 p-2 text-red-600 dark:bg-red-900/30">
              <TrendingDown className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {analytics.total_expired + analytics.total_cancelled}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {analytics.total_expired} expired · {analytics.total_cancelled} cancelled
          </p>
        </div>
      </div>

      {/* Revenue by Plan */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Revenue by Plan
        </h3>
        {analytics.revenue_by_plan.length === 0 ? (
          <p className="text-sm text-slate-500">No revenue data available for the selected period.</p>
        ) : (
          <div className="space-y-3">
            {analytics.revenue_by_plan.map((plan, index) => {
              const maxRevenue = Math.max(...analytics.revenue_by_plan.map(p => p.total_revenue));
              const percentage = maxRevenue > 0 ? (plan.total_revenue / maxRevenue) * 100 : 0;
              
              return (
                <div key={index}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700 dark:text-slate-300">
                      {plan.plan_name}
                      <span className="ml-2 text-xs text-slate-500 capitalize">({plan.tier})</span>
                    </span>
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {formatCurrency(plan.total_revenue)}
                    </span>
                  </div>
                  <div className="mt-1 h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800">
                    <div
                      className="h-2 rounded-full bg-blue-600 transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};