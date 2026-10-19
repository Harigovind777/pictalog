import { LANGUAGES } from '@/lib/languages'
import { textProps } from '@/lib/script'
import { cn } from '@/lib/utils'

/** Each language Pictalog reads lists in, written in its own script. The English name is there on hover and for
 *  screen readers. */
export function LanguageList({ className }: { className?: string }) {
  return (
    <ul className={cn('flex flex-wrap gap-1.5', className)} aria-label="Languages your lists can be in">
      {LANGUAGES.map((l) => (
        <li
          key={l.lang}
          lang={l.lang}
          title={l.name}
          {...textProps(l.native)}
          className="rounded-full border bg-white px-3 py-1 text-sm text-ink/75"
        >
          {l.native}
          {l.native !== l.name && (
            <span lang="en" className="sr-only">
              {` (${l.name})`}
            </span>
          )}
        </li>
      ))}
    </ul>
  )
}
