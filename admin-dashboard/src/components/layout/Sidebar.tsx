import React from "react"
import { NavLink } from "react-router-dom"
import { 
  LayoutDashboard, Users, ShieldCheck, CreditCard, 
  RefreshCw, Key, ShieldAlert, FileText, X 
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
    { to: "/invoices", label: "Invoice History", icon: FileText },
    { to: "/verifications", label: "Verification Center", icon: ShieldAlert },
    { to: "/callbacks", label: "Callback Engine Queue", icon: RefreshCw },
    { to: "/api-keys", label: "API Credentials", icon: Key },
  ]

  return (
    <>
      {/* Mobile Sidebar overlay scrim backdrop */}
      {isOpen && (
        <div 
          onClick={onClose}
          className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs lg:hidden"
        />
      )}

      <aside className={`
        fixed top-0 bottom-0 left-0 z-50 flex w-64 flex-col bg-slate-900 text-slate-200 border-r border-slate-800 transition-transform duration-300 lg:static lg:translate-x-0
        ${isOpen ? "translate-x-0" : "-translate-x-full"}
      `}>
        <div className="flex h-16 items-center justify-between px-6 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-md bg-blue-600 flex items-center justify-center font-bold text-white text-sm">Ω</div>
            <span className="text-sm font-bold tracking-wider uppercase text-white">Admin Platform</span>
          </div>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-slate-800 lg:hidden text-slate-400">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-4 py-6 overflow-y-auto">
          {links.map((link) => {
            const Icon = link.icon
            return (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) => `
                  flex items-center gap-3 rounded-lg px-4 py-2.5 text-xs font-medium tracking-wide transition-colors
                  ${isActive 
                    ? "bg-blue-600 text-white" 
                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"}
                `}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {link.label}
              </NavLink>
            )
          })}
        </nav>
        
        <div className="p-4 border-t border-slate-800 text-center">
          <span className="text-[10px] text-slate-500 font-mono tracking-widest">v1.0.0-PROD</span>
        </div>
      </aside>
    </>
  )
}