import React from "react"
import { Bell, Search, User, Menu } from "lucide-react"

interface NavbarProps {
  onMenuToggle: () => void
}

export const Navbar: React.FC<NavbarProps> = ({ onMenuToggle }) => {
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white px-6 shadow-xs">
      <div className="flex items-center gap-4">
        <button 
          onClick={onMenuToggle}
          className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="relative hidden max-w-xs sm:block">
          <Search className="absolute top-2.5 left-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Global system search..."
            className="w-64 rounded-lg border border-slate-200 bg-slate-50 py-1.5 pr-4 pl-9 text-xs focus:border-blue-500 focus:bg-white focus:outline-hidden transition"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 transition">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500" />
        </button>
        
        <div className="h-8 w-px bg-slate-200" />

        <div className="flex items-center gap-3">
          <div className="flex flex-col items-end hidden md:flex">
            <span className="text-xs font-semibold text-slate-700">System Operator</span>
            <span className="text-[10px] font-medium text-slate-400">Admin Console</span>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 border border-slate-200 text-slate-600">
            <User className="h-4 w-4" />
          </div>
        </div>
      </div>
    </header>
  )
}