# -*- coding: utf-8 -*-
"""Genera riv_cosmici.kicad_sch (formato KiCad 6, apribile in 7/8/9)
con verifica automatica: la connettivita' estratta dal file deve
coincidere con netdata.NETS.
"""
import uuid as _uuid
from symlib import SYMS, lib_symbols_sexpr
from netdata import COMPONENTS, NETS

def U():
    return str(_uuid.uuid4())

FP_MAP = {
    "R0805": "rivlib:R_0805", "C0805": "rivlib:C_0805",
    "C1206": "rivlib:C_1206", "C1210": "rivlib:C_1210",
    "L_PWR": "rivlib:L_PWR_5050", "DO35": "rivlib:D_DO35",
    "LED0805": "rivlib:LED_0805", "SOT23": "rivlib:SOT23",
    "SOT23-5": "rivlib:SOT23-5", "SOT23-6": "rivlib:SOT23-6",
    "SO8": "rivlib:SOIC8", "SOT223": "rivlib:SOT223",
    "3296W": "rivlib:TRIM_3296W", "HDR2": "rivlib:HDR1x02",
    "LEMO00": "rivlib:LEMO_EPL00", "TP": "rivlib:TP_THT",
    "SO14": "rivlib:SOIC14", "HDR3": "rivlib:HDR1x03",
}
SYM_MAP = {  # kind -> lib symbol
    "R": "R", "C": "C", "L": "L", "D": "D", "LED": "LED", "NPN": "NPN",
    "PNP": "PNP", "POT": "POT", "CONN2": "CONN2", "LT3461": "LT3461",
    "TLC555": "TLC555", "MAX961": "MAX961", "MCP1402": "MCP1402",
    "LP2985": "LP2985", "MCP1825": "MCP1825", "LT1636": "LT1636",
    "LVC1G17": "LVC1G17", "LVC1G11": "LVC1G11", "TP": "TP",
    "MCP3424": "MCP3424", "CONN3": "CONN3",
}

instances = []   # (ref, symname, x, y, rot, mirror, value, footprint)
wires = []       # ((x1,y1),(x2,y2))
junctions = []
labels = []      # (name, x, y)
powers = []      # (netname, x, y, rot)
noconn = []
texts = []       # (string, x, y)
flags = []       # PWR_FLAG positions

def place(ref, x, y, rot=0, mirror=None, sym=None):
    kind, value, fpk, _ = COMPONENTS[ref]
    instances.append((ref, sym or SYM_MAP[kind], x, y, rot, mirror, value, FP_MAP[fpk]))

def w(x1, y1, x2, y2):
    a = (round(x1, 3), round(y1, 3)); b = (round(x2, 3), round(y2, 3))
    if a != b:
        wires.append((a, b))

def path(*pts):
    for a, b in zip(pts, pts[1:]):
        w(a[0], a[1], b[0], b[1])

def J(x, y):
    junctions.append((x, y))

def L(name, x, y):
    labels.append((name, x, y))

def PW(net, x, y, rot=0):
    powers.append((net, x, y, rot))

def NCm(x, y):
    noconn.append((x, y))

def T(s, x, y):
    texts.append((s, x, y))

def FLG(x, y):
    flags.append((x, y))

# =============================== LAYOUT ===============================
def build_single():
    """disegno della scheda a 1 canale (blocchi 1..9)"""
    # ---- blocco 1: front-end SiPM
    place("J1", 30, 60, 180)
    T("SiPM (cavo Fileca)", 24, 53)
    path((36.35, 58.73), (41.91, 58.73), (41.91, 54.61)); L("BIAS", 41.91, 54.61)
    w(36.35, 61.27, 45.72, 61.27)
    place("R10", 45.72, 65.08); PW("GND", 45.72, 68.89); J(45.72, 61.27)
    w(45.72, 61.27, 50.8, 61.27)
    place("C7", 54.61, 61.27, 90)
    w(58.42, 61.27, 63.5, 61.27)
    place("R9", 63.5, 65.08); PW("GND", 63.5, 68.89); J(63.5, 61.27)
    place("Q1", 71.12, 61.27)
    w(63.5, 61.27, 66.04, 61.27)
    w(73.66, 66.35, 73.66, 67.62); PW("GND", 73.66, 67.62)
    # collettore Q1 su, R12, rail +3V3
    path((73.66, 56.19), (73.66, 48.26))
    place("R12", 73.66, 44.45, 180)
    w(73.66, 40.64, 73.66, 38.1)
    path((73.66, 38.1), (81.28, 38.1), (88.9, 38.1), (96.52, 38.1))
    PW("+3V3", 81.28, 38.1); J(88.9, 38.1)
    place("CF1", 96.52, 41.91); PW("GND", 96.52, 45.72)
    # retroazione R11 base-collettore
    path((63.5, 61.27), (63.5, 53.34), (64.77, 53.34))
    place("R11", 68.58, 53.34, 90)
    w(72.39, 53.34, 73.66, 53.34); J(73.66, 53.34)
    # Q2 PNP (simbolo con E in alto, senza mirror)
    place("Q2", 86.36, 53.34, 0, sym="PNP_EUP")
    w(73.66, 53.34, 81.28, 53.34)
    place("R13", 88.9, 44.45, 180)
    w(88.9, 40.64, 88.9, 38.1)
    # nodo D: collettore Q2 giu', R14, C11, R15
    path((88.9, 58.42), (88.9, 63.5))
    place("R14", 88.9, 67.31); PW("GND", 88.9, 71.12); J(88.9, 63.5)
    w(88.9, 63.5, 93.98, 63.5)
    place("C11", 97.79, 63.5, 90)
    w(101.6, 63.5, 106.68, 63.5)
    place("R15", 106.68, 67.31); PW("GND", 106.68, 71.12); J(106.68, 63.5)
    w(106.68, 63.5, 111.76, 63.5); L("CMP_IN", 111.76, 63.5)
    T("Amplificatore front-end SiPM", 45, 30)

    # ---- blocco 2: comparatore MAX961
    place("U3", 137.16, 57.15)
    w(127.0, 52.07, 121.92, 52.07); L("CMP_IN", 121.92, 52.07)
    w(127.0, 54.61, 119.38, 54.61); L("TH", 119.38, 54.61)
    # LE: R16 e C9
    path((127.0, 59.69), (118.11, 59.69))
    place("R16", 118.11, 63.5); PW("GND", 118.11, 67.31)
    J(124.46, 59.69)
    path((124.46, 59.69), (124.46, 73.66))
    place("C9", 128.27, 73.66, 90)
    w(132.08, 73.66, 152.4, 73.66)
    # SHDN a GND
    w(127.0, 62.23, 123.19, 62.23); PW("GND", 123.19, 62.23)
    # VCC / GND
    w(137.16, 46.99, 137.16, 43.18); PW("+3V3", 137.16, 43.18)
    path((137.16, 43.18), (144.78, 43.18), (144.78, 44.45))
    place("CF2", 144.78, 48.26); PW("GND", 144.78, 52.07)
    PW("GND", 137.16, 67.31)
    # uscite
    path((147.32, 54.61), (152.4, 54.61), (156.21, 54.61)); L("CMP_Q", 156.21, 54.61)
    J(152.4, 54.61)
    path((152.4, 54.61), (152.4, 73.66))
    w(147.32, 59.69, 156.21, 59.69); L("CMP_QB", 156.21, 59.69)
    T("Comparatore di soglia", 130, 36)

    # ---- blocco 3: soglia regolabile
    path((115.57, 80.01), (115.57, 83.82)); L("TH", 115.57, 80.01)
    place("R17", 115.57, 87.63)
    # V2 potenziometro: cursore -> R17 -> TH, estremo alto -> R19 -> +3V6
    place("V2", 115.57, 97.79)
    path((119.38, 97.79), (120.65, 97.79), (120.65, 91.44), (115.57, 91.44))
    path((115.57, 93.98), (107.95, 93.98), (107.95, 91.44))
    place("R19", 107.95, 87.63, 180)
    PW("+3V6", 107.95, 83.82)
    w(115.57, 101.6, 115.57, 104.14)
    place("R18", 115.57, 107.95); PW("GND", 115.57, 111.76)
    T("Soglia (V2)", 105, 78)
    # LP2985 3,6V (U5)
    place("U5", 147.32, 95.25)
    w(138.43, 92.71, 135.89, 92.71)
    path((138.43, 97.79), (135.89, 97.79), (135.89, 92.71)); J(135.89, 92.71)
    w(135.89, 92.71, 135.89, 90.17); PW("+5V", 135.89, 90.17)
    path((156.21, 92.71), (158.75, 92.71), (161.29, 92.71)); J(158.75, 92.71)
    w(158.75, 92.71, 158.75, 90.17); PW("+3V6", 158.75, 90.17)
    place("CF4", 161.29, 96.52); PW("GND", 161.29, 100.33)
    NCm(156.21, 97.79)
    PW("GND", 147.32, 102.87)
    T("Rif. soglia 3,6V", 140, 85)

    # ---- blocco 4: driver MCP1402 + TTL out
    place("U4", 198.12, 53.34)
    w(189.23, 53.34, 185.42, 53.34); L("CMP_Q", 185.42, 53.34)
    w(207.01, 53.34, 214.63, 53.34)
    place("J2", 220.98, 54.61)
    path((214.63, 55.88), (212.09, 55.88), (212.09, 58.42)); PW("GND", 212.09, 58.42)
    T("TTL OUT", 219, 50)
    w(198.12, 45.72, 198.12, 43.18); PW("+5V", 198.12, 43.18)
    path((198.12, 43.18), (203.2, 43.18), (203.2, 43.18))
    place("CF3", 203.2, 46.99)
    w(203.2, 43.18, 203.2, 43.18)
    path((203.2, 43.18), (203.2, 43.18))
    PW("GND", 203.2, 50.8)
    path((195.58, 60.96), (195.58, 63.5), (198.12, 63.5), (200.66, 63.5), (200.66, 60.96))
    PW("GND", 198.12, 63.5); J(198.12, 63.5)
    T("Driver uscita", 192, 38)

    # ---- blocco 5: monostabile TLC555 + LED
    place("U2", 261.62, 57.15)
    w(251.46, 52.07, 246.38, 52.07); L("CMP_QB", 246.38, 52.07)
    place("R20", 240.03, 48.26, 180)
    w(240.03, 44.45, 240.03, 41.91); PW("+3V3", 240.03, 41.91)
    w(251.46, 54.61, 240.03, 54.61)
    path((240.03, 52.07), (240.03, 54.61), (240.03, 58.42), (240.03, 72.39))
    J(240.03, 54.61); J(240.03, 58.42)
    w(240.03, 58.42, 234.95, 58.42)
    place("C21", 234.95, 62.23); PW("GND", 234.95, 66.04)
    path((271.78, 57.15), (275.59, 57.15), (275.59, 72.39), (240.03, 72.39))
    # CTL con CF6
    path((251.46, 59.69), (246.38, 59.69), (246.38, 60.96))
    place("CF6", 246.38, 64.77); PW("GND", 246.38, 68.58)
    # RESET a +3V3
    w(251.46, 62.23, 243.84, 62.23); PW("+3V3", 243.84, 62.23)
    # VCC + CF5
    w(261.62, 46.99, 261.62, 43.18); PW("+3V3", 261.62, 43.18)
    path((261.62, 43.18), (266.7, 43.18), (266.7, 43.18))
    place("CF5", 266.7, 46.99); PW("GND", 266.7, 50.8)
    PW("GND", 261.62, 67.31)
    # LED
    w(271.78, 52.07, 276.86, 52.07)
    place("R21", 280.67, 52.07, 90)
    place("D3", 289.56, 52.07, 180)
    w(284.48, 52.07, 285.75, 52.07)
    w(293.37, 52.07, 294.64, 52.07); PW("GND", 294.64, 52.07)
    T("Monostabile LED (~11ms)", 250, 36)

    # ---- blocco 6: boost LT3461 -> 40,2V
    place("U1", 66.04, 157.48)
    place("L1", 80.01, 146.05)
    PW("+5V", 80.01, 140.97)
    path((80.01, 151.13), (80.01, 154.94), (74.93, 154.94))
    w(57.15, 154.94, 53.34, 154.94)
    path((57.15, 157.48), (53.34, 157.48), (53.34, 154.94)); J(53.34, 154.94)
    w(53.34, 154.94, 48.26, 154.94)
    w(53.34, 154.94, 53.34, 152.4); PW("+5V", 53.34, 152.4)
    place("C22", 48.26, 158.75); PW("GND", 48.26, 162.56)
    path((57.15, 160.02), (55.88, 160.02), (55.88, 163.83)); PW("GND", 55.88, 163.83)
    # nodo VOUT40
    path((74.93, 157.48), (85.09, 157.48), (95.25, 157.48), (102.87, 157.48), (107.95, 157.48))
    L("VOUT40", 107.95, 157.48)
    J(85.09, 157.48); J(95.25, 157.48); J(102.87, 157.48)
    place("C2", 95.25, 161.29); PW("GND", 95.25, 165.1)
    place("C3", 102.87, 161.29); PW("GND", 102.87, 165.1)
    # feedback FB: R3 // C1, poi R1//R2//R22 a GND
    path((85.09, 157.48), (85.09, 160.02))
    place("R3", 85.09, 163.83)
    place("C1", 90.17, 163.83)
    w(85.09, 160.02, 90.17, 160.02); J(85.09, 160.02)
    path((74.93, 160.02), (77.47, 160.02), (77.47, 167.64))
    path((63.5, 167.64), (69.85, 167.64), (76.2, 167.64), (77.47, 167.64), (85.09, 167.64), (90.17, 167.64))
    J(69.85, 167.64); J(76.2, 167.64); J(77.47, 167.64); J(85.09, 167.64)
    place("R22", 63.5, 171.45)
    place("R2", 69.85, 171.45)
    place("R1", 76.2, 171.45)
    path((63.5, 175.26), (69.85, 175.26), (76.2, 175.26))
    PW("GND", 69.85, 175.26); J(69.85, 175.26)
    T("Boost 40,2V (bias SiPM)", 50, 140)

    # ---- blocco 7: regolatore lineare 38,4V (LT1636)
    place("U8", 152.4, 167.64)
    w(151.13, 160.02, 151.13, 157.48); L("VOUT40", 151.13, 157.48)
    PW("GND", 151.13, 175.26)
    w(144.78, 165.1, 140.97, 165.1); J(140.97, 165.1)
    place("R4", 140.97, 168.91); PW("GND", 140.97, 172.72)
    path((140.97, 165.1), (140.97, 158.75))
    place("R5", 144.78, 158.75, 90)
    path((148.59, 158.75), (165.1, 158.75), (165.1, 167.64))
    w(160.02, 167.64, 165.1, 167.64); J(165.1, 167.64)
    w(165.1, 167.64, 170.18, 167.64)
    place("R8", 173.99, 167.64, 90)
    path((177.8, 167.64), (182.88, 167.64), (187.96, 167.64)); J(182.88, 167.64)
    L("BIAS", 187.96, 167.64)
    place("C6", 182.88, 171.45); PW("GND", 182.88, 175.26)
    T("38,4V", 166, 164)
    # V+ = VOUT40 (sopra), VSET al pin +
    place("V1", 121.92, 177.8)
    path((125.73, 177.8), (128.27, 177.8), (128.27, 170.18), (133.35, 170.18), (137.16, 170.18), (144.78, 170.18))
    J(133.35, 170.18); J(137.16, 170.18)
    place("C4", 133.35, 173.99); PW("GND", 133.35, 177.8)
    place("R6", 137.16, 173.99); PW("GND", 137.16, 177.8)
    path((121.92, 173.99), (121.92, 171.45), (115.57, 171.45))
    place("R7", 115.57, 175.26); PW("GND", 115.57, 179.07)
    path((121.92, 181.61), (121.92, 184.15), (124.46, 184.15))
    place("D1", 128.27, 184.15)
    path((132.08, 184.15), (137.16, 184.15), (143.51, 184.15), (144.78, 184.15))
    J(137.16, 184.15)
    place("CF7", 137.16, 187.96); PW("GND", 137.16, 191.77)
    T("regolazione tensione (V1)", 112, 190)
    # U7 LP2985 ruotato 180 (OUT a sinistra)
    place("U7", 153.67, 181.61, 180)
    path((162.56, 184.15), (165.1, 184.15)); J(165.1, 184.15)
    path((162.56, 179.07), (165.1, 179.07), (165.1, 184.15))
    PW("+5V", 165.1, 179.07)
    NCm(144.78, 179.07)
    w(153.67, 173.99, 153.67, 171.45); PW("GND", 153.67, 171.45, 180)
    T("Rif. 3,6V (B)", 148, 194)

    # ---- blocco 8: alimentazione
    place("J3", 241.3, 170.18)
    T("+5V IN", 239, 165)
    path((234.95, 168.91), (232.41, 168.91), (229.87, 168.91)); PW("GND", 232.41, 168.91); FLG(229.87, 168.91)
    path((234.95, 171.45), (231.14, 171.45), (227.33, 171.45), (224.79, 171.45), (219.71, 171.45))
    J(227.33, 171.45); J(224.79, 171.45); J(231.14, 171.45); FLG(231.14, 171.45)
    w(227.33, 171.45, 227.33, 168.91); PW("+5V", 227.33, 168.91)
    place("CF8", 224.79, 175.26); PW("GND", 224.79, 179.07)
    place("U6", 210.82, 168.91, 180)
    path((201.93, 171.45), (196.85, 171.45), (194.31, 171.45)); J(196.85, 171.45)
    w(196.85, 171.45, 196.85, 168.91); PW("+3V3", 196.85, 168.91)
    place("CF9", 194.31, 175.26); PW("GND", 194.31, 179.07)
    path((213.36, 161.29), (213.36, 158.75), (210.82, 158.75), (208.28, 158.75), (208.28, 161.29))
    PW("GND", 210.82, 158.75, 180); J(210.82, 158.75)
    T("Alimentazione 5V -> 3,3V", 200, 152)

    # ---- blocco 9: buffer d'uscita 3,3 V verso Raspberry Pi (aggiunto)
    place("U9", 276.86, 160.02)
    w(264.16, 160.02, 269.24, 160.02); L("CMP_Q", 264.16, 160.02)
    NCm(269.24, 162.56)
    path((276.86, 153.67), (276.86, 143.51), (289.56, 143.51))
    PW("+3V3", 276.86, 143.51)
    place("CF10", 289.56, 147.32); PW("GND", 289.56, 151.13)
    w(276.86, 166.37, 276.86, 168.91); PW("GND", 276.86, 168.91)
    w(284.48, 160.02, 288.29, 160.02)
    place("R23", 292.1, 160.02, 90)
    w(295.91, 160.02, 300.99, 160.02)
    place("J4", 307.34, 161.29)
    path((300.99, 162.56), (298.45, 162.56), (298.45, 166.37)); PW("GND", 298.45, 166.37)
    T("Buffer uscita 3,3V -> Raspberry Pi (74LVC1G17)", 262, 136)
    T("LEMO", 311, 157)

    T("Riv. Cosmici 2024 - Amplif, alim, soglie - ricostruito da PDF INFN sez. Torino (S. Gallian, rev. A)", 130, 20)


import netdata as _nd
if not getattr(_nd, "VARIANT", None):   # la variante a 3 canali disegna da se'
    build_single()

# =============================== transform & check ===============================
def pin_sheet_pos(symname, x, y, rot, mirror, px, py):
    if mirror == "x" and rot == 0:
        dx, dy = px, py
    elif rot == 0:
        dx, dy = px, -py
    elif rot == 90:
        dx, dy = -py, -px
    elif rot == 180:
        dx, dy = -px, py
    elif rot == 270:
        dx, dy = py, px
    else:
        raise ValueError(rot)
    return (round(x + dx, 3), round(y + dy, 3))

def all_pins():
    """-> list of (ref, pin, (x,y), etype, hidden)"""
    out = []
    for ref, symname, x, y, rot, mirror, _v, _fp in instances:
        s = SYMS[symname]
        for num, (px, py, ang, name, etype, ln, hide) in s.pins.items():
            out.append((ref, num, pin_sheet_pos(symname, x, y, rot, mirror, px, py),
                        etype, hide))
    return out

def check_connectivity():
    pins = [(r, p, pos) for r, p, pos, et, hide in all_pins() if not hide]
    hidden_nc = {(r, p) for r, p, pos, et, hide in all_pins() if hide}
    pts = set()
    for a, b in wires:
        pts.add(a); pts.add(b)
    for _r, _p, pos in pins:
        pts.add(pos)
    for name, x, y in labels:
        pts.add((round(x, 3), round(y, 3)))
    for net, x, y, rot in powers:
        pts.add((round(x, 3), round(y, 3)))

    parent = {p: p for p in pts}
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    def on_seg(p, a, b):
        if a[0] == b[0]:  # vertical
            return p[0] == a[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1])
        if a[1] == b[1]:
            return p[1] == a[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0])
        return False

    for a, b in wires:
        union(a, b)
        for p in pts:
            if p != a and p != b and on_seg(p, a, b):
                union(p, a)

    groups = {}
    for r, p, pos in pins:
        groups.setdefault(find(pos), []).append((r, p))
    netname = {}
    for name, x, y in labels:
        root = find((round(x, 3), round(y, 3)))
        if root in netname and netname[root] != name:
            print(f"CONFLITTO label {name} vs {netname[root]}")
        netname[root] = name
    # power: global merge by name
    powroots = {}
    for net, x, y, rot in powers:
        root = find((round(x, 3), round(y, 3)))
        powroots.setdefault(net, set()).add(root)
    # merge groups by label name / power name
    merged = {}
    def add_to(name, members):
        merged.setdefault(name, set()).update(members)
    lblroots = {}
    for root, name in netname.items():
        lblroots.setdefault(name, set()).add(root)
    used_roots = set()
    for name, roots in list(lblroots.items()):
        mem = set()
        for r in roots:
            mem |= set(groups.get(r, []))
            used_roots.add(r)
        add_to(name, mem)
    for net, roots in powroots.items():
        mem = set()
        for r in roots:
            mem |= set(groups.get(r, []))
            used_roots.add(r)
        add_to(net, mem)
    ncpts0 = {(round(x, 3), round(y, 3)) for x, y in noconn}
    pinpos = {(r, p): pos for r, p, pos in pins}
    anon = 0
    for root, mem in groups.items():
        if root not in used_roots:
            if all(pinpos[m] in ncpts0 for m in mem):
                continue
            add_to(f"ANON{anon}", set(mem)); anon += 1

    # ora confronta con NETS (nomi possono differire per reti locali)
    want = {}
    for net, pl in NETS.items():
        want[net] = set((r, str(p)) for r, p in pl)
    # match per insieme
    got_sets = {n: frozenset(m) for n, m in merged.items() if m}
    want_sets = {n: frozenset(m) for n, m in want.items()}
    ok = True
    unmatched_got = dict(got_sets)
    for wname, wset in want_sets.items():
        hit = None
        for gname, gset in unmatched_got.items():
            if gset == wset:
                hit = gname
                break
        if hit:
            del unmatched_got[hit]
        else:
            ok = False
            print(f"MANCA/DIVERSA rete {wname}: attesa {sorted(wset)}")
            # aiuto: trova gruppi che intersecano
            for gname, gset in got_sets.items():
                inter = gset & wset
                if inter:
                    print(f"   ~ {gname}: {sorted(gset)}")
    for gname, gset in unmatched_got.items():
        ok = False
        print(f"RETE IN PIU' {gname}: {sorted(gset)}")
    # check NC markers
    ncpts = {(round(x, 3), round(y, 3)) for x, y in noconn}
    for r, p, pos, et, hide in all_pins():
        if hide:
            continue
        if not any((r, p) in s for s in want_sets.values()):
            if pos not in ncpts:
                ok = False
                print(f"pin {r}.{p} non in rete e senza no-connect a {pos}")
    print("CONNETTIVITA' SCHEMA:", "OK" if ok else "ERRORI")
    return ok

# =============================== writer ===============================
F = "(effects (font (size 1.27 1.27)))"

def write_sch(fn, paper="A3", title="Riv. Cosmici 2024 - Amplif, alim, soglie"):
    out = []
    out.append('(kicad_sch (version 20211123) (generator eeschema)')
    out.append(f'  (uuid {U()})')
    out.append(f'  (paper "{paper}")')
    out.append(f'  (title_block (title "{title}") '
               '(date "2026-10-09") (rev "A2") (company "INFN sez. Torino / ricostruzione") '
               '(comment 1 "Ricostruito dal PDF originale di S. Gallian (20/06/2024)"))')
    out.append('  (lib_symbols')
    for line in lib_symbols_sexpr().splitlines():
        out.append('    ' + line)
    out.append('  )')
    for x, y in junctions:
        out.append(f'  (junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid {U()}))')
    for x, y in noconn:
        out.append(f'  (no_connect (at {x} {y}) (uuid {U()}))')
    for (a, b) in wires:
        out.append(f'  (wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) '
                   f'(stroke (width 0) (type default) (color 0 0 0 0)) (uuid {U()}))')
    for name, x, y in labels:
        out.append(f'  (label "{name}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) '
                   f'(justify left bottom)) (uuid {U()}))')
    for s, x, y in texts:
        out.append(f'  (text "{s}" (at {x} {y} 0) (effects (font (size 1.7 1.7) bold)) (uuid {U()}))')

    sym_inst = []
    pwr_i = 0
    for net, x, y, rot in powers:
        u = U()
        sname = "PWR_" + net
        out.append(f'  (symbol (lib_id "riv:{sname}") (at {x} {y} {rot}) (unit 1) '
                   f'(in_bom no) (on_board yes) (uuid {u})')
        pwr_i += 1
        ref = f"#PWR0{pwr_i:03d}"
        out.append(f'    (property "Reference" "{ref}" (id 0) (at {x} {y} 0) '
                   f'(effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (property "Value" "{net}" (id 1) (at {x} {y + 3.81} 0) '
                   f'(effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (property "Footprint" "" (id 2) (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (pin "1" (uuid {U()}))')
        out.append('  )')
        sym_inst.append((u, ref, net, ""))
    for x, y in flags:
        u = U()
        pwr_i += 1
        ref = f"#FLG0{pwr_i:03d}"
        out.append(f'  (symbol (lib_id "riv:PWR_FLAG") (at {x} {y} 0) (unit 1) '
                   f'(in_bom no) (on_board yes) (uuid {u})')
        out.append(f'    (property "Reference" "{ref}" (id 0) (at {x} {y} 0) '
                   f'(effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (property "Value" "PWR_FLAG" (id 1) (at {x} {y - 2.54} 0) '
                   f'(effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (property "Footprint" "" (id 2) (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (pin "1" (uuid {U()}))')
        out.append('  )')
        sym_inst.append((u, ref, "PWR_FLAG", ""))

    for ref, symname, x, y, rot, mirror, value, fp in instances:
        u = U()
        mir = " (mirror x)" if mirror == "x" else ""
        out.append(f'  (symbol (lib_id "riv:{symname}") (at {x} {y} {rot}){mir} (unit 1) '
                   f'(in_bom yes) (on_board yes) (uuid {u})')
        out.append(f'    (property "Reference" "{ref}" (id 0) (at {x + 2.54} {y - 2.54} 0) '
                   f'(effects (font (size 1.27 1.27)) (justify left)))')
        out.append(f'    (property "Value" "{value}" (id 1) (at {x + 2.54} {y + 2.54} 0) '
                   f'(effects (font (size 1.27 1.27)) (justify left)))')
        out.append(f'    (property "Footprint" "{fp}" (id 2) (at {x} {y} 0) '
                   f'(effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (property "Datasheet" "" (id 3) (at {x} {y} 0) '
                   f'(effects (font (size 1.27 1.27)) hide))')
        for num in SYMS[symname].pins:
            out.append(f'    (pin "{num}" (uuid {U()}))')
        out.append('  )')
        sym_inst.append((u, ref, value, fp))

    out.append('  (sheet_instances (path "/" (page "1")))')
    out.append('  (symbol_instances')
    for u, ref, value, fp in sym_inst:
        out.append(f'    (path "/{u}" (reference "{ref}") (unit 1) (value "{value}") '
                   f'(footprint "{fp}"))')
    out.append('  )')
    out.append(')')
    with open(fn, "w") as f:
        f.write("\n".join(out) + "\n")
    print("scritto", fn, f"({len(instances)} simboli, {len(wires)} fili)")

if __name__ == "__main__":
    from netdata import check
    check()
    ok = check_connectivity()
    write_sch("riv_cosmici/riv_cosmici.kicad_sch")
    if not ok:
        raise SystemExit(1)
