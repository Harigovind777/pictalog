import type { createBrowserRouter } from 'react-router'

type Router = ReturnType<typeof createBrowserRouter>

const depth = (pathname: string) => pathname.split('/').filter(Boolean).length

/** Screens deeper in the app (a catalog, then one of its uploads) push in from the right; going up slides back. */
export function slideDirection(from: string, to: string): 'forward' | 'back' {
  return depth(to) < depth(from) ? 'back' : 'forward'
}

/**
 * Marks each animated navigation's direction on <html> for the slide in index.css. Subscribe before RouterProvider
 * mounts so this runs before the router starts the transition.
 */
export function followNavigationDirection(router: Router) {
  return router.subscribe((_state, { viewTransitionOpts }) => {
    if (!viewTransitionOpts) return
    const { currentLocation, nextLocation } = viewTransitionOpts
    document.documentElement.dataset.nav = slideDirection(currentLocation.pathname, nextLocation.pathname)
  })
}

/** The catalog last opened from the shelf, so coming back lands on its cover. */
export const shelfMemory = { catalogId: null as number | null }
