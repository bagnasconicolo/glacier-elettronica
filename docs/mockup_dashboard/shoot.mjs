// screenshot dei mock-up:  node shoot.mjs [pagina ...]
// three.js viene servito dai node_modules di hardware/render3d (stessa versione del CDN)
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import { execFileSync } from "node:child_process";
const here = path.dirname(new URL(import.meta.url).pathname);
const r3d = path.resolve(here, "../../hardware/render3d");
const require = createRequire(path.join(r3d, "package.json"));
const { chromium } = require("playwright-core");
const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".png": "image/png" };
const srv = http.createServer((q, r) => { const f = path.join(here, decodeURIComponent(q.url.split("?")[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { "Content-Type": types[path.extname(f)] || "application/octet-stream" }); r.end(d); }); }).listen(0);
const port = srv.address().port;
const pages = process.argv.slice(2).length ? process.argv.slice(2) : ["dashboard", "esperienze", "plateau", "poisson"];
const browser = await chromium.launch({ executablePath: process.env.CHROME || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
  args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
for (const p of pages) {
  const ctx = await browser.newContext({ viewport: { width: 1720, height: 1080 }, deviceScaleFactor: 1.5, ignoreHTTPSErrors: true });
  const page = await ctx.newPage();
  await page.route("https://cdn.jsdelivr.net/npm/three@0.160.0/**", rt => {
    const f = path.join(r3d, "node_modules/three", new URL(rt.request().url()).pathname.replace("/npm/three@0.160.0/", ""));
    rt.fulfill({ body: fs.readFileSync(f), contentType: "text/javascript" });
  });
  // font Google scaricati con curl (che usa il proxy dell'ambiente)
  await page.route(/fonts\.(googleapis|gstatic)\.com/, rt => {
    const u = rt.request().url();
    const body = execFileSync("curl", ["-s", "-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36", u], { maxBuffer: 1 << 26 });
    rt.fulfill({ body, contentType: u.includes("googleapis") ? "text/css" : "font/woff2", headers: { "Access-Control-Allow-Origin": "*" } });
  });
  page.on("response", x => { if (x.status() >= 400) console.log("[http]", x.status(), x.url()); });
  page.on("pageerror", e => console.log("[errore]", p, e.message));
  page.on("console", m => { if (m.type() === "error") console.log("[console]", p, m.text()); });
  await page.goto(`http://127.0.0.1:${port}/${p}.html`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 20000 }).catch(() => console.log("timeout", p));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(here, "screenshot_" + p + ".png"), fullPage: true });
  console.log("scritto screenshot_" + p + ".png");
  await ctx.close();
}
await browser.close(); srv.close();
