import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { RouterProvider } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "sonner"
import { router } from "./routes/index"
import { ErrorBoundary } from "./components/layout/ErrorBoundary"
import "./styles/index.css"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

const container = document.getElementById("root")
if (!container) throw new Error("Crucial Application Mount Target Node 'root' Missing from DOM.")

createRoot(container).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster position="top-right" closeButton richColors />
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>
)