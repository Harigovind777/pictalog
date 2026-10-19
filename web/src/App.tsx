import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MotionConfig } from 'motion/react'
import { createBrowserRouter, createHashRouter, RouterProvider, type RouteObject } from 'react-router'
import { AppShell } from '@/components/AppShell'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AuthProvider } from '@/lib/auth'
import { followNavigationDirection } from '@/lib/page-transitions'
import { catalogQuery, catalogsQuery, preload } from '@/lib/queries'
import { CatalogView } from '@/pages/CatalogView'
import { Catalogs } from '@/pages/Catalogs'

const queryClient = new QueryClient({
  // Data shown a few seconds ago is shown again at once when going back, then refreshed in the background.
  defaultOptions: { queries: { refetchOnWindowFocus: true, retry: 1, staleTime: 10_000 } },
})

const blank = <div className="min-h-svh" />

// The catalog screens are in the main bundle so they open instantly; the rest load the first time they're needed.
const routes: RouteObject[] = [
  {
    path: '/login',
    lazy: async () => {
      const { AuthPage } = await import('@/pages/AuthPage')
      return { Component: () => <AuthPage mode="login" /> }
    },
  },
  {
    path: '/signup',
    lazy: async () => {
      const { AuthPage } = await import('@/pages/AuthPage')
      return { Component: () => <AuthPage mode="signup" /> }
    },
  },
  { path: '/c/:token', lazy: async () => ({ Component: (await import('@/pages/PublicCatalog')).PublicCatalog }) },
  {
    element: <AppShell />,
    hydrateFallbackElement: blank,
    children: [
      { path: '/', element: <Catalogs />, loader: () => preload(() => queryClient.ensureQueryData(catalogsQuery)), hydrateFallbackElement: blank },
      {
        path: '/catalogs/:id',
        element: <CatalogView />,
        loader: ({ params }) => preload(() => queryClient.ensureQueryData(catalogQuery(Number(params.id)))),
        hydrateFallbackElement: blank,
      },
      {
        path: '/catalogs/:id/imports/:importId',
        lazy: async () => ({ Component: (await import('@/pages/ImportCheck')).ImportCheck }),
      },
    ],
  },
]

// The desktop app loads files from disk, where only hash URLs work.
const router = import.meta.env.VITE_ROUTER === 'hash' ? createHashRouter(routes) : createBrowserRouter(routes)
followNavigationDirection(router)

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
