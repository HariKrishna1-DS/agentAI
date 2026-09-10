import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api-key-status': 'http://127.0.0.1:8000',
      '/set-api-key': 'http://127.0.0.1:8000',
      '/files': 'http://127.0.0.1:8000',
      '/upload': 'http://127.0.0.1:8000',
      '/ask': 'http://127.0.0.1:8000',
      '/qc-audit': 'http://127.0.0.1:8000',
      '/chat': 'http://127.0.0.1:8000',
      '/run-code': 'http://127.0.0.1:8000',
      '/raw-file': 'http://127.0.0.1:8000',
    }
  }
})
