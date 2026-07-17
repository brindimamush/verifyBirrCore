import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  isLoading?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, trend, isLoading }) => {
  if (isLoading) {
    return (
      <div className="p-6 bg-white rounded-xl border border-gray-100 shadow-sm animate-pulse">
        <div className="h-10 w-10 bg-gray-200 rounded-lg mb-4"></div>
        <div className="h-4 w-24 bg-gray-200 rounded mb-2"></div>
        <div className="h-8 w-32 bg-gray-200 rounded"></div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
          <Icon size={24} />
        </div>
        {trend && (
          <span className={`text-sm font-medium px-2 py-1 rounded-full ${trend.isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {trend.isPositive ? '+' : '-'}{Math.abs(trend.value)}%
          </span>
        )}
      </div>
      <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
    </div>
  );
};