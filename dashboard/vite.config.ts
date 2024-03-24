import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import {fileURLToPath} from "node:url";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@/src": fileURLToPath(new URL("./src", import.meta.url)),
        },
    },
    base: process.env.VITE_URL_BASE_NAME
})
