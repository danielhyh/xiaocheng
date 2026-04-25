import { defineConfig } from 'vite'
// @ts-ignore
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/ws': {
        target: 'http://192.168.0.110:8000',
        ws: true,
      },
      '/api': {
        target: 'http://192.168.0.110:8000',
      },
      '/stream': {
        target: 'http://192.168.0.110:8000',
      },
    },
  },
})
