import { useRef } from 'react'

/** A hidden photo file input and a function that opens it. Render `input` once, call `pick` from any button. */
export function usePhotoPicker(onFile?: (file: File) => void) {
  const ref = useRef<HTMLInputElement>(null)
  const input = onFile ? (
    <input
      ref={ref}
      type="file"
      accept="image/*"
      hidden
      onChange={(e) => {
        const file = e.target.files?.[0]
        if (file) onFile(file)
        e.target.value = ''
      }}
    />
  ) : null
  return { input, pick: () => ref.current?.click() }
}
