// Scena 3D del rivelatore: tre barre scintillanti con SiPM, scheda di lettura, Raspberry Pi,
// traccia del muone con i punti d'impatto e i fotoni di scintillazione.
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

const COL = { 1: 0x2f6fd6, 2: 0x179a7e, 3: 0xe08a32 };
const GLOW = { 1: 0x7fb2ff, 2: 0x4ff0c4, 3: 0xffb468, and: 0xf09cff };
const BAR = { L: 5.2, T: 0.24, W: 1.15 }, YB = { 1: 1.05, 2: 0, 3: -1.05 };

function bagliore() {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d"), r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  r.addColorStop(0, "rgba(255,255,255,1)"); r.addColorStop(.18, "rgba(255,255,255,.75)");
  r.addColorStop(.45, "rgba(255,255,255,.18)"); r.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c);
}

export function scena(canvas, o = {}) {
  const W = o.w || canvas.clientWidth, H = o.h || canvas.clientHeight, dpr = o.dpr || 1.5;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: !o.bg, preserveDrawingBuffer: true });
  renderer.setPixelRatio(dpr); renderer.setSize(W, H, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = o.exposure || 1.05;
  const scene = new THREE.Scene();
  if (o.bg) scene.background = new THREE.Color(o.bg);
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  const cam = new THREE.PerspectiveCamera(o.fov || 30, W / H, 0.1, 200);
  cam.position.set(...(o.cam || [7.5, 4.6, 10.5])); cam.lookAt(new THREE.Vector3(...(o.target || [0.9, -0.2, 0])));
  scene.add(new THREE.HemisphereLight(0xbcd0ff, 0x1a1408, 0.7));
  const key = new THREE.DirectionalLight(0xffffff, 1.6); key.position.set(4, 8, 6); scene.add(key);
  const rim = new THREE.DirectionalLight(0x8fa8ff, 1.0); rim.position.set(-6, 3, -5); scene.add(rim);
  const tex = bagliore();
  const hl = o.evidenzia;                          // canale da mettere in risalto (gli altri attenuati)
  const rig = new THREE.Group(); scene.add(rig);   // pila (si puo' inclinare)
  rig.rotation.z = THREE.MathUtils.degToRad(o.incl || 0);

  // --- stelle
  if (o.stelle !== false) {
    const n = 900, p = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { const v = new THREE.Vector3().randomDirection().multiplyScalar(60 + Math.random() * 30); p.set([v.x, Math.abs(v.y) * .8 + 2, v.z - 20], i * 3); }
    const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(p, 3));
    scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xcfd8ff, size: 0.22, transparent: true, opacity: .75 })));
  }
  // --- base e montanti in alluminio
  const alu = new THREE.MeshStandardMaterial({ color: 0xb9c0cc, metalness: .85, roughness: .32 });
  const base = new THREE.Mesh(new RoundedBoxGeometry(BAR.L + .9, .12, BAR.W + .9, 3, .04), new THREE.MeshStandardMaterial({ color: 0x2a3142, metalness: .4, roughness: .6 }));
  base.position.y = -1.75; rig.add(base);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(.045, .045, 3.5, 16), alu);
    m.position.set(sx * (BAR.L / 2 - .25), -.05, sz * (BAR.W / 2 + .2)); rig.add(m);
  }
  // --- barre, SiPM, cavi
  const anchors = {};
  for (const c of [1, 2, 3]) {
    const dim = hl && hl !== c;
    const mat = new THREE.MeshPhysicalMaterial({ color: COL[c], roughness: .28, metalness: 0, clearcoat: 1, clearcoatRoughness: .2,
      transparent: true, opacity: dim ? .28 : .62, emissive: COL[c], emissiveIntensity: dim ? .02 : (hl === c ? .35 : .12) });
    const bar = new THREE.Mesh(new RoundedBoxGeometry(BAR.L, BAR.T, BAR.W, 3, .03), mat); bar.position.y = YB[c]; rig.add(bar);
    const ed = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(BAR.L, BAR.T, BAR.W)),
      new THREE.LineBasicMaterial({ color: GLOW[c], transparent: true, opacity: dim ? .25 : .9 }));
    ed.position.y = YB[c]; rig.add(ed);
    // scheda del SiPM all'estremita' +x
    const sp = new THREE.Mesh(new THREE.BoxGeometry(.05, .5, .5), new THREE.MeshStandardMaterial({ color: 0x0d5c36, roughness: .5 }));
    sp.position.set(BAR.L / 2 + .03, YB[c], 0); rig.add(sp);
    const chip = new THREE.Mesh(new THREE.BoxGeometry(.03, .14, .14), new THREE.MeshStandardMaterial({ color: 0x222831, metalness: .3, roughness: .3 }));
    chip.position.set(BAR.L / 2 + .07, YB[c], 0); rig.add(chip);
    const kk = new THREE.Mesh(new THREE.BoxGeometry(.12, .12, .22), new THREE.MeshStandardMaterial({ color: 0xf2f0ea, roughness: .6 }));
    kk.position.set(BAR.L / 2 + .12, YB[c] - .14, 0); rig.add(kk);
    anchors["bar" + c] = new THREE.Vector3(-BAR.L / 2 - .1, YB[c], BAR.W / 2);
    anchors["sipm" + c] = new THREE.Vector3(BAR.L / 2 + .1, YB[c] + .3, 0);
    if (o.pcb !== false) {
      const curve = new THREE.CatmullRomCurve3([new THREE.Vector3(BAR.L / 2 + .18, YB[c] - .14, 0), new THREE.Vector3(BAR.L / 2 + .7, YB[c] - .3, .1 * c),
        new THREE.Vector3(BAR.L / 2 + 1.1, -1.55, .3 - .3 * c + .3), new THREE.Vector3(BAR.L / 2 + 1.3, -1.62, -.35 + .3 * c)]);
      rig.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 40, .03, 8), new THREE.MeshStandardMaterial({ color: 0x15171c, roughness: .5 })));
    }
  }
  // --- scheda di lettura (103 x 224 mm in scala) e Raspberry Pi
  const leds = {};
  if (o.pcb !== false) {
    const pcb = new THREE.Group(); pcb.position.set(BAR.L / 2 + 2.15, -1.62, .05); rig.add(pcb);
    pcb.add(new THREE.Mesh(new RoundedBoxGeometry(1.03, .05, 2.24, 2, .01), new THREE.MeshStandardMaterial({ color: 0x0f6b3e, roughness: .45, metalness: .1 })));
    const ic = new THREE.MeshStandardMaterial({ color: 0x1b1d22, roughness: .4 });
    for (let i = 0; i < 14; i++) { const m = new THREE.Mesh(new THREE.BoxGeometry(.08 + (i % 3) * .03, .03, .1), ic); m.position.set(-.35 + (i % 5) * .17, .04, -.9 + Math.floor(i / 5) * .55); pcb.add(m); }
    for (const c of [1, 2, 3]) {
      const on = (o.accesi || [1, 2, 3]).includes(c);
      const led = new THREE.Mesh(new THREE.SphereGeometry(.035, 12, 8), new THREE.MeshBasicMaterial({ color: on ? 0xff4d3a : 0x5a1a14 }));
      led.position.set(.38, .05, -.7 + (c - 1) * .55); pcb.add(led); leds[c] = led;
      if (on) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, color: 0xff5a40, blending: THREE.AdditiveBlending, depthWrite: false })); s.scale.setScalar(.35); s.position.copy(led.position); pcb.add(s); }
      const lemo = new THREE.Mesh(new THREE.CylinderGeometry(.05, .05, .16, 16), alu); lemo.rotation.z = Math.PI / 2; lemo.position.set(.56, .05, -.7 + (c - 1) * .55); pcb.add(lemo);
    }
    anchors.pcb = new THREE.Vector3(BAR.L / 2 + 2.15, -1.5, -1.1);
    const pi = new THREE.Mesh(new RoundedBoxGeometry(.85, .05, .56, 2, .01), new THREE.MeshStandardMaterial({ color: 0x1f8a4c, roughness: .45 }));
    pi.position.set(BAR.L / 2 + 2.15, -1.62, 1.75); rig.add(pi);
    const soc = new THREE.Mesh(new THREE.BoxGeometry(.18, .04, .18), new THREE.MeshStandardMaterial({ color: 0xc9ccd2, metalness: .9, roughness: .25 }));
    soc.position.set(BAR.L / 2 + 2.05, -1.58, 1.72); rig.add(soc);
    anchors.pi = new THREE.Vector3(BAR.L / 2 + 2.15, -1.5, 2.05);
  }
  // --- tracce dei muoni
  const glow = (pos, col, s) => { const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, color: col, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); sp.position.copy(pos); sp.scale.setScalar(s); rig.add(sp); return sp; };
  for (const t of (o.tracce || [])) {
    const th = THREE.MathUtils.degToRad(t.theta || 0), ph = THREE.MathUtils.degToRad(t.phi || 0);
    const dir = new THREE.Vector3(Math.sin(th) * Math.cos(ph), -Math.cos(th), Math.sin(th) * Math.sin(ph));
    const p0 = new THREE.Vector3(t.x || 0, 0, t.z || 0);       // punto alla quota della barra 2
    const top = p0.clone().addScaledVector(dir, -(t.su || 9)), bot = p0.clone().addScaledVector(dir, t.giu || 2.2);
    const a = t.alpha ?? 1, len = top.distanceTo(bot);
    const mk = (r, col, op) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 10, 1, true), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: op, blending: THREE.AdditiveBlending, depthWrite: false }));
      m.position.copy(top.clone().add(bot).multiplyScalar(.5)); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().negate()); rig.add(m); };
    mk(.012, 0xffffff, .95 * a); mk(.045, GLOW.and, .35 * a); mk(.11, GLOW.and, .08 * a);
    for (const c of [1, 2, 3]) {
      if (t.hits && !t.hits[c - 1]) continue;
      const k = YB[c] / -dir.y, hp = p0.clone().addScaledVector(dir, -k);
      if (Math.abs(hp.x) > BAR.L / 2 || Math.abs(hp.z) > BAR.W / 2) continue;
      glow(hp, GLOW[c], (t.main ? 1.15 : .6) * a); glow(hp, 0xffffff, (t.main ? .3 : .16) * a);
      if (t.main && t.fotoni !== false) {                     // fotoni di scintillazione verso il SiPM (+x)
        for (let j = 0; j < 7; j++) {
          const pts = [hp.clone()]; let p = hp.clone(), zz = (Math.random() - .5) * BAR.W, sgn = 1;
          for (let s = 0; s < 5; s++) { p = p.clone(); p.x += (BAR.L / 2 - hp.x) / 5; zz = -zz * .9 + (Math.random() - .5) * .25; p.z = Math.max(-BAR.W / 2 + .05, Math.min(BAR.W / 2 - .05, zz)); p.y = YB[c] + sgn * (BAR.T / 2 - .03); sgn = -sgn; pts.push(p); }
          const g = new THREE.BufferGeometry().setFromPoints(pts);
          rig.add(new THREE.Line(g, new THREE.LineBasicMaterial({ color: GLOW[c], transparent: true, opacity: .55, blending: THREE.AdditiveBlending })));
        }
        glow(new THREE.Vector3(BAR.L / 2 + .07, YB[c], 0), GLOW[c], .55);
      }
    }
    if (t.main) anchors.muone = top.clone().lerp(p0, .82);
  }
  // --- sciame: tracce secondarie lontane, molto deboli
  if (o.sciame) for (let i = 0; i < 26; i++) {
    const a = new THREE.Vector3(o.sciame[0] + (Math.random() - .5) * .6, 16, o.sciame[1] - 4), b = new THREE.Vector3((Math.random() - .5) * 18, -2.5, (Math.random() - .5) * 10 - 2);
    rig.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([a, b]), new THREE.LineBasicMaterial({ color: 0x9fb0ff, transparent: true, opacity: .1 + Math.random() * .12, blending: THREE.AdditiveBlending })));
  }
  // --- render con bagliore
  const comp = new EffectComposer(renderer); comp.setPixelRatio(dpr); comp.setSize(W, H);
  comp.addPass(new RenderPass(scene, cam));
  if (o.bloom !== false) comp.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), o.bloomStr ?? .75, .55, .55));
  comp.addPass(new OutputPass());
  comp.render();
  scene.updateMatrixWorld(true);
  const proietta = v => { const w = rig.localToWorld(v.clone()).project(cam); return [(w.x + 1) / 2 * W, (1 - w.y) / 2 * H]; };
  const out = {}; for (const k in anchors) out[k] = proietta(anchors[k]);
  window.__scene = (window.__scene || 0) + 1;
  return { anchors: out, renderer };
}
