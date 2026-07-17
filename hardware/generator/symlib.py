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
          [("1", 2.54, "SW", "output"), ("5", 0, "CAP", "output"), ("3", -2.54, "FB", "input")],
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
