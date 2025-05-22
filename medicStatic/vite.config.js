import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import path from 'path'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@configs': path.resolve(__dirname, './src/configs')
    },
  },
  optimizeDeps: {
    include: [
      'cropper/dist/cropper.css',
      'cropperjs'
    ],
    esbuildOptions: {
      supported: {
        'top-level-await': true // 启用顶级await支持
      }
    }
  },
  server: {
    hmr: {
      overlay: false
    }
  }
})
