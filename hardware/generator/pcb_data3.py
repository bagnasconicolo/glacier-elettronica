# -*- coding: utf-8 -*-
"""Piazzamento PCB della VARIANTE A 3 CANALI - versione didattica.

Scheda 95 x 205 mm organizzata a blocchi, leggibile dall'alto in basso:

  fascia ALIMENTAZIONE   ingresso 5 V -> 3,3 V -> alta tensione 41 V -> riferimenti 3,6 V
  CANALE 1               riga alta  = percorso del segnale, da sinistra a destra:
  CANALE 2                  1 SiPM -> 2 amplificatore -> 3 comparatore -> 4 uscita LEMO
  CANALE 3               riga bassa = circuiti di supporto sotto il blocco che servono:
                            A alimentazione SiPM (~38 V) | B soglia | C LED (555)
  fascia COINCIDENZA     jumper -> AND a 3 -> LEMO

Ogni canale ha lo stesso piazzamento (spostato di STRIP mm) e i test point stanno
accanto al nodo che misurano (pochi mm di pista: niente antenne sul segnale).
I blocchi (BLOCKS) e le scritte (NOTES) servono a silk3.py per la serigrafia.
"""
import netdata3 as N

X0, Y0 = 20.0, 20.0
W = 95.0
PWR_H = 27.0              # fascia alimentazione
STRIP = 52.0              # altezza di un canale
COINC_H = 22.0            # fascia coincidenza
BOARD = (X0, Y0, X0 + W, Y0 + PWR_H + 3 * STRIP + COINC_H)


def ch_y(n):
    """y (assoluta) del bordo alto della striscia del canale n"""
    return Y0 + PWR_H + (n - 1) * STRIP


COINC_Y = Y0 + PWR_H + 3 * STRIP

# ---------------------------------------------------------------- canale
# coordinate locali (origine = angolo in alto a sinistra della striscia)
# riga alta (y 2..25): segnale; riga bassa (y 28..47): supporto (poi row_y)
CH = {
    # 1 SiPM: connettore, resistenza di carico, filtro del bias
    "J1":   (7.0, 11.5, 270),       # 1 = segnale, 2 = bias
    "R10":  (11.5, 12.5, 270),
    "R8":   (8.0, 19.0, 90),
    "C6":   (12.0, 19.0, 90),
    # 2 amplificatore a due transistor
    "C7":   (16.5, 11.5, 0),
    "R9":   (20.0, 16.0, 90),
    "Q1":   (25.0, 13.0, 0),
    "R11":  (25.0, 7.0, 0),
    "R12":  (31.0, 7.0, 90),
    "Q2":   (35.5, 12.5, 180),
    "R13":  (35.5, 7.0, 90),
    "R14":  (39.5, 16.0, 90),
    "CF1":  (27.5, 4.0, 0),
    # 3 comparatore
    "C11":  (43.5, 11.5, 0),
    "R15":  (47.0, 16.0, 90),
    "U3":   (54.5, 12.5, 0),
    "CF2":  (54.5, 6.5, 0),
    "R16":  (49.5, 19.0, 90),
    "C9":   (54.5, 19.0, 0),
    "R17":  (49.0, 23.5, 0),
    # 4 uscita: buffer 3,3 V + LEMO sul bordo destro
    "U9":   (73.0, 10.0, 0),
    "CF10": (73.0, 5.5, 0),
    "R23":  (79.0, 8.7, 0),
    "J4":   (91.0, 10.0, 0),
    # A alimentazione del SiPM (~38 V regolabile, compensata in temperatura)
    "U8":   (13.0, 34.0, 0),
    "R4":   (7.0, 30.5, 90),
    "R5":   (13.0, 29.0, 0),
    "R6":   (7.5, 38.5, 90),
    "C4":   (10.5, 42.0, 0),
    "V1":   (19.0, 43.5, 0),
    "R7":   (12.0, 45.5, 0),
    "D1":   (26.5, 38.0, 0),
    # monitor: partitore 1M/43k + 100n sull'uscita del regolatore (VREG38), verso l'ADC
    "R50":  (21.0, 29.0, 0),
    "R51":  (25.5, 31.5, 90),
    "C50":  (29.0, 31.5, 90),
    # B soglia del comparatore
    "V2":   (46.0, 35.5, 0),
    "R18":  (39.0, 30.5, 0),
    "R19":  (52.0, 31.0, 0),
    # C monostabile 555 + LED
    "U2":   (71.0, 34.0, 180),
    "R20":  (65.0, 29.5, 0),
    "C21":  (65.0, 38.0, 90),
    "CF5":  (76.0, 29.0, 0),
    "CF6":  (65.5, 34.0, 90),
    "R21":  (79.5, 34.0, 90),
    "D3":   (79.5, 40.0, 90),
}
# test point del canale, accanto al nodo misurato
CH_TP = {
    "TP01": (11.5, 7.5),     # SIG_IN: anodo SiPM (accanto a J1/R10)
    "TP06": (11.5, 3.5),     # GND per la molla della sonda
    "TP05": (10.0, 23.0),    # BIAS (accanto a R8/C6)
    "TP02": (48.5, 7.5),     # CMP_IN: ingresso del comparatore (U3.1)
    "TP03": (44.5, 21.5),    # TH: soglia (accanto a R17)
    "TP04": (62.0, 15.0),    # CMP_Q: uscita del comparatore
}

# ---------------------------------------------------------------- comuni
PWR = {
    # ingresso 5 V + regolatore 3,3 V
    "J3":  (4.0, 12.0, 270),        # 1 = GND, 2 = +5V
    "U6":  (17.0, 12.0, 0),
    "CF8": (14.0, 20.0, 0),
    "CF9": (20.0, 20.0, 0),
    # alta tensione: survoltore LT3461 5 V -> 41,7 V
    "C22": (29.0, 4.0, 90),
    "L1":  (31.0, 11.0, 90),
    "U1":  (39.0, 7.0, 0),
    "C2":  (44.5, 7.0, 90),
    "C3":  (48.5, 7.0, 90),
    "R3":  (39.0, 13.0, 0),
    "C1":  (39.0, 16.5, 0),
    "R22": (43.5, 17.0, 90),
    "R2":  (46.5, 17.0, 90),
    "R1":  (49.5, 17.0, 90),
    # riferimenti 3,6 V: U5 per le soglie, U7 per la compensazione del bias
    "U5":  (62.0, 8.0, 0),
    "CF4": (67.0, 8.0, 90),
    "U7":  (62.0, 18.0, 0),
    "CF7": (67.0, 18.0, 90),
    # partitore del monitor sull'alta tensione
    "R40": (57.0, 5.0, 90),
    "R41": (57.0, 10.5, 90),
    "C40": (57.0, 15.5, 90),
    # monitor tensioni: ADC MCP3424 + connettore I2C verso il Raspberry Pi
    "U11":  (79.5, 11.0, 0),
    "CF12": (77.0, 4.0, 0),
    "R42":  (87.3, 10.0, 0),
    "R43":  (87.3, 13.0, 0),
    "J6":   (93.0, 8.0, 270),
}
PWR_TP = {
    "TP2": (9.0, 19.5),      # +5V
    "TP6": (9.0, 23.5),      # GND
    "TP3": (24.5, 20.0),     # +3V3
    "TP1": (53.0, 7.0),      # VOUT40
    "TP4": (71.0, 8.0),      # +3V6
}
COINC = {
    # i jumper stanno sotto il corridoio delle uscite (vedi CORRIDOR); pull-up a
    # sinistra di ogni jumper; le tre piste verso U10 corrono parallele senza incroci
    "JP1":  (64.0, 5.5, 270),
    "JP2":  (70.0, 5.5, 270),
    "JP3":  (76.0, 5.5, 270),
    "R31":  (61.2, 9.0, 270),
    "R32":  (67.2, 9.0, 270),
    "R33":  (73.2, 9.0, 270),
    "U10":  (82.0, 12.5, 0),
    "CF11": (82.0, 7.5, 0),
    "R30":  (85.5, 13.5, 270),
    "J5":   (91.0, 12.0, 0),
    "TP5":  (89.5, 19.5, 0),
}


def row_y(y):
    """spazio per i titoli dei blocchi: riga alta giu' di 2,5 mm, riga bassa di 4"""
    return y + (2.5 if y < 26 else 4.0)


def placement():
    out = {}
    for ref, (x, y, r) in PWR.items():
        out[ref] = (X0 + x, Y0 + y, r)
    for ref, (x, y) in PWR_TP.items():
        out[ref] = (X0 + x, Y0 + y, 0)
    for n in N.CHANNELS:
        yy = ch_y(n)
        for ref, (x, y, r) in CH.items():
            out[N.chref(ref, n)] = (X0 + x, yy + row_y(y), r)
        for tp, (x, y) in CH_TP.items():
            out[f"TP{n}{tp[2:]}"] = (X0 + x, yy + row_y(y), 0)
    for ref, (x, y, r) in COINC.items():
        out[ref] = (X0 + x, COINC_Y + y, r)
    missing = set(N.COMPONENTS) ^ set(out)
    assert not missing, f"piazzamento incompleto: {missing}"
    return out


PLACEMENT = placement()

# ---------------------------------------------------------------- corridoio
# Le uscite dei buffer (BUF_Y1..3) scendono alla coincidenza in un corridoio
# riservato tra i blocchi e i LEMO (x locale 82,5 / 84 / 85,5), cosi' non
# attraversano i circuiti dei canali sottostanti. Ogni canale entra nel corridoio
# passando sotto le linee dei canali superiori (tratto su B.Cu), e in basso le
# linee piegano a sinistra in ordine verso JP1, JP2, JP3: nessun incrocio.
CORRIDOR_X = {1: 82.5, 2: 84.0, 3: 85.5}
JOG_Y = 15.5                       # y locale del tratto orizzontale di ingresso


def corridor_tracks():
    tracks, vias = [], []
    for n in N.CHANNELS:
        yy = ch_y(n)
        rx, ry, _ = PLACEMENT[N.chref("R23", n)]
        px = rx - 0.95                      # pad 1 di R23 (rete BUF_Yn)
        xc = X0 + CORRIDOR_X[n]
        yj = yy + JOG_Y
        net = f"BUF_Y{n}"
        jx, jy, _ = PLACEMENT[f"JP{n}"]     # pin 1 del jumper (in alto)
        yb = COINC_Y + n * 1.0              # piega verso il jumper
        if n == 1:
            tracks.append(dict(net=net, layer="F.Cu", w=0.3, fixed=True,
                               pts=[(px, ry), (px, yj), (xc, yj), (xc, yb), (jx, yb), (jx, jy)]))
        else:
            tracks.append(dict(net=net, layer="F.Cu", w=0.3, fixed=True, pts=[(px, ry), (px, yj)]))
            tracks.append(dict(net=net, layer="B.Cu", w=0.3, fixed=True, pts=[(px, yj), (xc, yj)]))
            tracks.append(dict(net=net, layer="F.Cu", w=0.3, fixed=True,
                               pts=[(xc, yj), (xc, yb), (jx, yb), (jx, jy)]))
            vias += [dict(net=net, x=px, y=yj, fixed=True), dict(net=net, x=xc, y=yj, fixed=True)]
    return tracks, vias


# reti ad alta tensione e larghezze pista per i nomi con suffisso di canale
HV_EXTRA = set()
WIDTH_EXTRA = {}
for n in N.CHANNELS:
    HV_EXTRA |= {f"VREG38{n}", f"BIAS{n}"}
    WIDTH_EXTRA.update({f"VREG38{n}": 0.4, f"BIAS{n}": 0.4})

# ---------------------------------------------------------------- serigrafia
# blocchi: (titolo, sottotitolo, riferimenti o None, rettangolo locale o None)
CH_BLOCKS = [
    ("1 SiPM", "J1: 1=segnale 2=bias", ["J1", "R10", "R8", "C6", "TP01", "TP05", "TP06"]),
    ("2 AMPLIFICATORE", "2 transistor", ["C7", "R9", "Q1", "R11", "R12", "Q2", "R13", "R14", "CF1"]),
    ("3 COMPARATORE", "segnale > soglia?", ["C11", "R15", "U3", "CF2", "R16", "C9", "R17", "TP02", "TP03", "TP04"]),
    ("4 USCITA", "buffer 3,3V -> LEMO", ["U9", "CF10", "R23"]),
    ("A ALIMENTAZIONE SiPM ~38V", "V1 regola la tensione", ["U8", "R4", "R5", "R6", "C4", "V1", "R7", "D1",
                                                            "R50", "R51", "C50"]),
    ("B SOGLIA", "V2 regola la soglia", ["V2", "R18", "R19"]),
    ("C LED", "lampeggia a ogni evento", ["U2", "R20", "C21", "CF5", "CF6", "R21", "D3"]),
]
PWR_BLOCKS = [
    ("5V IN", None, ["J3", "TP2", "TP6"]),
    ("3,3V", None, ["U6", "CF8", "CF9", "TP3"]),
    ("ALTA TENSIONE 41V", None, ["C22", "L1", "U1", "C2", "C3", "R3", "C1", "R22", "R2", "R1", "TP1",
                                  "R40", "R41", "C40"]),
    ("RIFERIMENTI", "3,6 V stabili", ["U5", "CF4", "U7", "CF7", "TP4"]),
    ("MONITOR", "J6 al Pi: 1 GND 2 SDA 3 SCL", ["U11", "CF12", "R42", "R43", "J6"]),
]
COINC_BLOCKS = [
    ("COINCIDENZA (AND)", "jumper chiuso = canale incluso",
     ["JP1", "JP2", "JP3", "R31", "R32", "R33", "U10", "CF11", "R30", "TP5"]),
]
# etichette dei test point (testo accanto al foro)
TP_LABEL = {"TP01": "SiPM", "TP06": "GND", "TP05": "BIAS", "TP02": "IN",
            "TP03": "SOGLIA", "TP04": "OUT",
            "TP1": "41V", "TP2": "5V", "TP3": "3,3V", "TP4": "3,6V", "TP5": "AND", "TP6": "GND"}
