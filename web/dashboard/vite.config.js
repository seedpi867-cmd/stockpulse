import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist'
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://prior-managers-winners-cups.trycloudflare.com',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
