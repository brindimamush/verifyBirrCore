import React,{ useState, useEffect } from "react"
import { Bell, Search, User, Menu, Sun, Moon, LogOut, Settings } from "lucide-react"
import { Breadcrumbs } from "./Breadcrumbs"
import { useAuthStore } from "@/store/authStore"

interface NavbarProps {
  onMenuToggle: () => void
}

export const Navbar: React.FC<NavbarProps> = ({ onMenuToggle }) => {
  const { user, clearAuth } = useAuthStore()
  const [isDark, setIsDark] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)

  // Theme Switch Logic
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 md:px-6 shadow-xs transition-colors">
      <div className="flex items-center gap-4 flex-1">
        <button 
          onClick={onMenuToggle}
          className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        
        <div className="hidden md:block">
          <Breadcrumbs />
        </div>
      </div>

      <div className="flex items-center gap-3 md:gap-4">
        {/* Global Search */}
        <div className="relative hidden max-w-xs sm:block">
          <Search className="absolute top-2.5 left-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Global system search..."
            className="w-48 md:w-64 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 py-1.5 pr-4 pl-9 text-sm focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 focus:outline-hidden transition"
          />
        </div>

        {/* Theme Switch */}
        <button 
          onClick={() => setIsDark(!isDark)}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>

        {/* Notifications */}
        <button className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white dark:ring-slate-900" />
        </button>
        
        <div className="h-8 w-px bg-slate-200 dark:bg-slate-700 hidden sm:block" />

        {/* Profile Dropdown */}
        <div className="relative">
          <button 
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 p-1 pr-2 transition"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400">
              <User className="h-4 w-4" />
            </div>
            <div className="flex-col items-start hidden md:flex">
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">
                {user?.email || 'Admin'}
              </span>
              <span className="text-[10px] font-medium text-slate-400 capitalize">
                {user?.role || 'System Operator'}
              </span>
            </div>
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-48 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 py-1 shadow-lg ring-1 ring-black/5 z-50">
              <div className="px-4 py-2 border-b border-slate-100 dark:border-slate-700 md:hidden">
                <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{user?.email}</p>
                <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
              </div>
              <button className="flex w-full items-center gap-2 px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700">
                <Settings className="h-4 w-4" />
                Account Settings
              </button>
              <button 
                onClick={() => clearAuth()}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}