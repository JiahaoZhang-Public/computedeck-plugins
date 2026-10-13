import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    lib: {
      entry: fileURLToPath(new URL('./web/entry.ts', import.meta.url)),
      formats: ['iife'],
      name: 'ComputeDeckNetwork',
      fileName: () => 'index.js',
      cssFileName: 'index',
    },
    outDir: 'network/src/computedeck_network/web',
    emptyOutDir: true,
    rollupOptions: {
      external: ['react', 'react/jsx-runtime'],
      output: {
        globals: { react: 'ComputeDeck.React', 'react/jsx-runtime': 'ComputeDeck.jsxRuntime' },
      },
    },
  },
});
