import { defineConfig } from 'vite';
import { writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { execSync } from 'node:child_process';
import type { OutputOptions } from 'rollup';

import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

function generateHash() {
  const data = { hash: execSync('git rev-parse HEAD').toString().trim() };

  return {
    name: 'generate-build-hash',
    writeBundle(options: OutputOptions) {
      const outputDir = options.dir || 'dist';
      const filePath = join(outputDir, 'build.json');

      writeFileSync(filePath, JSON.stringify(data, null, 2));
    },
  };
}

export default defineConfig({
  build: { manifest: true },
  server: { port: 3333 },

  plugins: [generateHash(), tailwindcss(), react()],

  define: {
    'import.meta.env.VITE_BUILD_HASH': JSON.stringify(
      execSync('git rev-parse HEAD').toString().trim(),
    ),
  },

  resolve: {
    alias: {
      '@': resolve('src'),
      '@worker': resolve('worker'),
      '#': resolve('src/components'),
    },
  },
});
