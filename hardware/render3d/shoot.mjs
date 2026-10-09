// Foto della scheda montata con Chromium headless (WebGL software).
//   node shoot.mjs 1ch iso top front detail
import { chromium } from "playwright-core";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";

const [variant = "1ch", ...views] = process.argv.slice(2);
const VIEWS = views.length ? views : ["iso", "top", "front", "detail"];
const root = path.dirname(new URL(import.meta.url).pathname);
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".png": "image/png" };
const srv = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split("?")[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; }
    r.writeHead(200, { "Content-Type": types[path.extname(f)] || "application/octet-stream" }); r.end(d); });
}).listen(0);
const port = srv.address().port;
const exe = process.env.CHROME || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const browser = await chromium.launch({ executablePath: exe, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const W = 2000, H = 1250;
for (const v of VIEWS) {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on("console", m => { if (m.type() !== "log") console.log("[page]", m.text()); });
  await page.goto(`http://localhost:${port}/viewer.html?v=${variant}&view=${v}&w=${W}&h=${H}`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  await page.waitForTimeout(2500);
  const out = path.join(root, "out", variant, `render_${v}.png`);
  await page.screenshot({ path: out });
  console.log("scritto", out);
  await page.close();
}
await browser.close(); srv.close();
