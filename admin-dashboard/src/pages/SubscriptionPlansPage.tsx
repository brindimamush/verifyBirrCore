import React, { useState } from 'react';
import { Plus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { PlanTable } from '@/features/subscriptions/components/PlanTable';
import { PlanDialog } from '@/features/subscriptions/components/PlanDialog';
import {
  useSubscriptionPlans,
  useCreateSubscriptionPlan,
  useUpdateSubscriptionPlan,
  useToggleSubscriptionPlanStatus,
  useDeleteSubscriptionPlan,
} from '@/features/subscriptions/hooks/useSubscriptionManagement';
import type { SubscriptionPlan } from '@/types/subscription';

export const SubscriptionPlansPage: React.FC = () => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);

  // Query
  const { data: plans, isLoading, isError } = useSubscriptionPlans(true);

  // Mutations
  const createPlan = useCreateSubscriptionPlan();
  const updatePlan = useUpdateSubscriptionPlan();
  const toggleStatus = useToggleSubscriptionPlanStatus();
  const deletePlan = useDeleteSubscriptionPlan();

  const handleCreate = () => {
    setDialogMode('create');
    setSelectedPlan(null);
    setIsDialogOpen(true);
  };

  const handleEdit = (plan: SubscriptionPlan) => {
    setDialogMode('edit');
    setSelectedPlan(plan);
    setIsDialogOpen(true);
  };

  const handleSave = async (data: any) => {
    if (dialogMode === 'create') {
      await createPlan.mutateAsync({ 
        plan: data,
        idempotencyKey: `plan-create-${Date.now()}` 
      });
    } else if (selectedPlan) {
      await updatePlan.mutateAsync({ id: selectedPlan.id, plan: data });
    }
    setIsDialogOpen(false);
    setSelectedPlan(null);
  };

  const handleToggleStatus = (id: number, isActive: boolean) => {
    toggleStatus.mutate({ id, isActive });
  };

  const handleDelete = (id: number) => {
    deletePlan.mutate(id);
  };

  if (isError) {
    return (
      <div className="p-8 text-center text-red-600 bg-red-50 rounded-lg border border-red-100 m-6">
        Failed to load subscription plans. Please check your connection or try again later.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Subscription Plans
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage pricing tiers and subscription offerings for merchants.
          </p>
        </div>
        <button
          onClick={handleCreate}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Plan
        </button>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <PlanTable
          plans={plans || []}
          isLoading={isLoading}
          onEdit={handleEdit}
          onToggleStatus={handleToggleStatus}
          onDelete={handleDelete}
          isToggling={toggleStatus.isPending}
          isDeleting={deletePlan.isPending}
        />
      </div>

      {/* Dialog */}
      <PlanDialog
        isOpen={isDialogOpen}
        mode={dialogMode}
        plan={selectedPlan}
        onClose={() => {
          setIsDialogOpen(false);
          setSelectedPlan(null);
        }}
        onSave={handleSave}
        isSaving={createPlan.isPending || updatePlan.isPending}
      />
    </div>
  );
};