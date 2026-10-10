# -*- coding: utf-8 -*-
"""Schema elettrico in A4 nello stile del foglio INFN ("Riv. Cosmici 2024 - Amplif, alim, soglie"),
per la scheda a 3 canali:  nero = circuito INFN originale,  ROSSO = parti aggiunte o modificate.

  pagina 1   schema a blocchi: i tre canali (ognuno col suo colore) e le parti comuni
  pagina 2   parti comuni: 3,3 V, alta tensione, riferimenti 3,6 V, monitor, coincidenza
  pagine 3-5 canale 1, 2, 3 (stesso circuito, riferimenti del canale, cornice del suo colore)

Valori e collegamenti sono quelli di netdata3.py (lo stesso modello di schema KiCad e PCB):
lo script controlla i valori di ogni componente disegnato.

    python3 schema_a4.py      ->  docs/schema_A4_3canali.pdf
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
import schemdraw
import schemdraw.elements as elm
import schemdraw.logic as logic

import netdata3 as N

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "docs", "schema_A4_3canali.pdf")

W, H = 70.0, 49.5                 # A4 orizzontale in unita' di disegno (1 unita' = 4,24 mm)
RED = "#d00000"
BLACK = "black"
CH_COL = {1: "#1f5fbf", 2: "#1a8a3a", 3: "#c86400"}
CH_TINT = {1: "#eef4fd", 2: "#eef8f0", 3: "#fdf4ea"}
FS = 6.5                          # testo dei componenti (pt)
DRAWN = {}                        # riferimento -> valore disegnato (controllo con netdata3)


def val_of(ref):
    return N.COMPONENTS[ref][1]


class Sheet:
    """una pagina A4: schemdraw disegna sugli assi matplotlib in unita' di pagina"""

    def __init__(self, pdf):
        self.pdf = pdf
        self.fig = plt.figure(figsize=(11.69, 8.27))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_axis_off()
        self.d = schemdraw.Drawing(canvas=self.ax, show=False)
        self.d.config(unit=2.5, fontsize=FS, lw=0.9)

    # ---------------------------------------------------------- primitive
    def add(self, e):
        return self.d.add(e)

    def wire(self, *pts, c=BLACK):
        xs, ys = zip(*[(p[0], p[1]) for p in pts])
        self.ax.plot(xs, ys, color=c, lw=0.9, solid_capstyle="round", zorder=1)

    def dot(self, p, c=BLACK):
        self.ax.add_patch(Circle((p[0], p[1]), 0.12, color=c, zorder=3))

    def gnd(self, p, c=BLACK):
        x, y = p[0], p[1]
        self.wire((x, y), (x, y - 0.35), c=c)
        for k, hw in enumerate((0.45, 0.3, 0.15)):
            self.ax.plot([x - hw, x + hw], [y - 0.35 - 0.17 * k] * 2, color=c, lw=0.9, zorder=1)

    def vdd(self, p, lab, c=BLACK, side="up"):
        x, y = p[0], p[1]
        dy = 0.35 if side == "up" else -0.35
        self.wire((x, y), (x, y + dy), c=c)
        self.ax.plot([x - 0.4, x + 0.4], [y + dy] * 2, color=c, lw=0.9)
        self.text(x, y + dy + (0.45 if side == "up" else -0.45), lab, c=c, fs=FS - 0.5, ha="center")

    def text(self, x, y, s, c=BLACK, fs=FS, ha="left", va="center", weight="normal", rot=0, style="normal"):
        self.ax.text(x, y, s, color=c, fontsize=fs, ha=ha, va=va, fontweight=weight, rotation=rot,
                     fontstyle=style, family="DejaVu Sans", zorder=5)

    def comp(self, kind, ref, p, direction, length=2.5, c=BLACK, loc="bot", val=None, lab=None):
        """R / C / L tra p e p + length nella direzione data; etichetta 'rif\\nvalore'"""
        v = val if val is not None else val_of(ref)
        DRAWN[ref] = v
        e = {"R": elm.Resistor, "C": elm.Capacitor, "L": elm.Inductor2}[kind]()
        e = getattr(e.at(p), direction)(length).color(c)
        vv = v.replace("uF", "µF")
        if vv.endswith("R") and vv[:-1].isdigit():
            vv = vv[:-1] + "Ω"
        e = e.label(lab or f"{ref}\n{vv}",
                    loc=loc, fontsize=FS)
        return self.add(e)

    def tp(self, p, lab, side="up", c=RED):
        """test point (aggiunti nella variante didattica)"""
        x, y = p
        dx, dy = {"up": (0, 0.9), "down": (0, -0.9), "left": (-0.9, 0), "right": (0.9, 0)}[side]
        self.wire(p, (x + dx, y + dy), c=c)
        cx, cy = x + dx * 1.22, y + dy * 1.22
        self.ax.add_patch(Circle((cx, cy), 0.2, fill=False, color=c, lw=0.8, zorder=3))
        ha = "right" if side == "left" else "left"
        self.text(cx + (-0.35 if side == "left" else 0.35), cy, lab, c=c, fs=FS - 1.2, ha=ha)

    def ic(self, x, y, w, h, pins, label, c=BLACK, lead=0.7):
        """integrato: rettangolo (x, y = angolo in basso a sinistra) e pin
        pins: (numero, nome, lato, posizione lungo il lato dal basso / da sinistra)
        ritorna {numero: estremo del pin}"""
        self.ax.add_patch(Rectangle((x, y), w, h, fill=False, color=c, lw=1.0, zorder=2))
        self.text(x + w / 2, y + h / 2, label, c=c, fs=FS, ha="center", weight="bold")
        out = {}
        for num, name, side, pos in pins:
            if side == "left":
                a, b, tx, ty, ha, va, nx, ny = (x, y + pos), (x - lead, y + pos), x - 0.1, y + pos + 0.22, "right", "bottom", x + 0.15, y + pos
                nha, nva = "left", "center"
            elif side == "right":
                a, b, tx, ty, ha, va, nx, ny = (x + w, y + pos), (x + w + lead, y + pos), x + w + 0.1, y + pos + 0.22, "left", "bottom", x + w - 0.15, y + pos
                nha, nva = "right", "center"
            elif side == "top":
                a, b, tx, ty, ha, va, nx, ny = (x + pos, y + h), (x + pos, y + h + lead), x + pos + 0.15, y + h + 0.1, "left", "bottom", x + pos, y + h - 0.2
                nha, nva = "center", "top"
            else:
                a, b, tx, ty, ha, va, nx, ny = (x + pos, y), (x + pos, y - lead), x + pos + 0.15, y - 0.1, "left", "top", x + pos, y + 0.2
                nha, nva = "center", "bottom"
            self.wire(a, b, c=c)
            self.text(tx, ty, str(num), c=c, fs=FS - 2.0, ha=ha, va=va)
            self.text(nx, ny, name, c=c, fs=FS - 1.4, ha=nha, va=nva)
            out[num] = b
        return out

    def lemo(self, p, lab, c=RED):
        x, y = p
        self.ax.add_patch(Circle((x + 0.7, y), 0.55, fill=False, color=c, lw=1.0, zorder=3))
        self.ax.add_patch(Circle((x + 0.7, y), 0.15, color=c, zorder=3))
        self.wire((x, y), (x + 0.55, y), c=c)
        self.gnd((x + 0.7, y - 0.55), c=c)
        self.text(x + 1.5, y + 0.1, lab, c=c, fs=FS - 0.6, va="bottom")

    def frame(self, title, board, sheet_no, sheets, color=BLACK, tint=None):
        ax = self.ax
        if tint:
            ax.add_patch(Rectangle((0.7, 0.7), W - 1.4, H - 1.4, facecolor=tint, edgecolor="none", zorder=-5))
        ax.add_patch(Rectangle((0.7, 0.7), W - 1.4, H - 1.4, fill=False, lw=2.5 if tint else 1.0,
                               color=color, zorder=6))
        x0, y0, bw, bh = 42.5, 1.4, 26.4, 6.9           # cartiglio come nel foglio INFN
        ax.add_patch(Rectangle((x0, y0), bw, bh, facecolor="white", edgecolor=BLACK, lw=0.9, zorder=6))
        rows = [("Co:", "INFN sez. TORINO  (variante 3 canali)"), ("Title:", "Riv. Cosmici 2024 - 3 canali"),
                ("Board:", board), ("Author:", "Silvano Gallian (originale, rev. A) + variante"),
                ("Date:", "10/10/2026")]
        for i, (k, v) in enumerate(rows):
            yy = y0 + bh - (i + 0.5) * bh / 5
            if i:
                ax.plot([x0, x0 + bw], [y0 + bh - i * bh / 5] * 2, color=BLACK, lw=0.5, zorder=7)
            ax.text(x0 + 0.4, yy, k, fontsize=5.8, va="center", zorder=7)
            big = i in (1, 2)
            ax.text(x0 + 3.9, yy, v, fontsize=9 if big else 6.6, va="center", zorder=7,
                    color=color if (i == 2 and tint) else BLACK, fontweight="bold" if i == 2 else "normal")
        ax.text(x0 + bw - 0.4, y0 + bh / 10, f"Sheet {sheet_no} of {sheets}", fontsize=6.4, ha="right",
                va="center", zorder=7)
        ax.text(1.8, 1.9, "nero = circuito INFN originale", fontsize=7, va="center", zorder=7)
        ax.text(16.5, 1.9, "rosso = aggiunto o modificato nella variante a 3 canali", fontsize=7,
                color=RED, va="center", zorder=7)

    def save(self):
        self.d.draw(show=False)
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(0, H)
        self.ax.set_aspect("equal")
        self.pdf.savefig(self.fig)
        plt.close(self.fig)


# ===================================================================== canale
def page_channel(pdf, n, sheet_no, sheets):
    s = Sheet(pdf)
    r = lambda ref: N.chref(ref, n)              # R10 -> R110, R210, R310 ...
    col = CH_COL[n]
    s.frame("", f"CANALE {n}", sheet_no, sheets, color=col, tint=CH_TINT[n])
    s.text(1.8, 47.3, f"CANALE {n}", c=col, fs=17, weight="bold")
    s.text(1.8, 45.6, "i tre canali sono identici: cambia solo la prima cifra dei riferimenti "
                      f"(R{n}10 = R10 del foglio INFN)", c=col, fs=7)

    # ------------------------------------------------ catena del segnale
    ys = 36.0
    # J1: connettore della barra (Molex KK 254 al posto della strip: ROSSO)
    s.ax.add_patch(Rectangle((1.9, 34.0), 1.3, 2.7, fill=False, color=RED, lw=1.0, zorder=2))
    s.ax.add_patch(Circle((2.55, 36.0), 0.2, fill=False, color=RED, lw=0.8))
    s.ax.add_patch(Circle((2.55, 34.7), 0.2, fill=False, color=RED, lw=0.8))
    s.text(1.4, 38.4, f"{r('J1')}  Molex KK", c=RED, fs=FS - 0.5, ha="left")
    s.text(1.2, 32.4, "dal SiPM della barra\n1 = anodo (segnale)\n2 = catodo (bias)", fs=FS - 1.2, va="top")
    s.text(3.35, 36.25, "1", c=RED, fs=FS - 2)
    s.text(2.0, 33.75, "2", c=RED, fs=FS - 2)
    s.wire((2.75, 36.0), (5.5, 36.0))
    s.tp((4.3, 36.0), "SiPM", "up")
    s.dot((4.3, 36.0), c=RED)
    s.dot((5.5, 36.0))
    s.comp("R", r("R10"), (5.5, 36.0), "down", loc="bot")
    s.gnd((5.5, 33.5))
    s.comp("C", r("C7"), (5.5, 36.0), "right", length=2.6, loc="top")
    xb = 9.0                                     # nodo Q1B
    s.wire((8.1, 36.0), (xb, 36.0))
    s.dot((xb, 36.0))
    s.comp("R", r("R9"), (xb, 36.0), "down", loc="bot")
    s.gnd((xb, 33.5))
    q1 = s.add(elm.BjtNpn(circle=True).right().anchor("base").at((xb + 1.3, ys))
               .label(f"{r('Q1')}\nBFR93A", loc="right", fontsize=FS, ofst=(0.05, -0.9)))
    s.wire((xb, ys), (xb + 1.3, ys))
    s.gnd(q1.emitter)
    xc, yc = q1.collector.x, ys + 3.2            # nodo Q1C
    s.wire(q1.collector, (xc, yc))
    s.dot((xc, yc))
    s.comp("R", r("R11"), (xc, yc), "left", length=xc - xb, loc="top")
    s.wire((xb, yc), (xb, ys))
    s.comp("R", r("R12"), (xc, yc), "up", length=2.3, loc="bot")
    s.vdd((xc, yc + 2.3), "+3,3V")
    q2 = s.add(elm.BjtPnp(circle=True).right().anchor("base").at((xc + 3.4, yc))
               .label(f"{r('Q2')}\nMMBTH81", loc="right", fontsize=FS, ofst=(0.05, -0.2)))
    s.wire((xc, yc), (xc + 3.4, yc))
    s.comp("R", r("R13"), q2.emitter, "up", length=1.9, loc="top")
    s.vdd((q2.emitter.x, q2.emitter.y + 1.9), "+3,3V")
    xq2, yq = q2.collector.x, ys - 0.5           # nodo Q2C
    s.wire(q2.collector, (xq2, yq))
    s.dot((xq2, yq))
    s.comp("R", r("R14"), (xq2, yq), "down", loc="bot")
    s.gnd((xq2, yq - 2.5))
    s.comp("C", r("C11"), (xq2, yq), "right", length=3.2, loc="top")
    xi = xq2 + 4.3                               # nodo CMP_IN
    s.wire((xq2 + 3.2, yq), (xi, yq))
    s.dot((xi, yq))
    s.comp("R", r("R15"), (xi, yq), "down", loc="top")
    s.gnd((xi, yq - 2.5))
    s.tp((xi, yq), "IN", "up")
    # comparatore MAX961 (pin LE, SHDN, GND in basso)
    ux, uy, uw, uh = xi + 2.6, yq - 4.0, 4.2, 5.2
    u3 = s.ic(ux, uy, uw, uh, [(1, "IN+", "left", 4.0), (2, "IN−", "left", 2.6),
                               (8, "VCC", "top", 2.1), (3, "SHDN", "bottom", 0.7),
                               (5, "GND", "bottom", 2.1), (4, "LE", "bottom", 3.5),
                               (6, "Q", "right", 4.0), (7, "Q̅", "right", 1.6)],
              f"{r('U3')}\nMAX961")
    DRAWN[r("U3")] = "MAX961"
    s.wire((xi, yq), u3[1])
    s.vdd(u3[8], "+3,3V")
    s.gnd(u3[3])
    s.gnd(u3[5])
    # latch: R16 a massa e C9 tra LE e Q
    xle, yle = u3[4][0], u3[4][1] - 0.6
    s.wire(u3[4], (xle, yle))
    s.dot((xle, yle))
    s.comp("R", r("R16"), (xle, yle), "down", length=2.0, loc="top")
    s.gnd((xle, yle - 2.0))
    xq = u3[6][0] + 1.4
    s.wire(u3[6], (xq, u3[6][1]))
    s.dot((xq, u3[6][1]))
    s.comp("C", r("C9"), (xle, yle), "right", length=xq - xle, loc="bot")
    s.wire((xq, yle), (xq, u3[6][1]))
    s.tp((xq, u3[6][1]), "OUT", "up")
    # soglia: V2 tra R19 (+3,6 V) e R18 (massa), cursore -> R17 -> IN-
    xth = u3[2][0] - 0.9
    s.wire(u3[2], (xth, u3[2][1]))
    s.dot((xth, u3[2][1]))
    yth = 29.0
    s.wire((xth, u3[2][1]), (xth, yth))
    s.tp((xth, (u3[2][1] + yth) / 2 + 0.3), "SOGLIA", "left")
    s.dot((xth, (u3[2][1] + yth) / 2 + 0.3), c=RED)
    s.dot((xth, yth))
    s.comp("R", r("R17"), (xth, yth), "down", length=2.3, loc="bot")
    v2 = s.add(elm.Potentiometer().right().at((xth - 1.25, yth - 3.6)).color(BLACK))
    DRAWN[r("V2")] = "10k"
    s.text(v2.end.x + 0.2, v2.end.y - 1.1, f"{r('V2')} 10k\nregola la soglia", fs=FS - 0.4, va="top")
    s.wire((xth, yth - 2.3), (xth, v2.tap.y) if abs(v2.tap.x - xth) < 0.05 else (v2.tap.x, yth - 2.3), v2.tap)
    s.comp("R", r("R19"), v2.start, "left", length=2.3, loc="bot")
    s.vdd((v2.start.x - 2.3, v2.start.y), "+3,6V")
    s.comp("R", r("R18"), v2.end, "right", length=1.8, loc="top")
    s.gnd((v2.end.x + 1.8, v2.end.y))
    # lettura della soglia per il monitor (ROSSO): R52 10k + C52 100n -> U12
    s.comp("R", r("R52"), (xth, yth), "left", length=2.6, c=RED, loc="top")
    xm = xth - 2.6
    s.dot((xm, yth), c=RED)
    s.comp("C", r("C52"), (xm, yth), "down", length=1.9, c=RED, loc="bot")
    s.gnd((xm, yth - 1.9), c=RED)
    s.wire((xm, yth), (xm - 0.9, yth), c=RED)
    s.text(xm - 1.0, yth, f"MONTH{n} -> U12\nlettura della soglia", c=RED, fs=FS - 0.9, ha="right")

    # uscita: buffer 3,3 V + 33 ohm -> LEMO (ROSSO: al posto del buffer a transistor e del TTL 5 V)
    yo = u3[6][1]
    b = s.add(logic.Buf(inputs=1).right().anchor("in1").at((xq + 1.0, yo)).color(RED))
    DRAWN[r("U9")] = "74LVC1G17"
    s.text(b.out.x - 0.7, yo - 1.0, f"{r('U9')}\n74LVC1G17", c=RED, fs=FS - 0.5, ha="center", va="top")
    s.wire((xq, yo), b.in1, c=RED)
    s.comp("R", r("R23"), b.out, "right", length=2.3, c=RED, loc="top")
    xo = b.out.x + 2.3
    s.dot((xo, yo), c=RED)
    s.lemo((xo + 0.6, yo), f"{r('J4')} LEMO\nuscita 0-3,3 V", c=RED)
    s.wire((xo, yo), (xo + 0.6, yo), c=RED)
    s.wire((xo, yo), (xo, yo + 2.4), (xo + 1.0, yo + 2.4), c=RED)
    s.text(xo + 1.1, yo + 2.4, f"BUF_Y{n} -> JP{n} (coincidenza)", c=RED, fs=FS - 0.8)
    s.text(xq + 0.6, yo - 3.1, "INFN: buffer 5 V a due transistor\ne uscita TTL (MCP1402): sostituiti",
           c=RED, fs=FS - 1.6, style="italic", va="top")

    # LED: monostabile TLC555 (~11 ms) avviato da Q negato
    lx, ly = 46.0, 21.0
    u2 = s.ic(lx, ly, 5.0, 5.4, [(2, "TRIG", "left", 4.2), (6, "THR", "left", 2.6), (7, "DIS", "left", 1.2),
                                 (8, "VCC", "top", 1.3), (4, "RST", "top", 3.7), (3, "OUT", "right", 4.2),
                                 (5, "CTRL", "right", 1.2), (1, "GND", "bottom", 2.5)],
              f"{r('U2')}\nTLC555")
    DRAWN[r("U2")] = "TLC555/LMC555"
    ytr = 29.6
    s.wire(u3[7], (u3[7][0] + 0.6, u3[7][1]), (u3[7][0] + 0.6, ytr), (u2[2][0] - 0.5, ytr),
           (u2[2][0] - 0.5, u2[2][1]), u2[2])
    s.text(u3[7][0] + 3.0, ytr + 0.35, "Q negato avvia il 555 (LED acceso ~11 ms)", fs=FS - 1.4, style="italic")
    s.vdd(u2[8], "+3,3V")
    s.wire(u2[4], (u2[4][0], u2[4][1] + 0.5), (u2[8][0], u2[4][1] + 0.5))
    s.dot((u2[8][0], u2[4][1] + 0.5))
    s.gnd(u2[1])
    xt = u2[6][0] - 0.9
    s.wire(u2[6], (xt, u2[6][1]))
    s.wire(u2[7], (xt, u2[7][1]), (xt, u2[6][1]))
    s.dot((xt, u2[6][1]))
    xt2 = xt - 1.9
    s.wire((xt, u2[6][1]), (xt2, u2[6][1]))
    s.dot((xt2, u2[6][1]))
    s.comp("R", r("R20"), (xt2, u2[6][1]), "up", length=3.4, loc="top")
    s.vdd((xt2, u2[6][1] + 3.4), "+3,3V")
    s.comp("C", r("C21"), (xt2, u2[6][1]), "down", length=2.4, loc="top")
    s.gnd((xt2, u2[6][1] - 2.4))
    s.comp("C", r("CF6"), u2[5], "down", length=1.9, loc="bot")
    s.gnd((u2[5][0], u2[5][1] - 1.9))
    s.comp("R", r("R21"), u2[3], "right", length=2.4, loc="top")
    led = s.add(elm.LED().down().at((u2[3][0] + 2.4, u2[3][1])).label(f"{r('D3')}\nLED rosso", loc="bot",
                                                                       fontsize=FS))
    DRAWN[r("D3")] = "LED rosso"
    s.gnd(led.end)

    # ------------------------------------------------ alimentazione del SiPM (~38,4 V)
    yb0 = 15.5
    op = s.add(elm.Opamp(leads=True).right().anchor("in2").at((15.0, yb0)))
    DRAWN[r("U8")] = "LT1636"
    s.text(op.in2.x + 1.55, (op.in1.y + op.in2.y) / 2, f"{r('U8')}\nLT1636", fs=FS - 0.6, ha="left",
           weight="bold")
    s.text(op.in1.x - 0.9, op.in1.y + 4.6, f"{r('U8')}: V+ = VOUT40 (39,4 V, foglio 2), V− = massa",
           fs=FS - 1.3)
    xs = op.in2.x - 1.2                          # nodo VSET (+)
    s.wire(op.in2, (xs, op.in2.y))
    s.dot((xs, op.in2.y))
    s.comp("C", r("C4"), (xs, op.in2.y), "down", length=2.4, loc="bot")
    s.gnd((xs, op.in2.y - 2.4))
    xr6 = xs - 1.9
    s.wire((xs, op.in2.y), (xr6, op.in2.y))
    s.dot((xr6, op.in2.y))
    s.comp("R", r("R6"), (xr6, op.in2.y), "down", length=2.4, loc="bot")
    s.gnd((xr6, op.in2.y - 2.4))
    xv1 = xr6 - 2.6
    v1 = s.add(elm.Potentiometer().down().at((xv1, op.in2.y + 1.5)).color(BLACK))
    DRAWN[r("V1")] = "10k"
    s.wire((xr6, op.in2.y), (v1.tap.x, op.in2.y) if abs(v1.tap.y - op.in2.y) < 0.05 else (xr6 - 0.6, op.in2.y),
           *([] if abs(v1.tap.y - op.in2.y) < 0.05 else [(xr6 - 0.6, v1.tap.y), v1.tap]))
    s.text(xv1 - 0.6, op.in2.y + 0.2, f"{r('V1')} 10k\nregola la\ntensione", fs=FS - 0.6, ha="right")
    d1 = s.add(elm.Diode().right().at((v1.start.x - 3.0, v1.start.y)).to(v1.start)
               .label(f"{r('D1')}\n1N4148", loc="top", fontsize=FS))
    DRAWN[r("D1")] = "1N4148"
    s.text(v1.start.x - 3.1, v1.start.y, "VREF_B\n3,6 V (U7)", fs=FS - 1.0, ha="right")
    s.comp("R", r("R7"), v1.end, "down", length=2.2, loc="bot")
    s.gnd((v1.end.x, v1.end.y - 2.2))
    # retroazione: R4 a massa, R5 dall'uscita (guadagno 1 + 15k/1k2)
    xn = op.in1.x - 0.7
    s.wire(op.in1, (xn, op.in1.y))
    s.dot((xn, op.in1.y))
    yfb = op.in1.y + 2.3
    xout = op.out.x + 0.9
    s.wire((xn, op.in1.y), (xn, yfb))
    s.comp("R", r("R5"), (xn, yfb), "right", length=xout - xn, loc="top")
    s.wire(op.out, (xout, op.out.y))
    s.wire((xout, yfb), (xout, op.out.y))
    s.dot((xout, op.out.y))
    s.comp("R", r("R4"), (xn, op.in1.y), "up", length=0.0001) if False else None
    s.wire((xn, op.in1.y), (xn, op.in1.y))
    xr4 = xn - 0.0
    s.text(xout + 0.25, op.out.y - 0.45, "VREG38", fs=FS - 1.6)
    # R4: dal nodo INV verso massa, disegnato a sinistra sopra il nodo VSET
    s.comp("R", r("R4"), (xn, yfb), "left", length=2.0, loc="top")
    s.gnd((xn - 2.0, yfb))
    # VREG38 -> R8 -> BIAS (C6) -> J1.2
    s.comp("R", r("R8"), (xout, op.out.y), "right", length=2.4, loc="top")
    xbias = xout + 3.2
    s.wire((xout + 2.4, op.out.y), (xbias, op.out.y))
    s.dot((xbias, op.out.y))
    s.comp("C", r("C6"), (xbias, op.out.y), "down", length=2.4, loc="bot")
    s.gnd((xbias, op.out.y - 2.4))
    s.tp((xbias, op.out.y), "BIAS", "right")
    s.wire((xbias, op.out.y), (xbias, 22.3), (1.1, 22.3), (1.1, 34.7), (2.35, 34.7))
    s.text(xbias + 0.3, 21.85, "BIAS ~38,4 V -> catodo del SiPM (calza del cavo, J1 pin 2)", fs=FS - 1.0)
    # monitor del bias (ROSSO): 1M / 43k + 100n su VREG38 -> U11 (dentro l'anello: il bias non cambia)
    s.comp("R", r("R50"), (xout, op.out.y), "down", length=2.4, c=RED, loc="bot")
    ym = op.out.y - 2.4
    s.dot((xout, ym), c=RED)
    s.comp("R", r("R51"), (xout, ym), "down", length=2.2, c=RED, loc="bot")
    s.gnd((xout, ym - 2.2), c=RED)
    s.wire((xout, ym), (xout + 2.8, ym), c=RED)
    s.comp("C", r("C50"), (xout + 2.8, ym), "down", length=1.9, c=RED, loc="bot")
    s.gnd((xout + 2.8, ym - 1.9), c=RED)
    s.wire((xout + 2.8, ym), (xout + 5.4, ym), c=RED)
    s.text(xout + 5.5, ym, f"MON{n} -> U11\nlettura del bias", c=RED, fs=FS - 0.9)

    # ------------------------------------------------ disaccoppiamenti del canale
    xd, yd = 44.0, 14.2
    s.text(xd - 1.0, yd + 1.9, "Disaccoppiamenti 100 nF vicino a ogni integrato:", fs=FS - 0.8)
    for k, (ref, lab, c) in enumerate([("CF1", "ampl.", BLACK), ("CF2", r("U3"), BLACK),
                                       ("CF5", r("U2"), BLACK), ("CF10", r("U9"), RED)]):
        x = xd + k * 6.2
        s.vdd((x, yd), "+3,3V", c=c)
        s.comp("C", r(ref), (x, yd), "down", length=1.6, c=c, loc="bot", lab=f"{r(ref)} ({lab})")
        s.gnd((x, yd - 1.6), c=c)
    s.save()


# ===================================================================== schema a blocchi
def page_overview(pdf, sheet_no, sheets):
    s = Sheet(pdf)
    ax = s.ax
    s.frame("", "SCHEMA A BLOCCHI", sheet_no, sheets)
    s.text(1.8, 47.3, "SCHEMA A BLOCCHI", fs=17, weight="bold")
    s.text(1.8, 45.6, "tre canali identici (ognuno col suo colore) + parti comuni; "
                      "in rosso le parti aggiunte o modificate rispetto al foglio INFN", fs=7)

    def box(x, y, w, h, t, c=BLACK, fill="white", fs=6.4, dashed=False, bold=False):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=c, lw=1.1,
                               ls="--" if dashed else "-", zorder=3))
        ax.text(x + w / 2, y + h / 2, t, color=c, fontsize=fs, ha="center", va="center", zorder=4,
                fontweight="bold" if bold else "normal")
        return (x, y, w, h)

    def arrow(p, q, c=BLACK, lw=1.0):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=7, color=c, lw=lw, zorder=2,
                                     shrinkA=0, shrinkB=0))

    # parti comuni (colonna sinistra)
    s.text(1.8, 43.0, "PARTI COMUNI (foglio 2)", fs=7.2, weight="bold")
    b5 = box(1.8, 38.2, 11.0, 3.6, "ingresso 5 V (J3)\n-> 3,3 V  MCP1825 (U6)")
    bhv = box(1.8, 29.6, 11.0, 5.6, "alta tensione\nLT3461 (U1)\n39,4 V", bold=True)
    s.text(7.3, 29.0, "R3 = 255k (INFN 270k)", c=RED, fs=5.6, ha="center")
    bref = box(1.8, 21.0, 11.0, 5.6, "riferimenti 3,6 V\nLP2985 (U5, U7)")
    s.text(7.3, 20.4, "uscite 2,2 µF (INFN 100n)", c=RED, fs=5.6, ha="center")
    bmon = box(1.8, 11.4, 11.0, 6.6, "monitor\nADC MCP3424\nU11 (bias, 40 V)\nU12 (soglie, °C)", c=RED)
    box(1.8, 9.6 - 0.0, 11.0, 1.4, "J6 I2C -> Raspberry Pi", c=RED, fs=5.6)

    # canali
    x0, w = 15.5, 41.5
    for k, n in enumerate(N.CHANNELS):
        col, tint = CH_COL[n], CH_TINT[n]
        y0 = 33.6 - k * 10.6
        ax.add_patch(Rectangle((x0, y0), w, 9.6, facecolor=tint, edgecolor=col, lw=2.0, zorder=1))
        ax.text(x0 + 0.5, y0 + 9.0, f"CANALE {n}  (foglio {n + 2})", color=col, fontsize=8, fontweight="bold",
                va="center", zorder=4)
        yr = y0 + 4.9
        bb = box(x0 + 0.6, yr - 1.3, 4.6, 2.6, "barra\n+ SiPM", c=col, fill="white", dashed=True)
        bj = box(x0 + 6.0, yr - 1.1, 3.6, 2.2, f"J{n}01\nMolex KK", c=RED)
        ba = box(x0 + 10.6, yr - 1.3, 6.4, 2.6, f"amplificatore\nQ{n}01 - Q{n}02")
        bc = box(x0 + 18.0, yr - 1.3, 6.8, 2.6, f"comparatore\nU{n}03 MAX961")
        bu = box(x0 + 25.8, yr - 1.3, 5.6, 2.6, f"buffer 3,3 V\nU{n}09", c=RED)
        bl = box(x0 + 32.4, yr - 1.1, 4.0, 2.2, f"LEMO\nJ{n}04", c=RED)
        for a, b in ((bb, bj), (bj, ba), (ba, bc), (bc, bu), (bu, bl)):
            arrow((a[0] + a[2], yr), (b[0], yr), c=RED if a in (bc, bu) or b in (bj, bu, bl) else BLACK)
        # riga di supporto
        ys = y0 + 0.6
        bbias = box(x0 + 6.0, ys, 9.4, 2.2, f"bias SiPM ~38,4 V\nLT1636 U{n}08 (V{n}01)")
        bth = box(x0 + 18.0, ys, 6.8, 2.2, f"soglia\nV{n}02")
        bled = box(x0 + 25.8, ys, 5.6, 2.2, f"LED\n555 U{n}02")
        arrow((bbias[0] + 1.8, ys + 2.2), (bj[0] + 1.8, yr - 1.1))
        arrow((bth[0] + 3.4, ys + 2.2), (bc[0] + 3.4, yr - 1.3))
        arrow((bc[0] + 6.8, yr - 0.8), (bled[0] + 1.0, ys + 2.2))
        ax.text(x0 + 15.7, ys + 0.5, "lettura bias -> U11\nlettura soglia -> U12", color=RED, fontsize=5.2,
                va="center", zorder=4)
        # uscite verso coincidenza
        arrow((bu[0] + 2.8, yr + 1.3), (bu[0] + 2.8, y0 + 8.4), c=RED, lw=0.8)
        ax.plot([bu[0] + 2.8, x0 + w + 0.6], [y0 + 8.4] * 2, color=RED, lw=0.8, zorder=2)
        # alimentazioni dai blocchi comuni
        arrow((bhv[0] + bhv[2], bhv[1] + 2.8), (x0, ys + 1.1), c=BLACK, lw=0.7)
        arrow((bref[0] + bref[2], bref[1] + 2.8), (x0, ys + 1.8), c=BLACK, lw=0.7)
    s.text(13.3, 36.4, "39,4 V ai\nregolatori\ndel bias", fs=5.2, ha="left") if False else None
    # coincidenza e uscita (colonna destra)
    xr = 58.8
    for k, n in enumerate(N.CHANNELS):
        y0 = 33.6 - k * 10.6
        ax.plot([x0 + w + 0.6, xr + 1.0], [y0 + 8.4, y0 + 8.4], color=RED, lw=0.8, zorder=2)
        arrow((xr + 1.0, y0 + 8.4), (xr + 1.0, 24.6 if k == 0 else (24.6 if k == 1 else 18.2)), c=RED, lw=0.8) \
            if False else None
    band = box(xr, 18.0, 10.0, 7.0, "COINCIDENZA\nAND a 3\n74LVC1G11 (U10)\nJP1-JP3: includi canale", c=RED, fs=6.0)
    for k, n in enumerate(N.CHANNELS):
        y0 = 33.6 - k * 10.6
        yy = y0 + 8.4
        xx = xr + 2.5 + k * 2.5
        if yy > 25.0:
            ax.plot([x0 + w + 0.6, xx], [yy, yy], color=RED, lw=0.8, zorder=2)
            arrow((xx, yy), (xx, 25.0), c=RED, lw=0.8)
        else:
            arrow((x0 + w + 0.6, yy), (xr, yy), c=RED, lw=0.8)
    bJ5 = box(xr + 1.5, 12.8, 7.0, 2.6, "LEMO J5\nuscita AND", c=RED)
    arrow((xr + 5.0, 18.0), (xr + 5.0, 15.4), c=RED)
    s.text(xr, 11.2, "uscite J104/J204/J304\ne J5 -> GPIO del\nRaspberry Pi (0-3,3 V)", c=RED, fs=5.6, va="top")

    # elenco modifiche
    lines = ["Cosa cambia rispetto al foglio INFN (S. Gallian, rev. A):",
             "- 3 canali sulla stessa scheda; alta tensione, 3,3 V e riferimenti in comune",
             "- R3 = 255k: alta tensione 39,4 V (INFN 270k = 41,7 V > 40 V max LT3461)",
             "- uscite dei regolatori da 2,2 µF, come da datasheet (INFN 100n)",
             "- uscita 0-3,3 V su LEMO per il Raspberry (74LVC1G17 + 33 ohm)",
             "- coincidenza AND a 3; monitor di bias, 40 V, soglie e temperatura",
             "- connettori Molex KK per barre e I2C; test point su ogni nodo utile"]
    for i, t in enumerate(lines):
        ax.text(15.5, 9.6 - i * 0.98, t, fontsize=6.6 if i else 7.0, color=BLACK if i == 0 else RED,
                fontweight="bold" if i == 0 else "normal", va="center", zorder=4)
    s.save()


# ===================================================================== parti comuni
def page_common(pdf, sheet_no, sheets):
    s = Sheet(pdf)
    s.frame("", "PARTI COMUNI ai tre canali", sheet_no, sheets)
    s.text(1.8, 47.3, "PARTI COMUNI", fs=17, weight="bold")
    s.text(1.8, 45.6, "alimentazioni, alta tensione, riferimenti 3,6 V, monitor e coincidenza: "
                      "un solo esemplare per tutta la scheda", fs=7)

    def title(x, y, t, c=BLACK):
        s.text(x, y, t, c=c, fs=FS + 0.6, weight="bold")

    # ---------------- ingresso 5 V e 3,3 V
    title(1.8, 43.2, "Ingresso 5 V e 3,3 V")
    s.ax.add_patch(Rectangle((1.9, 37.4), 1.2, 2.6, fill=False, color=BLACK, lw=1.0))
    s.text(1.6, 40.6, "J3 5 V", fs=FS - 0.5)
    s.wire((3.1, 39.4), (4.2, 39.4))
    s.wire((3.1, 38.0), (3.6, 38.0))
    s.gnd((3.6, 38.0))
    s.text(3.25, 39.65, "2", fs=FS - 2)
    s.text(3.25, 38.25, "1", fs=FS - 2)
    s.dot((4.2, 39.4))
    s.vdd((4.2, 39.4), "+5V")
    s.comp("C", "CF8", (5.6, 39.4), "down", length=1.9, loc="bot")
    s.gnd((5.6, 37.5))
    s.wire((4.2, 39.4), (8.2, 39.4))
    s.dot((5.6, 39.4))
    s.tp((7.0, 39.4), "5V", "up")
    s.dot((7.0, 39.4), c=RED)
    u6 = s.ic(8.9, 37.6, 3.4, 2.6, [(1, "VIN", "left", 1.8), (3, "VOUT", "right", 1.8), (2, "GND", "bottom", 1.7)],
              "U6\nMCP1825-3,3")
    DRAWN["U6"] = val_of("U6")
    s.gnd(u6[2])
    xo = u6[3][0] + 0.8
    s.wire(u6[3], (xo + 3.2, u6[3][1]))
    s.dot((xo, u6[3][1]))
    s.comp("C", "CF9", (xo, u6[3][1]), "down", length=1.9, c=RED, loc="bot")
    s.gnd((xo, u6[3][1] - 1.9), c=RED)
    s.text(xo + 0.5, u6[3][1] - 2.9, "INFN: 100n", c=RED, fs=FS - 1.6, style="italic")
    s.tp((xo + 2.0, u6[3][1]), "3,3V", "down")
    s.dot((xo + 2.0, u6[3][1]), c=RED)
    s.vdd((xo + 3.2, u6[3][1]), "+3,3V")
    s.text(2.0, 35.8, "+3,3 V: amplificatori, comparatori, 555, buffer, AND, ADC", fs=FS - 1.2, style="italic")
    s.text(2.0, 34.9, "test point: 5V, GND (TP6), 3,3V, 40V, 3,6V, AND; 8 fori di fissaggio M3 a massa (MH1-MH8)",
           c=RED, fs=FS - 1.4, style="italic")

    # ---------------- alta tensione
    title(1.8, 33.4, "Alta tensione: survoltore LT3461 (5 V -> 39,4 V)")
    u1 = s.ic(8.0, 25.2, 4.2, 4.8, [(6, "VIN", "left", 3.8), (4, "SHDN", "left", 2.4), (2, "GND", "bottom", 2.1),
                                   (1, "SW", "top", 2.1), (5, "VOUT", "right", 3.8), (3, "FB", "right", 1.2)],
              "U1\nLT3461")
    DRAWN["U1"] = "LT3461"
    s.wire(u1[6], (5.0, u1[6][1]))
    s.wire(u1[4], (5.0, u1[4][1]), (5.0, u1[6][1]))
    s.dot((5.0, u1[6][1]))
    s.wire((5.0, u1[6][1]), (5.0, 31.6))
    s.dot((5.0, 31.6))
    s.vdd((3.2, 31.6), "+5V")
    s.wire((3.2, 31.6), (5.0, 31.6))
    s.comp("C", "C22", (3.2, 31.6), "down", length=2.0, loc="bot")
    s.gnd((3.2, 29.6))
    s.comp("L", "L1", (5.0, 31.6), "right", length=5.1, loc="top")
    s.wire((10.1, 31.6), u1[1])
    s.gnd(u1[2])
    xv = u1[5][0] + 1.6                           # nodo VOUT40
    s.wire(u1[5], (xv + 6.0, u1[5][1]))
    s.dot((xv, u1[5][1]))
    s.comp("C", "C2", (xv, u1[5][1]), "down", length=2.3, loc="bot")
    s.gnd((xv, u1[5][1] - 2.3))
    s.dot((xv + 3.0, u1[5][1]))
    s.comp("C", "C3", (xv + 3.0, u1[5][1]), "down", length=2.3, loc="bot")
    s.gnd((xv + 3.0, u1[5][1] - 2.3))
    s.tp((xv + 4.6, u1[5][1]), "40V", "up")
    s.dot((xv + 4.6, u1[5][1]), c=RED)
    s.text(xv + 6.2, u1[5][1] + 0.1, "VOUT40 -> V+ di U108, U208, U308\n(regolatori del bias, fogli 3-5)",
           fs=FS - 1.0)
    # retroazione: R3 (255k, ROSSO) || C1 da VOUT40 a FB; R1 || R2 || R22 da FB a massa
    xr3 = u1[5][0] + 0.6
    s.wire((xr3, u1[5][1]), (xr3, u1[3][1] + 0.0))
    s.dot((xr3, u1[5][1]))
    s.wire(u1[3], (u1[3][0] + 0.0, u1[3][1]))
    yfb = 23.0
    s.wire(u1[3], (xr3 - 0.0, u1[3][1])) if False else None
    s.wire((u1[3][0], u1[3][1]), (u1[3][0], yfb))
    s.dot((u1[3][0], yfb))
    s.comp("R", "R3", (u1[3][0], yfb), "right", length=5.0, c=RED, loc="top")
    s.text(u1[3][0] + 5.4, yfb + 0.9, "INFN: 270k -> 41,7 V (max assoluto LT3461: 40 V)", c=RED,
           fs=FS - 1.6, ha="left", va="center", style="italic")
    s.wire((u1[3][0] + 5.0, yfb), (xv + 5.6, yfb), (xv + 5.6, u1[5][1]))
    s.dot((xv + 5.6, u1[5][1]))
    s.wire((u1[3][0] + 0.0, yfb), (u1[3][0], yfb))
    s.wire((u1[3][0] + 5.0, yfb), (u1[3][0] + 5.0, yfb - 1.6))
    s.wire((u1[3][0], yfb), (u1[3][0], yfb - 1.6))
    s.comp("C", "C1", (u1[3][0], yfb - 1.6), "right", length=5.0, loc="bot")
    for k, ref in enumerate(("R1", "R2", "R22")):
        x = u1[3][0] - 1.5 - k * 2.0
        s.wire((u1[3][0], yfb), (x, yfb))
        s.dot((x, yfb))
        s.comp("R", ref, (x, yfb), "down", length=2.2, loc="bot")
        s.gnd((x, yfb - 2.2))


    # ---------------- riferimenti 3,6 V
    title(1.8, 16.8, "Riferimenti 3,6 V (LP2985)")
    for k, (u, cf, net, dest) in enumerate([("U5", "CF4", "+3V6", "R19 dei tre canali\n(alimentazione delle soglie)"),
                                            ("U7", "CF7", "VREF_B", "D1 dei tre canali\n(riferimento del bias)")]):
        y0 = 11.2 - k * 5.4
        ux = 5.0
        uu = s.ic(ux, y0, 3.6, 3.0, [(1, "VIN", "left", 2.2), (3, "ON", "left", 0.8), (2, "GND", "bottom", 1.8),
                                    (5, "VOUT", "right", 2.2), (4, "BYP", "right", 0.8)], f"{u}\nLP2985-3,6")
        DRAWN[u] = val_of(u)
        s.wire(uu[1], (3.0, uu[1][1]))
        s.wire(uu[3], (3.0, uu[3][1]), (3.0, uu[1][1]))
        s.dot((3.0, uu[1][1]))
        s.vdd((3.0, uu[1][1]), "+5V")
        s.gnd(uu[2])
        s.text(uu[4][0] + 0.2, uu[4][1], "n.c.", fs=FS - 1.6)
        xo2 = uu[5][0] + 0.9
        s.wire(uu[5], (xo2 + 3.2, uu[5][1]))
        s.dot((xo2, uu[5][1]))
        s.comp("C", cf, (xo2, uu[5][1]), "down", length=1.8, c=RED, loc="bot")
        s.gnd((xo2, uu[5][1] - 1.8), c=RED)
        s.text(xo2 + 0.5, uu[5][1] - 2.6, "INFN: 100n", c=RED, fs=FS - 1.8, style="italic")
        if k == 0:
            s.tp((xo2 + 1.7, uu[5][1]), "3,6V", "up")
            s.dot((xo2 + 1.7, uu[5][1]), c=RED)
        s.text(xo2 + 3.4, uu[5][1], f"{net} -> {dest}", fs=FS - 1.0)

    # ---------------- monitor (tutto ROSSO)
    mx = 37.0
    title(mx, 44.3, "Monitor: bias, alta tensione, soglie, temperatura -> Raspberry Pi (I2C)", c=RED)
    u11 = s.ic(mx + 9.0, 34.6, 4.6, 7.2,
               [(1, "CH1+", "left", 6.3), (2, "CH1−", "left", 5.4), (3, "CH2+", "left", 4.5), (4, "CH2−", "left", 3.6),
                (11, "CH3+", "left", 2.7), (12, "CH3−", "left", 1.8), (13, "CH4+", "left", 0.9),
                (14, "CH4−", "bottom", 0.9), (5, "VSS", "bottom", 2.3), (9, "A0", "bottom", 3.2), (10, "A1", "bottom", 4.0),
                (6, "VDD", "top", 2.3), (7, "SDA", "right", 5.0), (8, "SCL", "right", 3.6)],
               "U11\nMCP3424\n0x68", c=RED)
    DRAWN["U11"] = "MCP3424"
    for pin, lab in ((1, "MON1 ch1"), (3, "MON2 ch2"), (11, "MON3 ch3")):
        s.wire(u11[pin], (u11[pin][0] - 1.0, u11[pin][1]), c=RED)
        s.text(u11[pin][0] - 1.1, u11[pin][1], lab, c=RED, fs=FS - 1.3, ha="right")
    for pin in (2, 4, 12):
        s.wire(u11[pin], (u11[pin][0] - 0.5, u11[pin][1]), c=RED)
        s.gnd((u11[pin][0] - 0.5, u11[pin][1]), c=RED)
    for pin in (14, 5, 9, 10):
        s.gnd(u11[pin], c=RED)
    s.vdd(u11[6], "+3,3V", c=RED)
    s.comp("C", "CF12", (u11[6][0] + 2.0, u11[6][1] + 0.0), "down", length=1.6, c=RED, loc="bot")
    s.gnd((u11[6][0] + 2.0, u11[6][1] - 1.6), c=RED)
    s.text(u11[6][0] + 2.0, u11[6][1] + 0.5, "+3,3V", c=RED, fs=FS - 1.4, ha="center")
    # partitore sull'alta tensione -> CH4
    x40 = mx + 0.3
    s.text(x40 - 0.2, 41.2, "VOUT40", c=RED, fs=FS - 1.0)
    s.comp("R", "R40", (x40, 40.6), "down", length=2.3, c=RED, loc="bot")
    s.dot((x40, 38.3), c=RED)
    s.comp("R", "R41", (x40, 38.3), "down", length=2.1, c=RED, loc="bot")
    s.gnd((x40, 36.2), c=RED)
    s.wire((x40, 38.3), (x40 + 2.4, 38.3), c=RED)
    s.comp("C", "C40", (x40 + 2.4, 38.3), "down", length=1.7, c=RED, loc="bot")
    s.gnd((x40 + 2.4, 36.6), c=RED)
    s.wire((x40 + 2.4, 38.3), (x40 + 3.6, 38.3), (x40 + 3.6, u11[13][1]), u11[13], c=RED)
    s.text(x40 + 3.8, u11[13][1] + 0.35, "MON4", c=RED, fs=FS - 1.6)
    # U12: soglie + temperatura
    u12 = s.ic(mx + 9.0, 24.2, 4.6, 7.2,
               [(1, "CH1+", "left", 6.3), (2, "CH1−", "left", 5.4), (3, "CH2+", "left", 4.5), (4, "CH2−", "left", 3.6),
                (11, "CH3+", "left", 2.7), (12, "CH3−", "left", 1.8), (13, "CH4+", "left", 0.9),
                (14, "CH4−", "bottom", 0.9), (5, "VSS", "bottom", 2.3), (9, "A0", "top", 3.6), (10, "A1", "bottom", 3.9),
                (6, "VDD", "top", 2.3), (7, "SDA", "right", 5.0), (8, "SCL", "right", 3.6)],
               "U12\nMCP3424", c=RED)
    DRAWN["U12"] = "MCP3424"
    for pin, lab in ((1, "MONTH1 ch1"), (3, "MONTH2 ch2"), (11, "MONTH3 ch3")):
        s.wire(u12[pin], (u12[pin][0] - 1.0, u12[pin][1]), c=RED)
        s.text(u12[pin][0] - 1.1, u12[pin][1], lab, c=RED, fs=FS - 1.3, ha="right")
    for pin in (2, 4, 12):
        s.wire(u12[pin], (u12[pin][0] - 0.5, u12[pin][1]), c=RED)
        s.gnd((u12[pin][0] - 0.5, u12[pin][1]), c=RED)
    for pin in (14, 5, 10):
        s.gnd(u12[pin], c=RED)
    s.vdd(u12[6], "+3,3V", c=RED)
    s.wire(u12[9], (u12[9][0], u12[9][1] + 0.4), (u12[6][0], u12[9][1] + 0.4), c=RED)
    s.dot((u12[6][0], u12[9][1] + 0.4), c=RED)
    s.comp("C", "CF13", (u12[6][0] + 2.6, u12[6][1]), "down", length=1.6, c=RED, loc="bot")
    s.gnd((u12[6][0] + 2.6, u12[6][1] - 1.6), c=RED)
    s.text(u12[6][0] + 2.6, u12[6][1] + 0.5, "+3,3V", c=RED, fs=FS - 1.4, ha="center")
    s.text(u12[9][0] + 0.3, u12[9][1] + 1.1, "A0 = VDD: indirizzo diverso da U11", c=RED, fs=FS - 1.8)
    # termistore -> CH4 di U12
    xt = mx + 0.3
    s.vdd((xt, 29.4), "+3,3V", c=RED)
    s.comp("R", "R44", (xt, 29.4), "down", length=2.0, c=RED, loc="bot")
    s.dot((xt, 27.4), c=RED)
    s.comp("R", "RT1", (xt, 27.4), "down", length=2.0, c=RED, loc="bot", lab="RT1\nNTC 10k")
    s.gnd((xt, 25.4), c=RED)
    s.wire((xt, 27.4), (xt + 2.4, 27.4), c=RED)
    s.comp("C", "C41", (xt + 2.4, 27.4), "down", length=1.7, c=RED, loc="bot")
    s.gnd((xt + 2.4, 25.7), c=RED)
    s.wire((xt + 2.4, 27.4), (xt + 3.6, 27.4), (xt + 3.6, u12[13][1]), u12[13], c=RED)
    s.text(xt - 0.3, 23.6, "temperatura della scheda", c=RED, fs=FS - 1.4)
    # bus I2C -> R42/R43 -> J6
    xs = u11[7][0] + 1.2
    s.wire(u11[7], (xs, u11[7][1]), c=RED)
    s.wire(u11[8], (xs + 1.0, u11[8][1]), c=RED)
    s.wire(u12[7], (xs, u12[7][1]), (xs, u11[7][1]), c=RED)
    s.wire(u12[8], (xs + 1.0, u12[8][1]), (xs + 1.0, u11[8][1]), c=RED)
    s.dot((xs, u11[7][1]), c=RED)
    s.dot((xs + 1.0, u11[8][1]), c=RED)
    s.text(xs + 0.2, u12[7][1] - 0.4, "SDA_ADC", c=RED, fs=FS - 1.8)
    s.text(xs + 1.2, u12[8][1] - 0.4, "SCL_ADC", c=RED, fs=FS - 1.8)
    s.comp("R", "R42", (xs, u11[7][1]), "right", length=2.6, c=RED, loc="top")
    s.comp("R", "R43", (xs + 1.0, u11[8][1]), "right", length=1.6, c=RED, loc="bot")
    xj = xs + 2.6
    s.ax.add_patch(Rectangle((xj + 1.0, u11[8][1] - 2.2), 1.3, 4.2, fill=False, color=RED, lw=1.0))
    s.wire((xj, u11[7][1]), (xj + 1.0, u11[7][1]), c=RED)
    s.wire((xj, u11[8][1]), (xj + 1.0, u11[8][1]), c=RED)
    s.wire((xj + 0.6, u11[8][1] - 1.4), (xj + 1.0, u11[8][1] - 1.4), c=RED)
    s.gnd((xj + 0.6, u11[8][1] - 1.4), c=RED)
    for k, (yy, lab) in enumerate(((u11[8][1] - 1.4, "1 GND"), (u11[7][1], "2 SDA"), (u11[8][1], "3 SCL"))):
        s.text(xj + 2.45, yy, lab, c=RED, fs=FS - 1.3)
    s.text(xj + 0.9, u11[7][1] + 1.3, "J6 Molex KK\n-> Raspberry Pi", c=RED, fs=FS - 1.0, va="bottom")
    s.text(xj + 0.5, u11[8][1] - 3.0, "pull-up sul Raspberry", c=RED, fs=FS - 1.8, style="italic")

    # ---------------- coincidenza (ROSSO)
    cx0 = 37.0
    title(cx0, 19.9, "Coincidenza: AND dei tre canali -> LEMO", c=RED)
    u10 = s.ic(cx0 + 12.0, 10.6, 3.6, 7.0, [(3, "B", "left", 6.2), (1, "A", "left", 3.9), (6, "C", "left", 1.6),
                                           (5, "VCC", "top", 1.8), (2, "GND", "bottom", 1.8), (4, "Y", "right", 3.9)],
              "U10\n74LVC1G11\nAND a 3", c=RED)
    DRAWN["U10"] = "74LVC1G11"
    for k, (n, pin) in enumerate(((1, 3), (2, 1), (3, 6))):
        y = u10[pin][1]
        xjp = cx0 + 4.6
        s.text(cx0 + 0.2, y, f"BUF_Y{n} (ch{n})", c=RED, fs=FS - 1.3)
        s.wire((cx0 + 3.4, y), (xjp, y), c=RED)
        s.ax.add_patch(Rectangle((xjp, y - 0.25), 1.0, 0.5, fill=False, color=RED, lw=0.9))
        s.text(xjp + 0.5, y - 0.75, f"JP{n}", c=RED, fs=FS - 1.6, ha="center")
        DRAWN[f"JP{n}"] = val_of(f"JP{n}")
        xr = xjp + 2.6
        s.wire((xjp + 1.0, y), u10[pin], c=RED)
        s.dot((xr, y), c=RED)
        s.comp("R", f"R3{n}", (xr, y), "up", length=1.1, c=RED, loc="top", lab=f"R3{n}\n10k")
        s.vdd((xr, y + 1.1), "+3,3V", c=RED)
    s.text(cx0 + 0.2, 10.2, "JP chiuso = canale nella coincidenza; aperto = ingresso a 1 (pull-up) = escluso",
           c=RED, fs=FS - 1.6, style="italic", va="top")
    s.vdd(u10[5], "+3,3V", c=RED)
    s.gnd(u10[2], c=RED)
    s.comp("R", "R30", u10[4], "right", length=2.4, c=RED, loc="top")
    xa = u10[4][0] + 2.4
    s.dot((xa, u10[4][1]), c=RED)
    s.tp((xa, u10[4][1]), "AND", "up")
    s.lemo((xa + 0.3, u10[4][1]), "J5 LEMO AND", c=RED)
    s.wire((xa, u10[4][1]), (xa + 0.3, u10[4][1]), c=RED)
    s.comp("C", "CF11", (u10[5][0] + 2.0, u10[5][1]), "down", length=1.4, c=RED, loc="bot")
    s.gnd((u10[5][0] + 2.0, u10[5][1] - 1.4), c=RED)
    s.save()


def check():
    bad = [(r, v, N.COMPONENTS[r][1]) for r, v in DRAWN.items()
           if r in N.COMPONENTS and N.COMPONENTS[r][1] != v]
    missing = [r for r in DRAWN if r not in N.COMPONENTS]
    assert not bad and not missing, (bad, missing)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sheets = 5
    with PdfPages(OUT) as pdf:
        page_overview(pdf, 1, sheets)
        page_common(pdf, 2, sheets)
        for k, n in enumerate(N.CHANNELS):
            page_channel(pdf, n, k + 3, sheets)
    check()
    print("scritto", os.path.normpath(OUT), "-", len(DRAWN), "componenti disegnati, valori = netdata3")


if __name__ == "__main__":
    main()
