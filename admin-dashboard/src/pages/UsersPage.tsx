import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, UserCheck, UserX, Loader2, Eye } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';
import { fetchUsers, toggleUserStatus } from '../services/api/admin';
import { ConfirmDialog } from '../components/dialogs/ConfirmDialog';
import type { SystemUser } from '../types/admin';

export const UsersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const limit = 10;

  // Dialog State
  const [dialogConfig, setDialogConfig] = useState<{
    isOpen: boolean;
    user: SystemUser | null;
    intendedStatus: boolean;
  }>({
    isOpen: false,
    user: null,
    intendedStatus: false,
  });

  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin', 'users', page, searchTerm],
    queryFn: () => fetchUsers(limit, page * limit, searchTerm),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) => 
      toggleUserStatus(id, isActive),
    onMutate: async ({ id, isActive }) => {
      await queryClient.cancelQueries({ queryKey: ['admin', 'users', page, searchTerm] });
      const previousData = queryClient.getQueryData(['admin', 'users', page, searchTerm]);

      // Optimistic update
      queryClient.setQueryData(['admin', 'users', page, searchTerm], (old: any) => ({
        ...old,
        items: old?.items.map((user: SystemUser) => 
          user.id === id ? { ...user, is_active: isActive } : user
        )
      }));

      return { previousData };
    },
    onError: (err, newTodo, context) => {
      queryClient.setQueryData(['admin', 'users', page, searchTerm], context?.previousData);
      toast.error('Failed to update user status.');
    },
    onSuccess: (updatedUser) => {
      toast.success(`User access ${updatedUser.is_active ? 'granted' : 'revoked'}.`);
      setDialogConfig({ isOpen: false, user: null, intendedStatus: false });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });

  const handleToggleClick = (user: SystemUser) => {
    setDialogConfig({
      isOpen: true,
      user,
      intendedStatus: !user.is_active,
    });
  };

  const confirmToggle = () => {
    if (dialogConfig.user) {
      toggleMutation.mutate({ 
        id: dialogConfig.user.id, 
        isActive: dialogConfig.intendedStatus 
      });
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">User Management</h1>
          <p className="mt-1 text-sm text-slate-500">Monitor and manage administrative and merchant platform access.</p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by email..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(0); // Reset pagination on search
            }}
            className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-red-100 bg-red-50 p-8 text-center text-red-600">
          Failed to load system users. Please verify the backend connection.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
            <thead className="bg-slate-50 dark:bg-slate-950">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">User Email</th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Role</th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Status</th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Created Date</th>
                <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-800 dark:bg-slate-900">
              {data?.items.map((user) => (
                <tr key={user.id} className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="text-sm font-medium text-slate-900 dark:text-slate-100">{user.email}</div>
                    <div className="text-xs text-slate-500">ID: {user.id}</div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium capitalize ring-1 ring-inset ${
                      user.role === 'admin' 
                        ? 'bg-purple-50 text-purple-700 ring-purple-600/20 dark:bg-purple-900/30 dark:text-purple-400' 
                        : 'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-900/30 dark:text-blue-400'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
                      user.is_active 
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' 
                        : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    }`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${user.is_active ? 'bg-green-600' : 'bg-red-600'}`}></span>
                      {user.is_active ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-500 dark:text-slate-400">
                    {format(new Date(user.created_at), 'MMM dd, yyyy HH:mm')}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <button className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800">
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleToggleClick(user)}
                        className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                          user.is_active 
                            ? 'border-red-200 text-red-700 hover:bg-red-50 dark:border-red-900/50 dark:text-red-400 dark:hover:bg-red-900/20' 
                            : 'border-green-200 text-green-700 hover:bg-green-50 dark:border-green-900/50 dark:text-green-400 dark:hover:bg-green-900/20'
                        }`}
                      >
                        {user.is_active ? (
                          <><UserX className="h-4 w-4" /> Disable</>
                        ) : (
                          <><UserCheck className="h-4 w-4" /> Enable</>
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {(!data?.items || data.items.length === 0) && (
            <div className="p-8 text-center text-sm text-slate-500">
              No users found matching your criteria.
            </div>
          )}

          {/* Simple Pagination Controls */}
          {data && data.total > limit && (
            <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-6 py-3 dark:border-slate-800 dark:bg-slate-950">
              <span className="text-sm text-slate-500">
                Showing {page * limit + 1} to Math.min((page + 1) * limit, data.total) of {data.total}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="rounded border border-slate-300 px-3 py-1 text-sm disabled:opacity-50 dark:border-slate-700 dark:text-slate-300"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={(page + 1) * limit >= data.total}
                  className="rounded border border-slate-300 px-3 py-1 text-sm disabled:opacity-50 dark:border-slate-700 dark:text-slate-300"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={dialogConfig.isOpen}
        title={`${dialogConfig.intendedStatus ? 'Enable' : 'Disable'} User Access`}
        description={`Are you sure you want to ${dialogConfig.intendedStatus ? 'enable' : 'disable'} access for ${dialogConfig.user?.email}? This will immediately affect their ability to log into the platform.`}
        confirmText={dialogConfig.intendedStatus ? "Enable User" : "Disable User"}
        isDestructive={!dialogConfig.intendedStatus}
        isLoading={toggleMutation.isPending}
        onConfirm={confirmToggle}
        onCancel={() => setDialogConfig({ isOpen: false, user: null, intendedStatus: false })}
      />
    </div>
  );
};