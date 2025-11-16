import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { nodePolyfills } from 'vite-plugin-node-polyfills';

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
		})
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
		noExternal: ['force-graph']
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

