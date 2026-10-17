import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router'
import { Wordmark } from '@/components/Wordmark'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/lib/auth'

export function AuthPage({ mode }: { mode: 'login' | 'signup' }) {
  const { user, login, signup } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [company, setCompany] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      if (mode === 'signup') await signup(email, password, company)
      else await login(email, password)
      navigate('/', { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  const isSignup = mode === 'signup'
  return (
    <main className="grid min-h-svh lg:grid-cols-[1.1fr_1fr]">
      <section className="flex flex-col justify-between px-6 py-8 sm:px-12 lg:py-12">
        <Wordmark className="text-2xl" />
        <div className="mx-auto w-full max-w-sm py-12">
          <h1 className="text-3xl font-semibold">{isSignup ? 'Create your company account' : 'Sign in'}</h1>
          <p className="mt-2 text-muted-foreground">
            {isSignup
              ? 'Upload a product list and get a catalog with a photo for every product.'
              : 'Welcome back. Your catalogs are where you left them.'}
          </p>
          <form onSubmit={submit} className="mt-8 grid gap-5">
            {isSignup && (
              <div className="grid gap-2">
                <Label htmlFor="company">Company name</Label>
                <Input id="company" value={company} onChange={(e) => setCompany(e.target.value)} required autoComplete="organization" />
              </div>
            )}
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={isSignup ? 8 : undefined}
                autoComplete={isSignup ? 'new-password' : 'current-password'}
              />
              {isSignup && <p className="text-sm text-muted-foreground">At least 8 characters.</p>}
            </div>
            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}
            <Button type="submit" size="lg" disabled={busy}>
              {busy ? (isSignup ? 'Creating account…' : 'Signing in…') : isSignup ? 'Create account' : 'Sign in'}
            </Button>
          </form>
          <p className="mt-6 text-sm text-muted-foreground">
            {isSignup ? 'Already have an account? ' : 'New to Pictalog? '}
            <Link to={isSignup ? '/login' : '/signup'} className="font-medium text-foreground underline underline-offset-4">
              {isSignup ? 'Sign in' : 'Create an account'}
            </Link>
          </p>
        </div>
        <p className="text-xs text-muted-foreground">Product photos are made by AI from your product details.</p>
      </section>
      <StudioPanel />
    </main>
  )
}

/** The right half: a lit studio sweep with a small contact sheet of what the app makes. */
function StudioPanel() {
  const cells = [
    { label: 'Cotton tee, red, M', status: 'ready' },
    { label: 'Steel bottle, 1 L', status: 'light' },
    { label: 'SKU-10023', status: 'grey' },
    { label: 'Ceramic mug, 350 ml', status: 'ready' },
  ] as const
  return (
    <aside className="relative hidden overflow-hidden bg-tile lg:flex lg:items-center lg:justify-center" aria-hidden>
      <div className="absolute inset-0 bg-[radial-gradient(70%_60%_at_50%_30%,color-mix(in_srgb,var(--amber)_16%,transparent),transparent_70%)]" />
      <div className="relative grid w-[min(28rem,80%)] grid-cols-2 gap-4">
        {cells.map((cell) => (
          <figure key={cell.label} className="grid gap-2">
            <div
              className={
                cell.status === 'light'
                  ? 'studio-light aspect-square rounded-md'
                  : cell.status === 'grey'
                    ? 'grey-card aspect-square rounded-md'
                    : 'aspect-square rounded-md bg-sweep'
              }
            />
            <figcaption className="text-sm text-muted-foreground">{cell.label}</figcaption>
          </figure>
        ))}
      </div>
    </aside>
  )
}
