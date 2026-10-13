import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// One classic script that registers with the page. React comes from the page
// (window.ComputeDeck), so it is not bundled.
export default defineConfig({
  plugins: [react()],
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    lib: {
      entry: fileURLToPath(new URL('./src/index.jsx', import.meta.url)),
      formats: ['iife'],
      name: 'ComputeDeckPlugin_computedeck_hello',
      fileName: () => 'index.js',
      cssFileName: 'index',
    },
    outDir: fileURLToPath(new URL('../src/computedeck_hello/web', import.meta.url)),
    emptyOutDir: true,
    rollupOptions: {
      external: ['react', 'react/jsx-runtime'],
      output: {
        globals: { react: 'ComputeDeck.React', 'react/jsx-runtime': 'ComputeDeck.jsxRuntime' },
      },
    },
  },
});
