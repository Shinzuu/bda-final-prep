// Layout check: loads index.html at phone and desktop widths in headless Chrome, reports any
// element wider than the viewport, opens every answer, and saves screenshots.
//   node test_layout.mjs [outdir]
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const out = resolve(process.argv[2] || "/tmp/claude-1000/layout");
mkdirSync(out, { recursive: true });
const url = "file://" + resolve(new URL(".", import.meta.url).pathname, "index.html");
const port = 9333;
const chrome = spawn("google-chrome-stable", ["--headless=new", "--disable-gpu", `--remote-debugging-port=${port}`,
  "--user-data-dir=/tmp/claude-1000/layout-profile", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let ws;
for (let i = 0; i < 50 && !ws; i++) {
  try {
    const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
    const page = list.find((t) => t.type === "page");
    ws = new WebSocket(page.webSocketDebuggerUrl);
  } catch { await sleep(200); }
}
await new Promise((r) => ws.addEventListener("open", r));
let id = 0;
const pending = new Map();
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
});
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expr) => (await send("Runtime.evaluate", { expression: expr, returnByValue: true })).result.result.value;

const CHECK = `(() => {
  document.body.classList.add('all');
  document.querySelectorAll('details').forEach(d => d.open = true);
  const W = document.documentElement.clientWidth, bad = [];
  for (const el of document.querySelectorAll('main *')) {
    if (el.closest('.tw, pre, .bar-in')) continue;
    const r = el.getBoundingClientRect();
    if (r.width && (r.right > W + 1 || r.left < -1)) bad.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right) + '>' + W + ' ' + (el.textContent||'').slice(0,50));
  }
  return { W, scrollW: document.documentElement.scrollWidth, bad: bad.slice(0, 15), nbad: bad.length,
           svgs: document.querySelectorAll('.dia svg').length, height: document.documentElement.scrollHeight };
})()`;

const results = {};
for (const [name, w, h, mobile] of [["phone", 390, 844, true], ["desktop", 1366, 900, false]]) {
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile });
  await send("Page.navigate", { url });
  await sleep(1500);
  results[name] = await evaluate(CHECK);
  for (const [i, frac] of [[0, 0], [1, 0.12], [2, 0.3]]) {
    await evaluate(`window.scrollTo(0, ${frac} * document.documentElement.scrollHeight)`);
    await sleep(200);
    const shot = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(`${out}/${name}-${i}.png`, Buffer.from(shot.result.data, "base64"));
  }
}
console.log(JSON.stringify(results, null, 1));
ws.close();
chrome.kill();
