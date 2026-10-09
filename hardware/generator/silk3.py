# -*- coding: utf-8 -*-
"""Serigrafia didattica della VARIANTE A 3 CANALI.

Produce poligoni pieni (senza fori: le lettere come A, O, 8 vengono tagliate in
pezzi) per F.SilkS e B.SilkS, cosi' sono identici nel .kicad_pcb (gr_poly) e
nei Gerber (regioni). Il testo usa DejaVu Sans Bold; altezza minima 0,9 mm
(tratto ~0,17 mm, sopra il minimo di 0,15 mm di JLCPCB). Tutto cio' che cadrebbe
su un pad viene ritagliato.

    python silk3.py   ->  riv_cosmici_3ch/silk.json + riv_cosmici_3ch/silk_preview.svg
"""
import json, os, sys
from functools import reduce

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import netdata3                                    # noqa: E402
sys.modules["netdata"] = netdata3
import pcb_data as PD                              # noqa: E402
import pcb_data3 as P3                             # noqa: E402
PD.BOARD = P3.BOARD
PD.PLACEMENT.clear()
PD.PLACEMENT.update(P3.PLACEMENT)
from footprints import FPS                         # noqa: E402

from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.textpath import TextPath            # noqa: E402
from shapely.geometry import Polygon, MultiPolygon, LineString, box  # noqa: E402
from shapely.ops import unary_union, split          # noqa: E402
import shapely.affinity as aff                      # noqa: E402

FONT = FontProperties(fname="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
CAP = 0.729                     # altezza delle maiuscole / em (DejaVu Sans)
LINE_W = 0.15                   # linee di serigrafia
X1, Y1, X2, Y2 = P3.BOARD
PADS = PD.abs_pads()
PAD_KEEP = unary_union([PD.pad_rect(p, 0.2) for p in PADS])


def courtyard(ref):
    x, y, rot = PD.PLACEMENT[ref]
    fp = FPS[PD.FP_OF[PD.COMPONENTS[ref][2]]]
    b = aff.rotate(box(*fp.courtyard), -rot, origin=(0, 0))
    return aff.translate(b, x, y)


COURT = {r: courtyard(r) for r in PD.PLACEMENT}


# ------------------------------------------------------------- testo
_glyph_cache = {}


def _raw_text(s, h):
    key = (s, h)
    if key not in _glyph_cache:
        tp = TextPath((0, 0), s, size=h / CAP, prop=FONT)
        polys = [Polygon([(x, -y) for x, y in ring]) for ring in tp.to_polygons() if len(ring) >= 3]
        polys = [p.buffer(0) for p in polys if p.area > 1e-6]
        g = reduce(lambda a, b: a.symmetric_difference(b), polys) if polys else Polygon()
        _glyph_cache[key] = g
    return _glyph_cache[key]


def text(s, x, y, h, anchor="l", valign="top", rot=0):
    """testo con l'angolo indicato in (x, y); rot in gradi (90 = dal basso verso l'alto)"""
    g = _raw_text(s, h)
    if g.is_empty:
        return g
    bx1, by1, bx2, by2 = g.bounds
    dx = {"l": -bx1, "c": -(bx1 + bx2) / 2, "r": -bx2}[anchor]
    dy = {"top": -by1, "mid": -(by1 + by2) / 2, "bot": -by2}[valign]
    g = aff.translate(g, dx, dy)
    if rot:
        g = aff.rotate(g, -rot, origin=(0, 0))
    return aff.translate(g, x, y)


def size_of(s, h):
    b = _raw_text(s, h).bounds
    return b[2] - b[0], b[3] - b[1]


# ------------------------------------------------------------- ostacoli
class Layer:
    def __init__(self, name):
        self.name = name
        self.items = []          # geometrie gia' piazzate
        self.free_check = []     # ingombri da rispettare per i testi

    def add(self, g, keep=None):
        self.items.append(g)
        self.free_check.append(keep if keep is not None else g.buffer(0.25))


TOP = Layer("F.SilkS")
BOT = Layer("B.SilkS")
COURT_ALL = unary_union([c.buffer(0.1) for c in COURT.values()])
BOARD_IN = box(X1 + 0.6, Y1 + 0.6, X2 - 0.6, Y2 - 0.6)


def fits(g, layer, avoid_courtyards=True, own=None):
    if g.is_empty or not BOARD_IN.contains(g.envelope):
        return False
    if g.intersects(PAD_KEEP):
        return False
    if avoid_courtyards:
        cg = COURT_ALL if own is None else unary_union(
            [c.buffer(0.1) for r, c in COURT.items() if r != own])
        if g.intersects(cg):
            return False
    for k in layer.free_check:
        if g.intersects(k):
            return False
    return True


def place_text(s, h, candidates, layer=TOP, avoid_courtyards=True, required=False, rot=0):
    """prova le posizioni (x, y, anchor, valign) in ordine; ritorna True se piazzato"""
    for (x, y, anc, va) in candidates:
        g = text(s, x, y, h, anc, va, rot)
        if fits(g.envelope, layer, avoid_courtyards):
            layer.add(g, g.envelope.buffer(0.3))
            return True
    if required:
        print(f"!! non trovo spazio per '{s}'")
    return False


def near(cx, cy, w, h, step=0.5, rmax=6.0):
    """posizioni (centro) a spirale quadrata attorno a (cx, cy)"""
    out = [(cx, cy)]
    r = step
    while r <= rmax:
        k = -r
        while k <= r + 1e-9:
            out += [(cx + k, cy - r), (cx + k, cy + r), (cx - r, cy + k), (cx + r, cy + k)]
            k += step
        r += step
    return [(x, y, "c", "mid") for x, y in out]


def outline(rect, layer=TOP):
    """rettangolo di blocco, interrotto sui pad"""
    x1, y1, x2, y2 = rect
    ring = LineString([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)])
    g = ring.buffer(LINE_W / 2, cap_style=2, join_style=2).difference(PAD_KEEP)
    layer.add(g, ring.buffer(0.35))
    return len(layer.items) - 1


def hline(x1, x2, y, layer=TOP, dash=None):
    g = LineString([(x1, y), (x2, y)]).buffer(LINE_W / 2, cap_style=2)
    if dash:
        segs = []
        x = x1
        while x < x2:
            segs.append(box(x, y - 1, min(x + dash, x2), y + 1))
            x += 2 * dash
        g = g.intersection(unary_union(segs))
    g = g.difference(PAD_KEEP)
    layer.add(g, LineString([(x1, y), (x2, y)]).buffer(0.3))


def arrow(x1, x2, y, layer=TOP):
    """freccia orizzontale del flusso del segnale"""
    shaft = LineString([(x1, y), (x2 - 0.6, y)]).buffer(0.1, cap_style=2)
    head = Polygon([(x2, y), (x2 - 0.9, y - 0.55), (x2 - 0.9, y + 0.55)])
    g = unary_union([shaft, head])
    if fits(g.buffer(0.05), layer):
        layer.add(g, g.buffer(0.3))
        return True
    return False


def arrow_v(x, y1, y2, layer=TOP):
    """freccia verticale da y1 a y2"""
    sgn = 1 if y2 > y1 else -1
    shaft = LineString([(x, y1), (x, y2 - sgn * 0.6)]).buffer(0.1, cap_style=2)
    head = Polygon([(x, y2), (x - 0.55, y2 - sgn * 0.9), (x + 0.55, y2 - sgn * 0.9)])
    g = unary_union([shaft, head])
    layer.add(g, g.buffer(0.3))


def diagram(x0, y0, layer=TOP):
    """schema a blocchi di un canale + coincidenza"""
    bw, bh, gap = 9.5, 3.2, 3.0
    names = ["SiPM", "AMPLIF.", "COMPAR.", "USCITA"]
    xs = [x0 + i * (bw + gap) for i in range(4)]
    def cell(x, y, s):
        g = LineString([(x, y), (x + bw, y), (x + bw, y + bh), (x, y + bh), (x, y)]).buffer(
            0.075, cap_style=2, join_style=2)
        t = text(s, x + bw / 2, y + bh / 2, 0.9, "c", "mid")
        layer.add(unary_union([g, t]), box(x - 0.3, y - 0.3, x + bw + 0.3, y + bh + 0.3))
    for x, s in zip(xs, names):
        cell(x, y0, s)
    for i in range(3):
        a = LineString([(xs[i] + bw + 0.3, y0 + bh / 2), (xs[i + 1] - 0.9, y0 + bh / 2)]).buffer(0.1, cap_style=2)
        h = Polygon([(xs[i + 1] - 0.3, y0 + bh / 2), (xs[i + 1] - 1.2, y0 + bh / 2 - 0.55),
                     (xs[i + 1] - 1.2, y0 + bh / 2 + 0.55)])
        layer.add(unary_union([a, h]))
    y1 = y0 + bh + 3.0
    cell(xs[0], y1, "A 38V")
    cell(xs[2], y1, "B SOGLIA")
    cell(xs[3], y1, "C LED")
    arrow_v(xs[0] + bw / 2, y1 - 0.3, y0 + bh + 0.3)
    arrow_v(xs[2] + bw / 2, y1 - 0.3, y0 + bh + 0.3)
    # comparatore -> LED: dal lato destro del comparatore in basso a C
    a = LineString([(xs[2] + bw + 0.3, y0 + bh - 0.6), (xs[3] + 1.5, y0 + bh - 0.6 + 0.0)]).buffer(0.1)
    layer.add(a)
    arrow_v(xs[3] + 1.5, y0 + bh - 0.6, y1 - 0.3)
    t = text("schema di un canale (x3) -> COINCIDENZA AND", x0, y1 + bh + 1.2, 0.9, "l", "top")
    layer.add(t, t.envelope.buffer(0.3))


def block_rect(refs, abs_refs, margin=0.55):
    g = unary_union([COURT[r] for r in abs_refs])
    b = g.bounds
    return (b[0] - margin, b[1] - margin - 0.5, b[2] + margin, b[3] + margin)


def title_for(rect, title, sub, layer=TOP, idx=None):
    x1, y1, x2, y2 = rect
    th, sh = 1.25, 0.9
    # prima scelta: titolo "a linguetta" sul bordo alto del riquadro (linea interrotta)
    if idx is not None:
        keep = layer.free_check[idx]
        layer.free_check[idx] = Polygon()
        placed = None
        for k in (0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10):
            g = text(title, x1 + 1.0 + k, y1, th, "l", "mid")
            if fits(g.envelope.buffer(0.15), layer):
                placed = g
                break
        layer.free_check[idx] = keep
        if placed is not None:
            cut = placed.envelope.buffer(0.4, join_style=2)
            layer.items[idx] = layer.items[idx].difference(cut)
            layer.add(placed, placed.envelope.buffer(0.3))
            title = None
    cands = []
    for yy in (y1 - 0.3,):                       # appena sopra il riquadro
        cands += [(x1 + 0.3 + k, yy, "l", "bot") for k in (0, 1, 2, 3, 4, 6, 8, 10)]
    cands += [(x1 + 0.6 + k, y1 + 0.5, "l", "top") for k in (0, 1, 2, 3, 4, 6, 8)]
    cands += [(x2 - 0.6, y1 + 0.5, "r", "top"), (x1 + 0.3, y2 + 0.3, "l", "top"),
              (x1 + 0.6, y2 - 0.5, "l", "bot")]
    if title:
        place_text(title, th, cands, layer, required=True)
    if sub:
        w, h = size_of(sub, sh)
        cands = []
        yy = y2 - 0.4 - h / 2
        while yy > y1 + h:
            for xx in [x1 + 0.6 + w / 2 + k for k in range(0, int(max(1, x2 - x1 - w - 1)), 1)]:
                cands.append((xx, yy, "c", "mid"))
            yy -= 0.5
        # fuori dal riquadro: sotto, sopra, a sinistra
        for d in (0.3, 0.8, 1.5, 2.5):
            cands += [(x1 + w / 2 + k, y2 + d + h / 2, "c", "mid") for k in range(0, 12)]
        for d in (0.3, 0.8):
            cands += [(x1 + w / 2 + k, y1 - d - h / 2, "c", "mid") for k in range(0, 12)]
        cands += [(x1 - 0.6, y1 + h + k, "r", "mid") for k in range(0, 8)]
        place_text(sub, sh, cands, layer, required=True)


# ------------------------------------------------------------- costruzione
def build_top():
    N = netdata3
    # separatori tra le fasce
    for n in N.CHANNELS:
        hline(X1 + 0.8, X2 - 0.8, P3.ch_y(n), dash=1.2)
    hline(X1 + 0.8, X2 - 0.8, P3.COINC_Y, dash=1.2)

    blocks = []
    for (t, s, refs) in P3.PWR_BLOCKS:
        blocks.append((t, s, refs))
    for n in N.CHANNELS:
        for (t, s, refs) in P3.CH_BLOCKS:
            ab = [f"TP{n}{r[2:]}" if r.startswith("TP") else N.chref(r, n) for r in refs]
            blocks.append((t, s, ab))
    for (t, s, refs) in P3.COINC_BLOCKS:
        blocks.append((t, s, refs))
    rects = []
    for (t, s, ab) in blocks:
        r = block_rect(None, ab)
        rects.append((r, outline(r)))
    for (t, s, ab), (r, idx) in zip(blocks, rects):
        title_for(r, t, s, idx=idx)

    # nome del canale in verticale sul bordo sinistro
    for n in N.CHANNELS:
        yc = P3.ch_y(n) + P3.STRIP / 2
        place_text(f"CANALE {n}", 1.6, [(X1 + 1.0 + k * 0.25, yc, "c", "top") for k in range(0, 8)],
                   rot=90, required=True)
    # frecce del percorso del segnale (riga alta di ogni canale)
    for n in N.CHANNELS:
        yy = P3.ch_y(n)
        for xa, xb in ((14.6, 16.0), (41.0, 42.5), (63.5, 66.0), (85.0, 87.0)):
            for dy in (1.0, 0.6, 1.4, 25.6, 26.2):
                if arrow(X1 + xa, X1 + xb, yy + dy):
                    break
    # etichette dei connettori e dei trimmer
    for n in N.CHANNELS:
        x, y, _ = PD.PLACEMENT[f"J{n}04"]
        place_text(f"CH{n}", 1.25, near(x - 0.5, y + 6.0, 0, 0, rmax=3), required=True)
        for v, lab in (("V1", "V1 TENSIONE"), ("V2", "V2 SOGLIA")):
            x, y, _ = PD.PLACEMENT[N.chref(v, n)]
            # sopra il corpo del trimmer (che sporge fino a ~3,4 mm dai pin)
            place_text(lab, 0.9, near(x, y - 4.4, 0, 0, rmax=3), required=True)
        x, y, _ = PD.PLACEMENT[N.chref("D3", n)]
        place_text("LED", 0.9, near(x + 3.0, y, 0, 0, rmax=3), required=True)
        x, y, _ = PD.PLACEMENT[N.chref("J1", n)]
        place_text("1", 0.9, near(x - 2.0, y, 0, 0, rmax=1.5), required=True)
        place_text("2", 0.9, near(x - 2.0, y + 2.54, 0, 0, rmax=1.5), required=True)
    x, y, _ = PD.PLACEMENT["J5"]
    place_text("AND", 1.25, near(x - 0.5, y - 5.5, 0, 0, rmax=2) + near(x - 0.5, y + 6.0, 0, 0, rmax=3),
               required=True)
    x, y, _ = PD.PLACEMENT["J3"]
    place_text("GND", 0.9, near(x + 3.5, y, 0, 0, rmax=2), required=True)
    place_text("+5V", 0.9, near(x + 3.5, y + 2.54, 0, 0, rmax=2), required=True)
    for n in N.CHANNELS:
        x, y, _ = PD.PLACEMENT[f"JP{n}"]
        place_text(f"CH{n}", 1.1, near(x, y + 5.6, 0, 0, rmax=1) + near(x, y - 2.4, 0, 0, rmax=1),
                   required=True)

    # schema a blocchi nella fascia coincidenza (a sinistra)
    diagram(X1 + 4.0, P3.COINC_Y + 2.5)

    # cartiglio nella fascia alimentazione (a destra)
    tx = X1 + 80.0
    ty = Y1 + 1.6
    for s, h in (("RIVELATORE DI", 1.2), ("RAGGI COSMICI", 1.2), ("3 canali + AND", 0.95),
                 ("INFN Torino 2024", 0.9), ("CERN-OHL-W-2.0", 0.9)):
        place_text(s, h, [(tx + k * 0.5, ty + j * 0.5, "l", "top") for j in range(0, 6) for k in range(-2, 6)],
                   required=True)
        ty += h + 1.0
    hv = "ATTENZIONE: fino a 41 V"
    place_text(hv, 0.9, near(X1 + 85.0, Y1 + 24.0, 0, 0, rmax=3), required=True)

    # etichette dei test point
    for ref in PD.PLACEMENT:
        if not ref.startswith("TP"):
            continue
        key = ref if len(ref) == 3 else "TP" + ref[3:]
        lab = P3.TP_LABEL[key]
        x, y, _ = PD.PLACEMENT[ref]
        w, h = size_of(lab, 0.9)
        cands = [(x + 1.6, y, "l", "mid"), (x - 1.6, y, "r", "mid"),
                 (x, y - 1.6, "c", "bot"), (x, y + 1.6, "c", "top")]
        cands += [(x + 1.6 + dx, y + dy, "l", "mid") for dx in (0, 0.5, 1) for dy in (-0.5, 0.5, -1, 1)]
        cands += [(x - 1.6 - dx, y + dy, "r", "mid") for dx in (0, 0.5, 1) for dy in (-0.5, 0.5, -1, 1)]
        cands += [(x + dx, y + 1.6 + dy, "c", "top") for dy in (0.5, 1, 1.5, 2) for dx in (0, -1, 1, -2, 2)]
        cands += [(x + dx, y - 1.6 - dy, "c", "bot") for dy in (0.5, 1, 1.5, 2) for dx in (0, -1, 1, -2, 2)]
        place_text(lab, 0.9, cands, required=True)

    # riferimenti dei componenti
    miss = []
    for ref in sorted(PD.PLACEMENT, key=lambda r: (PD.PLACEMENT[r][1], PD.PLACEMENT[r][0])):
        if ref.startswith("TP"):
            continue
        b = COURT[ref].bounds
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        ok = False
        for hh in (0.9, 0.8):
            D = (0, 0.3, 0.6, 1.0, 1.5)
            cands = [(cx, b[1] - 0.15 - d, "c", "bot") for d in D]
            cands += [(cx, b[3] + 0.15 + d, "c", "top") for d in D]
            cands += [(b[2] + 0.15 + d, cy, "l", "mid") for d in D]
            cands += [(b[0] - 0.15 - d, cy, "r", "mid") for d in D]
            cands += [(cx + dx, b[1] - 0.15, "c", "bot") for dx in (-1.5, 1.5, -3, 3)]
            cands += [(cx + dx, b[3] + 0.15, "c", "top") for dx in (-1.5, 1.5, -3, 3)]
            if place_text(ref, hh, cands):
                ok = True
                break
            # in verticale accanto al pezzo
            vc = [(b[2] + 0.15 + d, cy + e, "c", "top") for d in (0, 0.4, 0.8) for e in (0, -1, 1)]
            vc += [(b[0] - 0.15 - d, cy + e, "c", "bot") for d in (0, 0.4, 0.8) for e in (0, -1, 1)]
            if place_text(ref, hh, vc, rot=90):
                ok = True
                break
        if not ok:
            miss.append(ref)
    return miss


# ------------------------------------------------------------- lato inferiore: legenda
LEGEND = [
    ("COME FUNZIONA", 1.6), ("", 0.8),
    ("Un muone attraversa la", 1.0), ("barra di scintillatore:", 1.0),
    ("la barra emette un lampo", 1.0), ("di luce che il SiPM", 1.0),
    ("trasforma in un piccolo", 1.0), ("impulso di corrente.", 1.0), ("", 0.8),
    ("1 SiPM: sensore di luce,", 1.0), ("  alimentato a ~38 V", 1.0),
    ("2 AMPLIFICATORE: due", 1.0), ("  transistor ingrandiscono", 1.0), ("  l'impulso", 1.0),
    ("3 COMPARATORE: l'impulso", 1.0), ("  supera la soglia? SI/NO", 1.0),
    ("4 USCITA: impulso digitale", 1.0), ("  0-3,3 V sul LEMO", 1.0), ("", 0.8),
    ("A ALIMENTAZIONE SiPM:", 1.0), ("  genera i ~38 V; V1 la", 1.0), ("  regola, il diodo D1 la", 1.0),
    ("  corregge con la", 1.0), ("  temperatura", 1.0),
    ("B SOGLIA: la regola V2", 1.0),
    ("C LED: si accende ~10 ms", 1.0), ("  a ogni evento", 1.0), ("", 0.8),
    ("COINCIDENZA: l'uscita AND", 1.0), ("va a 1 solo se tutti i", 1.0),
    ("canali inclusi (jumper", 1.0), ("chiusi) vedono un evento", 1.0),
    ("nello stesso istante:", 1.0), ("un muone che attraversa", 1.0), ("piu' barre.", 1.0), ("", 0.8),
    ("ALIMENTAZIONE: 5 V su J3.", 1.0), ("Il survoltore produce", 1.0),
    ("41 V: non toccare la", 1.0), ("scheda accesa.", 1.0),
]
# colonna senza fori passanti (tra i blocchi dei canali e i LEMO)
LEG_X1, LEG_X2 = X1 + 63.8, X1 + 85.8
THT_KEEP = unary_union([PD.pad_rect(p, 0.25) for p in PADS if p["kind"] != "smd"])


def build_bottom():
    """legenda specchiata sul lato saldature (si legge girando la scheda)"""
    y = P3.ch_y(1) + 2.0
    for s_, h in LEGEND:
        if s_:
            w, _ = size_of(s_, h)
            room = LEG_X2 - LEG_X1 - (1.6 if s_.startswith("  ") else 0.0)
            if w > room:
                h = h * room / w
                assert h >= 0.9, f"riga troppo lunga per la legenda: {s_}"
            g = text(s_, 0, 0, h, "l", "top")
            g = aff.scale(g, xfact=-1, yfact=1, origin=(0, 0))
            ind = 1.6 if s_.startswith("  ") else 0.0   # rientro (gli spazi iniziali non contano nel testo)
            g = aff.translate(g, LEG_X2 - ind, y)       # specchiato: dal retro parte da sinistra
            assert not g.intersects(THT_KEEP), f"legenda su un foro: {s_}"
            BOT.add(g)
        y += h + 0.9
    g = text("Riv. Cosmici 2024 - 3 canali - INFN Torino", 0, 0, 1.0, "l", "top")
    g = aff.translate(aff.scale(g, xfact=-1, yfact=1, origin=(0, 0)), X2 - 6.0, Y2 - 4.0)
    BOT.add(g.difference(THT_KEEP))


# ------------------------------------------------------------- uscita
def no_holes(geom):
    """spezza i poligoni con fori in pezzi senza fori (per gr_poly e regioni Gerber)"""
    out = []
    todo = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    while todo:
        p = todo.pop()
        if p.is_empty or p.geom_type != "Polygon":
            if hasattr(p, "geoms"):
                todo += list(p.geoms)
            continue
        if p.area < 1e-4:
            continue
        if not p.interiors:
            out.append(p)
            continue
        hx = p.interiors[0].centroid.x
        b = p.bounds
        cut = LineString([(hx, b[1] - 1), (hx, b[3] + 1)])
        parts = split(p, cut)
        if len(parts.geoms) < 2:          # taglio degenere: sposta un poco
            cut = LineString([(hx + 0.013, b[1] - 1), (hx + 0.013, b[3] + 1)])
            parts = split(p, cut)
        todo += list(parts.geoms)
    return out


def build():
    miss = build_top()
    build_bottom()
    res = {}
    for L in (TOP, BOT):
        g = unary_union(L.items)
        res[L.name] = [[(round(x, 4), round(y, 4)) for x, y in p.exterior.coords] for p in no_holes(g)]
    return res, miss


def preview(res, fn):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{X1 - 2} {Y1 - 2} {X2 - X1 + 4} {Y2 - Y1 + 4}" '
         f'width="{int((X2 - X1 + 4) * 14)}" height="{int((Y2 - Y1 + 4) * 14)}">',
         f'<rect x="{X1}" y="{Y1}" width="{X2 - X1}" height="{Y2 - Y1}" fill="#1e6b3c"/>']
    for p in PADS:
        r = PD.pad_rect(p)
        s.append('<polygon points="' + " ".join(f"{x:.2f},{y:.2f}" for x, y in r.exterior.coords)
                 + '" fill="#d9d6cc"/>')
    for ref, c in COURT.items():
        s.append('<polygon points="' + " ".join(f"{x:.2f},{y:.2f}" for x, y in c.exterior.coords)
                 + '" fill="none" stroke="#000" stroke-width="0.05" opacity="0.4"/>')
    for ring in res["F.SilkS"]:
        s.append('<polygon points="' + " ".join(f"{x:.3f},{y:.3f}" for x, y in ring) + '" fill="#f4f4ee"/>')
    s.append("</svg>")
    open(fn, "w").write("\n".join(s))


if __name__ == "__main__":
    res, miss = build()
    out = os.path.join(HERE, "riv_cosmici_3ch")
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, "silk.json"), "w"))
    preview(res, os.path.join(out, "silk_preview.svg"))
    print(f"serigrafia: {len(res['F.SilkS'])} poligoni sopra, {len(res['B.SilkS'])} sotto")
    print("riferimenti senza spazio:", miss)
