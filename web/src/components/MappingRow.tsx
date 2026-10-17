import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { FIELD_LABELS } from '@/lib/items'
import { ITEM_FIELDS, type ItemField } from '@/lib/types'

const IGNORE = '__ignore'

type Props = {
  headers: string[]
  mapping: Record<string, ItemField | null>
  sample: Record<string, string>
  disabled?: boolean
  onChange: (header: string, field: ItemField | null) => void
}

/** One small card per column of the file: its heading, an example value, and what it becomes. */
export function MappingRow({ headers, mapping, sample, disabled, onChange }: Props) {
  const used = new Set(Object.values(mapping).filter(Boolean))
  return (
    <div className="-mx-4 flex gap-3 overflow-x-auto px-4 pb-2 sm:mx-0 sm:px-0">
      {headers.map((header) => {
        const field = mapping[header] ?? null
        return (
          <div key={header} className="grid w-48 shrink-0 content-start gap-2 rounded-lg bg-tile p-3">
            <div className="grid gap-0.5">
              <p className="truncate font-medium" title={header}>
                {header}
              </p>
              <p className="truncate text-sm text-muted-foreground" title={sample[header]}>
                {sample[header] || 'Empty in the first row'}
              </p>
            </div>
            <Select
              value={field ?? IGNORE}
              disabled={disabled}
              onValueChange={(value) => onChange(header, value === IGNORE ? null : (value as ItemField))}
            >
              <SelectTrigger aria-label={`What the ${header} column is`} className="w-full bg-sweep">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ITEM_FIELDS.map((f) => (
                  <SelectItem key={f} value={f} disabled={used.has(f) && f !== field}>
                    {FIELD_LABELS[f]}
                  </SelectItem>
                ))}
                <SelectItem value={IGNORE}>Keep as extra detail</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )
      })}
    </div>
  )
}
