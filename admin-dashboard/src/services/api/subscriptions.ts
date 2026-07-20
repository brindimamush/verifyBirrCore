import { apiClient } from './client';
import type {
  SubscriptionPlan,
  SubscriptionPlanCreate,
  SubscriptionPlanUpdate,
  Subscription,
  SubscriptionInvoice,
  SubscriptionAnalytics,
  PaginatedSubscriptions
} from '@/types/subscription';

// ============ Plan Management ============

export const fetchSubscriptionPlans = async (includeInactive = false): Promise<SubscriptionPlan[]> => {
  const { data } = await apiClient.get<SubscriptionPlan[]>('/v1/admin/subscription-plans', {
    params: { include_inactive: includeInactive }
  });
  return data;
};

export const fetchSubscriptionPlan = async (id: number): Promise<SubscriptionPlan> => {
  const { data } = await apiClient.get<SubscriptionPlan>(`/v1/admin/subscription-plans/${id}`);
  return data;
};

export const createSubscriptionPlan = async (
  plan: SubscriptionPlanCreate,
  idempotencyKey?: string
): Promise<SubscriptionPlan> => {
  const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {};
  const { data } = await apiClient.post<SubscriptionPlan>('/v1/admin/subscription-plans', plan, { headers });
  return data;
};

export const updateSubscriptionPlan = async (id: number, plan: SubscriptionPlanUpdate): Promise<SubscriptionPlan> => {
  const { data } = await apiClient.patch<SubscriptionPlan>(`/v1/admin/subscription-plans/${id}`, plan);
  return data;
};

export const toggleSubscriptionPlanStatus = async (id: number, isActive: boolean): Promise<SubscriptionPlan> => {
  const { data } = await apiClient.patch<SubscriptionPlan>(
    `/v1/admin/subscription-plans/${id}/toggle-status`,
    null,
    { params: { is_active: isActive } }
  );
  return data;
};

export const deleteSubscriptionPlan = async (id: number): Promise<void> => {
  await apiClient.delete(`/v1/admin/subscription-plans/${id}`);
};

// ============ Subscription Management ============

export const fetchAllSubscriptions = async (
  params: {
    status?: string;
    plan_id?: number;
    merchant_id?: number;
    limit?: number;
    offset?: number;
  }
): Promise<Subscription[]> => {
  const { data } = await apiClient.get<Subscription[]>('/v1/admin/subscriptions', { params });
  return data;
};

export const fetchSubscription = async (id: number): Promise<Subscription> => {
  const { data } = await apiClient.get<Subscription>(`/v1/admin/subscriptions/${id}`);
  return data;
};

export const updateSubscriptionStatus = async (id: number, status: string): Promise<Subscription> => {
  const { data } = await apiClient.patch<Subscription>(
    `/v1/admin/subscriptions/${id}/status`,
    null,
    { params: { status } }
  );
  return data;
};

export const renewSubscription = async (id: number): Promise<Subscription> => {
  const { data } = await apiClient.post<Subscription>(`/v1/admin/subscriptions/${id}/renew`);
  return data;
};

// ============ Subscription Invoices ============

export const fetchSubscriptionInvoices = async (
  params: {
    subscription_id?: number;
    is_processed?: boolean;
    limit?: number;
    offset?: number;
  }
): Promise<SubscriptionInvoice[]> => {
  const { data } = await apiClient.get<SubscriptionInvoice[]>('/v1/admin/subscription-invoices', { params });
  return data;
};

// ============ Analytics ============

export const fetchSubscriptionAnalytics = async (
  startDate?: string,
  endDate?: string
): Promise<SubscriptionAnalytics> => {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  const { data } = await apiClient.get<SubscriptionAnalytics>(`/v1/admin/subscription-analytics?${params.toString()}`);
  return data;
};