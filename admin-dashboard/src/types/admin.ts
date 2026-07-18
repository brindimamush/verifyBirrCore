export interface PlatformStats {
  total_users: number;
  total_merchants: number;
  total_revenue: number;
  successful_verifications: number;
  failed_verifications: number;
  pending_callbacks: number;
}

export interface MerchantProfile {
  id: number;
  business_name: string;
  contact_email: string;
  phone_number?: string;
}

export interface Merchant {
  id: number;
  user_id: number;
  is_active: boolean;
  profile: MerchantProfile;
  created_at: string;
}
export interface SystemUser {
  id: number;
  email: string;
  role: 'admin' | 'merchant';
  is_active: boolean;
  created_at: string;
}

export interface PaginatedUsers {
  items: SystemUser[];
  total: number;
}