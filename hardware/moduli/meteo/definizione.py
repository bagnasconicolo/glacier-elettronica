# -*- coding: utf-8 -*-
"""MODULO METEO: temperatura, umidita' e pressione su I2C, con due prese Qwiic.

Si collega a una porta dell'hub I2C della scatolina di acquisizione (o a qualunque
scheda con Qwiic/STEMMA QT: Raspberry Pi, Pico, Arduino, ESP32), anche in catena.

  U1  Sensirion SHT45-AD1B   temperatura +-0,1 C, umidita' +-1 %UR   I2C 0x44
      (SHT41-AD1B o SHT40-AD1B montabili al suo posto: stessa impronta e indirizzo)
  U2  ST LPS22HH             pressione 260-1260 hPa, +-0,5 hPa assoluti,
                             0,65 Pa di rumore (rms)                 I2C 0x5D (0x5C con JP2)
  J1, J2  JST SH 4 poli (Qwiic): 1 GND, 2 3,3 V, 3 SDA, 4 SCL (entrata e uscita)
  R1, R2  pull-up 4,7k, inseriti solo chiudendo JP1 (servono se il modulo e' da solo:
          le porte della scatolina hanno gia' i loro)
  JP2     indirizzo dell'LPS22HH: di fabbrica 1-2 (SA0 = 3,3 V, 0x5D); tagliando la pista
          e saldando 2-3, 0x5C (per due moduli sullo stesso bus)

Il sensore di umidita' sta su un'isola separata da due fessure, senza piano di rame
sotto (linee guida Sensirion: misura l'aria, non la scheda); niente vernice protettiva
sul sensore. Pinout dei due sensori dalle librerie ufficiali KiCad (Sensor_Humidity:SHT4x,
Sensor_Pressure:LPS22HH).
"""
NOME = "modulo_meteo"
TITOLO = "Modulo meteo (SHT45 + LPS22HH, Qwiic)"
W, H = 36.0, 22.0

COMPONENTS = {
    "U1":  ("SHT4X", "SHT45-AD1B", "DFN4_SHT4X", {"note": "temperatura e umidita', 0x44"}),
    "U2":  ("LPS22HH", "LPS22HHTR", "HLGA10", {"note": "pressione, 0x5D (0x5C)"}),
    "C1":  ("C", "100n", "C0603", {"note": "disaccoppiamento U1"}),
    "C2":  ("C", "100n", "C0603", {"note": "disaccoppiamento U2 VDD"}),
    "C3":  ("C", "100n", "C0603", {"note": "disaccoppiamento U2 VDD_IO"}),
    "R1":  ("R", "4k7", "R0603", {"note": "pull-up SDA (con JP1 chiuso)"}),
    "R2":  ("R", "4k7", "R0603", {"note": "pull-up SCL (con JP1 chiuso)"}),
    "JP1": ("SJ2", "PULL-UP", "SJ2", {"note": "aperto di fabbrica: chiudere se il modulo e' da solo"}),
    "JP2": ("SJ3", "ADDR", "SJ3", {"note": "1-2 = 0x5D (di fabbrica), 2-3 = 0x5C"}),
    "J1":  ("QWIIC", "Qwiic", "JSTSH4", {"note": "JST SM04B-SRSS-TB"}),
    "J2":  ("QWIIC", "Qwiic", "JSTSH4", {"note": "JST SM04B-SRSS-TB"}),
    "H1":  ("MH", "M3", "MH3", {}),
    "H2":  ("MH", "M3", "MH3", {}),
    "H3":  ("MH", "M3", "MH3", {}),
}
NETS = {
    "GND":  [("J1", "1"), ("J2", "1"), ("U1", "4"), ("U2", "3"), ("U2", "8"), ("U2", "9"),
             ("C1", "2"), ("C2", "2"), ("C3", "2"), ("JP2", "3")],
    "+3V3": [("J1", "2"), ("J2", "2"), ("U1", "3"), ("U2", "10"), ("U2", "1"), ("U2", "6"),
             ("C1", "1"), ("C2", "1"), ("C3", "1"), ("JP1", "2"), ("JP2", "1")],
    "SDA":  [("J1", "3"), ("J2", "3"), ("U1", "1"), ("U2", "4"), ("R1", "1")],
    "SCL":  [("J1", "4"), ("J2", "4"), ("U1", "2"), ("U2", "2"), ("R2", "1")],
    "PU":   [("R1", "2"), ("R2", "2"), ("JP1", "1")],
    "SA0":  [("U2", "5"), ("JP2", "2")],
}
PIN_COUNT = {"SHT4X": 4, "LPS22HH": 10, "C": 2, "R": 2, "SJ2": 2, "SJ3": 3, "QWIIC": 4, "MH": 0}
NC_PINS = {("U2", "7")}                       # INT_DRDY non usato (si legge a interrogazione)


def check():
    used = {}
    for net, pins in NETS.items():
        for r, p in pins:
            assert r in COMPONENTS, r
            assert (r, p) not in used, (r, p)
            used[(r, p)] = net
    miss = [(r, p) for r, (k, *_x) in COMPONENTS.items() for p in map(str, range(1, PIN_COUNT[k] + 1))
            if (r, p) not in used and (r, p) not in NC_PINS]
    assert not miss, miss
    print(f"netlist {NOME}: {len(COMPONENTS)} componenti, {len(NETS)} reti, {len(used)} pin")


# ---------------------------------------------------------------- PCB
FP = {"DFN4_SHT4X": "Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_KeepoutCentro",   # vedi librerie/crea_impronte.py
      "HLGA10": "ST_HLGA-10_2x2mm_P0.5mm_LayoutBorder3x2y",
      "C0603": "C_0603_1608Metric", "R0603": "R_0603_1608Metric",
      "SJ2": "SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
      "SJ3": "SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm",
      "JSTSH4": "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
      "MH3": "MountingHole_3.2mm_M3"}
CONTORNO = [(0, 0), (W, 0), (W, H), (0, H)]
# isola del sensore di umidita' (x 17..26, y 1..8,5): due fessure a L larghe 1 mm,
# ponte di 5 mm in basso al centro per le quattro piste
FESSURE = [[(16.0, 1.0), (17.0, 1.0), (17.0, 8.5), (19.0, 8.5), (19.0, 9.5), (16.0, 9.5)],
           [(24.0, 8.5), (26.0, 8.5), (26.0, 1.0), (27.0, 1.0), (27.0, 9.5), (24.0, 9.5)]]
SENZA_RAME = [[(17.0, 1.0), (26.0, 1.0), (26.0, 10.0), (17.0, 10.0)]]  # niente piano sull'isola e sul ponte
PLACEMENT = {
    "J1":  (3.6, 11.0, 270),        # bocca verso il bordo sinistro (a 1 mm dal bordo)
    "J2":  (32.4, 11.0, 90),        # bocca verso il bordo destro
    "U1":  (21.0, 3.8, 0),
    "C1":  (22.475, 6.2, 0),       # sotto i pad VDD/VSS di U1
    "U2":  (14.0, 15.0, 0),
    "C2":  (11.6, 13.2, 90),
    "C3":  (11.6, 16.6, 90),
    "JP2": (17.2, 18.0, 0),
    "R1":  (8.4, 6.2, 90),
    "R2":  (10.4, 6.2, 90),
    "JP1": (13.2, 6.2, 90),
    "H1":  (3.5, 3.5, 0),
    "H2":  (3.5, 18.5, 0),
    "H3":  (32.5, 18.5, 0),
}
RETI_POTENZA = ("+3V3", "GND")
# isola del sensore: quattro piste tracciate a mano fino a sotto il ponte (Freerouting non
# trova la strada nel ponte stretto). Pad di U1: 1 SDA (20,3; 3,4), 2 SCL (20,3; 4,2),
# 3 VDD (21,7; 4,2), 4 VSS (21,7; 3,4); C1: 1 (21,7; 6,2), 2 (23,25; 6,2)
PISTE_FISSE = [
    ("SDA", 0.25, [(20.3, 3.4), (19.7, 3.4), (19.7, 10.6)]),
    ("SCL", 0.25, [(20.3, 4.2), (20.3, 4.6), (20.5, 4.8), (20.5, 10.6)]),
    ("+3V3", 0.3, [(21.7, 4.2), (21.7, 10.6)]),
    ("GND", 0.3, [(21.7, 3.4), (23.25, 3.4), (23.25, 10.6)]),
]
# i pad d'angolo dell'impronta ST (HLGA-10) distano 0,129 mm: per U2 vale il disegno del
# costruttore (JLCPCB accetta 0,127 mm), per il resto della scheda 0,15 mm
CLEARANCE_LOCALE = {"U2": 0.127}
TRACK_POTENZA = 0.3
RIF_VISIBILI = {"U1": False, "U2": False, "H1": False, "H2": False, "H3": False, "JP1": False}   # sensori: col nome; JP1 scritto sotto
RIF_POS = {"C1": (0, 1.3), "R1": (0, -2.0), "R2": (0, -2.0), "JP1": (-1.8, 0, 90),
           "C2": (-1.6, 0, 90), "C3": (-1.6, 0, 90), "JP2": (-3.6, 0), "J1": (0, -5.0), "J2": (0, -5.0)}
SCRITTE = [
    ("METEO", 10.6, 2.0, {"size": 1.4, "bold": True}),
    ("U1 SHT45", 21.0, 2.0, {"size": 0.8}),
    ("U2 LPS22HH", 15.6, 15.0, {"size": 0.8, "just": "left"}),
    ("JP1", 13.2, 8.45, {"size": 0.8}),
    ("PULL-UP", 13.2, 9.6, {"size": 0.8}),
    ("5D", 15.9, 20.7, {"size": 0.8}),
    ("5C", 18.5, 20.7, {"size": 0.8}),
    ("Qwiic", 3.6, 15.9, {"size": 0.8}),
    ("Qwiic", 32.4, 15.9, {"size": 0.8}),
    ("Qwiic: 1 GND 2 3V3 3 SDA 4 SCL", 16.0, 11.6, {"size": 0.8, "layer": "B"}),
    ("I2C: SHT45 0x44, LPS22HH 0x5D", 16.0, 13.2, {"size": 0.8, "layer": "B"}),
    ("JP2 su 5C: LPS22HH a 0x5C", 16.0, 14.8, {"size": 0.8, "layer": "B"}),
    ("JP1 chiuso: pull-up 4,7k", 16.0, 16.4, {"size": 0.8, "layer": "B"}),
    ("glacier-elettronica", 16.0, 18.4, {"size": 0.8, "layer": "B"}),          # lato saldature
    ("modulo meteo rev. A", 16.0, 20.0, {"size": 0.8, "layer": "B"}),
]
DNP = set()                                  # tutto montato da JLCPCB
# (valore, impronta) -> (codice del produttore, codice JLCPCB/LCSC)
CODICI = {
    ("SHT45-AD1B", "DFN4_SHT4X"): ("SHT45-AD1B-R2", ""),
    ("LPS22HHTR", "HLGA10"): ("LPS22HHTR", "C2827824"),
    ("100n", "C0603"): ("CC0603KRX7R9BB104", "C14663"),
    ("4k7", "R0603"): ("0603WAF4701T5E", "C23162"),
    ("Qwiic", "JSTSH4"): ("SM04B-SRSS-TB(LF)(SN)", "C160404"),
}
# schema KiCad: posizione dei simboli (x, y in mm sul foglio A4)
SCHEMA = {
    "J1": (40, 60), "J2": (40, 95), "U1": (110, 60), "C1": (130, 55), "U2": (110, 110),
    "C2": (140, 105), "C3": (150, 105), "JP2": (85, 135), "R1": (175, 60), "R2": (185, 60), "JP1": (180, 85),
}
