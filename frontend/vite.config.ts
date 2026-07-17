import { defineConfig } from 'vite'
// @ts-ignore
import vue from '@vitejs/plugin-vue'
// @ts-ignore
import tailwindcss from '@tailwindcss/vite'
import { BACKEND_TARGET, DEV_SERVER_HOST, DEV_SERVER_PORT } from './dev.config'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    host: DEV_SERVER_HOST,
    port: DEV_SERVER_PORT,
    proxy: {
      '/ws': {
        target: BACKEND_TARGET,
        ws: true,
      },
      '/api': {
        target: BACKEND_TARGET,
      },
      '/stream': {
        target: BACKEND_TARGET,
      },
    },
  },
})
