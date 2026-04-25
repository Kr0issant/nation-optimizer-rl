import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// File watching is set to polling because the project lives on a
// WSL-mounted Windows drive where native fs.watch() throws EISDIR.
//
// `/api/*` is proxied to the FastAPI server in `server/visualizer_server.py`.
// SSE works through Vite's proxy as long as we disable buffering.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    watch: {
      usePolling: true,
      interval: 300,
    },
    proxy: {
      '/api': {
        target: process.env.VIZ_BACKEND_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
        ws: false,
        // Disable response buffering so SSE chunks arrive immediately.
        configure: proxy => {
          proxy.on('proxyRes', (proxyRes, req) => {
            if (req.url?.endsWith('/stream')) {
              proxyRes.headers['cache-control'] = 'no-cache, no-transform'
              proxyRes.headers['x-accel-buffering'] = 'no'
            }
          })
        },
      },
    },
  },
})
