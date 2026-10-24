import { defineConfig } from 'vite';

export default defineConfig({
  base: '/', // served at https://circulatorysensing.com (custom domain on GitHub Pages)
  build: {
    rollupOptions: {
      input: {
        main: './index.html',
        circulation: './circulation/index.html',
        system: './circulation/system.html',
        sim: './circulation/sim.html',
        log: './circulation/log.html',
        manual: './circulation/manual.html',
        design: './circulation/design.html',
        toolkit: './circulation/toolkit.html',
        brand: './brand/index.html',
      },
    },
  },
});
