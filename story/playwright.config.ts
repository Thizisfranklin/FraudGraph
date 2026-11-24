import {defineConfig,devices} from "@playwright/test";
export default defineConfig({
 testDir:"./tests",
 timeout:30000,
 expect:{timeout:10000},
 retries:1,
 use:{baseURL:"http://127.0.0.1:4173",trace:"retain-on-failure"},
 webServer:{command:"npm run preview -- --host 127.0.0.1 --port 4173",url:"http://127.0.0.1:4173",reuseExistingServer:!process.env.CI,timeout:60000},
 projects:[{name:"chromium",use:{...devices["Desktop Chrome"]}}],
 reporter:"list"
});
