# -*- coding: utf-8 -*-
"""Render SVG del PCB per controllo visivo."""
import json
import gen_pcb as G
from shapely.geometry import Polygon as _Poly

# usa il routing salvato da gen_pcb.py (stesso stato dei Gerber e del .kicad_pcb)
st = json.load(open(globals().get("STATE", "routing_state.json")))
G.tracks[:] = st["tracks"]
G.vias[:] = st["vias"]
pour_keep = [_Poly(ext, holes) for ext, holes in zip(st["pour"], st["pour_holes"])]

X1, Y1, X2, Y2 = G.X1, G.Y1, G.X2, G.Y2
svg = []
def rect(x1, y1, x2, y2, fill, op=1.0, stroke="none"):
    svg.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" fill="{fill}" opacity="{op}" stroke="{stroke}" stroke-width="0.08"/>')
def poly_svg(geom, fill, op):
    from shapely.geometry import MultiPolygon
    geoms = geom.geoms if hasattr(geom, "geoms") else [geom]
    for g in geoms:
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in g.exterior.coords)
        svg.append(f'<polygon points="{pts}" fill="{fill}" opacity="{op}"/>')
        for hole in g.interiors:
            pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in hole.coords)
            svg.append(f'<polygon points="{pts}" fill="white" opacity="1"/>')

svg.append(f'<rect x="{X1}" y="{Y1}" width="{X2-X1}" height="{Y2-Y1}" fill="#f8f4e8" stroke="#a08000" stroke-width="0.2"/>')
# pour B.Cu
for part in pour_keep:
    poly_svg(part, "#4060c0", 0.25)
# tracce B poi F
for t in G.tracks:
    col = "#2040a0" if t["layer"] == "B.Cu" else "#c03020"
    op = 0.75 if t["layer"] == "B.Cu" else 0.9
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in t["pts"])
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{t["w"]}" stroke-linecap="round" stroke-linejoin="round" opacity="{op}"/>')
# pads
for p in G.pads:
    r = G.pad_rect(p)
    col = "#b02020" if p["kind"] == "smd" else "#c08000"
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in r.exterior.coords)
    svg.append(f'<polygon points="{pts}" fill="{col}" opacity="0.95"/>')
    if p["kind"] != "smd":
        svg.append(f'<circle cx="{p["x"]}" cy="{p["y"]}" r="{p["drill"]/2}" fill="white"/>')
# vias
for v in G.vias:
    svg.append(f'<circle cx="{v["x"]}" cy="{v["y"]}" r="{G.VIA_D/2}" fill="#208020"/>')
    svg.append(f'<circle cx="{v["x"]}" cy="{v["y"]}" r="{G.VIA_DRILL/2}" fill="white"/>')
# serigrafia didattica (se passata): sostituisce courtyard + riferimenti
SILKJSON = globals().get("SILKJSON")
if SILKJSON:
    for ring in json.load(open(SILKJSON))["F.SilkS"]:
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in ring)
        svg.append(f'<polygon points="{pts}" fill="#202020" opacity="0.85"/>')
for ref, ct in ([] if SILKJSON else G.courtyards()):
    b = ct.bounds
    rect(b[0], b[1], b[2], b[3], "none", 1.0, "#909090")
    svg.append(f'<text x="{(b[0]+b[2])/2:.2f}" y="{b[1]-0.3:.2f}" font-size="1.1" text-anchor="middle" fill="#202020" font-family="monospace">{ref}</text>')

hdr = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{X1-3} {Y1-3} {X2-X1+6} {Y2-Y1+6}" width="2200" height="{int(2200*(Y2-Y1+6)/(X2-X1+6))}">'
       f'<rect x="{X1-3}" y="{Y1-3}" width="{X2-X1+6}" height="{Y2-Y1+6}" fill="white"/>')
open(globals().get("OUTSVG", "pcb_render.svg"), "w").write(hdr + "\n".join(svg) + "</svg>")
print("pcb_render.svg ok")
