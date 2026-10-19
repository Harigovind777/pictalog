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
          className="inline-flex h-9 min-w-9 items-center justify-center gap-2 rounded-full border bg-tile px-2.5 text-sm text-muted-foreground shadow-sm outline-ring focus-visible:outline-2 sm:px-3.5"
        >
          <span className={cn('size-2 rounded-full', online ? 'pulse-dot bg-ink' : 'bg-greycard')} />
          <span className="max-sm:sr-only">{online ? 'Image helper on' : 'Image helper off'}</span>
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
