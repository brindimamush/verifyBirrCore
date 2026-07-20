export type PlanTier = 'free' | 'starter' | 'professional' | 'enterprise';

export interface SubscriptionPlan {
  id: number;
  tier: PlanTier;
  name: string;
  price: number;
  duration_days: number;
  is_active: boolean;
  created_at: string;
}

export interface SubscriptionPlanCreate {
  tier: PlanTier;
  name: string;
  price: number;
  duration_days: number;
  is_active?: boolean;
}

export interface SubscriptionPlanUpdate {
  tier?: PlanTier;
  name?: string;
  price?: number;
  duration_days?: number;
}

export interface Subscription {
  id: number;
  merchant_id: number;
  plan_id: number;
  status: 'pending' | 'active' | 'expired' | 'cancelled';
  current_period_start: string | null;
  current_period_end: string | null;
  auto_renew: boolean;
  created_at: string;
  updated_at: string;
  merchant?: Merchant;
  plan?: SubscriptionPlan;
  invoices?: SubscriptionInvoice[];
}

export interface SubscriptionInvoice {
  id: number;
  subscription_id: number;
  invoice_id: number;
  is_processed: boolean;
  created_at: string;
  subscription?: Subscription;
  invoice?: Invoice;
}

export interface Merchant {
  id: number;
  user_id: number;
  is_active: boolean;
  profile: MerchantProfile;
  created_at: string;
}

export interface MerchantProfile {
  id: number;
  business_name: string;
  business_email: string;
  phone_number?: string;
}

export interface PlanRevenue {
  plan_name: string;
  tier: PlanTier;
  total_revenue: number;
}

export interface SubscriptionAnalytics {
  total_active: number;
  total_pending: number;
  total_expired: number;
  total_cancelled: number;
  new_this_period: number;
  total_revenue: number;
  conversion_rate: number;
  revenue_by_plan: PlanRevenue[];
  period_start: string;
  period_end: string;
}

export interface PaginatedSubscriptions {
  items: Subscription[];
  total: number;
}