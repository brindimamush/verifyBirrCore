import axios from 'axios';
import type { PlatformStats } from '../../types/admin';

// Assuming you have an axios instance configured with interceptors in Phase 2
import { apiClient } from './client'; 

export const fetchAdminStats = async (): Promise<PlatformStats> => {
  const { data } = await apiClient.get<PlatformStats>('/v1/admin/stats');
  return data;
};