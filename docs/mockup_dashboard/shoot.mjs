// screenshot dei mock-up:  node shoot.mjs   (usa playwright-core di hardware/render3d)
import { createRequire } from "node:module";
import path from "node:path";
const require = createRequire(path.resolve("../../hardware/render3d/package.json"));
const { chromium } = require("playwright-core");
const here = path.dirname(new URL(import.meta.url).pathname);
const pages = process.argv.slice(2).length ? process.argv.slice(2) : ["dashboard", "esperienze", "plateau", "poisson"];
const browser = await chromium.launch({ executablePath: process.env.CHROME || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
for (const p of pages) {
  const page = await browser.newPage({ viewport: { width: 1720, height: 1080 }, deviceScaleFactor: 1.5 });
  page.on("pageerror", e => console.log("[errore]", p, e.message));
  await page.goto("file://" + path.join(here, p + ".html"));
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(here, "screenshot_" + p + ".png"), fullPage: true });
  console.log("scritto screenshot_" + p + ".png");
}
await browser.close();
