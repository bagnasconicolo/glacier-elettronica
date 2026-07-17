// Esegue lo script della pagina con un DOM finto e serializza l'SVG #schem
const fs = require("fs");
const path = process.argv[2];
const src = fs.readFileSync(path, "utf8");
const a = src.indexOf("<script>") + 8, b = src.indexOf("</script>");
let js = src.slice(a, b);

// --- mini DOM ---
function El(tag) {
  return {
    tag, attrs: {}, children: [], textContent: "", dataset: {}, style: {},
    classList: { toggle(){}, add(){}, remove(){} },
    setAttribute(k, v) { this.attrs[k] = String(v); },
    getAttribute(k) { return this.attrs[k]; },
    appendChild(c) { this.children.push(c); return c; },
    addEventListener(){}, setPointerCapture(){},
    querySelector(sel) {
      const cls = sel.replace(".", "");
      const find = n => {
        for (const c of n.children) {
          if ((c.attrs.class || "").split(" ").includes(cls)) return c;
          const r = find(c); if (r) return r;
        }
        return null;
      };
      return find(this) || new El("stub");
    },
    querySelectorAll(){ return []; },
    getBoundingClientRect(){ return {top:0,left:0,width:1000,height:250}; },
    closest(){ return null; },
    get clientWidth(){ return 1000; },
  };
}
const registry = {};
const svgRoot = new El("svg");
svgRoot.attrs.id = "schem";
["schem","scope","chips","tip","npe","vth","spd","loop","npev","vthv","spdv",
 "launch","newmu","muLine","flash","ledGlow","cmpBody","trimmer","j2box","muTrack"]
 .forEach(id => { registry[id] = id === "schem" ? svgRoot : new El("div"); registry[id].attrs = registry[id].attrs||{}; registry[id].attrs.id=id; });
registry.npe.value = "180"; registry.vth.value = "100"; registry.spd.value = "8";
registry.loop.checked = false;
registry.scope.width = 1000; registry.scope.height = 250;
registry.scope.getContext = () => new Proxy({}, { get: () => () => {} });
registry.scope.getAttribute = k => k === "height" ? "250" : null;

global.document = {
  createElementNS: (ns, tag) => {
    const e = new El(tag);
    return e;
  },
  getElementById: id => {
    if (!registry[id]) registry[id] = new El("div");
    return registry[id];
  },
  createElement: tag => new El(tag),
  querySelectorAll: () => [],
  addEventListener(){},
};
global.window = { addEventListener(){}, devicePixelRatio: 1, innerWidth: 1200 };
global.requestAnimationFrame = () => {};
global.performance = { now: () => 0 };

// dopo la creazione via createElementNS, gli elementi con id vanno nel registry
const origCreate = global.document.createElementNS;
global.document.createElementNS = (ns, tag) => {
  const e = new El(tag);
  const origSet = e.setAttribute.bind(e);
  e.setAttribute = (k, v) => { origSet(k, v); if (k === "id") registry[v] = e; };
  return e;
};

try { eval(js); } catch (err) { console.error("ERRORE ESECUZIONE:", err.message); }

// --- serializza ---
const styles = `
.wire{stroke:#7f97d9;stroke-width:2;fill:none;stroke-linecap:round}
.wireglow{display:none}
.sym{stroke:#c9d4f6;stroke-width:2;fill:none;stroke-linecap:round}
.symfill{fill:#0d1430;stroke:#c9d4f6;stroke-width:2}
.lbl{fill:#9fb0dd;font-size:11px;font-family:monospace}
.lblv{fill:#ffd166;font-size:10.5px;font-family:monospace}
.gnd{stroke:#7688bb;stroke-width:2}
.probe text{font-family:monospace;font-size:11px;font-weight:700}
text{font-family:sans-serif}
`;
function ser(n) {
  if (n.tag === "stub") return "";
  const attrs = Object.entries(n.attrs).map(([k, v]) => `${k}="${String(v).replace(/&/g,"&amp;").replace(/"/g, "&quot;").replace(/</g,"&lt;")}"`).join(" ");
  const kids = n.children.map(ser).join("");
  const txt = String(n.textContent ?? "").replace(/&/g,"&amp;").replace(/</g, "&lt;");
  return `<${n.tag} ${attrs}>${txt}${kids}</${n.tag}>`;
}
const vb = svgRoot.attrs.viewBox || "0 0 1180 560";
const out = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb}" width="1770">
<rect x="-20" y="-20" width="1250" height="620" fill="#10172e"/>
<style>${styles}</style>
${svgRoot.children.map(ser).join("\n")}
</svg>`;
fs.writeFileSync("schem_check.svg", out);
console.log("scritto schem_check.svg,", svgRoot.children.length, "elementi top-level");
