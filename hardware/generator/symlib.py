# -*- coding: utf-8 -*-
"""Libreria simboli KiCad 6 (lib 'riv') generata via codice.
Ogni simbolo espone: pins {num: (px, py, angle, name, etype)} in coordinate
libreria (Y verso l'alto), e il testo s-expression.
"""
F = "(effects (font (size 1.27 1.27)))"
FH = "(effects (font (size 1.27 1.27)) hide)"

def _pin(num, px, py, ang, name="~", etype="passive", hide=False):
    h = " hide" if hide else ""
    ln = 1.27 if etype != "power_in_hidden" else 0
    et = "power_in" if etype == "power_in_hidden" else etype
    return (f'(pin {et} line (at {px} {py} {ang}) (length {{ln}}){h} '
            f'(name "{name}" {F}) (number "{num}" {F}))', num)

class Sym:
    def __init__(self, name, pins, body, ref_prefix, pin_len=1.27,
                 power=False, pin_names_off=0.508, hide_pin_names=False,
                 hide_pin_numbers=False):
        # pins: list of (num, px, py, ang, name, etype)  - px,py = punto di aggancio
        self.name = name
        self.pins = {p[0]: p[1:] for p in pins}
        self.body = body
        self.ref_prefix = ref_prefix
        self.pin_len = pin_len
        self.power = power
        self.pin_names_off = pin_names_off
        self.hide_pin_names = hide_pin_names
        self.hide_pin_numbers = hide_pin_numbers

    def sexpr(self):
        p = []
        pw = " (power)" if self.power else ""
        pn = f'(pin_names (offset {self.pin_names_off})' + (" hide)" if self.hide_pin_names else ")")
        pnum = "(pin_numbers hide) " if self.hide_pin_numbers else ""
        p.append(f'(symbol "riv:{self.name}" {pw} {pnum}{pn} (in_bom yes) (on_board yes)')
        p.append(f'  (property "Reference" "{self.ref_prefix}" (id 0) (at 0 2.54 0) {F})')
        p.append(f'  (property "Value" "{self.name}" (id 1) (at 0 -2.54 0) {F})')
        p.append(f'  (property "Footprint" "" (id 2) (at 0 0 0) {FH})')
        p.append(f'  (property "Datasheet" "" (id 3) (at 0 0 0) {FH})')
        p.append(f'  (symbol "{self.name}_0_1"')
        for b in self.body:
            p.append("    " + b)
        p.append('  )')
        p.append(f'  (symbol "{self.name}_1_1"')
        for num, (px, py, ang, name, etype, ln, hide) in self.pins.items():
            h = " hide" if hide else ""
            p.append(f'    (pin {etype} line (at {px} {py} {ang}) (length {ln}){h} '
                     f'(name "{name}" {F}) (number "{num}" {F}))')
        p.append('  )')
        p.append(')')
        return "\n".join(p)

def P(num, px, py, ang, name="~", etype="passive", ln=1.27, hide=False):
    return (str(num), px, py, ang, name, etype, ln, hide)

def rect(x1, y1, x2, y2, fill="none"):
    return (f'(rectangle (start {x1} {y1}) (end {x2} {y2}) '
            f'(stroke (width 0.254) (type default) (color 0 0 0 0)) (fill (type {fill})))')

def poly(pts, width=0.254, fill="none"):
    s = " ".join(f"(xy {x} {y})" for x, y in pts)
    return (f'(polyline (pts {s}) (stroke (width {width}) (type default) '
            f'(color 0 0 0 0)) (fill (type {fill})))')

def circ(cx, cy, r, fill="none", width=0.254):
    return (f'(circle (center {cx} {cy}) (radius {r}) (stroke (width {width}) '
            f'(type default) (color 0 0 0 0)) (fill (type {fill})))')

def arc(sx, sy, mx, my, ex, ey, width=0.254):
    return (f'(arc (start {sx} {sy}) (mid {mx} {my}) (end {ex} {ey}) '
            f'(stroke (width {width}) (type default) (color 0 0 0 0)) (fill (type none)))')

def txt(t, x, y, ang=0):
    return f'(text "{t}" (at {x} {y} {ang}) {F})'

SYMS = {}

def add(sym):
    SYMS[sym.name] = sym

# ---------------- R -----------------
add(Sym("R", [P(1, 0, 3.81, 270), P(2, 0, -3.81, 90)],
        [rect(-1.016, -2.54, 1.016, 2.54)], "R", hide_pin_names=True))

# ---------------- C -----------------
add(Sym("C", [P(1, 0, 3.81, 270, ln=3.048), P(2, 0, -3.81, 90, ln=3.048)],
        [poly([(-1.905, 0.762), (1.905, 0.762)], width=0.3),
         poly([(-1.905, -0.762), (1.905, -0.762)], width=0.3)],
        "C", hide_pin_names=True))

# ---------------- L -----------------
add(Sym("L", [P(1, 0, 5.08, 270, ln=1.27), P(2, 0, -5.08, 90, ln=1.27)],
        [arc(0, 3.81, 0.9525, 2.8575, 0, 1.905),
         arc(0, 1.905, 0.9525, 0.9525, 0, 0),
         arc(0, 0, 0.9525, -0.9525, 0, -1.905),
         arc(0, -1.905, 0.9525, -2.8575, 0, -3.81)],
        "L", hide_pin_names=True))

# ---------------- D (1=K a sinistra, 2=A a destra) -----------------
add(Sym("D", [P(1, -3.81, 0, 0, "K", ln=3.175), P(2, 3.81, 0, 180, "A", ln=3.175)],
        [poly([(-0.635, 1.016), (-0.635, -1.016)], width=0.3),
         poly([(0.635, 1.016), (0.635, -1.016), (-0.635, 0), (0.635, 1.016)], fill="none")],
        "D", hide_pin_names=True))

# ---------------- LED (1=K sinistra, 2=A destra) -----------------
add(Sym("LED", [P(1, -3.81, 0, 0, "K", ln=3.175), P(2, 3.81, 0, 180, "A", ln=3.175)],
        [poly([(-0.635, 1.016), (-0.635, -1.016)], width=0.3),
         poly([(0.635, 1.016), (0.635, -1.016), (-0.635, 0), (0.635, 1.016)]),
         poly([(0.254, 1.27), (1.016, 2.286)]),
         poly([(0.508, 2.286), (1.016, 2.286), (1.016, 1.778)]),
         poly([(1.27, 1.016), (2.032, 2.032)]),
         poly([(1.524, 2.032), (2.032, 2.032), (2.032, 1.524)])],
        "D", hide_pin_names=True))

# ---------------- NPN / PNP (1=B 2=E 3=C) -----------------
_tr_body_common = [
    circ(0.635, 0, 2.8, width=0.254),
    poly([(-0.254, 1.778), (-0.254, -1.778)], width=0.5),   # barra base
    poly([(-2.54, 0), (-0.254, 0)]),                        # base line dal pin
]
add(Sym("NPN", [P(1, -5.08, 0, 0, "B", ln=2.54),
                P(2, 2.54, -5.08, 90, "E", ln=2.54),
                P(3, 2.54, 5.08, 270, "C", ln=2.54)],
        _tr_body_common + [
            poly([(2.54, 2.54), (-0.254, 0.508)]),                    # collettore
            poly([(-0.254, -0.508), (2.54, -2.54)]),                  # emettitore
            poly([(1.778, -2.286), (2.54, -2.54), (2.286, -1.778), (1.778, -2.286)], fill="outline"),  # freccia out
        ], "Q", hide_pin_names=True))
add(Sym("PNP", [P(1, -5.08, 0, 0, "B", ln=2.54),
                P(2, 2.54, -5.08, 90, "E", ln=2.54),
                P(3, 2.54, 5.08, 270, "C", ln=2.54)],
        _tr_body_common + [
            poly([(2.54, 2.54), (-0.254, 0.508)]),
            poly([(-0.254, -0.508), (2.54, -2.54)]),
            poly([(0.508, -0.762), (0.254, -1.524), (1.27, -1.27), (0.508, -0.762)], fill="outline"),  # freccia in (verso base)
        ], "Q", hide_pin_names=True))

# ---------------- POT (1=alto, 2=cursore dx, 3=basso) -----------------
add(Sym("PNP_EUP", [P(1, -5.08, 0, 0, "B", ln=2.54),
                    P(2, 2.54, 5.08, 270, "E", ln=2.54),
                    P(3, 2.54, -5.08, 90, "C", ln=2.54)],
        _tr_body_common + [
            poly([(2.54, -2.54), (-0.254, -0.508)]),                  # collettore (giu')
            poly([(-0.254, 0.508), (2.54, 2.54)]),                    # emettitore (su)
            poly([(0.508, 0.762), (0.254, 1.524), (1.27, 1.27), (0.508, 0.762)], fill="outline"),
        ], "Q", hide_pin_names=True))

add(Sym("POT", [P(1, 0, 3.81, 270), P(2, 3.81, 0, 180, "W", ln=2.032),
                P(3, 0, -3.81, 90)],
        [rect(-1.016, -2.54, 1.016, 2.54),
         poly([(1.778, 0), (1.27, 0.381), (1.27, -0.381), (1.778, 0)], fill="outline")],
        "RV", hide_pin_names=True))

# ---------------- CONN2 -----------------
add(Sym("CONN2", [P(1, -6.35, 1.27, 0, "1", ln=3.81),
                  P(2, -6.35, -1.27, 0, "2", ln=3.81)],
        [rect(-2.54, -2.54, 2.54, 2.54),
         circ(-1.27, 1.27, 0.508), circ(-1.27, -1.27, 0.508)],
        "J", hide_pin_names=True))

# ---------------- CONN3 -----------------
add(Sym("CONN3", [P(1, -6.35, 2.54, 0, "1", ln=3.81),
                  P(2, -6.35, 0, 0, "2", ln=3.81),
                  P(3, -6.35, -2.54, 0, "3", ln=3.81)],
        [rect(-2.54, -3.81, 2.54, 3.81),
         circ(-1.27, 2.54, 0.508), circ(-1.27, 0, 0.508), circ(-1.27, -2.54, 0.508)],
        "J", hide_pin_names=True))

# ---------------- foro di fissaggio -----------------
add(Sym("MH", [P(1, 0, -3.81, 90, "1", ln=1.27)],
        [circ(0, 0, 1.27), circ(0, 0, 2.54)],
        "H", hide_pin_names=True, hide_pin_numbers=True))

# ---------------- test point -----------------
add(Sym("TP", [P(1, 0, -2.54, 90, "1", ln=1.524)],
        [circ(0, 0, 0.762)],
        "TP", hide_pin_names=True, hide_pin_numbers=True))

# ---------------- IC helper -----------------
def icbox(name, w, h, left, right, top, bottom, ref="U", label_extra=None):
    """left/right/top/bottom: list of (num, offset_from_center, pname, etype)."""
    hw, hh = w / 2, h / 2
    pins = []
    for num, off, pname, et in left:
        pins.append(P(num, -hw - 2.54, off, 0, pname, et, ln=2.54))
    for num, off, pname, et in right:
        pins.append(P(num, hw + 2.54, off, 180, pname, et, ln=2.54))
    for num, off, pname, et in top:
        pins.append(P(num, off, hh + 2.54, 270, pname, et, ln=2.54))
    for num, off, pname, et in bottom:
        pins.append(P(num, off, -hh - 2.54, 90, pname, et, ln=2.54))
    body = [rect(-hw, -hh, hw, hh, fill="background")]
    if label_extra:
        body.append(txt(label_extra, 0, 0))
    return Sym(name, pins, body, ref, pin_names_off=0.762)

# LT3461: left: VIN(6) SHDN(4) GND(2) | right: SW(1) CAP(5) FB(3)
add(icbox("LT3461", 12.7, 10.16,
          [("6", 2.54, "VIN", "power_in"), ("4", 0, "~SHDN", "input"), ("2", -2.54, "GND", "power_in")],
          [("1", 2.54, "SW", "output"), ("5", 0, "CAP", "power_out"), ("3", -2.54, "FB", "input")],
          [], []))

# MAX961: left: IN+(1) IN-(2) LE(4) SHDN(3) ; right: Q(6) ~Q(7) ; top VCC(8) ; bottom GND(5)
add(icbox("MAX961", 15.24, 15.24,
          [("1", 5.08, "+", "input"), ("2", 2.54, "-", "input"),
           ("4", -2.54, "LE", "input"), ("3", -5.08, "SHDN", "input")],
          [("6", 2.54, "Q", "output"), ("7", -2.54, "~Q", "output")],
          [("8", 0, "VCC", "power_in")],
          [("5", 0, "GND", "power_in")]))

# TLC555: left: TR(2) TH(6) CTL(5) R(4) ; right: Q(3) DIS(7) ; top VCC(8) ; bottom GND(1)
add(icbox("TLC555", 15.24, 15.24,
          [("2", 5.08, "TR", "input"), ("6", 2.54, "TH", "input"),
           ("5", -2.54, "CTL", "input"), ("4", -5.08, "~R", "input")],
          [("3", 5.08, "Q", "output"), ("7", 0, "DIS", "open_collector")],
          [("8", 0, "VCC", "power_in")],
          [("1", 0, "GND", "power_in")]))

# MCP1402: left IN(3) ; right OUT(5) ; top VDD(2) ; bottom GND(1) GND(4)
add(icbox("MCP1402", 12.7, 10.16,
          [("3", 0, "IN", "input")],
          [("5", 0, "OUT", "output")],
          [("2", 0, "VDD", "power_in")],
          [("1", -2.54, "GND", "power_in"), ("4", 2.54, "GND", "power_in")]))

# 74LVC1G17 buffer Schmitt (SOT-23-5 DBV): 1 NC, 2 A, 3 GND, 4 Y, 5 VCC
add(icbox("LVC1G17", 10.16, 7.62,
          [("2", 0, "A", "input"), ("1", -2.54, "NC", "no_connect")],
          [("4", 0, "Y", "output")],
          [("5", 0, "VCC", "power_in")],
          [("3", 0, "GND", "power_in")]))

# 74LVC1G11 AND a 3 ingressi (SOT-23-6 DBV): 1 A, 2 GND, 3 B, 4 Y, 5 VCC, 6 C
add(icbox("LVC1G11", 10.16, 10.16,
          [("1", 2.54, "A", "input"), ("3", 0, "B", "input"), ("6", -2.54, "C", "input")],
          [("4", 0, "Y", "output")],
          [("5", 0, "VCC", "power_in")],
          [("2", 0, "GND", "power_in")]))

# MCP3424 ADC delta-sigma 4 canali I2C (SOIC-14): 1 CH1+ 2 CH1- 3 CH2+ 4 CH2- 5 VSS
# 6 VDD 7 SDA 8 SCL 9 Adr0 10 Adr1 11 CH3+ 12 CH3- 13 CH4+ 14 CH4-
add(icbox("MCP3424", 15.24, 20.32,
          [("1", 7.62, "CH1+", "input"), ("2", 5.08, "CH1-", "input"),
           ("3", 2.54, "CH2+", "input"), ("4", 0, "CH2-", "input"),
           ("11", -2.54, "CH3+", "input"), ("12", -5.08, "CH3-", "input"),
           ("13", -7.62, "CH4+", "input"), ("14", -10.16, "CH4-", "input")],
          [("7", 2.54, "SDA", "bidirectional"), ("8", 0, "SCL", "input"),
           ("9", -5.08, "A0", "input"), ("10", -7.62, "A1", "input")],
          [("6", 0, "VDD", "power_in")],
          [("5", 0, "VSS", "power_in")]))

# LP2985: left IN(1) EN(3) ; right OUT(5) BYP(4) ; bottom GND(2)
add(icbox("LP2985", 12.7, 10.16,
          [("1", 2.54, "IN", "power_in"), ("3", -2.54, "EN", "input")],
          [("5", 2.54, "OUT", "power_out"), ("4", -2.54, "BYP", "passive")],
          [], [("2", 0, "GND", "power_in")]))

# MCP1825: left IN(1) ; right OUT(3) ; bottom GND(2) TAB(4)
add(icbox("MCP1825", 12.7, 10.16,
          [("1", 2.54, "IN", "power_in")],
          [("3", 2.54, "OUT", "power_out")],
          [], [("2", -2.54, "GND", "power_in"), ("4", 2.54, "TAB", "passive")]))

# LT1636 opamp triangolo: 2=- (alto sx), 3=+ (basso sx), 6=out, 7=V+ su, 4=V- giu; 1,5,8 NC nascosti
add(Sym("LT1636",
        [P(2, -7.62, 2.54, 0, "-", "input", ln=2.54),
         P(3, -7.62, -2.54, 0, "+", "input", ln=2.54),
         P(6, 7.62, 0, 180, "~", "output", ln=2.54),
         P(7, -1.27, 7.62, 270, "V+", "power_in", ln=3.81),
         P(4, -1.27, -7.62, 90, "V-", "power_in", ln=3.81),
         P(1, 2.54, 2.54, 270, "NC", "no_connect", ln=0, hide=True),
         P(5, 2.54, 0, 270, "NC", "no_connect", ln=0, hide=True),
         P(8, 2.54, -2.54, 270, "NC", "no_connect", ln=0, hide=True)],
        [poly([(-5.08, 5.08), (-5.08, -5.08), (5.08, 0), (-5.08, 5.08)], fill="background"),
         txt("+", -3.81, -2.54), txt("-", -3.81, 2.54)],
        "U", hide_pin_names=True))

# ---------------- power symbols -----------------
# ---------------- protezione dell'alimentazione -----------------
# USB-C solo alimentazione: 1 VBUS, 2 CC1, 3 CC2, 4 GND (pin a destra)
add(icbox("USBC", 10.16, 10.16, [],
          [("1", 3.81, "VBUS", "passive"), ("2", 1.27, "CC1", "passive"),
           ("3", -1.27, "CC2", "passive"), ("4", -3.81, "GND", "passive")],
          [], [], ref="J"))
# fusibile ripristinabile (verticale come R): rettangolo attraversato da una linea
add(Sym("FUSE", [P(1, 0, 3.81, 270), P(2, 0, -3.81, 90)],
        [rect(-0.762, -2.54, 0.762, 2.54), poly([(0, 2.54), (0, -2.54)])],
        "F", hide_pin_names=True))
# TVS unidirezionale (1 = K sinistra, 2 = A destra): diodo con barra piegata
add(Sym("TVS", [P(1, -3.81, 0, 0, "K", ln=3.175), P(2, 3.81, 0, 180, "A", ln=3.175)],
        [poly([(-1.016, 1.27), (-0.635, 1.016), (-0.635, -1.016), (-0.254, -1.27)], width=0.3),
         poly([(0.635, 1.016), (0.635, -1.016), (-0.635, 0), (0.635, 1.016)])],
        "D", hide_pin_names=True))
# MOSFET P (1 = G sinistra, 2 = S in alto, 3 = D in basso); freccia verso il gate esterna
add(Sym("PMOS", [P(1, -5.08, 0, 0, "G", ln=2.54),
                 P(2, 2.54, 5.08, 270, "S", ln=2.54),
                 P(3, 2.54, -5.08, 90, "D", ln=2.54)],
        [poly([(-2.54, 0), (-1.27, 0)]),
         poly([(-1.27, 1.905), (-1.27, -1.905)], width=0.3),          # gate
         poly([(-0.508, 2.286), (-0.508, 1.27)], width=0.4),          # canale (3 tratti)
         poly([(-0.508, 0.508), (-0.508, -0.508)], width=0.4),
         poly([(-0.508, -1.27), (-0.508, -2.286)], width=0.4),
         poly([(-0.508, 1.778), (2.54, 1.778), (2.54, 2.54)]),         # source
         poly([(-0.508, -1.778), (2.54, -1.778), (2.54, -2.54)]),      # drain
         poly([(-0.508, 0), (2.54, 0), (2.54, 1.778)]),                # body al source
         poly([(0.762, 0), (0.254, 0.381), (0.254, -0.381), (0.762, 0)], fill="outline")],   # freccia (P: verso l'esterno)
        "Q", hide_pin_names=True))


# ---------------- moduli: meteo e scatolina di acquisizione -----------------
# Sensirion SHT4x (DFN-4): 1 SDA, 2 SCL, 3 VDD, 4 VSS (libreria KiCad Sensor_Humidity:SHT4x)
add(icbox("SHT4X", 10.16, 7.62,
          [("1", 1.27, "SDA", "bidirectional"), ("2", -1.27, "SCL", "input")], [],
          [("3", 0, "VDD", "power_in")], [("4", 0, "VSS", "power_in")]))
# ST LPS22HH (HLGA-10): pinout della libreria KiCad (LPS22HH estende LPS25HB)
add(icbox("LPS22HH", 12.7, 12.7,
          [("4", 2.54, "SDA", "bidirectional"), ("2", 0, "SCL", "input"),
           ("5", -2.54, "SA0", "input"), ("6", -5.08, "~CS", "input")],
          [("7", 0, "INT_DRDY", "output")],
          [("10", -1.27, "VDD", "power_in"), ("1", 1.27, "VDD_IO", "power_in")],
          [("3", -2.54, "GND", "passive"), ("8", 0, "GND", "power_in"), ("9", 2.54, "GND", "passive")]))
# connettore Qwiic / STEMMA QT (JST SH 4 poli): 1 GND, 2 3V3, 3 SDA, 4 SCL
add(Sym("QWIIC", [P(1, -6.35, 3.81, 0, "GND", ln=3.81), P(2, -6.35, 1.27, 0, "3V3", ln=3.81),
                  P(3, -6.35, -1.27, 0, "SDA", ln=3.81), P(4, -6.35, -3.81, 0, "SCL", ln=3.81)],
        [rect(-2.54, -5.08, 2.54, 5.08)] + [circ(-1.27, y, 0.508) for y in (3.81, 1.27, -1.27, -3.81)],
        "J", pin_names_off=0.762))
# connettore 1x6 (GPS)
add(Sym("CONN6", [P(k, -6.35, 6.35 - (k - 1) * 2.54, 0, str(k), ln=3.81) for k in range(1, 7)],
        [rect(-2.54, -7.62, 2.54, 8.89)] + [circ(-1.27, 6.35 - k * 2.54, 0.508) for k in range(6)],
        "J", hide_pin_names=True))
# ponticelli a saldare: SJ2 aperto (1-2), SJ3 con il centrale (2) verso 1 o 3
add(Sym("SJ2", [P(1, -3.81, 0, 0, "1", ln=2.286), P(2, 3.81, 0, 180, "2", ln=2.286)],
        [arc(-0.254, 1.016, -1.27, 0, -0.254, -1.016), poly([(-0.254, 1.016), (-0.254, -1.016)]),
         arc(0.254, -1.016, 1.27, 0, 0.254, 1.016), poly([(0.254, 1.016), (0.254, -1.016)])],
        "JP", hide_pin_names=True))
add(Sym("SJ3", [P(1, -5.08, 0, 0, "1", ln=2.54), P(3, 5.08, 0, 180, "3", ln=2.54),
                P(2, 0, -3.81, 90, "2", ln=2.54)],
        [rect(-2.54, -1.27, -1.016, 1.27), rect(-0.762, -1.27, 0.762, 1.27), rect(1.016, -1.27, 2.54, 1.27),
         poly([(-1.016, 0), (-0.762, 0)], width=0.6)],
        "JP", hide_pin_names=True))
# TI TCA9548A (TSSOP-24): pinout della libreria KiCad (TCA9548APWR)
_sd = []
for k in range(8):
    _sd.append((str(4 + 2 * k + (1 if k >= 4 else 0)), 10.16 - k * 2.54 * 1.0 - 0.0, f"SD{k}", "bidirectional"))
add(icbox("TCA9548A", 15.24, 43.18,
          [("23", 17.78, "SDA", "bidirectional"), ("22", 15.24, "SCL", "input"), ("3", 10.16, "~RESET", "input"),
           ("1", 2.54, "A0", "input"), ("2", 0, "A1", "input"), ("21", -2.54, "A2", "input")],
          [(str(4 + 2 * k + (1 if k >= 4 else 0)), 19.05 - k * 5.08, f"SD{k}", "bidirectional") for k in range(8)]
          + [(str(5 + 2 * k + (1 if k >= 4 else 0)), 16.51 - k * 5.08, f"SC{k}", "output") for k in range(8)],
          [("24", 0, "VCC", "power_in")], [("12", 0, "GND", "power_in")]))
# Diodes AP2112K (SOT-23-5): 1 VIN, 2 GND, 3 EN, 4 NC, 5 VOUT
add(icbox("AP2112K", 10.16, 7.62,
          [("1", 1.27, "VIN", "power_in"), ("3", -1.27, "EN", "input")],
          [("5", 1.27, "VOUT", "power_out"), ("4", -1.27, "NC", "no_connect")],
          [], [("2", 0, "GND", "power_in")]))
# Raspberry Pi Pico / Pico 2 (modulo su zoccolo): pin 1-20 a sinistra, 40-21 a destra
_PL = ["GP0", "GP1", "GND", "GP2", "GP3", "GP4", "GP5", "GND", "GP6", "GP7", "GP8", "GP9", "GND",
       "GP10", "GP11", "GP12", "GP13", "GND", "GP14", "GP15"]
_PR = ["VBUS", "VSYS", "GND", "3V3_EN", "3V3(OUT)", "ADC_VREF", "GP28", "GND", "GP27", "GP26",
       "RUN", "GP22", "GND", "GP21", "GP20", "GP19", "GP18", "GND", "GP17", "GP16"]   # pin 40 ... 21
PICO_PINS = {k + 1: n for k, n in enumerate(_PL)}
PICO_PINS.update({40 - k: n for k, n in enumerate(_PR)})
add(icbox("PICO2", 20.32, 53.34,
          [(str(k + 1), 24.13 - k * 2.54, _PL[k], "power_in" if _PL[k] == "GND" else "bidirectional")
           for k in range(20)],
          [(str(40 - k), 24.13 - k * 2.54, _PR[k],
            "power_in" if _PR[k] in ("GND",) else ("power_out" if _PR[k] in ("3V3(OUT)", "VBUS") else "bidirectional"))
           for k in range(20)],
          [], [], ref="A"))
# diodo ESD bidirezionale (SOD-323): due diodi contrapposti
add(Sym("TVSB", [P(1, 0, 3.81, 270, ln=1.27), P(2, 0, -3.81, 90, ln=1.27)],
        [poly([(-1.016, 2.54), (1.016, 2.54), (0, 0.508), (-1.016, 2.54)]),
         poly([(-1.016, -2.54), (1.016, -2.54), (0, -0.508), (-1.016, -2.54)]),
         poly([(-1.27, 0.508), (1.27, 0.508)], width=0.3), poly([(-1.27, -0.508), (1.27, -0.508)], width=0.3),
         poly([(0, 2.54), (0, 2.54)])],
        "D", hide_pin_names=True))


def power_sym(name, down=False):
    if name == "GND":
        body = [poly([(0, 0), (0, -1.27)]),
                poly([(-1.27, -1.27), (1.27, -1.27)]),
                poly([(-0.762, -1.778), (0.762, -1.778)]),
                poly([(-0.254, -2.286), (0.254, -2.286)])]
        pin = P(1, 0, 0, 270, "GND", "power_in", ln=0, hide=True)
    else:
        body = [poly([(0, 0), (0, 1.27)]),
                poly([(-0.762, 1.27), (0.762, 1.27), (0, 2.54), (-0.762, 1.27)], fill="outline"),
                ]
        pin = P(1, 0, 0, 90, name, "power_in", ln=0, hide=True)
    s = Sym("PWR_" + name, [pin], body, "#PWR", power=True, hide_pin_names=True,
            hide_pin_numbers=True)
    return s

for n in ("+5V", "+3V3", "+3V6", "GND"):
    add(power_sym(n))

# PWR_FLAG (power_out per ERC)
add(Sym("PWR_FLAG",
        [P(1, 0, 0, 90, "pwr", "power_out", ln=0)],
        [poly([(0, 0), (0, 1.27), (-1.016, 1.905), (0, 2.54), (1.016, 1.905), (0, 1.27)])],
        "#FLG", power=True, hide_pin_names=True, hide_pin_numbers=True))

def lib_symbols_sexpr():
    return "\n".join(s.sexpr() for s in SYMS.values())
