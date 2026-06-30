import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/api': {
        // 代理后端 API 到后端服务（后端当前运行在 8001）
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
