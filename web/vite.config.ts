/// <reference types="vitest/config" />
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
    // node_modules is a link to node_modules.nosync; following it hides packages from Vite's dependency handling.
    preserveSymlinks: true,
  },
  server: {
    host: true,
    proxy: { '/api': 'http://localhost:8000' },
    // node_modules really lives in node_modules.nosync (kept out of iCloud), which the default ignores don't cover.
    watch: { ignored: ['**/*.nosync/**'] },
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
