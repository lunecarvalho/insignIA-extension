import { build } from 'esbuild';
import { mkdirSync } from 'fs';

mkdirSync('dist', { recursive: true });

async function buildAll() {
  await build({
    entryPoints: ['src/background.ts'],
    bundle: true,
    outfile: 'dist/background.js',
    platform: 'browser',
    target: ['es2020'],
    charset: 'utf8'
  });

  await build({
    entryPoints: ['src/content.ts'],
    bundle: true,
    outfile: 'dist/content.js',
    platform: 'browser',
    target: ['es2020'],
    charset: 'utf8'
  });

  await build({
    entryPoints: ['src/popup.ts'],
    bundle: true,
    outfile: 'dist/popup.js',
    platform: 'browser',
    target: ['es2020'],
    charset: 'utf8'
  });
}

buildAll().catch((e) => {
  console.error(e);
  process.exit(1);
});
