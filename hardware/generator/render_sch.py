# -*- coding: utf-8 -*-
"""Render SVG dello schema per controllo visivo (usa gli stessi dati di gen_sch)."""
import re
import gen_sch as G
from symlib import SYMS

def tf(x, y, rot, mirror, px, py):
    return G.pin_sheet_pos(None, x, y, rot, mirror, px, py)

svg = []
def line(a, b, col="#008000", w2=0.25):
    svg.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{col}" stroke-width="{w2}"/>')
def text(s, x, y, size=1.6, col="#000", anchor="start"):
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-family="monospace">{s}</text>')
def circle(c, r, col="#800000", fill="none", w2=0.25):
    svg.append(f'<circle cx="{c[0]}" cy="{c[1]}" r="{r}" stroke="{col}" fill="{fill}" stroke-width="{w2}"/>')

# fili
for a, b in G.wires:
    line(a, b)
for x, y in G.junctions:
    circle((x, y), 0.5, col="none", fill="#008000")
for name, x, y in G.labels:
    text(name, x + 0.5, y - 0.3, col="#a05000")
for s, x, y in G.texts:
    text(s, x, y, size=2.2, col="#404040")
for x, y in G.noconn:
    line((x - 0.6, y - 0.6), (x + 0.6, y + 0.6), col="#0000c0")
    line((x - 0.6, y + 0.6), (x + 0.6, y - 0.6), col="#0000c0")
for net, x, y, rot in G.powers:
    circle((x, y), 0.4, col="#c00000")
    text(net, x + 0.6, y - 0.6, size=1.2, col="#c00000")

NUM = re.compile(r"-?\d+\.?\d*")
for ref, symname, x, y, rot, mirror, value, fp in G.instances:
    s = SYMS[symname]
    # corpo: interpreta le s-expr base
    for b in s.body:
        nums = [float(v) for v in NUM.findall(b)]
        if b.startswith("(rectangle"):
            x1, y1, x2, y2 = nums[:4]
            pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
            pp = [tf(x, y, rot, mirror, px, py) for px, py in pts]
            for a2, b2 in zip(pp, pp[1:]):
                line(a2, b2, col="#800000")
        elif b.startswith("(polyline"):
            coords = nums[:-4] if "(width" in b else nums
            # nums include anche width: prendi coppie fino a numero pari di xy
            m = re.search(r"\(pts (.*?)\)\s*\(stroke", b)
            xy = [float(v) for v in NUM.findall(m.group(1))]
            pts = list(zip(xy[0::2], xy[1::2]))
            pp = [tf(x, y, rot, mirror, px, py) for px, py in pts]
            for a2, b2 in zip(pp, pp[1:]):
                line(a2, b2, col="#800000")
        elif b.startswith("(circle"):
            cx, cy, r = nums[:3]
            circle(tf(x, y, rot, mirror, cx, cy), r, col="#800000")
        elif b.startswith("(arc"):
            sx, sy, mx, my, ex, ey = nums[:6]
            pp = [tf(x, y, rot, mirror, px, py) for px, py in ((sx, sy), (mx, my), (ex, ey))]
            for a2, b2 in zip(pp, pp[1:]):
                line(a2, b2, col="#800000")
        elif b.startswith("(text"):
            m = re.match(r'\(text "([^"]*)" \(at ([-\d.]+) ([-\d.]+)', b)
            p = tf(x, y, rot, mirror, float(m.group(2)), float(m.group(3)))
            text(m.group(1), p[0], p[1], anchor="middle", col="#800000")
    # pin
    for num, (px, py, ang, name, etype, ln, hide) in s.pins.items():
        if hide:
            continue
        p = tf(x, y, rot, mirror, px, py)
        # direzione verso il corpo, in coordinate libreria (Y verso l'alto)
        dd = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[ang]
        q_lib = (px + dd[0] * ln, py + dd[1] * ln)
        q = tf(x, y, rot, mirror, q_lib[0], q_lib[1])
        line(p, q, col="#800000")
        text(num, (p[0] + q[0]) / 2 + 0.3, (p[1] + q[1]) / 2 - 0.3, size=0.9, col="#4060a0")
    text(ref, x - 1, y - 1.2, size=1.6, col="#000080", anchor="middle")
    text(value, x - 1, y + 2.2, size=1.3, col="#000080", anchor="middle")

# area e file d'uscita sovrascrivibili (la variante a 3 canali usa un foglio A1)
VIEW = globals().get("VIEW", (10, 10, 340, 200))
OUTSVG = globals().get("OUTSVG", "sch_render.svg")
_W = 2720
# MM=True: dimensioni in millimetri (per il PDF a grandezza reale del foglio)
_size = (f'width="{VIEW[2]}mm" height="{VIEW[3]}mm"' if globals().get("MM")
         else f'width="{_W}" height="{int(_W * VIEW[3] / VIEW[2])}"')
hdr = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEW[0]} {VIEW[1]} {VIEW[2]} {VIEW[3]}" '
       f'{_size}>'
       f'<rect x="{VIEW[0]}" y="{VIEW[1]}" width="{VIEW[2]}" height="{VIEW[3]}" fill="white"/>')
EXTRA = globals().get("EXTRA", [])          # elementi aggiuntivi (cornice, cartiglio)
open(OUTSVG, "w").write(hdr + "\n".join(svg + EXTRA) + "</svg>")
print(OUTSVG, "scritto")
