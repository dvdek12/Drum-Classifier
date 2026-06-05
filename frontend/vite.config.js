import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/upload-batch': 'http://localhost:8000',
      '/upload': 'http://localhost:8000',
      '/files': 'http://localhost:8000',
      '/dataset': 'http://localhost:8000',
      '/train': 'http://localhost:8000',
      '/tree': 'http://localhost:8000',
      '/predict': 'http://localhost:8000',
      '/export': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    }
  }
})
