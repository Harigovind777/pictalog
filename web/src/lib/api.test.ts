import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, SIGNED_OUT_EVENT, api, apiUpload, assetUrl, getToken, setToken } from './api'

function mockFetch(status: number, body: unknown) {
  const fn = vi.fn(async (_url: string, _init?: RequestInit) =>
    new Response(status === 204 ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
  vi.stubGlobal('fetch', fn)
  return fn
}

function sentHeaders(fn: ReturnType<typeof mockFetch>): Headers {
  const init = fn.mock.calls[0][1] as RequestInit
  return new Headers(init.headers)
}

describe('api', () => {
  beforeEach(() => setToken(null))
  afterEach(() => vi.unstubAllGlobals())

  it('adds bearer header', async () => {
    setToken('abc')
    const fn = mockFetch(200, { ok: true })
    await expect(api('/api/catalogs')).resolves.toEqual({ ok: true })
    expect(fn.mock.calls[0][0]).toBe('/api/catalogs')
    expect(sentHeaders(fn).get('Authorization')).toBe('Bearer abc')
  })

  it('sends JSON bodies as JSON', async () => {
    const fn = mockFetch(200, {})
    await api('/api/catalogs', { method: 'POST', body: JSON.stringify({ name: 'x' }) })
    expect(sentHeaders(fn).get('Content-Type')).toBe('application/json')
  })

  it('does not set a content type for uploads', async () => {
    const fn = mockFetch(201, {})
    await apiUpload('/api/catalogs/1/imports', new Blob(['a,b']), 'a.csv')
    expect(sentHeaders(fn).get('Content-Type')).toBeNull()
    expect((fn.mock.calls[0][1] as RequestInit).body).toBeInstanceOf(FormData)
  })

  it('401 clears token', async () => {
    setToken('abc')
    mockFetch(401, { detail: 'Please sign in again.' })
    await expect(api('/api/auth/me')).rejects.toMatchObject({ status: 401 })
    expect(getToken()).toBeNull()
  })

  it('announces sign-out on 401 so the app returns to the sign-in page', async () => {
    setToken('expired')
    const heard = vi.fn()
    window.addEventListener(SIGNED_OUT_EVENT, heard)
    mockFetch(401, { detail: 'Please sign in again.' })
    await api('/api/catalogs').catch(() => {})
    window.removeEventListener(SIGNED_OUT_EVENT, heard)
    expect(heard).toHaveBeenCalledOnce()
  })

  it('ApiError carries server detail message', async () => {
    mockFetch(409, { detail: 'An account with this email already exists.' })
    const error = (await api('/api/auth/signup').catch((e: unknown) => e)) as ApiError
    expect(error).toBeInstanceOf(ApiError)
    expect(error.message).toBe('An account with this email already exists.')
  })

  it('ApiError joins validation messages', async () => {
    mockFetch(422, { detail: [{ msg: 'String should have at least 8 characters' }, { msg: 'Field required' }] })
    const error = (await api('/api/auth/signup').catch((e: unknown) => e)) as ApiError
    expect(error.message).toBe('String should have at least 8 characters. Field required')
  })

  it('204 resolves to undefined', async () => {
    mockFetch(204, null)
    await expect(api('/api/catalogs/1', { method: 'DELETE' })).resolves.toBeUndefined()
  })
})

describe('assetUrl', () => {
  it('prefixes API_BASE to server file URLs only', () => {
    expect(assetUrl('/api/files/img/a.webp', 'http://10.0.2.2:8000')).toBe('http://10.0.2.2:8000/api/files/img/a.webp')
    expect(assetUrl('https://cdn.example.com/a.jpg', 'http://h')).toBe('https://cdn.example.com/a.jpg')
    expect(assetUrl(null, 'http://h')).toBeNull()
  })
})
