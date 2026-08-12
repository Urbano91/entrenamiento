import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const apiOrigin = env.VITE_API_ORIGIN?.trim().replace(/\/+$/, '')

  return {
    plugins: [react()],
    server: apiOrigin ? {
      proxy: {
        '/api': {
          target: apiOrigin,
          changeOrigin: true,
        },
      },
    } : undefined,
  }
})
