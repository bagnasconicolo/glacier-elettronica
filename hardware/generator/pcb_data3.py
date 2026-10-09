# -*- coding: utf-8 -*-
"""Piazzamento PCB della VARIANTE A 3 CANALI.

Scheda 80 x 165 mm = tre "strisce" da 55 mm, ognuna con lo stesso piazzamento
della scheda a 1 canale (pcb_data.PLACEMENT) spostato in basso di 55 mm per
canale. Le parti comuni restano dove sono nella striscia 1; negli spazi lasciati
liberi nelle strisce 2 e 3 vanno coincidenza e test point.
"""
from pcb_data import PLACEMENT as P1
import netdata3 as N

STRIP = 55.0
BOARD = (20.0, 20.0, 100.0, 20.0 + 3 * STRIP)


def placement():
    out = {}
    for ref, (x, y, rot) in P1.items():
        if ref in N.DROP:
            continue
        if ref in N.SHARED:
            out[ref] = (x, y, rot)
            continue
        for n in N.CHANNELS:
            dy = (n - 1) * STRIP
            r = N.chref(ref, n)
            if ref == "J4":            # LEMO al bordo destro, frontale verso l'esterno
                out[r] = (96.0, 55.0 + dy, 0)
            elif ref == "R23":         # 33 ohm accanto al LEMO
                out[r] = (89.8, 57.6 + dy, 90)
            else:
                out[r] = (x, y + dy, rot)
    # test point di canale: angolo in alto a destra (dove c'era il driver TTL)
    for n in N.CHANNELS:
        dy = (n - 1) * STRIP
        pos = [(79.0, 22.5), (83.0, 22.5), (87.0, 22.5), (91.0, 22.5), (95.0, 22.5), (95.0, 27.0)]
        for i, (x, y) in enumerate(pos, 1):
            out[f"TP{n}{i:02d}"] = (x, y + dy, 0)
    # coincidenza: angolo in basso a destra della striscia 2 (dove c'e' U6 nella 1)
    dy = STRIP
    out.update({
        "U10":  (84.0, 64.5 + dy, 0),
        "CF11": (84.0, 60.5 + dy, 0),
        "R30":  (90.0, 64.5 + dy, 90),
        "J5":   (96.0, 66.0 + dy, 0),
        "JP1":  (77.0, 71.0 + dy, 0),
        "JP2":  (82.5, 71.0 + dy, 0),
        "JP3":  (88.0, 71.0 + dy, 0),
        "R31":  (78.0, 66.0 + dy, 90),
        "R32":  (80.5, 61.5 + dy, 90),
        "R33":  (87.5, 62.5 + dy, 90),
    })
    # test point comuni: angolo in basso a sinistra della striscia 3 (dove c'e' il boost nella 1)
    dy = 2 * STRIP
    for i in range(1, 7):
        x = 25.0 + ((i - 1) % 3) * 5.0
        y = 50.0 + ((i - 1) // 3) * 5.0 + dy
        out[f"TP{i}"] = (x, y, 0)
    return out


PLACEMENT = placement()

# reti ad alta tensione e larghezze pista per i nomi con suffisso di canale
HV_EXTRA = set()
WIDTH_EXTRA = {}
for n in N.CHANNELS:
    HV_EXTRA |= {f"VREG38{n}", f"BIAS{n}"}
    WIDTH_EXTRA.update({f"VREG38{n}": 0.4, f"BIAS{n}": 0.4})
