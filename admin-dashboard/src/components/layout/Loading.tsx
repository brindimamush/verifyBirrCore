import React from "react"

export const Loading: React.FC = () => {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-50/50 backdrop-blur-xs">
      <div className="flex flex-col items-center gap-3">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />
        <span className="text-sm font-medium text-slate-500 animate-pulse">Initializing Interface...</span>
      </div>
    </div>
  )
}