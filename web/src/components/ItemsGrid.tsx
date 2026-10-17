import { X } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { hasEnoughDetail, type TextField } from '@/lib/items'
import type { ExtractedItem } from '@/lib/types'

const COLUMNS: { field: TextField; label: string; width: string }[] = [
  { field: 'name', label: 'Name', width: 'min-w-48' },
  { field: 'size', label: 'Size', width: 'min-w-24' },
  { field: 'colour', label: 'Colour', width: 'min-w-24' },
  { field: 'price_text', label: 'Price', width: 'min-w-24' },
  { field: 'category', label: 'Category', width: 'min-w-32' },
  { field: 'sku', label: 'Code', width: 'min-w-28' },
  { field: 'description', label: 'Description', width: 'min-w-64' },
]

const PAGE = 150

type Props = {
  items: ExtractedItem[]
  onChange: (index: number, field: TextField, value: string) => void
  onRemove: (index: number) => void
}

/** The rows we read, editable in place. Rows without enough detail for a photo are marked. */
export function ItemsGrid({ items, onChange, onRemove }: Props) {
  const [limit, setLimit] = useState(PAGE)
  const shown = items.slice(0, limit)
  return (
    <div className="grid gap-3">
      <div className="overflow-x-auto rounded-lg bg-tile">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-muted-foreground">
              <th className="w-10 px-3 py-2 font-normal" aria-label="Photo" />
              {COLUMNS.map((c) => (
                <th key={c.field} className={`px-2 py-2 font-normal ${c.width}`}>
                  {c.label}
                </th>
              ))}
              <th className="w-10" aria-label="Remove" />
            </tr>
          </thead>
          <tbody>
            {shown.map((item, index) => {
              const detail = hasEnoughDetail(item)
              return (
                <tr key={index} className="border-b last:border-b-0">
                  <td className="px-3">
                    <span
                      title={detail ? 'Gets a photo' : 'Not enough detail for a photo'}
                      className={`block size-2.5 rounded-full ${detail ? 'bg-amber' : 'bg-greycard/50'}`}
                    />
                  </td>
                  {COLUMNS.map((c) => (
                    <td key={c.field} className="px-1 py-1">
                      <input
                        value={item[c.field] ?? ''}
                        onChange={(e) => onChange(index, c.field, e.target.value)}
                        aria-label={`${c.label}, row ${index + 1}`}
                        className="h-8 w-full rounded-sm bg-transparent px-1.5 outline-ring hover:bg-sweep focus:bg-sweep focus-visible:outline-2"
                      />
                    </td>
                  ))}
                  <td className="px-1">
                    <Button size="icon" variant="ghost" className="size-8" aria-label={`Remove row ${index + 1}`} onClick={() => onRemove(index)}>
                      <X />
                    </Button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted-foreground">
        <span className="inline-flex items-center gap-2">
          <span className="size-2.5 rounded-full bg-amber" /> Gets a photo
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="size-2.5 rounded-full bg-greycard/50" /> Not enough detail, left without a photo
        </span>
        {items.length > limit && (
          <Button variant="link" className="h-auto p-0" onClick={() => setLimit(items.length)}>
            Show all {items.length} rows
          </Button>
        )}
      </div>
    </div>
  )
}
