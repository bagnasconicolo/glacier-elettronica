# -*- coding: utf-8 -*-
"""Piazzamento PCB e utilita' comuni. Board 80x55 mm, origine (20,20)."""
import math
from netdata import COMPONENTS, NETS
from footprints import FPS

FP_OF = {
    "R0805": "R_0805", "C0805": "C_0805", "C1206": "C_1206", "C1210": "C_1210",
    "L_PWR": "L_PWR_5050", "DO35": "D_DO35", "LED0805": "LED_0805",
    "SOT23": "SOT23", "SOT23-5": "SOT23-5", "SOT23-6": "SOT23-6",
    "SO8": "SOIC8", "SOT223": "SOT223", "3296W": "TRIM_3296W", "HDR2": "HDR1x02",
    "LEMO00": "LEMO_EPL00", "TP": "TP_THT",
    "SO14": "SOIC14", "HDR3": "HDR1x03", "MH3": "MH_M3", "KK2": "MOLEX_KK_2",
}

BOARD = (20.0, 20.0, 100.0, 75.0)  # x1 y1 x2 y2

# ref: (x, y, rot)  - rot CCW gradi
PLACEMENT = {
    # ingresso SiPM + bias (alto sx)
    "J1":  (24.0, 29.0, 270),
    "R10": (30.0, 33.5, 90),
    "C7":  (33.5, 29.0, 0),
    "R9":  (37.0, 33.5, 90),
    "Q1":  (42.0, 30.5, 0),
    "R11": (42.0, 24.5, 0),
    "R12": (48.0, 24.5, 90),
    "Q2":  (52.5, 30.0, 180),
    "R13": (52.5, 24.5, 90),
    "R14": (56.5, 33.5, 90),
    "C11": (60.5, 29.0, 0),
    "R15": (64.0, 33.5, 90),
    # rail 3V3 alto
    "CF1": (44.5, 21.5, 0),
    # comparatore
    "U3":  (71.5, 30.0, 0),
    "CF2": (71.5, 24.0, 0),
    "R16": (66.5, 36.5, 90),
    "C9":  (71.5, 36.5, 0),
    "R17": (66.0, 41.0, 0),
    # driver TTL
    "U4":  (83.0, 27.5, 90),
    "CF3": (83.0, 22.0, 0),
    "J2":  (96.5, 26.0, 270),
    # 555 + LED
    "U2":  (84.0, 40.0, 0),
    "R20": (78.0, 35.5, 0),
    "C21": (78.0, 44.0, 90),
    "CF5": (89.0, 35.0, 0),
    "CF6": (78.5, 40.0, 90),
    "R21": (92.5, 40.0, 90),
    "D3":  (92.5, 46.0, 90),
    # soglia
    "V2":  (63.0, 51.0, 0),
    "R18": (56.0, 46.0, 0),
    "R19": (69.0, 46.5, 0),
    "U5":  (75.0, 51.0, 0),
    "CF4": (80.6, 47.8, 90),
    # boost 40,2V (basso sx)
    "L1":  (27.0, 47.5, 90),
    "U1":  (34.5, 44.5, 0),
    "C22": (24.0, 41.0, 90),
    "C2":  (40.0, 44.5, 90),
    "C3":  (44.0, 44.5, 90),
    "R3":  (34.0, 51.0, 0),
    "C1":  (34.0, 54.0, 0),
    "R22": (24.0, 58.0, 0),
    "R2":  (24.0, 61.0, 0),
    "R1":  (24.0, 64.0, 0),
    # regolatore 38,4V
    "U8":  (47.0, 60.0, 0),
    "R4":  (41.0, 56.5, 90),
    "R5":  (47.0, 55.0, 0),
    "R6":  (41.5, 64.5, 90),
    "C4":  (44.5, 68.0, 0),
    "V1":  (53.0, 69.5, 0),
    "R7":  (46.0, 71.5, 0),
    "D1":  (60.5, 64.0, 0),
    "U7":  (67.0, 61.0, 0),
    "CF7": (61.5, 57.5, 0),
    "R8":  (28.0, 37.0, 0),
    "C6":  (34.5, 37.0, 0),
    # alimentazione (basso dx)
    "J3":  (96.5, 65.0, 270),
    "CF8": (92.3, 60.8, 0),
    "U6":  (86.0, 65.5, 0),
    "CF9": (80.0, 61.5, 0),
    # buffer d'uscita 3,3 V verso Raspberry Pi (dx, sotto il LED)
    "U9":   (88.0, 52.5, 0),
    "CF10": (88.0, 48.5, 0),
    "R23":  (92.5, 52.5, 0),
    "J4":   (97.0, 54.0, 270),
}

NETCLASS_W = {  # larghezza pista
    "+5V": 0.5, "+3V3": 0.5, "GND": 0.5,
    "SW": 0.5, "VOUT40": 0.4, "VREG38": 0.4, "BIAS": 0.4,
}
def track_w(net):
    return NETCLASS_W.get(net, 0.3)

CLEARANCE = 0.22
HV_NETS = {"VOUT40", "VREG38", "BIAS", "SW"}
HV_CLEAR = 0.4          # clearance extra per reti 40V verso altre reti

def pad_net():
    """(ref,pin) -> net"""
    m = {}
    for net, pins in NETS.items():
        for ref, p in pins:
            m[(ref, str(p))] = net
    return m

def rot_delta(dx, dy, rot):
    a = math.radians(rot)
    return (dx * math.cos(a) + dy * math.sin(a),
            -dx * math.sin(a) + dy * math.cos(a))

def abs_pads():
    """list of dict: ref,pin,net,x,y,w,h,kind,drill,rot"""
    pn = pad_net()
    out = []
    for ref, (x, y, rot) in PLACEMENT.items():
        kind0, value, fpk, _ = COMPONENTS[ref]
        fp = FPS[FP_OF[fpk]]
        for num, (px, py, w, h, k, drill) in fp.pads.items():
            dx, dy = rot_delta(px, py, rot)
            out.append(dict(ref=ref, pin=num, net=pn.get((ref, num.split("#")[0])),
                            x=round(x + dx, 4), y=round(y + dy, 4),
                            w=w, h=h, kind=k, drill=drill, rot=rot % 360))
    return out

def pad_rect(p, extra=0.0):
    """rettangolo (shapely) del pad, tenendo conto della rotazione."""
    from shapely.geometry import box
    import shapely.affinity as aff
    b = box(p["x"] - p["w"] / 2 - extra, p["y"] - p["h"] / 2 - extra,
            p["x"] + p["w"] / 2 + extra, p["y"] + p["h"] / 2 + extra)
    if p["rot"] % 180 != 0:
        b = aff.rotate(b, -p["rot"], origin=(p["x"], p["y"]))
    return b

def pad_shape(p, extra=0.0):
    """forma REALE del rame del pad (cerchio per i THT tondi, rettangolo per gli altri),
    come nei Gerber e in KiCad. pad_rect resta l'ingombro (prudente) per gli ostacoli."""
    if p["kind"] == "tht" and abs(p["w"] - p["h"]) < 1e-6:
        from shapely.geometry import Point
        return Point(p["x"], p["y"]).buffer(p["w"] / 2 + extra, 32)
    return pad_rect(p, extra)

if __name__ == "__main__":
    pads = abs_pads()
    print(len(pads), "pad")
    missing = [p for p in pads if p["net"] is None and (p["ref"], p["pin"]) not in
               {("U8","1"),("U8","5"),("U8","8"),("U5","4"),("U7","4"),("U9","1")}]
    print("pad senza rete:", [(p['ref'], p['pin']) for p in missing])
    refs = set(PLACEMENT) ^ set(COMPONENTS)
    print("piazzamento mancante/di troppo:", refs)
