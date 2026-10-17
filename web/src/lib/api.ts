import type {
  AuthOut, Catalog, CatalogSummary, ExtractedItem, HelperStatus, ImportOut, ItemField, PublicCatalog, ShareOut,
  User, Variant,
} from './types'

/** Empty in the browser (Vite proxies /api); an absolute server URL in the desktop and mobile apps. */
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? ''

const TOKEN_KEY = 'pictalog.token'

/** Fired when the server rejects the saved sign-in (expired or revoked), so the app can show the sign-in page. */
export const SIGNED_OUT_EVENT = 'pictalog:signed-out'

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // storage unavailable (private mode): the session just won't persist
  }
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) return body.detail.map((d: { msg: string }) => d.msg).join('. ')
  } catch {
    // not JSON
  }
  return res.status >= 500 ? 'Something went wrong on the server. Please try again.' : res.statusText
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (typeof init.body === 'string' && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  let res: Response
  try {
    res = await fetch(API_BASE + path, { ...init, headers })
  } catch {
    throw new ApiError(0, "Can't reach Pictalog. Check your internet connection.")
  }
  if (res.status === 401 && token) {
    setToken(null)
    window.dispatchEvent(new Event(SIGNED_OUT_EVENT))
  }
  if (!res.ok) throw new ApiError(res.status, await errorMessage(res))
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export function apiUpload<T>(path: string, file: Blob, filename?: string): Promise<T> {
  const form = new FormData()
  form.append('file', file, filename ?? (file instanceof File ? file.name : 'upload'))
  return api<T>(path, { method: 'POST', body: form })
}

export function assetUrl(url: string | null | undefined, base: string = API_BASE): string | null {
  if (!url) return null
  return url.startsWith('/api/') ? base + url : url
}

const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) })

// Accounts
export const signup = (email: string, password: string, company_name: string) =>
  api<AuthOut>('/api/auth/signup', json('POST', { email, password, company_name }))
export const login = (email: string, password: string) => api<AuthOut>('/api/auth/login', json('POST', { email, password }))
export const me = () => api<User>('/api/auth/me')
export const updateMe = (company_name: string) => api<User>('/api/auth/me', json('PATCH', { company_name }))
export const uploadLogo = (file: File) => apiUpload<User>('/api/auth/me/logo', file)

// Catalogs
export const listCatalogs = () => api<CatalogSummary[]>('/api/catalogs')
export const createCatalog = (name: string, currency: string) => api<Catalog>('/api/catalogs', json('POST', { name, currency }))
export const getCatalog = (id: number) => api<Catalog>(`/api/catalogs/${id}`)
export const updateCatalog = (id: number, changes: { name?: string; currency?: string }) =>
  api<Catalog>(`/api/catalogs/${id}`, json('PATCH', changes))
export const deleteCatalog = (id: number) => api<void>(`/api/catalogs/${id}`, { method: 'DELETE' })
export const setShare = (id: number, enabled: boolean) => api<ShareOut>(`/api/catalogs/${id}/share`, json('POST', { enabled }))
export const pdfUrl = (id: number) => `/api/catalogs/${id}/pdf`

// Uploads and the check screen
export const uploadImport = (catalogId: number, file: File) => apiUpload<ImportOut>(`/api/catalogs/${catalogId}/imports`, file)
export const getImport = (id: number) => api<ImportOut>(`/api/imports/${id}`)
export const setMapping = (id: number, mapping: Record<string, ItemField | null>) =>
  api<ImportOut>(`/api/imports/${id}/mapping`, json('PUT', { mapping }))
export const applyImport = (id: number, items: ExtractedItem[]) => api<Catalog>(`/api/imports/${id}/apply`, json('POST', { items }))

// Images
export const regenerate = (variantId: number) => api<Variant>(`/api/variants/${variantId}/regenerate`, { method: 'POST' })
export const uploadVariantPhoto = (variantId: number, file: File) => apiUpload<Variant>(`/api/variants/${variantId}/image`, file)
export const helperStatus = () => api<HelperStatus>('/api/helper/status')

// Public share links (no login)
export const getPublic = (token: string) => api<PublicCatalog>(`/api/public/${encodeURIComponent(token)}`)
export const publicPdfUrl = (token: string) => `${API_BASE}/api/public/${encodeURIComponent(token)}/pdf`
