import { API_BASE, getToken } from './api'

/** Where shared catalogs are opened. The apps run from a local origin, so they need the real site address. */
export const PUBLIC_URL: string = import.meta.env.VITE_PUBLIC_URL ?? window.location.origin

export function shareLink(token: string): string {
  return `${PUBLIC_URL}/c/${encodeURIComponent(token)}`
}

/** Download a file that needs the signed-in user's token (a plain link can't send it). */
export async function downloadWithAuth(path: string, filename: string): Promise<void> {
  const token = getToken()
  const res = await fetch(API_BASE + path, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!res.ok) throw new Error('The download failed. Please try again.')
  const url = URL.createObjectURL(await res.blob())
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.append(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 10_000)
}
