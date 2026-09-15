import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // GitHub Pages serves this app from https://<user>.github.io/Study-Mate/,
  // so built asset URLs need that prefix. Dev server stays at the root.
  base: command === 'build' ? '/Study-Mate/' : '/',
  server: {
    port: 3000,
    proxy: {
      // '^/api/' (not plain '/api') so this only matches API calls like
      // /api/chat/ask and doesn't swallow the frontend's own api.js module.
      '^/api/': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
}))
