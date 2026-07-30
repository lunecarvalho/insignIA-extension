# InsignIA — Chrome Extension (TypeScript, Manifest V3)

This repository contains the TypeScript sources for the InsignIA Chrome extension (Manifest V3). Use `npm run build` to produce `dist/` artifacts.

Build:
```bash
npm install
npm run build
```

The `manifest.json` references `dist/background.js` and `dist/content.js`. The extension popup loads `dist/popup.js` from `popup.html`.
