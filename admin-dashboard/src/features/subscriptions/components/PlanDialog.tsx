import React from 'react';
import { X } from 'lucide-react';
import { PlanForm } from './PlanForm';
import type { SubscriptionPlan, SubscriptionPlanCreate, SubscriptionPlanUpdate } from '@/types/subscription';

interface PlanDialogProps {
  isOpen: boolean;
  mode: 'create' | 'edit';
  plan?: SubscriptionPlan | null;
  onClose: () => void;
  onSave: (data: SubscriptionPlanCreate | SubscriptionPlanUpdate) => Promise<void>;
  isSaving: boolean;
}

export const PlanDialog: React.FC<PlanDialogProps> = ({
  isOpen,
  mode,
  plan,
  onClose,
  onSave,
  isSaving,
}) => {
  if (!isOpen) return null;

  const isEdit = mode === 'edit';
  const title = isEdit ? `Edit Plan: ${plan?.name}` : 'Create New Plan';

  const defaultValues = isEdit && plan
    ? {
        tier: plan.tier,
        name: plan.name,
        price: plan.price,
        duration_days: plan.duration_days,
        is_active: plan.is_active,
      }
    : undefined;

  const handleSubmit = async (data: any) => {
    await onSave(data);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900 dark:border dark:border-slate-800">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-500 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <div className="mt-6">
          <PlanForm
            defaultValues={defaultValues}
            onSubmit={handleSubmit}
            isSubmitting={isSaving}
          />
        </div>
      </div>
    </div>
  );
};