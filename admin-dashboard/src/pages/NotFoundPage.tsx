import React from "react"
import { useNavigate } from "react-router-dom"
import { AlertCircle } from "lucide-react"

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-center">
      <div className="rounded-full bg-amber-50 p-4 border border-amber-200 text-amber-600 mb-6 animate-bounce">
        <AlertCircle className="h-10 w-10" />
      </div>
      <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight sm:text-5xl">404 - Path Missing</h1>
      <p className="mt-3 text-base text-slate-600 max-w-md">
        The system routing map failed to locate the resource namespace you requested.
      </p>
      <div className="mt-8 flex gap-4">
        <button
          onClick={() => navigate(-1)}
          className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition"
        >
          Return to Previous Namespace
        </button>
        <button
          onClick={() => navigate("/dashboard")}
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition"
        >
          Go to Control Deck
        </button>
      </div>
    </div>
  )
}