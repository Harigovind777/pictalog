import { AnimatePresence, motion, useMotionValueEvent, useScroll } from 'motion/react'
import { useRef, useState } from 'react'
import { Link, Navigate, Outlet, ScrollRestoration, useNavigation } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { assetUrl, uploadLogo } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { easeOut } from '@/lib/motion'
import { HelperStatus } from './HelperStatus'
import { Wordmark } from './Wordmark'

// The top bar lifts off into a floating glass pill once the page scrolls (Aceternity's resizable navbar).
const FLOATING = {
  maxWidth: '52rem',
  y: 8,
  paddingLeft: 16,
  paddingRight: 16,
  backgroundColor: 'rgba(255, 255, 255, 0.82)',
  boxShadow: '0 0 0 1px rgb(15 23 42 / 0.05), 0 1px 1px rgb(15 23 42 / 0.04), 0 16px 48px -12px rgb(15 23 42 / 0.18)',
}
const DOCKED = {
  maxWidth: '80rem',
  y: 0,
  paddingLeft: 8,
  paddingRight: 8,
  backgroundColor: 'rgba(250, 250, 250, 0)',
  boxShadow: '0 0 0 0px rgb(15 23 42 / 0), 0 0 0 0 rgb(15 23 42 / 0), 0 0 0 0 rgb(15 23 42 / 0)',
}

export function AppShell() {
  const { user, loading, logout, setUser } = useAuth()
  const logoInput = useRef<HTMLInputElement>(null)
  const { scrollY } = useScroll()
  const [floating, setFloating] = useState(false)
  useMotionValueEvent(scrollY, 'change', (y) => setFloating(y > 40))
  const navigating = useNavigation().state === 'loading'

  if (loading) return <div className="min-h-svh" />
  if (!user) return <Navigate to="/login" replace />

  async function onLogo(file: File | undefined) {
    if (!file) return
    try {
      setUser(await uploadLogo(file))
      toast.success('Logo updated')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Could not upload the logo.')
    }
  }

  const logo = assetUrl(user.logo_url)
  return (
    <div className="min-h-svh">
      {/* Each screen's data is fetched before it slides in. If that takes a moment, a hairline fills across the top. */}
      <AnimatePresence>
        {navigating && (
          <motion.div
            initial={{ scaleX: 0, opacity: 0 }}
            animate={{ scaleX: 0.85, opacity: 1, transition: { duration: 2.4, ease: easeOut, opacity: { delay: 0.15 } } }}
            exit={{ scaleX: 1, opacity: 0, transition: { duration: 0.35 } }}
            className="fixed inset-x-0 top-0 z-50 h-0.5 origin-left bg-ink"
            aria-hidden
          />
        )}
      </AnimatePresence>
      {/* Stays still while screens slide underneath it. */}
      <header className="sticky top-0 z-30 px-2 pt-safe [view-transition-name:app-header] sm:px-4">
        <motion.div
          initial={false}
          animate={floating ? FLOATING : DOCKED}
          transition={{ type: 'spring', stiffness: 200, damping: 40 }}
          className="mx-auto flex h-16 items-center gap-3 rounded-2xl backdrop-blur-xl"
        >
          <Link to="/" className="rounded-sm focus-visible:outline-2 focus-visible:outline-ring">
            <Wordmark className="text-2xl" />
          </Link>
          <div className="ml-auto flex items-center gap-2">
            <HelperStatus />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="gap-2.5 pr-3 pl-1">
                  {logo ? (
                    <img src={logo} alt="" className="size-8 rounded-full bg-tile object-contain ring-1 ring-line" />
                  ) : (
                    <span className="grid size-8 place-items-center rounded-full bg-brand-gradient font-heading text-sm text-white shadow-accent">
                      {user.company_name.slice(0, 1).toUpperCase()}
                    </span>
                  )}
                  <span className="hidden max-w-40 truncate sm:inline">{user.company_name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel className="font-normal">
                  <div className="truncate font-medium">{user.company_name}</div>
                  <div className="truncate text-xs text-muted-foreground">{user.email}</div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onSelect={() => logoInput.current?.click()}>
                  {logo ? 'Change logo' : 'Add your logo'}
                </DropdownMenuItem>
                <DropdownMenuItem onSelect={logout}>Sign out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <input
              ref={logoInput}
              type="file"
              accept="image/*"
              hidden
              onChange={(e) => {
                void onLogo(e.target.files?.[0])
                e.target.value = ''
              }}
            />
          </div>
        </motion.div>
      </header>
      <Outlet />
      {/* New screens open at the top; going back returns to where you were. */}
      <ScrollRestoration />
    </div>
  )
}
