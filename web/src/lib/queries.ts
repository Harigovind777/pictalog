import { queryOptions } from '@tanstack/react-query'
import { getCatalog, getToken, listCatalogs } from './api'

export const catalogsQuery = queryOptions({ queryKey: ['catalogs'], queryFn: listCatalogs })

export const catalogQuery = (id: number) => queryOptions({ queryKey: ['catalog', id], queryFn: () => getCatalog(id) })

/**
 * Runs a route loader's fetch (usually `queryClient.ensureQueryData`) before the router shows the screen, so the
 * screen slides in complete instead of as a skeleton. Data already in the cache (from a prefetch when a cover was
 * touched) is used at once. Errors are left for the screen to show.
 */
export function preload(load: () => Promise<unknown>) {
  if (!getToken()) return null
  return load().catch(() => null)
}
