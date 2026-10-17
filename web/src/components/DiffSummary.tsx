import type { DiffSummary as Diff } from '@/lib/types'

function Group({ count, label, names, tone }: { count: number; label: string; names: string[]; tone: string }) {
  if (count === 0) return null
  return (
    <details className="group rounded-lg bg-tile px-4 py-3">
      <summary className="flex cursor-pointer list-none items-baseline gap-2 outline-ring focus-visible:outline-2">
        <span className={`text-2xl font-semibold tabular-nums ${tone}`}>{count}</span>
        <span>{label}</span>
      </summary>
      <ul className="mt-2 grid gap-1 text-sm text-muted-foreground">
        {names.map((n, i) => (
          <li key={i}>{n}</li>
        ))}
        {count > names.length && <li>and {count - names.length} more</li>}
      </ul>
    </details>
  )
}

export function DiffSummary({ diff }: { diff: Diff }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <Group count={diff.new} label={diff.new === 1 ? 'new row' : 'new rows'} names={diff.new_names} tone="" />
      <Group count={diff.changed} label="changed" names={diff.changed_names} tone="" />
      <Group count={diff.removed} label="no longer in the file, will be removed" names={diff.removed_names} tone="text-destructive" />
      {diff.new + diff.changed + diff.removed === 0 && (
        <p className="rounded-lg bg-tile px-4 py-3 text-muted-foreground sm:col-span-3">
          Nothing has changed since the last upload.
        </p>
      )}
    </div>
  )
}
