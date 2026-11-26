import path from 'node:path';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export const API_ORIGIN = 'http://127.0.0.1:8780';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [{ find: /^@\//, replacement: `${path.join(import.meta.dirname, 'src')}/` }],
  },
  server: {
    port: 5180,
    strictPort: true,
    proxy: { '/api': API_ORIGIN },
  },
});
