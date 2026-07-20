import React, { useState } from 'react';
import { Edit2, Trash2, Power, PowerOff, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import type { SubscriptionPlan } from '@/types/subscription';
import { ConfirmDialog } from '@/components/dialogs/ConfirmDialog';

interface PlanTableProps {
  plans: SubscriptionPlan[];
  isLoading: boolean;
  onEdit: (plan: SubscriptionPlan) => void;
  onToggleStatus: (id: number, isActive: boolean) => void;
  onDelete: (id: number) => void;
  isToggling?: boolean;
  isDeleting?: boolean;
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(amount);
};

export const PlanTable: React.FC<PlanTableProps> = ({
  plans,
  isLoading,
  onEdit,
  onToggleStatus,
  onDelete,
  isToggling = false,
  isDeleting = false,
}) => {
  const [deleteDialog, setDeleteDialog] = useState<{ isOpen: boolean; plan: SubscriptionPlan | null }>({
    isOpen: false,
    plan: null,
  });

  const handleDeleteClick = (plan: SubscriptionPlan) => {
    setDeleteDialog({ isOpen: true, plan });
  };

  const confirmDelete = () => {
    if (deleteDialog.plan) {
      onDelete(deleteDialog.plan.id);
      setDeleteDialog({ isOpen: false, plan: null });
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!plans || plans.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        No subscription plans found. Create your first plan to get started.
      </div>
    );
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
          <thead className="bg-slate-50 dark:bg-slate-950">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                Tier
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                Plan Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                Price
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                Duration
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                Status
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-800 dark:bg-slate-900">
            {plans.map((plan) => (
              <tr key={plan.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                <td className="whitespace-nowrap px-4 py-3">
                  <span className="inline-flex items-center rounded-md px-2 py-1 text-xs font-medium capitalize ring-1 ring-inset bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-900/30 dark:text-blue-400">
                    {plan.tier}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    {plan.name}
                  </div>
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {formatCurrency(plan.price)}
                  </div>
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <div className="text-sm text-slate-600 dark:text-slate-400">
                    {plan.duration_days} days
                  </div>
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
                      plan.is_active
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    }`}
                  >
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        plan.is_active ? 'bg-green-600' : 'bg-red-600'
                      }`}
                    />
                    {plan.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => onEdit(plan)}
                      className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300 transition-colors"
                      title="Edit plan"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => onToggleStatus(plan.id, !plan.is_active)}
                      disabled={isToggling}
                      className={`rounded-lg p-2 transition-colors ${
                        plan.is_active
                          ? 'text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20'
                          : 'text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
                      } disabled:opacity-50`}
                      title={plan.is_active ? 'Deactivate plan' : 'Activate plan'}
                    >
                      {plan.is_active ? (
                        <PowerOff className="h-4 w-4" />
                      ) : (
                        <Power className="h-4 w-4" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDeleteClick(plan)}
                      disabled={isDeleting}
                      className="rounded-lg p-2 text-red-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors disabled:opacity-50"
                      title="Delete plan"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        title="Delete Subscription Plan"
        description={`Are you sure you want to delete the plan "${deleteDialog.plan?.name}"? This action cannot be undone.`}
        confirmText="Delete Plan"
        isDestructive={true}
        isLoading={isDeleting}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteDialog({ isOpen: false, plan: null })}
      />
    </>
  );
};