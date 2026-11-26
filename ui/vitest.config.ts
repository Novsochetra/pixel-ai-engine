import path from 'node:path';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

const suite = (name: string) => ({
  extends: true,
  test: { name, include: [`test/${name}/**/*.test.{ts,tsx}`] },
});

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [{ find: /^@\//, replacement: `${path.join(import.meta.dirname, 'src')}/` }],
  },
  test: {
    environment: 'happy-dom',
    projects: [suite('unit'), suite('integration'), suite('regression')],
    passWithNoTests: true,
  },
});
