import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Required for GitHub Pages deployment — assets are served from /adaptive-trail-simulator/
  base: '/adaptive-trail-simulator/',
})
