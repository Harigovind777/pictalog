import type { Variants } from 'motion/react'

/** The style's one easing curve: quick out of the gate, long gentle settle. */
export const easeOut = [0.16, 1, 0.3, 1] as const

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: easeOut } },
}

export const stagger: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
}

/** Animate once, when a little of the element is on screen. */
export const inView = { once: true, amount: 0.15, margin: '-40px' } as const
