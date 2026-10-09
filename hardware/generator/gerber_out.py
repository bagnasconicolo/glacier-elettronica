# -*- coding: utf-8 -*-
"""Genera i Gerber (RS-274X) + Excellon dal modello dati del PCB,
poi li ri-parsa con gerbonara e produce un render di verifica.
"""
import os, math
import json
import gen_pcb as G
from shapely.geometry import Polygon as _Poly

STATE = globals().get("STATE", "routing_state.json")
NAME = globals().get("NAME", "riv_cosmici")
st = json.load(open(STATE))
G.tracks[:] = st["tracks"]
G.vias[:] = st["vias"]
pour_keep = [_Poly(ext, holes) for ext, holes in zip(st["pour"], st["pour_holes"])]

OUT = globals().get("OUT", "riv_cosmici/gerber")
os.makedirs(OUT, exist_ok=True)
X1, Y1, X2, Y2 = G.X1, G.Y1, G.X2, G.Y2

def fmt(v):
    # mm, 4.6 (x1e6), senza zeri iniziali
    return str(int(round(v * 1e6)))

class Gerber:
    def __init__(self, fname, function):
        self.lines = ["%TF.GenerationSoftware,rivgen,1.0*%",
                      f"%TF.FileFunction,{function}*%",
                      "%FSLAX46Y46*%", "%MOMM*%", "%LPD*%",
                      "G01*"]
        self.fname = fname
        self.apertures = {}
        self.acode = 9
        self.cur = None
        self.body = []

    def ap(self, spec):
        if spec not in self.apertures:
            self.acode += 1
            self.apertures[spec] = self.acode
        return self.apertures[spec]

    def use(self, spec):
        code = self.ap(spec)
        if self.cur != code:
            self.body.append(f"D{code}*")
            self.cur = code

    def line(self, a, b, w):
        self.use(f"C,{w:.3f}")
        self.body.append(f"X{fmt(a[0])}Y{fmt(-a[1])}D02*")
        self.body.append(f"X{fmt(b[0])}Y{fmt(-b[1])}D01*")

    def flash_rect(self, x, y, w, h):
        self.use(f"R,{w:.3f}X{h:.3f}")
        self.body.append(f"X{fmt(x)}Y{fmt(-y)}D03*")

    def flash_circle(self, x, y, d):
        self.use(f"C,{d:.3f}")
        self.body.append(f"X{fmt(x)}Y{fmt(-y)}D03*")

    def region(self, coords, clear=False):
        self.body.append("%LPC*%" if clear else "%LPD*%")
        self.body.append("G36*")
        first = True
        for (x, y) in coords:
            self.body.append(f"X{fmt(x)}Y{fmt(-y)}D{'02' if first else '01'}*")
            first = False
        self.body.append(f"X{fmt(coords[0][0])}Y{fmt(-coords[0][1])}D01*")
        self.body.append("G37*")
        self.body.append("%LPD*%")
        self.cur = None

    def write(self):
        out = list(self.lines)
        for spec, code in self.apertures.items():
            out.append(f"%ADD{code}{spec}*%")
        out += self.body
        out.append("M02*")
        with open(os.path.join(OUT, self.fname), "w") as f:
            f.write("\n".join(out) + "\n")

def pad_flash(g, p, grow=0.0):
    w, h = p["w"] + 2 * grow, p["h"] + 2 * grow
    if p["rot"] % 180 != 0:
        w, h = h, w
    if p["kind"] == "tht" and abs(w - h) < 1e-6:
        g.flash_circle(p["x"], p["y"], w)
    else:
        g.flash_rect(p["x"], p["y"], w, h)

# ---------------- copper ----------------
for layer, fname, fn in (("F.Cu", f"{NAME}-F_Cu.gbr", "Copper,L1,Top"),
                         ("B.Cu", f"{NAME}-B_Cu.gbr", "Copper,L2,Bot")):
    g = Gerber(fname, fn)
    if layer == "B.Cu":   # regioni PRIMA: le LPC non devono cancellare pad/via/tracce
        for part in pour_keep:
            g.region(list(part.exterior.coords))
            for hole in part.interiors:
                g.region(list(hole.coords), clear=True)
    for t in G.tracks:
        if t["layer"] == layer:
            for a, b in zip(t["pts"], t["pts"][1:]):
                g.line(a, b, t["w"])
    for v in G.vias:
        g.flash_circle(v["x"], v["y"], G.VIA_D)
    for p in G.pads:
        if p["kind"] == "smd" and layer == "F.Cu":
            pad_flash(g, p)
        elif p["kind"] != "smd":
            pad_flash(g, p)
    g.write()

# ---------------- mask (aperture = pad + 0.05) ----------------
for layer, fname, fn in (("F", f"{NAME}-F_Mask.gbr", "Soldermask,Top"),
                         ("B", f"{NAME}-B_Mask.gbr", "Soldermask,Bot")):
    g = Gerber(fname, fn)
    for p in G.pads:
        if p["kind"] == "smd" and layer == "F":
            pad_flash(g, p, grow=0.05)
        elif p["kind"] != "smd":
            pad_flash(g, p, grow=0.05)
    g.write()

# ---------------- paste (solo smd top) ----------------
g = Gerber(f"{NAME}-F_Paste.gbr", "Paste,Top")
for p in G.pads:
    if p["kind"] == "smd":
        pad_flash(g, p)
g.write()

# ---------------- silk top ----------------
from pcb_data import rot_delta
from footprints import FPS
from pcb_data import FP_OF, COMPONENTS
g = Gerber(f"{NAME}-F_SilkS.gbr", "Legend,Top")
for ref, (x, y, rot) in G.PLACEMENT.items():
    fp = FPS[FP_OF[COMPONENTS[ref][2]]]
    for (sx1, sy1, sx2, sy2) in fp.silk:
        d1 = rot_delta(sx1, sy1, rot); d2 = rot_delta(sx2, sy2, rot)
        g.line((x + d1[0], y + d1[1]), (x + d2[0], y + d2[1]), 0.12)
g.write()

# ---------------- edge ----------------
g = Gerber(f"{NAME}-Edge_Cuts.gbr", "Profile,NP")
for a, b in (((X1, Y1), (X2, Y1)), ((X2, Y1), (X2, Y2)),
             ((X2, Y2), (X1, Y2)), ((X1, Y2), (X1, Y1))):
    g.line(a, b, 0.1)
g.write()

# ---------------- drill (Excellon, PTH) ----------------
holes = {}
for p in G.pads:
    if p["kind"] != "smd":
        holes.setdefault(p["drill"], []).append((p["x"], p["y"]))
for v in G.vias:
    holes.setdefault(G.VIA_DRILL, []).append((v["x"], v["y"]))
lines = ["M48", "METRIC,TZ"]
tools = {}
for i, d in enumerate(sorted(holes), 1):
    tools[d] = i
    lines.append(f"T{i}C{d:.3f}")
lines.append("%")
lines.append("G90")
lines.append("G05")
for d in sorted(holes):
    lines.append(f"T{tools[d]}")
    for (x, y) in holes[d]:
        lines.append(f"X{x:.3f}Y{-y:.3f}")
lines.append("M30")
open(os.path.join(OUT, f"{NAME}-PTH.drl"), "w").write("\n".join(lines) + "\n")

print("gerber scritti in", OUT)

# ---------------- verifica: riparse + render ----------------
from gerbonara import LayerStack
stack = LayerStack.open_dir(OUT)
print("gerbonara ha letto:", stack)
svg = stack.to_pretty_svg(side="top")
open("gerber_check_top.svg", "w").write(str(svg))
svg = stack.to_pretty_svg(side="bottom")
open("gerber_check_bottom.svg", "w").write(str(svg))
print("render di verifica scritti")
