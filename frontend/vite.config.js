import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { nodePolyfills } from 'vite-plugin-node-polyfills';

// Plugin to replace Node.js modules with browser stubs during SSR
const browserPolyfill = () => {
  return {
    name: 'browser-polyfill',
    resolveId(id) {
      // Intercept Vite's browser external modules and provide our own
      if (id === '__vite-browser-external') {
        return '\0vite-browser-external';
      }
      // Replace Node.js built-ins with virtual modules for SSR
      if (['stream', 'util', 'events', 'http', 'https', 'http2', 'crypto', 'zlib', 'fs', 'path', 'url', 'tty', 'assert'].includes(id)) {
        return '\0' + id;
      }
    },
    load(id) {
      // Handle Vite's browser external - provide all exports that might be needed
      if (id === '\0vite-browser-external') {
        return `
          // Browser polyfill for Node.js modules
          export const Readable = class {
            constructor() {}
          };
          export const Writable = class {
            constructor() {}
          };
          export const Transform = class {
            constructor() {}
          };
          export const Duplex = class {
            constructor() {}
          };
          export const EventEmitter = class {
            constructor() {}
            on() { return this; }
            emit() { return false; }
            once() { return this; }
            off() { return this; }
            removeListener() { return this; }
          };
          export const inspect = () => '';
          export const promisify = () => () => Promise.resolve();
          export default {};
        `;
      }
      // Provide exports that axios expects
      if (id === '\0stream') {
        return `
          export class Readable {
            constructor() {}
          }
          export class Writable {
            constructor() {}
          }
          export class Transform {
            constructor() {}
          }
          export class Duplex {
            constructor() {}
          }
          export default { Readable, Writable, Transform, Duplex };
        `;
      }
      if (id === '\0events') {
        return `
          export class EventEmitter {
            constructor() {}
            on() { return this; }
            emit() { return false; }
            once() { return this; }
            off() { return this; }
            removeListener() { return this; }
          }
          export default EventEmitter;
        `;
      }
      if (id === '\0util') {
        return `
          export function inspect() { return ''; }
          export function promisify() { return () => Promise.resolve(); }
          export default { inspect, promisify };
        `;
      }
      // Return empty exports for other Node.js built-ins
      if (id.startsWith('\0') && ['http', 'https', 'http2', 'crypto', 'zlib', 'fs', 'path', 'url', 'tty', 'assert'].includes(id.slice(1))) {
        return 'export default {}; export {};';
      }
    }
  };
};

export default defineConfig({
  plugins: [
    sveltekit(),
    nodePolyfills({
      include: ['stream', 'util', 'events'],
      globals: {
        Buffer: true,
        global: true,
        process: true
      }
    }),
    browserPolyfill()
  ],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  ssr: {
    noExternal: ['force-graph'],
    external: ['axios', 'stream', 'util', 'events', 'http', 'https', 'http2', 'crypto', 'zlib', 'fs', 'path', 'url', 'tty', 'assert'],
    resolve: {
      conditions: ['browser', 'import', 'module', 'default']
    }
  },
  resolve: {
    alias: [
      // Force axios to use browser code even in SSR - exact path matches
      {
        find: /^axios\/lib\/adapters\/http(\.js)?$/,
        replacement: 'axios/lib/adapters/xhr.js'
      },
      {
        find: /^axios\/lib\/platform\/node(\/index\.js)?$/,
        replacement: 'axios/lib/platform/browser/index.js'
      },
      {
        find: /^axios\/lib\/helpers\/formDataToStream(\.js)?$/,
        replacement: false
      }
    ]
  },
  optimizeDeps: {
    include: ['axios']
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'production'),
    global: 'globalThis'
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: undefined
      }
    }
  }
});

