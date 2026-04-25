import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// File watching is set to polling because the project lives on a
// WSL-mounted Windows drive where native fs.watch() throws EISDIR.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
})
