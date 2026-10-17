import { useQuery } from '@tanstack/react-query'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { helperStatus } from '@/lib/api'
import { cn } from '@/lib/utils'

export function useHelperOnline(): boolean | undefined {
  const { data } = useQuery({ queryKey: ['helper'], queryFn: helperStatus, refetchInterval: 10_000 })
  return data?.online
}

export function HelperStatus() {
  const online = useHelperOnline()
  if (online === undefined) return null
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          tabIndex={0}
          className="inline-flex h-8 items-center gap-2 rounded-full border bg-tile px-3 text-sm text-muted-foreground outline-ring focus-visible:outline-2"
        >
          <span className={cn('size-2 rounded-full', online ? 'bg-amber shadow-[0_0_0_3px_color-mix(in_srgb,var(--amber)_25%,transparent)]' : 'bg-greycard')} />
          <span className="hidden sm:inline">{online ? 'Image helper on' : 'Image helper off'}</span>
        </span>
      </TooltipTrigger>
      <TooltipContent className="max-w-64">
        {online
          ? 'Your Mac is making images and reading files.'
          : "Images and file reading wait until the image helper on your Mac is running. Nothing is lost while it's off."}
      </TooltipContent>
    </Tooltip>
  )
}
