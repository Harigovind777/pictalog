declare global {
  interface Window {
    __pictalogReady?: boolean
  }
}

/** Tells the launch intro (public/intro/intro.js) that the first real screen is ready, so it can fade away. */
export function markAppReady(): void {
  if (window.__pictalogReady) return
  window.__pictalogReady = true
  window.dispatchEvent(new Event('pictalog:ready'))
}
