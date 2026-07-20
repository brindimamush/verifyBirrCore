import React from "react"
import { NavLink } from "react-router-dom"
import { 
  LayoutDashboard, Users, ShieldCheck, CreditCard, 
  RefreshCw, Key, ShieldAlert, FileText, X, TrendingUp
} from "lucide-react"

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const links = [
    { to: "/dashboard", label: "Dashboard Overview", icon: LayoutDashboard },
    { to: "/merchants", label: "Merchants Profile", icon: ShieldCheck },
    { to: "/users", label: "User Management", icon: Users },
    { to: "/subscriptions", label: "Subscription Tiers", icon: CreditCard },
    { to: "/subscriptions/analytics", label: "Subscription Analytics", icon: TrendingUp },
    { to: "/invoices", label: "Invoice History", icon: FileText },
    { to: "/verifications", label: "Verification Center", icon: ShieldAlert },
    { to: "/callbacks", label: "Callback Engine Queue", icon: RefreshCw },
    { to: "/api-keys", label: "API Credentials", icon: Key },
  ]

  return (
    <>
      {/* Mobile & Tablet Overlay */}
      {isOpen && (
        <div 
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm lg:hidden transition-opacity"
        />
      )}

      {/* Desktop First Layout */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-slate-900 text-slate-200 border-r border-slate-800 transition-transform duration-300 ease-in-out
        lg:static lg:translate-x-0
        ${isOpen ? "translate-x-0" : "-translate-x-full"}
      `}>
        <div className="flex h-16 shrink-0 items-center justify-between px-6 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-blue-600 shadow-lg shadow-blue-500/20 flex items-center justify-center font-bold text-white text-sm">
              Ω
            </div>
            <span className="text-sm font-bold tracking-wider uppercase text-white">
              Admin Platform
            </span>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-slate-800 lg:hidden text-slate-400 transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1.5 px-3 py-6 overflow-y-auto custom-scrollbar">
          {links.map((link) => {
            const Icon = link.icon
            return (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={() => {
                  if (window.innerWidth < 1024) onClose()
                }}
                className={({ isActive }) => `
                  group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium tracking-wide transition-all duration-200
                  ${isActive 
                    ? "bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-sm" 
                    : "text-slate-400 hover:bg-slate-800/80 hover:text-slate-100 border border-transparent"}
                `}
              >
                {({ isActive }) => (
                  <>
                    <Icon className={`h-4 w-4 shrink-0 transition-colors ${isActive ? 'text-blue-500' : 'group-hover:text-slate-300'}`} />
                    {link.label}
                  </>
                )}
              </NavLink>
            )
          })}
        </nav>
        
        <div className="shrink-0 p-4 border-t border-slate-800 bg-slate-950/30 text-center">
          <span className="text-[10px] text-slate-500 font-mono tracking-widest">
            v1.0.0-PROD
          </span>
        </div>
      </aside>
    </>
  )
}