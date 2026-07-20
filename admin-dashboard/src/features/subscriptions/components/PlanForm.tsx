import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2 } from 'lucide-react';
import type { PlanTier } from '@/types/subscription';

const planSchema = z.object({
  tier: z.enum(['free', 'starter', 'professional', 'enterprise'], {
    required_error: 'Tier is required',
  }),
  name: z.string().min(2, 'Name must be at least 2 characters').max(50),
  price: z.coerce.number().min(0, 'Price must be 0 or greater'),
  duration_days: z.coerce.number().min(1, 'Duration must be at least 1 day').max(365),
  is_active: z.boolean().default(true),
});

type PlanFormValues = z.infer<typeof planSchema>;

interface PlanFormProps {
  defaultValues?: Partial<PlanFormValues>;
  onSubmit: (data: PlanFormValues) => Promise<void>;
  isSubmitting?: boolean;
}

const TIER_OPTIONS: { value: PlanTier; label: string }[] = [
  { value: 'free', label: 'Free' },
  { value: 'starter', label: 'Starter' },
  { value: 'professional', label: 'Professional' },
  { value: 'enterprise', label: 'Enterprise' },
];

export const PlanForm: React.FC<PlanFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting = false,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<PlanFormValues>({
    resolver: zodResolver(planSchema),
    defaultValues: {
      tier: 'free',
      duration_days: 30,
      is_active: true,
      ...defaultValues,
    },
  });

  const isFree = watch('tier') === 'free';

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Tier Selection */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Tier
          </label>
          <select
            {...register('tier')}
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          >
            {TIER_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {errors.tier && (
            <p className="mt-1 text-sm text-red-600">{errors.tier.message}</p>
          )}
        </div>

        {/* Plan Name */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Plan Name
          </label>
          <input
            type="text"
            {...register('name')}
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
            placeholder="e.g., Premium Tier"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        {/* Price */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Price (USD)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            {...register('price')}
            disabled={isFree}
            className={`mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white ${
              isFree ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            placeholder={isFree ? 'Free plans cannot have a price' : '0.00'}
          />
          {errors.price && (
            <p className="mt-1 text-sm text-red-600">{errors.price.message}</p>
          )}
          {isFree && (
            <p className="mt-1 text-xs text-slate-500">
              Free tier plans automatically have a price of $0.00
            </p>
          )}
        </div>

        {/* Duration */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Duration (Days)
          </label>
          <input
            type="number"
            min="1"
            max="365"
            {...register('duration_days')}
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
            placeholder="30"
          />
          {errors.duration_days && (
            <p className="mt-1 text-sm text-red-600">{errors.duration_days.message}</p>
          )}
        </div>
      </div>

      {/* Active Status Toggle */}
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          {...register('is_active')}
          className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-2 focus:ring-blue-500 dark:border-slate-700"
        />
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Active (available for new subscriptions)
        </label>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            'Save Plan'
          )}
        </button>
      </div>
    </form>
  );
};