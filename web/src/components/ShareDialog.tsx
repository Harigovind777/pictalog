import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Share2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { setShare } from '@/lib/api'
import { shareLink } from '@/lib/links'
import type { Catalog } from '@/lib/types'

export function ShareDialog({ catalog }: { catalog: Catalog }) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (enabled: boolean) => setShare(catalog.id, enabled),
    onSuccess: (share) => {
      queryClient.setQueryData<Catalog>(['catalog', catalog.id], (old) => (old ? { ...old, ...share } : old))
    },
    onError: (e) => toast.error(e.message),
  })
  const link = catalog.share_token ? shareLink(catalog.share_token) : ''

  async function copy() {
    try {
      if (navigator.share) await navigator.share({ title: catalog.name, url: link })
      else {
        await navigator.clipboard.writeText(link)
        toast.success('Link copied')
      }
    } catch {
      // share sheet dismissed
    }
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Share2 />
          Share
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Share this catalog</DialogTitle>
          <DialogDescription>People with the link can view the catalog and download the PDF. They don't need an account.</DialogDescription>
        </DialogHeader>
        <div className="flex items-center justify-between gap-4 rounded-xl border bg-muted/50 px-4 py-3.5">
          <Label htmlFor="share-switch">Anyone with the link can view</Label>
          <Switch
            id="share-switch"
            checked={catalog.share_enabled}
            disabled={mutation.isPending}
            onCheckedChange={(on) => mutation.mutate(on)}
          />
        </div>
        {catalog.share_enabled && link && (
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input readOnly value={link} aria-label="Share link" onFocus={(e) => e.target.select()} />
            <Button size="lg" onClick={copy}>{typeof navigator.share === 'function' ? 'Share link' : 'Copy link'}</Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
