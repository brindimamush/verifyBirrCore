import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Shield, ShieldOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { fetchMerchants, toggleMerchantStatus } from '../services/api/admin';
import type { Merchant } from '../types/admin';

export const MerchantsPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Query: Fetch all merchants
  const { data: merchants, isLoading, isError } = useQuery({
    queryKey: ['admin', 'merchants'],
    queryFn: () => fetchMerchants(50, 0),
  });

  // Mutation: Toggle status with Atomic State Rollback
  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) => 
      toggleMerchantStatus(id, isActive),
    
    // Optimistically update the UI before the backend confirms
    onMutate: async ({ id, isActive }) => {
      await queryClient.cancelQueries({ queryKey: ['admin', 'merchants'] });
      const previousMerchants = queryClient.getQueryData<Merchant[]>(['admin', 'merchants']);

      queryClient.setQueryData<Merchant[]>(['admin', 'merchants'], (old) => 
        old?.map(merchant => 
          merchant.id === id ? { ...merchant, is_active: isActive } : merchant
        )
      );

      return { previousMerchants };
    },
    
    // Rollback if the backend transaction fails (Frontend Atomicity)
    onError: (err, newTodo, context) => {
      queryClient.setQueryData(['admin', 'merchants'], context?.previousMerchants);
      toast.error('Transaction Failed', {
        description: 'Failed to update merchant status. State has been rolled back.',
      });
    },
    
    // Confirm success
    onSuccess: (data) => {
      toast.success('Status Updated', {
        description: `${data.profile.business_name} is now ${data.is_active ? 'Active' : 'Inactive'}.`,
      });
    },
    
    // Ensure final state matches the server
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'merchants'] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8 text-center text-red-600 bg-red-50 rounded-lg border border-red-100 m-6">
        Failed to load merchants. Please verify the backend connection.
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Merchants Profile</h1>
          <p className="text-sm text-slate-500 mt-1">Manage platform merchants and system access.</p>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Business Name</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Contact Info</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {merchants?.map((merchant) => (
              <tr key={merchant.id} className="hover:bg-slate-50 transition-colors">
                <td className="whitespace-nowrap px-6 py-4">
                  <div className="text-sm font-medium text-slate-900">{merchant.profile.business_name}</div>
                  <div className="text-xs text-slate-500">ID: {merchant.id}</div>
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  <div className="text-sm text-slate-900">{merchant.profile.contact_email}</div>
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
                    merchant.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${merchant.is_active ? 'bg-green-600' : 'bg-red-600'}`}></span>
                    {merchant.is_active ? 'Active' : 'Suspended'}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                  <button
                    onClick={() => toggleMutation.mutate({ id: merchant.id, isActive: !merchant.is_active })}
                    disabled={toggleMutation.isPending}
                    className={`inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50 ${
                      merchant.is_active 
                        ? 'text-red-700 hover:bg-red-50 border border-red-200' 
                        : 'text-green-700 hover:bg-green-50 border border-green-200'
                    }`}
                  >
                    {merchant.is_active ? (
                      <><ShieldOff className="h-4 w-4" /> Revoke Access</>
                    ) : (
                      <><Shield className="h-4 w-4" /> Restore Access</>
                    )}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {(!merchants || merchants.length === 0) && (
          <div className="p-8 text-center text-slate-500 text-sm">
            No registered merchants found in the system.
          </div>
        )}
      </div>
    </div>
  );
};