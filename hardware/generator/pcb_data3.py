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
            elif ref == "U2":          # 555 ruotato: uscita (pin 3) verso R21/LED,
                out[r] = (x, y + dy, 180)  # pin 5-6-7 verso R20/C21/CF6
            else:
                out[r] = (x, y + dy, rot)
    # test point di canale: colonna lungo il bordo destro, sopra il LEMO
    # (lascia libero il corridoio in alto a destra per le reti verso la coincidenza)
    for n in N.CHANNELS:
        dy = (n - 1) * STRIP
        for i in range(1, 7):
            out[f"TP{n}{i:02d}"] = (97.0, 22.0 + (i - 1) * 4.0 + dy, 0)
    # coincidenza: angolo in basso a destra della striscia 2 (dove c'e' U6 nella 1)
    dy = STRIP
    out.update({
        "U10":  (84.0, 65.5 + dy, 0),
        "CF11": (86.5, 60.5 + dy, 90),
        "R30":  (89.5, 64.0 + dy, 0),
        "J5":   (96.0, 66.0 + dy, 0),
        "R31":  (78.0, 65.5 + dy, 90),
        "R32":  (80.0, 65.5 + dy, 90),
        "R33":  (81.5, 60.5 + dy, 90),
        "JP1":  (77.0, 71.0 + dy, 0),
        "JP2":  (82.5, 71.0 + dy, 0),
        "JP3":  (88.0, 71.0 + dy, 0),
    })
    # test point comuni: accanto al circuito che misurano
    out.update({
        "TP1": (49.0, 47.0, 0),               # VOUT40, vicino a C2/C3
        "TP2": (92.5, 71.0, 0),               # +5V, vicino a J3
        "TP3": (79.0, 71.0, 0),               # +3V3, vicino a U6
        "TP4": (72.5, 47.0, 0),               # +3V6, vicino a U5
        "TP5": (94.0, 127.5, 0),              # AND_OUT, vicino al LEMO J5
        "TP6": (84.5, 72.5, 0),               # GND
    })
    return out


PLACEMENT = placement()

# reti ad alta tensione e larghezze pista per i nomi con suffisso di canale
HV_EXTRA = set()
WIDTH_EXTRA = {}
for n in N.CHANNELS:
    HV_EXTRA |= {f"VREG38{n}", f"BIAS{n}"}
    WIDTH_EXTRA.update({f"VREG38{n}": 0.4, f"BIAS{n}": 0.4})
