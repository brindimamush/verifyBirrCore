import { useQuery } from '@tanstack/react-query';
import { fetchAdminStats } from '../../../services/api/admin';

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: fetchAdminStats,
    refetchInterval: 30000, // Refresh every 30 seconds for live feel
  });
};