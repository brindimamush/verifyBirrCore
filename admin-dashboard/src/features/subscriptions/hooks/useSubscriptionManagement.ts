import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  fetchSubscriptionPlans,
  fetchSubscriptionPlan,
  createSubscriptionPlan,
  updateSubscriptionPlan,
  toggleSubscriptionPlanStatus,
  deleteSubscriptionPlan,
  fetchAllSubscriptions,
  fetchSubscription,
  updateSubscriptionStatus,
  renewSubscription,
  fetchSubscriptionInvoices,
  fetchSubscriptionAnalytics
} from '@/services/api/subscriptions';
import type { SubscriptionPlanCreate, SubscriptionPlanUpdate } from '@/types/subscription';

// ============ Plans ============

export const useSubscriptionPlans = (includeInactive = false) => {
  return useQuery({
    queryKey: ['subscription-plans', includeInactive],
    queryFn: () => fetchSubscriptionPlans(includeInactive),
    staleTime: 5 * 60 * 1000,
  });
};

export const useSubscriptionPlan = (id: number) => {
  return useQuery({
    queryKey: ['subscription-plan', id],
    queryFn: () => fetchSubscriptionPlan(id),
    enabled: !!id,
  });
};

export const useCreateSubscriptionPlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ plan, idempotencyKey }: { plan: SubscriptionPlanCreate; idempotencyKey?: string }) =>
      createSubscriptionPlan(plan, idempotencyKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription-plans'] });
      toast.success('Subscription plan created successfully');
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail || 'Failed to create subscription plan';
      toast.error('Creation Failed', { description: detail });
    },
  });
};

export const useUpdateSubscriptionPlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, plan }: { id: number; plan: SubscriptionPlanUpdate }) =>
      updateSubscriptionPlan(id, plan),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['subscription-plans'] });
      queryClient.invalidateQueries({ queryKey: ['subscription-plan', data.id] });
      toast.success(`Plan "${data.name}" updated successfully`);
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail || 'Failed to update subscription plan';
      toast.error('Update Failed', { description: detail });
    },
  });
};

export const useToggleSubscriptionPlanStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) =>
      toggleSubscriptionPlanStatus(id, isActive),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['subscription-plans'] });
      queryClient.invalidateQueries({ queryKey: ['subscription-plan', data.id] });
      toast.success(`Plan "${data.name}" ${data.is_active ? 'activated' : 'deactivated'}`);
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail || 'Failed to change plan status';
      toast.error('Status Update Failed', { description: detail });
    },
  });
};

export const useDeleteSubscriptionPlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: deleteSubscriptionPlan,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['subscription-plans'] });
      toast.success('Plan deleted successfully');
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail || 'Failed to delete plan';
      toast.error('Deletion Failed', { description: detail });
    },
  });
};

// ============ Subscriptions ============

export const useAllSubscriptions = (filters: {
  status?: string;
  plan_id?: number;
  merchant_id?: number;
  limit?: number;
  offset?: number;
}) => {
  return useQuery({
    queryKey: ['subscriptions', filters],
    queryFn: () => fetchAllSubscriptions(filters),
    staleTime: 30 * 1000,
  });
};

export const useSubscription = (id: number) => {
  return useQuery({
    queryKey: ['subscription', id],
    queryFn: () => fetchSubscription(id),
    enabled: !!id,
  });
};

export const useUpdateSubscriptionStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateSubscriptionStatus(id, status),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      queryClient.invalidateQueries({ queryKey: ['subscription', data.id] });
      toast.success(`Subscription status updated to "${data.status}"`);
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail || 'Failed to update subscription status';
      toast.error('Status Update Failed', { description: detail });
    },
  });
};

export const useRenewSubscription = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => renewSubscription(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      queryClient.invalidateQueries({ queryKey: ['subscription', data.id] });
      toast.success('Subscription renewed successfully');
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail || 'Failed to renew subscription';
      toast.error('Renewal Failed', { description: detail });
    },
  });
};

// ============ Analytics ============

export const useSubscriptionAnalytics = (startDate?: string, endDate?: string) => {
  return useQuery({
    queryKey: ['subscription-analytics', startDate, endDate],
    queryFn: () => fetchSubscriptionAnalytics(startDate, endDate),
    staleTime: 2 * 60 * 1000,
    refetchInterval: 60 * 1000, // Refresh every minute
  });
};