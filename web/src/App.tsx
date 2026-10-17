import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MotionConfig } from 'motion/react'
import { createBrowserRouter, createHashRouter, RouterProvider, type RouteObject } from 'react-router'
import { AppShell } from '@/components/AppShell'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AuthProvider } from '@/lib/auth'
import { AuthPage } from '@/pages/AuthPage'
import { CatalogView } from '@/pages/CatalogView'
import { Catalogs } from '@/pages/Catalogs'
import { ImportCheck } from '@/pages/ImportCheck'
import { PublicCatalog } from '@/pages/PublicCatalog'

const routes: RouteObject[] = [
  { path: '/login', element: <AuthPage mode="login" /> },
  { path: '/signup', element: <AuthPage mode="signup" /> },
  { path: '/c/:token', element: <PublicCatalog /> },
  {
    element: <AppShell />,
    children: [
      { path: '/', element: <Catalogs /> },
      { path: '/catalogs/:id', element: <CatalogView /> },
      { path: '/catalogs/:id/imports/:importId', element: <ImportCheck /> },
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
        {/* Animations follow the device's "reduce motion" setting. */}
        <MotionConfig reducedMotion="user">
          <TooltipProvider>
            <RouterProvider router={router} />
            <Toaster position="bottom-center" />
          </TooltipProvider>
        </MotionConfig>
      </AuthProvider>
    </QueryClientProvider>
  )
}
