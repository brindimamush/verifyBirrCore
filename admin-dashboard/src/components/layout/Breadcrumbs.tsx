import React from "react"
import { useLocation, Link } from "react-router-dom"
import { ChevronRight, Home } from "lucide-react"

export const Breadcrumbs: React.FC = () => {
  const location = useLocation()
  const pathnames = location.pathname.split("/").filter((x) => x)

  return (
    <nav className="flex items-center space-x-1 text-sm text-slate-500 dark:text-slate-400">
      <Link to="/" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
        <Home className="h-4 w-4" />
      </Link>
      
      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join("/")}`
        const isLast = index === pathnames.length - 1
        const formattedValue = value.charAt(0).toUpperCase() + value.slice(1).replace(/-/g, ' ')

        return (
          <React.Fragment key={to}>
            <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" />
            {isLast ? (
              <span className="font-semibold text-slate-900 dark:text-slate-100 cursor-default">
                {formattedValue}
              </span>
            ) : (
              <Link to={to} className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                {formattedValue}
              </Link>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}