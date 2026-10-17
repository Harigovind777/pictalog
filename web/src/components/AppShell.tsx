import { useRef, type ReactNode } from 'react'
import { Link, Navigate, Outlet } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { assetUrl, uploadLogo } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Wordmark } from './Wordmark'

export function AppShell({ status }: { status?: ReactNode }) {
  const { user, loading, logout, setUser } = useAuth()
  const logoInput = useRef<HTMLInputElement>(null)

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
      <header className="sticky top-0 z-30 border-b bg-sweep/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-4 sm:px-6">
          <Link to="/" className="rounded-sm focus-visible:outline-2 focus-visible:outline-ring">
            <Wordmark />
          </Link>
          <div className="ml-auto flex items-center gap-2">
            {status}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="gap-2 px-2">
                  {logo ? (
                    <img src={logo} alt="" className="size-7 rounded-sm bg-tile object-contain" />
                  ) : (
                    <span className="grid size-7 place-items-center rounded-sm bg-ink text-xs font-semibold text-white">
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
        </div>
      </header>
      <Outlet />
    </div>
  )
}
