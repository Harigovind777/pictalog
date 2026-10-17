import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, createHashRouter, RouterProvider, type RouteObject } from 'react-router'
import { AppShell } from '@/components/AppShell'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AuthProvider } from '@/lib/auth'
import { AuthPage } from '@/pages/AuthPage'
import { CatalogView } from '@/pages/CatalogView'
import { Catalogs } from '@/pages/Catalogs'

const routes: RouteObject[] = [
  { path: '/login', element: <AuthPage mode="login" /> },
  { path: '/signup', element: <AuthPage mode="signup" /> },
  {
    element: <AppShell />,
    children: [
      { path: '/', element: <Catalogs /> },
      { path: '/catalogs/:id', element: <CatalogView /> },
    ],
  },
]

// The desktop app loads files from disk, where only hash URLs work.
const router = import.meta.env.VITE_ROUTER === 'hash' ? createHashRouter(routes) : createBrowserRouter(routes)

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: true, retry: 1 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <RouterProvider router={router} />
          <Toaster position="bottom-center" />
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
