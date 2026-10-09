# -*- coding: utf-8 -*-
"""Esporta la scena 3D della scheda montata: texture della faccia superiore
(maschera verde, piste, pad stagnati, serigrafia) + elenco dei componenti
con posizione, rotazione e tipo di package. La disegna viewer.html (three.js).

    python scene.py 1ch   ->  out/1ch/scene.json + out/1ch/top.png
    python scene.py 3ch   ->  out/3ch/scene.json + out/3ch/top.png
    python scene.py 3ch nero  ->  out/3ch/top_nero.png (maschera nera)
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "generator")
sys.path.insert(0, GEN)

variant = sys.argv[1] if len(sys.argv) > 1 else "1ch"
if variant == "3ch":
    import netdata3
    sys.modules["netdata"] = netdata3
    import pcb_data as PD
    import pcb_data3 as P3
    PD.BOARD = P3.BOARD
    PD.PLACEMENT.clear()
    PD.PLACEMENT.update(P3.PLACEMENT)
    STATE = os.path.join(GEN, "riv_cosmici_3ch", "routing_state.json")
    TITLE = "Riv. Cosmici - 3 canali + coincidenza"
else:
    import pcb_data as PD
    STATE = os.path.join(GEN, "routing_state.json")
    TITLE = "Riv. Cosmici - 1 canale"
from footprints import FPS                       # noqa: E402

PX = 20                    # pixel per mm della texture
OUT = os.path.join(HERE, "out", variant)
os.makedirs(OUT, exist_ok=True)
X1, Y1, X2, Y2 = PD.BOARD
st = json.load(open(STATE))
pads = PD.abs_pads()

# colore della maschera: verde (default) o nero  ->  python scene.py 3ch nero
BLACK = "nero" in sys.argv[2:]
MASK = "#141414" if BLACK else "#1e6b3c"
TRACK = "#242424" if BLACK else "#2f8d50"
COPPER = "#d9d6cc"         # HASL
SILK_C = "#f4f4ee"


def tx(x):
    return (x - X1) * PX


def ty(y):
    return (y - Y1) * PX


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{(X2 - X1) * PX:.0f}" '
       f'height="{(Y2 - Y1) * PX:.0f}">',
       f'<rect width="100%" height="100%" fill="{MASK}"/>']
for t in st["tracks"]:
    if t["layer"] != "F.Cu":
        continue
    pts = " ".join(f"{tx(x):.1f},{ty(y):.1f}" for x, y in t["pts"])
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{TRACK}" '
               f'stroke-width="{t["w"] * PX:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
for v in st["vias"]:
    svg.append(f'<circle cx="{tx(v["x"]):.1f}" cy="{ty(v["y"]):.1f}" r="{0.4 * PX:.1f}" fill="{TRACK}"/>')
    svg.append(f'<circle cx="{tx(v["x"]):.1f}" cy="{ty(v["y"]):.1f}" r="{0.2 * PX:.1f}" fill="#0b2a16"/>')
for p in pads:
    w, h = p["w"], p["h"]
    if p["rot"] % 180 != 0:
        w, h = h, w
    if p["kind"] == "tht" and abs(w - h) < 1e-6:
        svg.append(f'<circle cx="{tx(p["x"]):.1f}" cy="{ty(p["y"]):.1f}" r="{w / 2 * PX:.1f}" fill="{COPPER}"/>')
    else:
        svg.append(f'<rect x="{tx(p["x"] - w / 2):.1f}" y="{ty(p["y"] - h / 2):.1f}" '
                   f'width="{w * PX:.1f}" height="{h * PX:.1f}" rx="{0.15 * PX:.1f}" fill="{COPPER}"/>')
    if p["kind"] != "smd":
        svg.append(f'<circle cx="{tx(p["x"]):.1f}" cy="{ty(p["y"]):.1f}" r="{p["drill"] / 2 * PX:.1f}" fill="#111"/>')
# serigrafia: contorni dei footprint + riferimenti (o la serigrafia didattica, se c'e')
SILK = os.path.join(os.path.dirname(STATE), "silk.json") if variant == "3ch" else None
silk = json.load(open(SILK)) if SILK and os.path.exists(SILK) else None
if silk:
    for ring in silk["F.SilkS"]:
        pts = " ".join(f"{tx(x):.1f},{ty(y):.1f}" for x, y in ring)
        svg.append(f'<polygon points="{pts}" fill="{SILK_C}"/>')
for ref, (x, y, rot) in PD.PLACEMENT.items():
    fp = FPS[PD.FP_OF[PD.COMPONENTS[ref][2]]]
    for (sx1, sy1, sx2, sy2) in fp.silk:
        a = PD.rot_delta(sx1, sy1, rot)
        b = PD.rot_delta(sx2, sy2, rot)
        svg.append(f'<line x1="{tx(x + a[0]):.1f}" y1="{ty(y + a[1]):.1f}" x2="{tx(x + b[0]):.1f}" '
                   f'y2="{ty(y + b[1]):.1f}" stroke="{SILK_C}" stroke-width="{0.15 * PX:.1f}"/>')
    if silk:
        continue
    cy1 = fp.courtyard[1]
    lx, ly = PD.rot_delta(0, cy1 - 0.5, rot)
    svg.append(f'<text x="{tx(x + lx):.1f}" y="{ty(y + ly):.1f}" font-family="DejaVu Sans, Arial" '
               f'font-size="{0.9 * PX:.1f}" fill="{SILK_C}" text-anchor="middle">{ref}</text>')
if not silk:
  svg.append(f'<text x="{tx(X1 + 2):.1f}" y="{ty(Y2 - 1.2):.1f}" font-family="DejaVu Sans, Arial" '
           f'font-size="{1.4 * PX:.1f}" fill="{SILK_C}">{TITLE} - CERN-OHL-W-2.0</text>')
svg.append("</svg>")
TOPNAME = "top_nero" if BLACK else "top"
open(os.path.join(OUT, TOPNAME + ".svg"), "w").write("\n".join(svg))
import cairosvg                                   # noqa: E402
cairosvg.svg2png(url=os.path.join(OUT, TOPNAME + ".svg"), write_to=os.path.join(OUT, TOPNAME + ".png"))

comps = []
for ref, (x, y, rot) in PD.PLACEMENT.items():
    kind, value, fpk, _e = PD.COMPONENTS[ref]
    comps.append(dict(ref=ref, kind=kind, value=value, fp=PD.FP_OF[fpk],
                      x=x, y=y, rot=math.radians(rot)))
json.dump(dict(board=[X1, Y1, X2, Y2], thickness=1.6, title=TITLE, comps=comps),
          open(os.path.join(OUT, "scene.json"), "w"), indent=1)
print(f"{OUT}: {len(comps)} componenti, texture {(X2 - X1) * PX:.0f}x{(Y2 - Y1) * PX:.0f} px")
