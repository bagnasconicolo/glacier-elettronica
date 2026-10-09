# -*- coding: utf-8 -*-
"""Footprint library 'rivlib' (formato KiCad 6 .kicad_mod).
Ogni footprint espone pads: {num: (x, y, w, h, kind)} con kind in
{'smd','tht','tht_rect'} per il generatore PCB e il DRC.
Convenzione: Y verso il basso (coordinate footprint KiCad).
"""

class FP:
    def __init__(self, name, pads, courtyard, silk=None, desc="", th_body=None):
        # pads: list of (num, x, y, w, h, kind, drill)
        self.name = name
        self.pads = {str(p[0]): p[1:] for p in pads}
        self.courtyard = courtyard  # (x1,y1,x2,y2)
        self.silk = silk or []      # list of line segs (x1,y1,x2,y2)
        self.desc = desc

    def sexpr(self):
        o = []
        o.append(f'(footprint "rivlib:{self.name}" (version 20211014) (generator rivgen) (layer "F.Cu")')
        o.append(f'  (attr smd)' if all(p[4] == "smd" for p in self.pads.values()) else '  (attr through_hole)')
        o.append(f'  (descr "{self.desc}")')
        o.append('  (fp_text reference "REF**" (at 0 -3.2) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        o.append('  (fp_text value "VAL**" (at 0 3.2) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        x1, y1, x2, y2 = self.courtyard
        o.append(f'  (fp_rect (start {x1} {y1}) (end {x2} {y2}) (layer "F.CrtYd") (width 0.05) (fill none))')
        for (sx1, sy1, sx2, sy2) in self.silk:
            o.append(f'  (fp_line (start {sx1} {sy1}) (end {sx2} {sy2}) (layer "F.SilkS") (width 0.12))')
        for num, (x, y, w, h, kind, drill) in self.pads.items():
            num = num.split("#")[0]          # "2#3" = terzo pad del pin 2
            if kind == "smd":
                o.append(f'  (pad "{num}" smd roundrect (at {x} {y}) (size {w} {h}) '
                         f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))')
            else:
                shape = "rect" if kind == "tht_rect" else "circle"
                o.append(f'  (pad "{num}" thru_hole {shape} (at {x} {y}) (size {w} {h}) '
                         f'(drill {drill}) (layers "*.Cu" "*.Mask"))')
        o.append(')')
        return "\n".join(o)

FPS = {}
def add(fp):
    FPS[fp.name] = fp

def chip2(name, px, w, h, cw, ch, desc):
    add(FP(name,
           [(1, -px, 0, w, h, "smd", 0), (2, px, 0, w, h, "smd", 0)],
           (-cw, -ch, cw, ch),
           silk=[(-cw, -ch, cw, -ch), (-cw, ch, cw, ch)],
           desc=desc))

chip2("R_0805", 0.95, 1.15, 1.45, 1.85, 1.0, "R 0805 (2012)")
chip2("C_0805", 0.95, 1.15, 1.45, 1.85, 1.0, "C 0805 (2012)")
chip2("C_1206", 1.4625, 1.15, 1.8, 2.4, 1.2, "C 1206 (3216)")
chip2("C_1210", 1.4625, 1.15, 2.8, 2.4, 1.7, "C 1210 (3225)")
add(FP("LED_0805",
       [(1, -0.95, 0, 1.15, 1.45, "smd", 0), (2, 0.95, 0, 1.15, 1.45, "smd", 0)],
       (-1.85, -1.0, 1.85, 1.0),
       silk=[(-1.85, -1.0, 1.85, -1.0), (-1.85, 1.0, 1.85, 1.0),
             (-1.85, -1.0, -1.85, 1.0)],   # barra lato catodo (pin 1)
       desc="LED 0805, pin1=K"))

# SOT-23: 1 SW-left(sud sx), 2 sud dx?? -> convenzione standard: 1,2 sud (y+), 3 nord
add(FP("SOT23",
       [(1, -0.95, 1.15, 0.9, 1.0, "smd", 0),
        (2, 0.95, 1.15, 0.9, 1.0, "smd", 0),
        (3, 0, -1.15, 0.9, 1.0, "smd", 0)],
       (-1.7, -1.9, 1.7, 1.9),
       silk=[(-1.55, -0.35, -1.55, 0.35), (1.55, -0.35, 1.55, 0.35)],
       desc="SOT-23 (1=B 2=E 3=C)"))

def sot23n(name, south, north, desc):
    pads = []
    for i, num in enumerate(south):
        pads.append((num, -0.95 + i * 0.95, 1.3, 0.6, 1.1, "smd", 0))
    for i, num in enumerate(north):
        pads.append((num, 0.95 - i * 0.95, -1.3, 0.6, 1.1, "smd", 0))
    add(FP(name, pads, (-1.7, -2.1, 1.7, 2.1),
           silk=[(-1.55, -0.5, -1.55, 0.5), (1.55, -0.5, 1.55, 0.5)],
           desc=desc))

sot23n("SOT23-5", ["1", "2", "3"], ["4", "5"], "SOT-23-5 (pin1 sud-sx)")
sot23n("SOT23-6", ["1", "2", "3"], ["4", "5", "6"], "SOT-23-6 / ThinSOT")

# SOIC-8: pin1 in alto a sinistra, colonna sx 1-4 (y -1.905..1.905), dx 8-5
_soic = []
for i in range(4):
    _soic.append((str(i + 1), -2.475, -1.905 + i * 1.27, 1.95, 0.6, "smd", 0))
for i in range(4):
    _soic.append((str(8 - i), 2.475, -1.905 + i * 1.27, 1.95, 0.6, "smd", 0))
add(FP("SOIC8", _soic, (-3.7, -2.7, 3.7, 2.7),
       silk=[(-1.95, -2.6, 1.95, -2.6), (-1.95, 2.6, 1.95, 2.6),
             (-1.95, -2.6, -1.95, -2.2)],  # tacca lato pin1
       desc="SOIC-8 3.9x4.9 P1.27"))

# SOIC-14 (MCP3424): pin1 in alto a sinistra, colonna sx 1-7, dx 14-8
_soic14 = []
for i in range(7):
    _soic14.append((str(i + 1), -2.475, -3.81 + i * 1.27, 1.95, 0.6, "smd", 0))
for i in range(7):
    _soic14.append((str(14 - i), 2.475, -3.81 + i * 1.27, 1.95, 0.6, "smd", 0))
add(FP("SOIC14", _soic14, (-3.7, -4.6, 3.7, 4.6),
       silk=[(-1.95, -4.45, 1.95, -4.45), (-1.95, 4.45, 1.95, 4.45),
             (-1.95, -4.45, -1.95, -4.05)],
       desc="SOIC-14 3.9x8.65 P1.27"))

# SOT-223 (tab = pad 4): pin 1,2,3 sud, tab nord
add(FP("SOT223",
       [(1, -2.3, 3.15, 1.5, 2.0, "smd", 0),
        (2, 0, 3.15, 1.5, 2.0, "smd", 0),
        (3, 2.3, 3.15, 1.5, 2.0, "smd", 0),
        (4, 0, -3.15, 3.6, 2.2, "smd", 0)],
       (-3.85, -4.4, 3.85, 4.4),
       silk=[(-3.4, -1.8, -3.4, 1.8), (3.4, -1.8, 3.4, 1.8)],
       desc="SOT-223-3, tab=pad4"))

# 1N4148 DO-35 orizzontale passo 7.62, pin1 = K (banda)
add(FP("D_DO35",
       [(1, -3.81, 0, 1.6, 1.6, "tht_rect", 0.8),
        (2, 3.81, 0, 1.6, 1.6, "tht", 0.8)],
       (-4.8, -1.2, 4.8, 1.2),
       silk=[(-2.3, -1.0, 2.3, -1.0), (-2.3, 1.0, 2.3, 1.0),
             (-2.3, -1.0, -2.3, 1.0), (-1.7, -1.0, -1.7, 1.0)],
       desc="DO-35 P7.62, pin1=K"))

# Trimmer Bourns 3296W: 3 fori in linea passo 2.54 (1 CCW, 2 wiper, 3 CW)
add(FP("TRIM_3296W",
       [(1, -2.54, 0, 1.7, 1.7, "tht_rect", 0.9),
        (2, 0, 0, 1.7, 1.7, "tht", 0.9),
        (3, 2.54, 0, 1.7, 1.7, "tht", 0.9)],
       (-4.9, -2.5, 4.9, 2.5),
       silk=[(-4.8, -2.4, 4.8, -2.4), (-4.8, 2.4, 4.8, 2.4),
             (-4.8, -2.4, -4.8, 2.4), (4.8, -2.4, 4.8, 2.4)],
       desc="Bourns 3296W 3/8in trimmer, inline P2.54"))

# Header 2.54 1x2 verticale
add(FP("HDR1x02",
       [(1, 0, 0, 1.7, 1.7, "tht_rect", 1.0),
        (2, 2.54, 0, 1.7, 1.7, "tht", 1.0)],
       (-1.3, -1.3, 3.85, 1.3),
       silk=[(-1.27, -1.27, 3.81, -1.27), (-1.27, 1.27, 3.81, 1.27),
             (-1.27, -1.27, -1.27, 1.27), (3.81, -1.27, 3.81, 1.27)],
       desc="Pin header 2.54 1x2"))

# Header 2.54 1x3 verticale (connettore I2C verso il Raspberry Pi)
add(FP("HDR1x03",
       [(1, 0, 0, 1.7, 1.7, "tht_rect", 1.0),
        (2, 2.54, 0, 1.7, 1.7, "tht", 1.0),
        (3, 5.08, 0, 1.7, 1.7, "tht", 1.0)],
       (-1.3, -1.3, 6.4, 1.3),
       silk=[(-1.27, -1.27, 6.35, -1.27), (-1.27, 1.27, 6.35, 1.27),
             (-1.27, -1.27, -1.27, 1.27), (6.35, -1.27, 6.35, 1.27)],
       desc="Pin header 2.54 1x3"))

# Foro di fissaggio M3: foro 3,2 mm metallizzato, piazzola 6 mm (a massa)
add(FP("MH_M3",
       [(1, 0, 0, 6.0, 6.0, "tht", 3.2)],
       (-3.5, -3.5, 3.5, 3.5),
       desc="Foro di fissaggio M3 metallizzato"))

# Test point per sonda d'oscilloscopio: foro 1,0 mm (anello Keystone 5001/5000
# o un filo piegato ad anello), pad 2,0 mm
add(FP("TP_THT",
       [(1, 0, 0, 2.0, 2.0, "tht", 1.0)],
       (-1.3, -1.3, 1.3, 1.3),
       desc="Test point THT, foro 1.0 mm"))

# LEMO serie 00, presa a gomito da circuito stampato EPL.00.250.NTN:
# contatto centrale + 4 piedini di schermo su quadrato 5,08 mm, fori 0,8 mm.
# Il frontale guarda verso +X: piazzare con X del centro a ~4 mm dal bordo
# scheda; il corpo (L = 17,5 mm) sporge oltre il bordo. Courtyard solo sulla
# parte sopra la scheda.
add(FP("LEMO_EPL00",
       [(1, 0, 0, 1.5, 1.5, "tht", 0.8),
        ("2", -2.54, -2.54, 1.5, 1.5, "tht", 0.8), ("2#2", 2.54, -2.54, 1.5, 1.5, "tht", 0.8),
        ("2#3", -2.54, 2.54, 1.5, 1.5, "tht", 0.8), ("2#4", 2.54, 2.54, 1.5, 1.5, "tht", 0.8)],
       (-3.8, -3.8, 4.0, 3.8),
       silk=[(-3.5, -3.5, 4.0, -3.5), (-3.5, 3.5, 4.0, 3.5), (-3.5, -3.5, -3.5, 3.5)],
       desc="LEMO EPL.00.250.NTN gomito, 00 serie (frontale verso +X)"))

# Induttore di potenza 5x5 (SRN5040 e simili)
add(FP("L_PWR_5050",
       [(1, -2.1, 0, 2.2, 5.8, "smd", 0), (2, 2.1, 0, 2.2, 5.8, "smd", 0)],
       (-3.6, -3.5, 3.6, 3.5),
       silk=[(-3.5, -3.4, 3.5, -3.4), (-3.5, 3.4, 3.5, 3.4)],
       desc="Power inductor SMD 5x5/6x6 (SRN5040/SRR6040) - verificare vs parte RS 6934344"))

def write_lib(dirname):
    import os
    os.makedirs(dirname, exist_ok=True)
    for fp in FPS.values():
        with open(os.path.join(dirname, fp.name + ".kicad_mod"), "w") as f:
            f.write(fp.sexpr() + "\n")
    print(f"scritti {len(FPS)} footprint in {dirname}")

if __name__ == "__main__":
    write_lib("riv_cosmici/rivlib.pretty")
