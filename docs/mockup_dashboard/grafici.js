// helper SVG per i mock-up (dati finti ma fisicamente plausibili)
function rng(seed){return function(){seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
function poisson(r,lam){if(lam>40)return Math.max(0,Math.round(lam+Math.sqrt(lam)*gauss(r)));let L=Math.exp(-lam),k=0,p=1;do{k++;p*=r()}while(p>L);return k-1}
function gauss(r){return Math.sqrt(-2*Math.log(r()+1e-12))*Math.cos(2*Math.PI*r())}
const NS="http://www.w3.org/2000/svg";
function el(tag,attrs,parent,txt){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(txt!=null)e.textContent=txt;if(parent)parent.appendChild(e);return e}
const fmt=(v,d=0)=>v.toLocaleString("it-IT",{minimumFractionDigits:d,maximumFractionDigits:d});
let _gid=0;
function grad(svg,col,a0=.28,a1=0){let defs=svg.querySelector("defs")||el("defs",{},svg);const id="g"+(++_gid);
  const g=el("linearGradient",{id,x1:0,y1:0,x2:0,y2:1},defs);el("stop",{offset:0,"stop-color":col,"stop-opacity":a0},g);el("stop",{offset:1,"stop-color":col,"stop-opacity":a1},g);return `url(#${id})`}
// assi: griglia orizzontale tratteggiata, niente cornice
function assi(svg,o){
  const W=+svg.getAttribute("width"),H=+svg.getAttribute("height");svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
  const m=Object.assign({l:46,r:14,t:14,b:34},o.m||{});if(o.yl)m.t=Math.max(m.t,30);const pw=W-m.l-m.r,ph=H-m.t-m.b;const ly=o.logy;
  const tr=v=>ly?Math.log10(v):v;
  const fy=v=>m.t+ph-(tr(v)-tr(o.y0))/(tr(o.y1)-tr(o.y0))*ph;
  const fx=v=>m.l+(v-o.x0)/(o.x1-o.x0)*pw;
  const g=el("g",{},svg);
  (o.yt||[]).forEach(v=>{el("line",{x1:m.l,x2:m.l+pw,y1:fy(v),y2:fy(v),stroke:"var(--grid)","stroke-width":1,"stroke-dasharray":v===o.y0?"":"2 4"},g);
    el("text",{x:m.l-10,y:fy(v)+4,"text-anchor":"end","font-size":11.5,fill:"var(--muted)",class:"n"},g,o.yf?o.yf(v):v)});
  (o.xt||[]).forEach(v=>{el("line",{x1:fx(v),x2:fx(v),y1:m.t+ph,y2:m.t+ph+4,stroke:"#cfc8b8"},g);
    el("text",{x:fx(v),y:m.t+ph+18,"text-anchor":"middle","font-size":11.5,fill:"var(--muted)",class:"n"},g,o.xf?o.xf(v):v)});
  el("line",{x1:m.l,x2:m.l+pw,y1:m.t+ph,y2:m.t+ph,stroke:"#cfc8b8","stroke-width":1},g);
  if(o.xl)el("text",{x:m.l+pw,y:H-3,"text-anchor":"end","font-size":12,fill:"var(--ink2)"},g,o.xl);
  if(o.yl)el("text",{x:m.l-10,y:m.t-12,"text-anchor":"start","font-size":12,fill:"var(--ink2)"},g,o.yl);
  return {fx,fy,m,pw,ph,W,H};
}
// curva liscia (Catmull-Rom -> Bezier)
function percorso(pts,s){const P=pts.map(p=>[s.fx(p[0]),s.fy(p[1])]);if(P.length<3)return "M"+P.map(p=>p.join(" ")).join("L");
  let d=`M${P[0][0].toFixed(1)} ${P[0][1].toFixed(1)}`;
  for(let i=0;i<P.length-1;i++){const p0=P[i-1]||P[i],p1=P[i],p2=P[i+1],p3=P[i+2]||p2;const k=6;
    d+=`C${(p1[0]+(p2[0]-p0[0])/k).toFixed(1)} ${(p1[1]+(p2[1]-p0[1])/k).toFixed(1)},${(p2[0]-(p3[0]-p1[0])/k).toFixed(1)} ${(p2[1]-(p3[1]-p1[1])/k).toFixed(1)},${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`}
  return d}
function linea(svg,pts,s,col,w=2,extra={}){return el("path",Object.assign({d:percorso(pts,s),fill:"none",stroke:col,"stroke-width":w,"stroke-linejoin":"round","stroke-linecap":"round"},extra),svg)}
function area(svg,pts,s,col,a0=.25){const d=percorso(pts,s)+`L${s.fx(pts[pts.length-1][0])} ${s.fy(s.base??0)}L${s.fx(pts[0][0])} ${s.fy(s.base??0)}Z`;return el("path",{d,fill:grad(svg,col,a0,0),stroke:"none"},svg)}
function banda(svg,lo,hi,s,col,op=.14){const d=percorso(hi,s)+"L"+percorso([...lo].reverse(),s).slice(1);return el("path",{d,fill:col,opacity:op},svg)}
// etichetta con linea di richiamo
function nota(svg,x,y,dx,dy,txt,sub,anchor="start"){const g=el("g",{},svg);
  el("path",{d:`M${x} ${y}L${x+dx*.35} ${y+dy}L${x+dx} ${y+dy}`,fill:"none",stroke:"var(--ink2)","stroke-width":1},g);
  el("circle",{cx:x,cy:y,r:3,fill:"var(--ink)"},g);
  const tx=x+dx+(anchor=="start"?6:-6);el("text",{x:tx,y:y+dy+4,"text-anchor":anchor,"font-size":12.5,"font-weight":600,fill:"var(--ink)"},g,txt);
  if(sub)el("text",{x:tx,y:y+dy+19,"text-anchor":anchor,"font-size":11.5,fill:"var(--muted)"},g,sub);return g}
// barre di istogramma arrotondate in alto, ancorate alla base
function barra(svg,x,y0,w,y1,col,op=1){const h=Math.max(0,y0-y1),r=Math.min(4,w/2,h);
  return el("path",{d:`M${x} ${y0}V${y1+r}Q${x} ${y1} ${x+r} ${y1}H${x+w-r}Q${x+w} ${y1} ${x+w} ${y1+r}V${y0}Z`,fill:col,opacity:op},svg)}
