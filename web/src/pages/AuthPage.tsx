import { ArrowRight } from 'lucide-react'
import { motion } from 'motion/react'
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router'
import { LanguageList } from '@/components/LanguageList'
import { SectionLabel } from '@/components/SectionLabel'
import { Wordmark } from '@/components/Wordmark'
import { ThreeDMarquee } from '@/components/ui/3d-marquee'
import { Button } from '@/components/ui/button'
import { ContainerTextFlip } from '@/components/ui/container-text-flip'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/lib/auth'
import { fadeInUp, stagger } from '@/lib/motion'
import { GALLERY } from '@/lib/showcase'

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
    <main className="grid min-h-svh lg:grid-cols-[1.1fr_0.9fr]">
      {/* On phones the wall of products is a band across the top. */}
      {/* Bleeds under the phone's side status area: it's background, not content. */}
      <div
        className="dot-pattern relative mr-[calc(env(safe-area-inset-right)*-1)] ml-[calc(env(safe-area-inset-left)*-1)] h-60 overflow-hidden bg-ink lg:hidden"
        aria-hidden
      >
        <ProductWall />
        <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-sweep to-transparent" />
        <div className="absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-ink/90 to-transparent" />
        <Wordmark className="absolute top-[calc(env(safe-area-inset-top)+1.25rem)] left-[calc(env(safe-area-inset-left)+1.25rem)] text-2xl text-white" />
      </div>

      <section className="flex flex-col gap-10 px-5 pb-8 sm:px-12 lg:py-12">
        <Wordmark className="hidden text-2xl lg:inline-flex" />
        <motion.div variants={stagger} initial="hidden" animate="visible" className="mx-auto grid w-full max-w-md gap-8 lg:my-auto">
          <motion.div variants={fadeInUp} className="grid gap-5">
            <SectionLabel live>AI product photos</SectionLabel>
            {isSignup ? (
              <h1 className="font-display text-[2.6rem] leading-[1.12] sm:text-6xl">
                Your{' '}
                <span className="whitespace-nowrap">
                  <ContainerTextFlip words={INPUTS} interval={2600} className="px-3" />,
                </span>{' '}
                photographed.
              </h1>
            ) : (
              <h1 className="font-display text-[2.75rem] sm:text-6xl">
                Welcome back
              </h1>
            )}
            <p className="text-lg leading-relaxed text-muted-foreground">
              {isSignup
                ? "Upload a spreadsheet, PDF or a photo of a printed list, in English or any of 15 of India's languages. Pictalog makes a studio photo of every product, in every size and colour, and turns them into a catalog you can share."
                : 'Your catalogs are where you left them.'}
            </p>
          </motion.div>
          <motion.form variants={fadeInUp} onSubmit={submit} className="grid gap-4">
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
            <Button type="submit" size="lg" className="mt-2 w-full" disabled={busy}>
              {busy ? (isSignup ? 'Creating account…' : 'Signing in…') : isSignup ? 'Create account' : 'Sign in'}
              {!busy && <ArrowRight className="transition-transform duration-200 group-hover/button:translate-x-1" />}
            </Button>
          </motion.form>
          <motion.p variants={fadeInUp} className="text-sm text-muted-foreground">
            {isSignup ? 'Already have an account? ' : 'New to Pictalog? '}
            <Link to={isSignup ? '/login' : '/signup'} className="font-semibold text-brand underline-offset-4 hover:underline">
              {isSignup ? 'Sign in' : 'Create an account'}
            </Link>
          </motion.p>
          <motion.section variants={fadeInUp} aria-labelledby="languages" className="grid gap-3 border-t pt-6">
            <SectionLabel>
              <span id="languages">Lists in your language</span>
            </SectionLabel>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Your product list can be in English or any of these languages of India. Names, sizes and colours stay
              in your language and script.
            </p>
            <LanguageList />
            <p className="text-xs text-muted-foreground">
              Santali and Manipuri lists can be spreadsheets or typed text; photos of them can't be read yet.
            </p>
          </motion.section>
        </motion.div>
        <p className="text-xs text-muted-foreground">Product photos are made by AI from your product details.</p>
      </section>

      <aside className="dot-pattern relative hidden overflow-hidden bg-ink lg:block" aria-hidden>
        <ProductWall />
        <p className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink via-ink/80 to-transparent px-10 pt-24 pb-10 text-white/70">
          Every photo here was made by Pictalog from one row of a price list.
        </p>
      </aside>
    </main>
  )
}

const INPUTS = ['price list', 'spreadsheet', 'PDF', 'Word file']

/** Aceternity's 3D marquee: a slowly drifting wall of real Pictalog photos, the only colour on a black wall. */
function ProductWall() {
  return (
    <>
      <div className="absolute -top-32 -left-24 size-96 rounded-full bg-white/10 blur-[120px]" />
      <div className="absolute -right-24 -bottom-32 size-96 rounded-full bg-white/8 blur-[120px]" />
      {/* Pinned to the panel: the marquee's 3D stage is far bigger than the space it shows. */}
      <ThreeDMarquee images={GALLERY} className="absolute inset-0 h-full rounded-none max-sm:h-full" />
    </>
  )
}
