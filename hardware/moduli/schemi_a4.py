# -*- coding: utf-8 -*-
"""Schemi elettrici A4 leggibili (stile del foglio INFN, come generator/schema_a4.py) per i
moduli del sistema:

  pagina 1   architettura del sistema completo (rivelatore, scatolina, Raspberry, meteo, GPS)
  pagina 2   scatolina di acquisizione: ingressi LEMO e uscita PPS
  pagina 3   scatolina di acquisizione: Pico 2, GPS, hub I2C, porte, alimentazione
  pagina 4   modulo meteo (SHT45 + LPS22HH)

Valori e collegamenti da <modulo>/definizione.py (gli stessi di schema KiCad e PCB): lo script
controlla il valore di ogni componente disegnato e che ogni pin disegnato sia sulla rete giusta.

    python3 schemi_a4.py      ->  docs/schema_A4_moduli.pdf
"""
import importlib.util, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, FancyArrowPatch
import schemdraw
import schemdraw.elements as elm
import schemdraw.logic as logic

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "generator"))
OUT = os.path.join(HERE, "..", "..", "docs", "schema_A4_moduli.pdf")

W, H = 70.0, 49.5
RED = "#d00000"
BLACK, BLUE, GREEN, ORANGE, GREY = "black", "#1f5fbf", "#1a8a3a", "#c86400", "#666666"
FS = 6.5


def carica(cartella):
    spec = importlib.util.spec_from_file_location(cartella, os.path.join(HERE, cartella, "definizione.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.check()
    return m


ACQ = carica("acquisizione")
MET = carica("meteo")
DRAWN = []                         # (modulo, rif, valore disegnato)
PINS = []                          # (modulo, rif, pin, rete attesa)


class Sheet:
    def __init__(self, pdf, mod=None):
        self.pdf, self.mod = pdf, mod
        self.fig = plt.figure(figsize=(11.69, 8.27))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_axis_off()
        self.d = schemdraw.Drawing(canvas=self.ax, show=False)
        self.d.config(unit=2.5, fontsize=FS, lw=0.9)

    def add(self, e):
        return self.d.add(e)

    def wire(self, *pts, c=BLACK, lw=0.9):
        xs, ys = zip(*pts)
        self.ax.plot(xs, ys, color=c, lw=lw, solid_capstyle="round", zorder=1)

    def dot(self, p, c=BLACK):
        self.ax.add_patch(Circle(p, 0.12, color=c, zorder=3))

    def gnd(self, p, c=BLACK):
        x, y = p
        self.wire((x, y), (x, y - 0.35), c=c)
        for k, hw in enumerate((0.45, 0.3, 0.15)):
            self.ax.plot([x - hw, x + hw], [y - 0.35 - 0.17 * k] * 2, color=c, lw=0.9, zorder=1)

    def vdd(self, p, lab, c=BLACK):
        x, y = p
        self.wire((x, y), (x, y + 0.35), c=c)
        self.ax.plot([x - 0.4, x + 0.4], [y + 0.35] * 2, color=c, lw=0.9)
        self.text(x, y + 0.8, lab, c=c, fs=FS - 0.5, ha="center")

    def text(self, x, y, s, c=BLACK, fs=FS, ha="left", va="center", weight="normal", rot=0, style="normal"):
        self.ax.text(x, y, s, color=c, fontsize=fs, ha=ha, va=va, fontweight=weight, rotation=rot,
                     fontstyle=style, family="DejaVu Sans", zorder=5)

    def label(self, p, net, side="right", c=BLUE):
        """etichetta di rete (come in KiCad): stesso nome = stesso filo"""
        x, y = p
        ha = {"right": "left", "left": "right"}[side]
        dx = 0.15 if side == "right" else -0.15
        self.ax.text(x + dx, y, net, color=c, fontsize=FS - 0.8, ha=ha, va="center", family="DejaVu Sans",
                     zorder=5, bbox=dict(boxstyle="larrow,pad=0.15" if side == "left" else "rarrow,pad=0.15",
                                         fc="white", ec=c, lw=0.6))

    def val(self, ref):
        v = self.mod.COMPONENTS[ref][1]
        DRAWN.append((self.mod.NOME, ref, v))
        vv = v.replace("u", "µ") if v[:-1].replace(".", "").isdigit() and v.endswith("u") else v
        if vv.isdigit():
            vv += " Ω"
        return vv

    def pin(self, ref, num, net):
        PINS.append((self.mod.NOME, ref, str(num), net))

    def comp(self, kind, ref, p, direction, length=2.0, c=BLACK, loc="bot", nets=None):
        e = {"R": elm.Resistor, "C": elm.Capacitor}[kind]()
        e = getattr(e.at(p), direction)(length).color(c).label(f"{ref}\n{self.val(ref)}", loc=loc, fontsize=FS - 0.3)
        if nets:
            for k, n in enumerate(nets):
                self.pin(ref, k + 1, n)
        return self.add(e)

    def ic(self, x, y, w, h, pins, label, ref=None, c=BLACK, lead=0.7):
        """pins: (numero, nome, lato, posizione) -> {numero: estremo del pin}"""
        self.ax.add_patch(Rectangle((x, y), w, h, facecolor="#fffbe6", edgecolor=c, lw=1.0, zorder=2))
        self.text(x + w / 2, y + h / 2, label, c=c, fs=FS, ha="center", weight="bold")
        if ref:
            self.text(x + w, y + h + 0.35, ref, c=c, fs=FS, ha="right", va="bottom", weight="bold")
        out = {}
        for num, name, side, pos in pins:
            if side == "left":
                a, b, tx, ty, ha, va, nx, ny, nha, nva = (x, y + pos), (x - lead, y + pos), x - 0.1, y + pos + 0.2, "right", "bottom", x + 0.15, y + pos, "left", "center"
            elif side == "right":
                a, b, tx, ty, ha, va, nx, ny, nha, nva = (x + w, y + pos), (x + w + lead, y + pos), x + w + 0.1, y + pos + 0.2, "left", "bottom", x + w - 0.15, y + pos, "right", "center"
            elif side == "top":
                a, b, tx, ty, ha, va, nx, ny, nha, nva = (x + pos, y + h), (x + pos, y + h + lead), x + pos + 0.12, y + h + 0.1, "left", "bottom", x + pos, y + h - 0.2, "center", "top"
            else:
                a, b, tx, ty, ha, va, nx, ny, nha, nva = (x + pos, y), (x + pos, y - lead), x + pos + 0.12, y - 0.1, "left", "top", x + pos, y + 0.2, "center", "bottom"
            self.wire(a, b, c=c)
            self.text(tx, ty, str(num), c=c, fs=FS - 2.0, ha=ha, va=va)
            self.text(nx, ny, name, c=c, fs=FS - 1.4, ha=nha, va=nva)
            out[num] = b
        return out

    def lemo(self, p, ref, lab, c=BLACK, verso="right"):
        """connettore LEMO 00: centro = segnale (pin 1), corpo = massa (pin 2); p = estremo del segnale"""
        x, y = p
        s = 1 if verso == "right" else -1
        cx = x - s * 0.7
        self.ax.add_patch(Circle((cx, y), 0.55, fill=False, color=c, lw=1.0, zorder=3))
        self.ax.add_patch(Circle((cx, y), 0.15, color=c, zorder=3))
        self.wire((cx + s * 0.15, y), (x, y), c=c)
        self.gnd((cx, y - 0.55), c=c)
        self.text(cx, y + 0.75, f"{ref}  {lab}", c=c, fs=FS - 0.4, ha="center", va="bottom", weight="bold")
        DRAWN.append((self.mod.NOME, ref, self.mod.COMPONENTS[ref][1]))

    def tvs(self, ref, p, length=2.0):
        """diodo ESD bidirezionale verso massa"""
        self.add(elm.Zener().at(p).down(length).label(f"{ref}\n{self.val(ref)}", loc="bot", fontsize=FS - 0.8))
        self.gnd((p[0], p[1] - length))

    def frame(self, title, board, sheet_no, sheets, color=BLACK):
        ax = self.ax
        ax.add_patch(Rectangle((0.7, 0.7), W - 1.4, H - 1.4, fill=False, lw=1.0, color=color, zorder=6))
        x0, y0, bw, bh = 42.5, 1.4, 26.4, 6.9
        ax.add_patch(Rectangle((x0, y0), bw, bh, facecolor="white", edgecolor=BLACK, lw=0.9, zorder=6))
        rows = [("Co:", "INFN sez. TORINO  -  progetto glacier-elettronica"), ("Title:", title),
                ("Board:", board), ("Author:", "progetto didattico rivelatore di muoni (rev. A)"),
                ("Date:", "11/10/2026")]
        for i, (k, v) in enumerate(rows):
            yy = y0 + bh - (i + 0.5) * bh / 5
            if i:
                ax.plot([x0, x0 + bw], [y0 + bh - i * bh / 5] * 2, color=BLACK, lw=0.5, zorder=7)
            ax.text(x0 + 0.4, yy, k, fontsize=5.8, va="center", zorder=7)
            ax.text(x0 + 3.9, yy, v, fontsize=9 if i in (1, 2) else 6.6, va="center", zorder=7,
                    fontweight="bold" if i == 2 else "normal")
        ax.text(x0 + bw - 0.4, y0 + bh / 10, f"Sheet {sheet_no} of {sheets}", fontsize=6.4, ha="right",
                va="center", zorder=7)

    def save(self):
        self.d.draw(show=False)
        if self.mod is not None:                     # scheda interamente nuova: tutto in rosso
            import matplotlib.colors as mc
            nero = mc.to_rgba("black")
            for a in self.ax.get_children():
                if a.get_zorder() >= 6:              # cornice e cartiglio restano neri
                    continue
                for get, set_ in (("get_color", "set_color"), ("get_edgecolor", "set_edgecolor"),
                                  ("get_facecolor", "set_facecolor")):
                    try:
                        c = getattr(a, get)()
                        if len(c) and not isinstance(c, str) and hasattr(c[0], "__len__"):
                            c = c[0]
                        if mc.to_rgba(c) == nero:
                            getattr(a, set_)(RED)
                    except Exception:                # noqa: BLE001
                        pass
            self.text(1.8, 1.9, "nero = circuito INFN originale", fs=7)
            self.text(16.5, 1.9, "rosso = aggiunto: scheda interamente nuova del progetto", c=RED, fs=7)
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(0, H)
        self.ax.set_aspect("equal")
        self.pdf.savefig(self.fig)
        plt.close(self.fig)


# ===================================================================== architettura
def pagina_sistema(pdf, n, tot):
    s = Sheet(pdf)
    s.frame("Sistema completo", "ARCHITETTURA", n, tot)
    s.text(1.8, 47.3, "ARCHITETTURA DEL SISTEMA", fs=17, weight="bold")
    s.text(1.8, 45.6, "tre schede progettate qui (rivelatore, scatolina di acquisizione, modulo meteo) "
                      "+ moduli del commercio (Raspberry Pi Pico 2, Raspberry Pi Zero 2 W, GPS)", fs=7)

    def box(x, y, w, h, title, lines, c=BLACK, fill="white"):
        s.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2", fc=fill, ec=c, lw=1.4, zorder=2))
        s.text(x + 0.4, y + h - 0.7, title, c=c, fs=8.2, weight="bold")
        for i, t in enumerate(lines):
            s.text(x + 0.4, y + h - 1.9 - i * 1.0, t, fs=FS - 0.6)

    def freccia(p, q, t="", c=BLACK, off=(0, 0.45), ha="center"):
        s.ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, color=c, lw=1.2, zorder=3))
        if t:
            s.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], t, c=c, fs=FS - 0.6, ha=ha)

    # barre
    for k, y in enumerate((38.5, 34.5, 30.5)):
        s.ax.add_patch(Rectangle((2.0, y), 7.0, 2.4, fc="#e8e8e8", ec=BLACK, lw=0.8))
        s.text(5.5, y + 1.2, f"barra {k + 1}\nscintillatore + SiPM", fs=FS - 1.2, ha="center")
        freccia((9.0, y + 1.2), (12.0, y + 1.2))
    s.text(2.0, 29.3, "cavi Molex KK (segnale + bias)", fs=FS - 1.4, style="italic")
    box(12.0, 26.0, 14.0, 17.0, "RIVELATORE (3 canali)",
        ["scheda 103 x 224 mm, schema INFN", "- bias SiPM (LT3461, 3 regolabili)",
         "- 3 amplificatori + comparatori", "- coincidenza AND (74LVC1G11)",
         "- monitor tensioni/soglie/temperatura", "  (2 x MCP3424 in I2C)",
         "- alimentazione 5 V protetta:", "  USB-C, fusibile, TVS, MOSFET",
         "  contro l'inversione", "", "fogli 1-6 del PDF del rivelatore"])
    box(33.0, 26.0, 15.0, 17.0, "SCATOLINA DI ACQUISIZIONE",
        ["scheda 105 x 70 mm (pagine 2-3)", "- Raspberry Pi Pico 2 su zoccolo:",
         "  conteggio e tempo con la PIO", "  (risoluzione 6,7 ns)", "- 4 ingressi LEMO con buffer",
         "  di Schmitt, uscita PPS LEMO", "- GPS: tempo assoluto UTC + PPS",
         "- hub I2C TCA9548A, 8 porte", "  (2 KK rivelatori, 6 Qwiic)", "- alimentata dalla USB"])
    freccia((26.2, 38.0), (32.8, 38.0), "4 x LEMO 00\nbarre 1-3 + AND", off=(0, 0.9))
    freccia((32.8, 30.0), (26.2, 30.0), "I2C (KK 3 poli)\nletture tensioni", off=(0, -1.1))
    box(53.0, 33.0, 15.0, 10.0, "RASPBERRY PI ZERO 2 W",
        ["- riceve gli eventi dal Pico (USB)", "- archivio su scheda SD",
         "- pagina web / dashboard via Wi-Fi", "- alimenta il Pico dalla USB"])
    freccia((48.2, 38.0), (52.8, 38.0), "USB\ndati + 5 V", off=(0, 0.9))
    box(53.0, 18.5, 15.0, 11.0, "GPS + ANTENNA",
        ["- modulo u-blox (NEO-M8N/M9N)", "  su strip 1x6 nella scatolina",
         "- antenna attiva SMA con cavo", "  di 3-5 m verso la finestra", "- UART + PPS (1 impulso/s)"])
    freccia((52.8, 24.0), (48.2, 29.0), "UART, PPS", off=(1.6, -0.3))
    box(33.0, 11.0, 15.0, 9.5, "MODULO METEO",
        ["scheda 36 x 22 mm (pagina 4)", "- SHT45: temperatura e umidita'",
         "- LPS22HH: pressione (0,65 Pa rms)", "- Qwiic in/out, in catena",
         "  (correzione barometrica del flusso)"])
    freccia((40.5, 25.8), (40.5, 20.8), "Qwiic (porta 2)", off=(0.4, 0), ha="left")
    s.text(12.0, 22.5, "Alimentazione", fs=8, weight="bold")
    s.text(12.0, 21.2, "rivelatore: 5 V da alimentatore USB-C (o da banco su J3)", fs=FS - 0.6)
    s.text(12.0, 20.2, "Raspberry Pi Zero 2 W: alimentatore USB 5 V 2,5 A", fs=FS - 0.6)
    s.text(12.0, 19.2, "scatolina, GPS e meteo: dalla USB del Raspberry", fs=FS - 0.6)
    s.text(12.0, 17.2, "Masse", fs=8, weight="bold")
    s.text(12.0, 15.9, "rivelatore e scatolina hanno la massa in comune", fs=FS - 0.6)
    s.text(12.0, 14.9, "tramite la calza dei LEMO e il GND dei cavi I2C", fs=FS - 0.6)
    s.text(1.8, 9.5, "Bus I2C (indirizzi): hub TCA9548A 0x70 | porta 0: rivelatore, MCP3424 0x68 e 0x69 | "
                     "porta 2: SHT45 0x44, LPS22HH 0x5D", fs=FS - 0.4)
    s.text(1.8, 8.4, "Ogni porta dell'hub e' un bus separato: dispositivi con lo stesso indirizzo su porte diverse "
                     "non si disturbano (scalabilita').", fs=FS - 0.4)
    s.save()


# ===================================================================== scatolina: ingressi
def pagina_ingressi(pdf, n, tot):
    s = Sheet(pdf, ACQ)
    s.frame("Scatolina di acquisizione", "INGRESSI LEMO E PPS", n, tot)
    s.text(1.8, 47.3, "SCATOLINA - INGRESSI LEMO E USCITA PPS", fs=15, weight="bold")
    s.text(1.8, 45.6, "4 ingressi identici: ESD, 100k a massa (ingresso aperto = 0), 100 Ω in serie, buffer "
                      "a trigger di Schmitt 74LVC1G17 a 3,3 V (ingresso tollerante 5,5 V)", fs=7)
    for i, (k, nome) in enumerate(ACQ.INGRESSI.items()):
        y = 41.0 - i * 8.2
        j, d, rp, rs, u, c = f"J{k}", f"D{k}", f"R{k}", f"R1{k}", f"U{k}", f"C{k}"
        s.lemo((4.0, y), j, nome.replace("BARRA", "BARRA "))
        s.pin(j, 1, f"IN_{nome}")
        s.pin(j, 2, "GND")
        s.wire((4.0, y), (13.5, y))
        s.dot((6.5, y)); s.tvs(d, (6.5, y)); s.pin(d, 1, f"IN_{nome}"); s.pin(d, 2, "GND")
        s.dot((11.0, y)); s.comp("R", rp, (11.0, y), "down", nets=[f"IN_{nome}", "GND"]); s.gnd((11.0, y - 2.0))
        s.comp("R", rs, (13.5, y), "right", length=2.5, loc="top", nets=[f"IN_{nome}", f"A_{nome}"])
        s.wire((16.0, y), (17.0, y))
        b = s.add(logic.Buf().at((17.0, y)).right().anchor("in1"))
        s.text(18.3, y + 1.3, f"{u}  74LVC1G17", fs=FS - 0.6, ha="center")
        DRAWN.append((ACQ.NOME, u, ACQ.COMPONENTS[u][1]))
        s.ax.plot([18.1, 18.4, 18.4, 18.7], [y - 0.15, y - 0.15, y + 0.15, y + 0.15], color=BLACK, lw=0.6, zorder=4)
        s.text(16.8, y - 0.35, "2", fs=FS - 2, ha="right", va="top")
        out = b.out
        s.text(out[0] + 0.1, y - 0.35, "4", fs=FS - 2, va="top")
        s.pin(u, 2, f"A_{nome}"); s.pin(u, 4, f"GP_{nome}")
        s.wire(out, (out[0] + 2.0, y))
        gp = int(ACQ.GP_IN[k]) - 2
        s.label((out[0] + 2.0, y), f"GP{gp}  (A1 pin {ACQ.GP_IN[k]})")
        # alimentazione del buffer
        s.text(16.6, y - 1.7, "5 VCC: +3V3   3 GND   1 NC", fs=FS - 1.8)
        s.pin(u, 5, "+3V3"); s.pin(u, 3, "GND")
        s.vdd((33.0, y - 0.2), "+3V3")
        s.comp("C", c, (33.0, y - 0.2), "down", length=1.8, loc="bot", nets=["+3V3", "GND"])
        s.gnd((33.0, y - 2.0))
    # PPS
    y = 8.6
    s.text(1.8, 12.4, "USCITA PPS (dal GPS)", fs=8, weight="bold")
    s.label((9.0, y), "PPS_GPS (J6 pin 6)", side="left")
    s.pin("J6", 6, "PPS_GPS")
    s.comp("R", "R30", (9.2, y), "right", length=2.5, loc="top", nets=["PPS_GPS", "PPS"])
    s.wire((11.7, y), (17.0, y))
    s.dot((13.5, y)); s.comp("R", "R31", (13.5, y), "down", length=2.0, nets=["PPS", "GND"]); s.gnd((13.5, y - 2.0))
    s.dot((15.5, y)); s.wire((15.5, y), (15.5, y + 1.6)); s.label((15.5, y + 1.6), "GP6  (A1 pin 9)")
    s.pin("A1", 9, "PPS")
    b = s.add(logic.Buf().at((17.0, y)).right().anchor("in1").label("U5\n74LVC1G17", loc="top", fontsize=FS - 0.6))
    DRAWN.append((ACQ.NOME, "U5", ACQ.COMPONENTS["U5"][1]))
    s.pin("U5", 2, "PPS"); s.pin("U5", 4, "PPS_BUF"); s.pin("U5", 5, "+3V3"); s.pin("U5", 3, "GND")
    s.comp("R", "R32", b.out, "right", length=2.5, loc="bot", nets=["PPS_BUF", "PPS_OUT"])
    x = b.out[0] + 2.5
    s.wire((x, y), (x + 4.5, y))
    s.dot((x + 1.5, y)); s.tvs("D5", (x + 1.5, y)); s.pin("D5", 1, "PPS_OUT")
    s.lemo((x + 4.5, y), "J5", "PPS OUT", verso="left")
    s.pin("J5", 1, "PPS_OUT"); s.pin("J5", 2, "GND")
    s.text(30.0, y - 1.7, "U5: VCC +3V3, C5 100 nF", fs=FS - 1.8)
    DRAWN.append((ACQ.NOME, "C5", ACQ.COMPONENTS["C5"][1]))
    # note
    note = ["Perche' cosi'",
            "- 74LVC1G17: soglie di Schmitt (isteresi ~0,5 V): fronti",
            "  puliti anche con cavi lunghi; con VCC 3,3 V accetta in",
            "  ingresso fino a 5,5 V (vecchio TTL a 5 V del rivelatore)",
            "- 100k a massa: ingresso scollegato = livello basso, nessun",
            "  conteggio spurio",
            "- 100 Ω + diodo PESD5V0U1BA: scariche elettrostatiche sul",
            "  connettore (IEC 61000-4-2) e corrente limitata",
            "- uscita PPS: 33 Ω in serie adattano il cavo coassiale e",
            "  proteggono il buffer da un corto sul LEMO",
            "",
            "Tempi: ritardo del 74LVC1G17 ~4 ns, uguale sui 4 canali",
            "(stesso componente, stesse piste): la PIO del Pico campiona",
            "a 150 MHz (6,7 ns), il PPS del GPS da' il tempo assoluto",
            "(errore tipico 30-60 ns)."]
    for i, t in enumerate(note):
        s.text(41.5, 42.0 - i * 1.15, t, fs=FS + 0.2 if i == 0 else FS - 0.6, weight="bold" if i == 0 else "normal")
    s.save()


# ===================================================================== scatolina: Pico, GPS, hub
def pagina_pico(pdf, n, tot):
    s = Sheet(pdf, ACQ)
    s.frame("Scatolina di acquisizione", "PICO 2, GPS, HUB I2C", n, tot)
    s.text(1.8, 47.3, "SCATOLINA - PICO 2, GPS, HUB I2C, ALIMENTAZIONE", fs=15, weight="bold")
    # Pico
    sx, sy = 6.5, 12.0
    lp = [("1", "GP0  UART0 TX"), ("2", "GP1  UART0 RX"), ("4", "GP2"), ("5", "GP3"), ("6", "GP4"),
          ("7", "GP5"), ("9", "GP6"), ("10", "GP7"), ("11", "GP8  I2C0 SDA"), ("12", "GP9  I2C0 SCL"),
          ("20", "GP15")]
    rp = [("40", "VBUS"), ("36", "3V3(OUT)"), ("3,8,13,18,23,28,33,38", "GND")]
    pins = [(num, name, "left", 28.0 - k * 2.4) for k, (num, name) in enumerate(lp)]
    pins += [("40", "VBUS", "right", 28.0), ("36", "3V3(OUT)", "right", 24.0), ("GND", "GND", "right", 2.0)]
    pp = s.ic(sx, sy, 9.0, 30.0, pins, "Raspberry Pi\nPico 2\n(RP2350)\n\nsu zoccolo\n2 x 1x20", ref="A1")
    DRAWN.append((ACQ.NOME, "A1", ACQ.COMPONENTS["A1"][1]))
    reti = {"1": "GPS_RX", "2": "GPS_TX", "4": "GP_BARRA1", "5": "GP_BARRA2", "6": "GP_BARRA3", "7": "GP_AND",
            "9": "PPS", "10": "HUB_RST", "11": "I2C_SDA", "12": "I2C_SCL", "20": "LED_ATT"}
    for num, net in reti.items():
        s.label(pp[num], net, side="left")
        s.pin("A1", num, net)
    s.text(sx + 4.5, sy - 1.2, "pin liberi: GP10-14, GP16-22, GP26-28 (espansioni future)", fs=FS - 1.6, ha="center")
    s.wire(pp["40"], (19.0, pp["40"][1])); s.label((19.0, pp["40"][1]), "+5V"); s.pin("A1", "40", "+5V")
    s.wire(pp["36"], (19.0, pp["36"][1])); s.label((19.0, pp["36"][1]), "+3V3"); s.pin("A1", "36", "+3V3")
    s.gnd(pp["GND"])
    for p in ACQ.PICO_GND:
        s.pin("A1", p, "GND")
    # GPS
    gx, gy = 26.0, 34.0
    gp = s.ic(gx, gy, 5.0, 7.5, [(str(k), nm, "left", 6.75 - (k - 1) * 1.25) for k, nm in
                                 enumerate(["+5V", "+3V3", "GND", "TX", "RX", "PPS"], 1)],
              "GPS\nstrip 1x6", ref="J6")
    DRAWN.append((ACQ.NOME, "J6", ACQ.COMPONENTS["J6"][1]))
    for k, net in {"1": "+5V", "2": "+3V3", "4": "GPS_TX", "5": "GPS_RX", "6": "PPS_GPS"}.items():
        s.label(gp[k], net, side="left")
        s.pin("J6", k, net)
    s.gnd(gp["3"]); s.pin("J6", "3", "GND")
    s.text(gx + 5.6, gy + 6.0, "modulo GPS u-blox con", fs=FS - 1.2)
    s.text(gx + 5.6, gy + 5.1, "antenna attiva (finestra)", fs=FS - 1.2)
    s.text(gx + 5.6, gy + 3.9, "TX del GPS -> GP1", fs=FS - 1.2)
    s.text(gx + 5.6, gy + 3.0, "GP0 -> RX del GPS", fs=FS - 1.2)
    s.text(gx + 5.6, gy + 1.8, "PPS -> R30 (pagina 2)", fs=FS - 1.2)
    # hub
    hx, hy = 30.0, 9.5
    hp = [("23", "SDA", "left", 19.0), ("22", "SCL", "left", 17.0), ("3", "~RESET", "left", 14.0),
          ("1", "A0", "left", 9.0), ("2", "A1", "left", 7.5), ("21", "A2", "left", 6.0)]
    for p in range(8):
        sd = str(4 + 2 * p + (1 if p >= 4 else 0))
        sc = str(5 + 2 * p + (1 if p >= 4 else 0))
        hp += [(sd, f"SD{p}", "right", 20.5 - p * 2.5), (sc, f"SC{p}", "right", 19.6 - p * 2.5)]
    hp += [("24", "VCC", "top", 2.5), ("12", "GND", "bottom", 2.5)]
    hh = s.ic(hx, hy, 6.0, 21.5, hp, "TCA9548A\nhub I2C\n1 -> 8\n0x70", ref="U6")
    DRAWN.append((ACQ.NOME, "U6", ACQ.COMPONENTS["U6"][1]))
    for num, net in {"23": "I2C_SDA", "22": "I2C_SCL", "3": "HUB_RST"}.items():
        s.wire(hh[num], (hh[num][0] - 2.6, hh[num][1]))
        s.label((hh[num][0] - 2.6, hh[num][1]), net, side="left")
        s.pin("U6", num, net)
    for num in ("1", "2", "21"):
        s.wire(hh[num], (hh[num][0] - 1.0, hh[num][1])); s.pin("U6", num, "GND")
    s.wire((hh["1"][0] - 1.0, hh["1"][1]), (hh["21"][0] - 1.0, hh["21"][1]))
    s.gnd((hh["21"][0] - 1.0, hh["21"][1]))
    for p in range(8):
        sd = str(4 + 2 * p + (1 if p >= 4 else 0))
        sc = str(5 + 2 * p + (1 if p >= 4 else 0))
        s.label(hh[sd], f"SDA{p}")
        s.label(hh[sc], f"SCL{p}")
    s.vdd(hh["24"], "+3V3"); s.pin("U6", "24", "+3V3")
    s.gnd(hh["12"]); s.pin("U6", "12", "GND")
    s.comp("C", "C6", (hx + 4.6, hy + 23.5), "down", length=1.6, loc="bot", nets=["+3V3", "GND"])
    s.vdd((hx + 4.6, hy + 23.5), "")
    s.gnd((hx + 4.6, hy + 21.9))
    # pull-up a monte
    for k, (ref, net) in enumerate((("R20", "I2C_SDA"), ("R21", "I2C_SCL"), ("R22", "HUB_RST"))):
        x = 19.0 + k * 2.3
        s.vdd((x, 30.0), "+3V3")
        s.comp("R", ref, (x, 30.0), "down", length=2.0, loc="bot", nets=[net, "+3V3"])
        s.label((x, 28.0), net) if False else s.text(x, 27.4, net.replace("I2C_", ""), c=BLUE, fs=FS - 1.6, ha="center")
    s.text(19.0, 32.4, "pull-up a monte (verso il Pico)", fs=FS - 1.6)
    # porte
    s.text(41.5, 42.3, "PORTE DELL'HUB (pull-up 4,7k per porta verso +3V3_QW)", fs=7.2, weight="bold")
    for p in range(8):
        col, row = p % 2, p // 2
        x0, y0 = 41.5 + col * 13.5, 38.3 - row * 7.4
        ref = f"J{7 + p}"
        kk = p < 2
        DRAWN.append((ACQ.NOME, ref, ACQ.COMPONENTS[ref][1]))
        names = ["GND", "SDA", "SCL"] if kk else ["GND", "3V3", "SDA", "SCL"]
        for i, nm in enumerate(names):
            yy = y0 - i * 0.9
            s.ax.add_patch(Circle((x0 + 9.6, yy), 0.15, fill=False, color=BLACK, lw=0.7, zorder=3))
            s.text(x0 + 9.95, yy, f"{i + 1} {nm}", fs=FS - 2.0)
        s.ax.add_patch(Rectangle((x0 + 9.3, y0 - (len(names) - 1) * 0.9 - 0.5), 2.9,
                                 (len(names) - 1) * 0.9 + 1.0, fill=False, color=BLACK, lw=0.8))
        s.text(x0 + 9.3, y0 + 1.0, f"{ref} " + ("KK rivelatore" if kk else "Qwiic"), fs=FS - 1.4, weight="bold")
        isda = names.index("SDA")
        iscl = names.index("SCL")
        ysda, yscl = y0 - isda * 0.9, y0 - iscl * 0.9
        s.label((x0 + 0.3, ysda), f"SDA{p}", side="left")
        s.label((x0 + 0.3, yscl), f"SCL{p}", side="left")
        s.wire((x0 + 0.3, ysda), (x0 + 9.45, ysda))
        s.wire((x0 + 0.3, yscl), (x0 + 9.45, yscl))
        for xr, yv, rr, net in ((x0 + 3.3, ysda, f"R5{p}", f"SDA{p}"), (x0 + 5.6, yscl, f"R6{p}", f"SCL{p}")):
            s.dot((xr, yv))
            s.wire((xr, yv), (xr, y0 + 0.6 if False else yv))
            s.add(elm.Resistor().at((xr, yv)).up(2.2 + (yv - yscl) * 0 + (ysda - yv)).color(BLACK)
                  .label(f"{rr} {s.val(rr)}", loc="bot", fontsize=FS - 2.2, ofst=0.1))
            s.pin(rr, 1, net); s.pin(rr, 2, "+3V3_QW")
        ytop = ysda + 2.2
        s.wire((x0 + 3.3, ytop), (x0 + 5.6, ytop))
        s.text(x0 + 4.45, ytop + 0.35, "+3V3_QW", c=BLUE, fs=FS - 2.0, ha="center")
        s.pin(ref, "1", "GND")
        s.pin(ref, str(isda + 1), f"SDA{p}"); s.pin(ref, str(iscl + 1), f"SCL{p}")
        if not kk:
            s.pin(ref, "2", "+3V3_QW")
        s.pin("U6", str(4 + 2 * p + (1 if p >= 4 else 0)), f"SDA{p}")
        s.pin("U6", str(5 + 2 * p + (1 if p >= 4 else 0)), f"SCL{p}")
    s.text(41.5, 10.2, "SDn / SCn di U6 = SDAn / SCLn delle porte (porta 0: rivelatore, porta 2: meteo)",
           fs=FS - 1.6)
    # alimentazione
    s.text(1.8, 8.7, "ALIMENTAZIONE", fs=8, weight="bold")
    y = 6.0
    s.vdd((3.0, y), "+5V"); s.comp("C", "C9", (3.0, y), "down", length=1.8, nets=["+5V", "GND"]); s.gnd((3.0, y - 1.8))
    s.vdd((6.0, y), "+5V"); s.comp("C", "C7", (6.0, y), "down", length=1.8, nets=["+5V", "GND"]); s.gnd((6.0, y - 1.8))
    ap = s.ic(9.5, 3.8, 4.4, 3.2, [("1", "VIN", "left", 2.4), ("3", "EN", "left", 0.9), ("5", "VOUT", "right", 2.4),
                                   ("2", "GND", "bottom", 2.2)], "AP2112K\n-3.3", ref="U7")
    DRAWN.append((ACQ.NOME, "U7", ACQ.COMPONENTS["U7"][1]))
    s.wire((6.0, y), ap["1"]); s.wire(ap["1"], (8.8, y), ap["3"]); s.dot((8.8, ap["1"][1]))
    s.pin("U7", "1", "+5V"); s.pin("U7", "3", "+5V"); s.pin("U7", "5", "+3V3_QW"); s.pin("U7", "2", "GND")
    s.gnd(ap["2"])
    s.wire(ap["5"], (22.0, ap["5"][1]))
    s.text(19.5, ap["5"][1] + 0.6, "+3V3_QW (porte Qwiic, pull-up)", c=BLUE, fs=FS - 1.6)
    for x, ref in ((15.8, "C8"), (18.0, "C10")):
        s.dot((x, ap["5"][1])); s.comp("C", ref, (x, ap["5"][1]), "down", length=1.8, nets=["+3V3_QW", "GND"])
        s.gnd((x, ap["5"][1] - 1.8))
    s.dot((22.0, ap["5"][1]))
    s.comp("R", "R40", (22.0, ap["5"][1]), "down", length=1.6, loc="bot", nets=["+3V3_QW", "LED_PWR"])
    s.add(elm.LED().at((22.0, ap["5"][1] - 1.6)).down(1.4).label("D10\nverde", loc="bot", fontsize=FS - 1.0))
    DRAWN.append((ACQ.NOME, "D10", ACQ.COMPONENTS["D10"][1])); s.pin("D10", "2", "LED_PWR"); s.pin("D10", "1", "GND")
    s.gnd((22.0, ap["5"][1] - 3.0))
    s.label((26.0, y), "LED_ATT", side="left"); s.wire((26.0, y), (27.0, y))
    s.comp("R", "R41", (27.0, y), "right", length=2.0, loc="top", nets=["LED_ATT", "LED_ATT_K"])
    s.add(elm.LED().at((29.0, y)).down(1.6).label("D11", loc="bot", fontsize=FS - 1.0))
    DRAWN.append((ACQ.NOME, "D11", ACQ.COMPONENTS["D11"][1])); s.pin("D11", "2", "LED_ATT_K"); s.pin("D11", "1", "GND")
    s.gnd((29.0, y - 1.6))
    s.text(32.0, 6.6, "+5V: dalla USB del Pico (pin 40 VBUS)", fs=FS - 1.6)
    s.text(32.0, 5.6, "+3V3: regolatore del Pico (pin 36), max 300 mA", fs=FS - 1.6)
    s.text(32.0, 4.6, "+3V3_QW: AP2112K, 600 mA, solo porte", fs=FS - 1.6)
    s.save()


# ===================================================================== meteo
def pagina_meteo(pdf, n, tot):
    s = Sheet(pdf, MET)
    s.frame("Modulo meteo", "MODULO METEO", n, tot)
    s.text(1.8, 47.3, "MODULO METEO - SHT45 + LPS22HH (Qwiic)", fs=15, weight="bold")
    s.text(1.8, 45.6, "temperatura ±0,1 °C, umidita' ±1 %UR, pressione ±0,5 hPa (rumore 0,65 Pa rms); "
                      "scheda 36 x 22 mm, si collega a una porta Qwiic dell'hub (anche in catena)", fs=7)
    # bus
    yb = {"+3V3": 40.0, "SDA": 38.0, "SCL": 36.0, "GND": 34.0}
    for net, y in yb.items():
        s.wire((9.0, y), (60.0, y), lw=1.2 if net in ("+3V3", "GND") else 0.9)
        s.text(60.3, y, net, c=BLUE, fs=FS - 0.6)
    for ref, x in (("J1", 3.0), ("J2", 63.5)):
        DRAWN.append((MET.NOME, ref, MET.COMPONENTS[ref][1]))
        names = ["GND", "3V3", "SDA", "SCL"]
        s.ax.add_patch(Rectangle((x, 33.3), 3.0, 7.4, fill=False, color=BLACK, lw=0.9))
        s.text(x + 1.5, 41.4, f"{ref} Qwiic", fs=FS, weight="bold", ha="center")
        for i, (nm, net) in enumerate(zip(names, ["GND", "+3V3", "SDA", "SCL"])):
            y = yb[net]
            s.text(x + 1.5, y, f"{i + 1} {nm}", fs=FS - 1.6, ha="center")
            s.pin(ref, i + 1, net)
            if ref == "J1":
                s.wire((x + 3.0, y), (9.0, y))
            else:
                s.wire((60.0, y), (x, y))
    s.text(3.0, 31.7, "entrata", fs=FS - 1.4)
    s.text(63.5, 31.7, "uscita (catena)", fs=FS - 1.4)
    # SHT45
    u1 = s.ic(14.0, 22.0, 5.0, 4.0, [("1", "SDA", "left", 3.0), ("2", "SCL", "left", 1.5),
                                     ("3", "VDD", "top", 2.5), ("4", "VSS", "bottom", 2.5)],
              "SHT45\nT + UR\n0x44", ref="U1")
    DRAWN.append((MET.NOME, "U1", MET.COMPONENTS["U1"][1]))
    s.wire(u1["3"], (u1["3"][0], yb["+3V3"])); s.dot((u1["3"][0], yb["+3V3"]))
    s.wire(u1["1"], (11.5, u1["1"][1]), (11.5, yb["SDA"])); s.dot((11.5, yb["SDA"]))
    s.wire(u1["2"], (10.5, u1["2"][1]), (10.5, yb["SCL"])); s.dot((10.5, yb["SCL"]))
    s.gnd(u1["4"])
    for p, net in (("1", "SDA"), ("2", "SCL"), ("3", "+3V3"), ("4", "GND")):
        s.pin("U1", p, net)
    s.dot((21.5, yb["+3V3"])); s.comp("C", "C1", (21.5, yb["+3V3"]), "down", length=2.0, nets=["+3V3", "GND"])
    s.dot((21.5, yb["GND"]))
    s.text(14.0, 19.8, "su isola separata da fessure,", fs=FS - 1.4)
    s.text(14.0, 18.9, "senza rame sotto (Sensirion)", fs=FS - 1.4)
    # LPS22HH
    u2 = s.ic(30.0, 17.0, 6.5, 9.0, [("4", "SDA", "left", 7.5), ("2", "SCL", "left", 6.0), ("5", "SA0", "left", 3.0),
                                     ("6", "CS", "left", 1.5), ("10", "VDD", "top", 2.0), ("1", "VDD_IO", "top", 4.5),
                                     ("7", "INT_DRDY", "right", 6.0), ("3,8,9", "GND", "bottom", 3.25)],
              "LPS22HH\npressione\n0x5D / 0x5C", ref="U2")
    DRAWN.append((MET.NOME, "U2", MET.COMPONENTS["U2"][1]))
    for p, net in (("4", "SDA"), ("2", "SCL"), ("5", "SA0"), ("6", "+3V3"), ("10", "+3V3"), ("1", "+3V3"),
                   ("3", "GND"), ("8", "GND"), ("9", "GND")):
        s.pin("U2", p, net)
    for k in ("10", "1"):
        s.wire(u2[k], (u2[k][0], yb["+3V3"])); s.dot((u2[k][0], yb["+3V3"]))
    s.wire(u2["4"], (27.5, u2["4"][1]), (27.5, yb["SDA"])); s.dot((27.5, yb["SDA"]))
    s.wire(u2["2"], (26.5, u2["2"][1]), (26.5, yb["SCL"])); s.dot((26.5, yb["SCL"]))
    s.wire(u2["6"], (28.4, u2["6"][1])); s.text(28.3, u2["6"][1] + 0.45, "+3V3 (I2C)", c=BLUE, fs=FS - 2, ha="right")
    s.gnd(u2["3,8,9"])
    s.ax.plot([u2["7"][0] - 0.2, u2["7"][0] + 0.2], [u2["7"][1] - 0.2, u2["7"][1] + 0.2], color=BLACK, lw=0.8)
    s.ax.plot([u2["7"][0] - 0.2, u2["7"][0] + 0.2], [u2["7"][1] + 0.2, u2["7"][1] - 0.2], color=BLACK, lw=0.8)
    s.text(u2["7"][0] + 0.4, u2["7"][1], "non usato", fs=FS - 1.8)
    for x, ref in ((40.5, "C2"), (43.0, "C3")):
        s.dot((x, yb["+3V3"])); s.comp("C", ref, (x, yb["+3V3"]), "down", length=2.0, nets=["+3V3", "GND"])
        s.dot((x, yb["GND"]))
    s.text(40.0, 31.2, "C2 su VDD, C3 su VDD_IO", fs=FS - 1.8)
    # JP2
    s.wire(u2["5"], (24.0, u2["5"][1]), (24.0, 12.0))
    s.ax.add_patch(Rectangle((21.6, 10.6), 4.8, 1.4, fill=False, color=BLACK, lw=0.9))
    for xx in (22.4, 24.0, 25.6):
        s.ax.add_patch(Rectangle((xx - 0.5, 10.8), 1.0, 1.0, fc="#dddddd", ec=BLACK, lw=0.6))
    s.ax.plot([22.9, 23.5], [11.3, 11.3], color=BLACK, lw=2.4)
    s.text(24.0, 9.9, "JP2  1-2 (di fabbrica) = 0x5D,  2-3 = 0x5C", fs=FS - 1.2, ha="center")
    DRAWN.append((MET.NOME, "JP2", MET.COMPONENTS["JP2"][1]))
    s.pin("JP2", "2", "SA0"); s.pin("JP2", "1", "+3V3"); s.pin("JP2", "3", "GND")
    s.wire((22.4, 10.8), (22.4, 9.0), (19.5, 9.0)); s.vdd((19.5, 9.0), "+3V3")
    s.wire((25.6, 10.8), (25.6, 9.0), (28.0, 9.0)); s.gnd((28.0, 9.0))
    # pull-up
    for x, ref, net in ((49.0, "R1", "SDA"), (52.0, "R2", "SCL")):
        s.dot((x, yb[net]))
        s.comp("R", ref, (x, yb[net]), "down", length=3.0, nets=[net, "PU"])
    s.wire((49.0, yb["SDA"] - 3.0), (49.0, 29.0), (52.0, 29.0), (52.0, yb["SCL"] - 3.0))
    s.dot((50.5, 29.0)); s.wire((50.5, 29.0), (50.5, 27.5))
    s.add(elm.Gap().at((50.5, 27.5)).down(1.0))
    s.ax.add_patch(Rectangle((49.9, 25.6), 1.2, 1.6, fill=False, color=BLACK, lw=0.9))
    s.ax.plot([49.9, 51.1], [26.4, 26.4], color=BLACK, lw=0.6, ls=":")
    s.text(51.4, 26.4, "JP1 aperto\n(chiudere se il modulo\ne' da solo sul bus)", fs=FS - 1.6)
    DRAWN.append((MET.NOME, "JP1", MET.COMPONENTS["JP1"][1]))
    s.pin("JP1", "1", "PU"); s.pin("JP1", "2", "+3V3")
    s.wire((50.5, 25.6), (50.5, 24.5)); s.vdd((50.5, 24.5), "") if False else None
    s.text(50.5, 23.8, "+3V3", c=BLUE, fs=FS - 1.2, ha="center")
    note = ["Note",
            "- SHT41-AD1B o SHT40-AD1B montabili al posto dell'SHT45 (stessa impronta e indirizzo)",
            "- l'LPS22HH sostituisce il BMP390: stessa classe di rumore, disponibile da JLCPCB (C2827824)",
            "- le porte della scatolina hanno gia' i pull-up: JP1 resta aperto",
            "- niente vernice protettiva sul sensore di umidita'"]
    for i, t in enumerate(note):
        s.text(1.8, 16.5 - i * 1.15, t, fs=FS + 0.2 if i == 0 else FS - 0.6, weight="bold" if i == 0 else "normal")
    s.save()


def check():
    bad = []
    for nome, ref, v in DRAWN:
        mod = ACQ if nome == ACQ.NOME else MET
        if ref not in mod.COMPONENTS or mod.COMPONENTS[ref][1] != v:
            bad.append((nome, ref, v))
    for nome, ref, pin, net in PINS:
        mod = ACQ if nome == ACQ.NOME else MET
        if (ref, pin) not in mod.NETS.get(net, []):
            bad.append((nome, ref, pin, net))
    assert not bad, bad
    for mod in (ACQ, MET):
        drawn = {r for n, r, _ in DRAWN if n == mod.NOME}
        manca = [r for r in mod.COMPONENTS if r not in drawn and mod.COMPONENTS[r][0] != "MH"]
        assert not manca, (mod.NOME, "non disegnati:", manca)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tot = 4
    with PdfPages(OUT) as pdf:
        pagina_sistema(pdf, 1, tot)
        pagina_ingressi(pdf, 2, tot)
        pagina_pico(pdf, 3, tot)
        pagina_meteo(pdf, 4, tot)
    check()
    print("scritto", os.path.normpath(OUT), "-", len(DRAWN), "componenti e", len(PINS),
          "pin controllati con le netlist")


if __name__ == "__main__":
    main()
