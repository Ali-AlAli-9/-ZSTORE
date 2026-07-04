import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/users': 'http://127.0.0.1:8000',
      '/products': 'http://127.0.0.1:8000',
      '/cart': 'http://127.0.0.1:8000',
      '/orders': 'http://127.0.0.1:8000',
      '/dashboard': 'http://127.0.0.1:8000',

      '/media': 'http://127.0.0.1:8000',
    },
  },
})
