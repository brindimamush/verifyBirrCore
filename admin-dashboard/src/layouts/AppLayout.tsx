import React, { useState } from "react"
import { Outlet, useLocation } from "react-router-dom"
import { Sidebar } from "../components/layout/Sidebar"
import { Navbar } from "../components/layout/Navbar"

export const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false)
  const location = useLocation()
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        <Navbar onMenuToggle={() => setSidebarOpen(true)} />
        
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50 dark:bg-slate-950 p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl h-full">
            {/* Page Transition Wrapper */}
            <div 
              key={location.pathname} 
              className="animate-fade-in-up h-full"
            >
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}