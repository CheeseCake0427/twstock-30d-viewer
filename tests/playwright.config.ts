import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.ts',
  timeout: 30_000,
  use: {
    baseURL: 'http://localhost:5173',
  },
  /* 啟動前後端 */
  webServer: [
    {
      command: 'cd ../backend && python -m uvicorn main:app --port 8082',
      port: 8082,
      reuseExistingServer: true,
    },
    {
      command: 'cd ../frontend && npm run dev',
      port: 5173,
      reuseExistingServer: true,
    },
  ],
})
