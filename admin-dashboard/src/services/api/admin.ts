

import type { PlatformStats, Merchant, SystemUser, PaginatedUsers } from '../../types/admin';

// Assuming you have an axios instance configured with interceptors in Phase 2
import { apiClient } from './client'; 

export const fetchAdminStats = async (): Promise<PlatformStats> => {
  const { data } = await apiClient.get<PlatformStats>('/v1/admin/stats');
  return data;
};

export const fetchMerchants = async (limit = 50, offset = 0): Promise<Merchant[]> => {
  const { data } = await apiClient.get<Merchant[]>(`/v1/admin/merchants?limit=${limit}&offset=${offset}`);
  return data;
};

export const toggleMerchantStatus = async (merchantId: number, isActive: boolean): Promise<Merchant> => {
  const { data } = await apiClient.patch<Merchant>(`/v1/admin/merchants/${merchantId}/status?is_active=${isActive}`);
  return data;
};

export const fetchUsers = async (limit = 50, offset = 0, search = ''): Promise<PaginatedUsers> => {
  // We pass search as a query parameter if the backend supports filtering by email/ID
  const { data } = await apiClient.get<PaginatedUsers>(`/v1/admin/users`, {
    params: { limit, offset, search }
  });
  return data;
};

export const toggleUserStatus = async (userId: number, isActive: boolean): Promise<SystemUser> => {
  const { data } = await apiClient.patch<SystemUser>(`/v1/admin/users/${userId}/status`, null, {
    params: { is_active: isActive }
  });
  return data;
};