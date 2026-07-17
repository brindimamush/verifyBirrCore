import React from "react"

interface PlaceholderPageProps {
  title: string
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({ title }) => {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center bg-white shadow-xs">
      <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">{title} Page</h3>
      <p className="mt-2 text-xs text-slate-500 max-w-sm mx-auto">
        This view is standard scaffolding generated during Phase 1. Complete interactive data hooks arrive in later phase configurations.
      </p>
    </div>
  )
}