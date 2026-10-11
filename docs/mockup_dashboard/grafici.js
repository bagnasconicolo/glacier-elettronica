// piccoli helper SVG per i mock-up (dati finti ma fisicamente plausibili)
function rng(seed){return function(){seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
function poisson(r,lam){let L=Math.exp(-lam),k=0,p=1;do{k++;p*=r()}while(p>L);return k-1}
function gauss(r){return Math.sqrt(-2*Math.log(r()+1e-12))*Math.cos(2*Math.PI*r())}
const NS="http://www.w3.org/2000/svg";
function el(tag,attrs,parent,txt){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(txt!=null)e.textContent=txt;if(parent)parent.appendChild(e);return e}
// assi + griglia: restituisce funzioni di scala
function assi(svg,o){
  const W=+svg.getAttribute("width"),H=+svg.getAttribute("height");svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
  const m=Object.assign({l:52,r:16,t:12,b:36},o.m||{});
  const pw=W-m.l-m.r,ph=H-m.t-m.b;
  const ly=o.logy;
  const fy=v=>{const a=ly?Math.log10(o.y0):o.y0,b=ly?Math.log10(o.y1):o.y1,x=ly?Math.log10(v):v;return m.t+ph-(x-a)/(b-a)*ph};
  const fx=v=>m.l+(v-o.x0)/(o.x1-o.x0)*pw;
  (o.yt||[]).forEach(v=>{el("line",{x1:m.l,x2:m.l+pw,y1:fy(v),y2:fy(v),stroke:"var(--grid)","stroke-width":1},svg);
    el("text",{x:m.l-8,y:fy(v)+4,"text-anchor":"end","font-size":11.5,fill:"var(--muted)"},svg,o.yf?o.yf(v):v)});
  (o.xt||[]).forEach(v=>{el("text",{x:fx(v),y:m.t+ph+18,"text-anchor":"middle","font-size":11.5,fill:"var(--muted)"},svg,o.xf?o.xf(v):v)});
  el("line",{x1:m.l,x2:m.l+pw,y1:m.t+ph,y2:m.t+ph,stroke:"#c9ccc8","stroke-width":1},svg);
  if(o.xl)el("text",{x:m.l+pw/2,y:H-4,"text-anchor":"middle","font-size":12,fill:"var(--ink2)"},svg,o.xl);
  if(o.yl)el("text",{x:14,y:m.t+ph/2,"text-anchor":"middle","font-size":12,fill:"var(--ink2)",transform:`rotate(-90 14 ${m.t+ph/2})`},svg,o.yl);
  return {fx,fy,m,pw,ph,W,H};
}
function linea(svg,pts,s,col,w=2){const d=pts.map((p,i)=>(i?"L":"M")+s.fx(p[0]).toFixed(1)+" "+s.fy(p[1]).toFixed(1)).join("");
  return el("path",{d,fill:"none",stroke:col,"stroke-width":w,"stroke-linejoin":"round","stroke-linecap":"round"},svg)}
