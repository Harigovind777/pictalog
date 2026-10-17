import { useInView, useReducedMotion } from 'motion/react'
import { useRef } from 'react'

/**
 * Photos arrive in black and white and develop into colour once they're on screen (the `.develop` class in
 * index.css). Spread the result onto the element: `<img {...develop} className="develop" />`.
 * With "reduce motion" on, photos are simply in colour.
 */
export function useDevelop<T extends Element = HTMLDivElement>(enabled = true) {
  const ref = useRef<T>(null)
  const seen = useInView(ref, { once: true, amount: 0.35 })
  const still = useReducedMotion()
  return { ref, 'data-developed': !enabled || still || seen }
}
