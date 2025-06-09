import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    optimizeDeps: {
        exclude: ['lucide-react'],
    },
    server: {
        port: 3000,
    },
    define: {
        'process.env.NODE_ENV': JSON.stringify(
            process.env.NODE_ENV || 'development'
        ),
        'process.env': JSON.stringify({
            NODE_ENV: process.env.NODE_ENV || 'development',
        }),
        global: 'globalThis',
    },
    resolve: {
        alias: {
            process: 'process/browser',
        },
    },
});
