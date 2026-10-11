# -*- coding: utf-8 -*-
"""SCATOLINA DI ACQUISIZIONE: Raspberry Pi Pico 2 su zoccolo, 4 ingressi LEMO, uscita PPS
LEMO, GPS, hub I2C a 8 porte. Alimentata dalla USB del Pico (cavo dal Raspberry Pi Zero 2 W,
che riceve i dati sulla stessa USB).

  A1      Raspberry Pi Pico 2 (RP2350) su due strip femmina 1x20: conta e marca il tempo
          degli impulsi con la PIO (risoluzione 6,7 ns a 150 MHz), legge GPS e I2C
  J1-J3   LEMO 00 ingressi BARRA 1, 2, 3 (uscite LEMO J104/J204/J304 del rivelatore)
  J4      LEMO 00 ingresso AND (uscita J5 del rivelatore)
          ogni ingresso: ESD PESD5V0U1BA, 100k a massa (ingresso scollegato = 0),
          100 ohm in serie, buffer a trigger di Schmitt 74LVC1G17 alimentato a 3,3 V
          (ingresso tollerante fino a 5,5 V: accetta anche il vecchio TTL a 5 V)
  J5      LEMO 00 uscita PPS (1 impulso al secondo del GPS) per oscilloscopio o altri
          strumenti: buffer 74LVC1G17 + 33 ohm
  J6      GPS (modulo con antenna attiva, es. u-blox NEO-M8N/M9N su breakout):
          1 +5V, 2 +3V3, 3 GND, 4 TX del GPS -> GP1 (UART0 RX), 5 RX del GPS <- GP0 (UART0 TX), 6 PPS
          PPS: 100 ohm in serie + 100k a massa -> GP6 e buffer dell'uscita J5
  U6      TI TCA9548A, hub I2C 1->8 (indirizzo 0x70), sul bus I2C0 del Pico (GP8 SDA, GP9 SCL),
          ~RESET da GP7 (con pull-up 10k)
  J7, J8  porte 0 e 1: Molex KK 254 3 poli verso i rivelatori (1 GND, 2 SDA, 3 SCL;
          il rivelatore ha la sua alimentazione)
  J9-J14  porte 2-7: Qwiic/STEMMA QT (1 GND, 2 3V3, 3 SDA, 4 SCL), modulo meteo e futuri sensori
          ogni porta: pull-up 4,7k su SDA e SCL verso +3V3_QW
  U7      AP2112K-3.3 (600 mA) dal +5V della USB: alimenta le porte Qwiic (il regolatore del Pico
          da' al massimo 300 mA e resta per il Pico e i buffer)
  D10     LED verde di alimentazione (+3V3_QW), D11 LED di attivita' (GP15)

Pinout: Pico dalla documentazione Raspberry Pi (pin 40 VBUS, 36 3V3(OUT)); TCA9548APWR, AP2112K
e 74LVC1G17 (SOT-23-5 DBV: 1 NC, 2 A, 3 GND, 4 Y, 5 VCC) dalle librerie ufficiali KiCad.
"""
NOME = "scheda_acquisizione"
TITOLO = "Scatolina di acquisizione (Pico 2, LEMO, GPS, hub I2C)"
W, H = 105.0, 70.0

COMPONENTS = {
    "A1":  ("PICO2", "Pico 2", "PICO", {"note": "Raspberry Pi Pico 2 (SC1631) su 2 strip femmina 1x20"}),
    "U6":  ("TCA9548A", "TCA9548APWR", "TSSOP24", {"note": "hub I2C 1->8, 0x70"}),
    "U7":  ("AP2112K", "AP2112K-3.3", "SOT235", {"note": "3,3 V 600 mA per le porte Qwiic"}),
    "C6":  ("C", "100n", "C0603", {"note": "disaccoppiamento U6"}),
    "C7":  ("C", "1u", "C0603", {"note": "ingresso U7"}),
    "C8":  ("C", "1u", "C0603", {"note": "uscita U7"}),
    "C9":  ("C", "10u", "C1206", {"note": "+5V, vicino al Pico"}),
    "C10": ("C", "10u", "C1206", {"note": "+3V3_QW, serbatoio per le porte"}),
    "R20": ("R", "4k7", "R0603", {"note": "pull-up SDA a monte dell'hub"}),
    "R21": ("R", "4k7", "R0603", {"note": "pull-up SCL a monte dell'hub"}),
    "R22": ("R", "10k", "R0603", {"note": "pull-up ~RESET dell'hub"}),
    "J6":  ("CONN6", "GPS", "HDR6", {"note": "strip 1x6 per il modulo GPS"}),
    "R30": ("R", "100", "R0603", {"note": "serie PPS"}),
    "R31": ("R", "100k", "R0603", {"note": "PPS a massa senza GPS"}),
    "U5":  ("LVC1G17", "74LVC1G17", "SOT235", {"note": "buffer uscita PPS"}),
    "C5":  ("C", "100n", "C0603", {"note": "disaccoppiamento U5"}),
    "R32": ("R", "33", "R0603", {"note": "serie uscita PPS (adatta il cavo)"}),
    "D5":  ("TVSB", "PESD5V0U1BA", "SOD323", {"note": "ESD uscita PPS"}),
    "J5":  ("CONN2", "LEMO_PPS", "LEMO00", {"note": "uscita PPS, LEMO EPL.00.250.NTN"}),
    "D10": ("LED", "LED verde", "LED0805", {"note": "alimentazione +3V3_QW"}),
    "R40": ("R", "1k5", "R0603", {"note": "LED alimentazione"}),
    "D11": ("LED", "LED verde", "LED0805", {"note": "attivita' (GP15)"}),
    "R41": ("R", "1k5", "R0603", {"note": "LED attivita'"}),
    "J7":  ("CONN3", "I2C_RIV0", "KK3", {"note": "porta 0, Molex KK 254 22-27-2031 verso il rivelatore"}),
    "J8":  ("CONN3", "I2C_RIV1", "KK3", {"note": "porta 1, Molex KK 254 22-27-2031 (secondo rivelatore)"}),
    "H1": ("MH", "M3", "MH3", {}), "H2": ("MH", "M3", "MH3", {}),
    "H3": ("MH", "M3", "MH3", {}), "H4": ("MH", "M3", "MH3", {}),
}
INGRESSI = {1: "BARRA1", 2: "BARRA2", 3: "BARRA3", 4: "AND"}
GP_IN = {1: "4", 2: "5", 3: "6", 4: "7"}             # GP2..GP5 = pin 4..7 del Pico
for k, nome in INGRESSI.items():
    COMPONENTS[f"J{k}"] = ("CONN2", f"LEMO_{nome}", "LEMO00", {"note": f"ingresso {nome}, LEMO EPL.00.250.NTN"})
    COMPONENTS[f"D{k}"] = ("TVSB", "PESD5V0U1BA", "SOD323", {"note": f"ESD ingresso {nome}"})
    COMPONENTS[f"R{k}"] = ("R", "100k", "R0603", {"note": f"ingresso {nome} a massa se scollegato"})
    COMPONENTS[f"R1{k}"] = ("R", "100", "R0603", {"note": f"serie ingresso {nome}"})
    COMPONENTS[f"U{k}"] = ("LVC1G17", "74LVC1G17", "SOT235", {"note": f"buffer di Schmitt {nome}"})
    COMPONENTS[f"C{k}"] = ("C", "100n", "C0603", {"note": f"disaccoppiamento U{k}"})
PORTE_QW = range(2, 8)
for p in range(8):
    COMPONENTS[f"R5{p}"] = ("R", "4k7", "R0603", {"note": f"pull-up SDA porta {p}"})
    COMPONENTS[f"R6{p}"] = ("R", "4k7", "R0603", {"note": f"pull-up SCL porta {p}"})
for p in PORTE_QW:
    COMPONENTS[f"J{7 + p}"] = ("QWIIC", "Qwiic", "JSTSH4", {"note": f"porta {p}, JST SM04B-SRSS-TB"})

PICO_GND = ["3", "8", "13", "18", "23", "28", "33", "38"]
NETS = {
    "GND":  [("A1", p) for p in PICO_GND] + [("U6", "12"), ("U6", "1"), ("U6", "2"), ("U6", "21"),
             ("U7", "2"), ("C6", "2"), ("C7", "2"), ("C8", "2"), ("C9", "2"), ("C10", "2"),
             ("J6", "3"), ("R31", "2"), ("U5", "3"), ("C5", "2"), ("D5", "2"), ("J5", "2"),
             ("D10", "1"), ("J7", "1"), ("J8", "1")],
    "+5V":  [("A1", "40"), ("C9", "1"), ("U7", "1"), ("U7", "3"), ("C7", "1"), ("J6", "1")],
    "+3V3": [("A1", "36"), ("U6", "24"), ("C6", "1"), ("R20", "2"), ("R21", "2"), ("R22", "2"),
             ("J6", "2"), ("U5", "5"), ("C5", "1")],
    "+3V3_QW": [("U7", "5"), ("C8", "1"), ("C10", "1"), ("R40", "1")],
    "I2C_SDA": [("A1", "11"), ("U6", "23"), ("R20", "1")],
    "I2C_SCL": [("A1", "12"), ("U6", "22"), ("R21", "1")],
    "HUB_RST": [("A1", "10"), ("U6", "3"), ("R22", "1")],
    "GPS_TX":  [("J6", "4"), ("A1", "2")],
    "GPS_RX":  [("J6", "5"), ("A1", "1")],
    "PPS_GPS": [("J6", "6"), ("R30", "1")],
    "PPS":     [("R30", "2"), ("R31", "1"), ("A1", "9"), ("U5", "2")],
    "PPS_BUF": [("U5", "4"), ("R32", "1")],
    "PPS_OUT": [("R32", "2"), ("D5", "1"), ("J5", "1")],
    "LED_PWR": [("R40", "2"), ("D10", "2")],
    "LED_ATT": [("A1", "20"), ("R41", "1")],
    "LED_ATT_K": [("R41", "2"), ("D11", "2")],
}
NETS["GND"].append(("D11", "1"))
for k, nome in INGRESSI.items():
    NETS["GND"] += [(f"D{k}", "2"), (f"R{k}", "2"), (f"J{k}", "2"), (f"U{k}", "3"), (f"C{k}", "2")]
    NETS["+3V3"] += [(f"U{k}", "5"), (f"C{k}", "1")]
    NETS[f"IN_{nome}"] = [(f"J{k}", "1"), (f"D{k}", "1"), (f"R{k}", "1"), (f"R1{k}", "1")]
    NETS[f"A_{nome}"] = [(f"R1{k}", "2"), (f"U{k}", "2")]
    NETS[f"GP_{nome}"] = [(f"U{k}", "4"), ("A1", GP_IN[k])]
# hub: SDn = 4/6/8/10/13/15/17/19, SCn = 5/7/9/11/14/16/18/20
for p in range(8):
    sd = str(4 + 2 * p + (1 if p >= 4 else 0))
    sc = str(5 + 2 * p + (1 if p >= 4 else 0))
    NETS[f"SDA{p}"] = [("U6", sd), (f"R5{p}", "1")]
    NETS[f"SCL{p}"] = [("U6", sc), (f"R6{p}", "1")]
    NETS["+3V3_QW"] += [(f"R5{p}", "2"), (f"R6{p}", "2")]
    if p < 2:
        j = f"J{7 + p}"
        NETS[f"SDA{p}"].append((j, "2"))
        NETS[f"SCL{p}"].append((j, "3"))
    else:
        j = f"J{7 + p}"
        NETS[f"SDA{p}"].append((j, "3"))
        NETS[f"SCL{p}"].append((j, "4"))
        NETS["GND"].append((j, "1"))
        NETS["+3V3_QW"].append((j, "2"))

PIN_COUNT = {"PICO2": 40, "TCA9548A": 24, "AP2112K": 5, "LVC1G17": 5, "C": 2, "R": 2, "CONN6": 6,
             "CONN2": 2, "CONN3": 3, "TVSB": 2, "LED": 2, "QWIIC": 4, "MH": 0}
# pin liberi: GP10-14, GP16-22, GP26-28, RUN, ADC_VREF, 3V3_EN, VSYS; NC dei buffer e dell'AP2112K
NC_PINS = ({("A1", str(p)) for p in [14, 15, 16, 17, 19, 21, 22, 24, 25, 26, 27, 29, 30, 31, 32, 34, 35, 37, 39]}
           | {(f"U{k}", "1") for k in (1, 2, 3, 4, 5)} | {("U7", "4")})


def check():
    used = {}
    for net, pins in NETS.items():
        for r, p in pins:
            assert r in COMPONENTS, r
            assert (r, p) not in used, (r, p, net, used.get((r, p)))
            used[(r, p)] = net
    miss = [(r, p) for r, (k, *_x) in COMPONENTS.items() for p in map(str, range(1, PIN_COUNT[k] + 1))
            if (r, p) not in used and (r, p) not in NC_PINS]
    assert not miss, miss
    assert not [x for x in NC_PINS if x in used], [x for x in NC_PINS if x in used]
    print(f"netlist {NOME}: {len(COMPONENTS)} componenti, {len(NETS)} reti, {len(used)} pin")


# ---------------------------------------------------------------- PCB
FP = {"PICO": "RPi_Pico2_Socket", "TSSOP24": "TSSOP-24_4.4x7.8mm_P0.65mm", "SOT235": "SOT-23-5",
      "C0603": "C_0603_1608Metric", "R0603": "R_0603_1608Metric", "C1206": "C_1206_3216Metric",
      "HDR6": "PinHeader_1x06_P2.54mm_Vertical", "SOD323": "D_SOD-323", "LEMO00": "LEMO_EPL00",
      "LED0805": "LED_0805_2012Metric", "KK3": "Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical",
      "JSTSH4": "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", "MH3": "MountingHole_3.2mm_M3"}
CONTORNO = [(0, 0), (W, 0), (W, H), (0, H)]
PLACEMENT = {
    "A1":  (33.0, 32.0, 90),        # USB del Pico verso il bordo sinistro
    "H1": (4.0, 4.0, 0), "H2": (101.0, 4.0, 0), "H3": (4.0, 66.0, 0), "H4": (101.0, 66.0, 0),
    # alimentazione Qwiic (in alto a sinistra)
    "U7":  (20.0, 10.0, 0), "C7": (15.5, 10.0, 90), "C8": (24.5, 10.0, 90), "C10": (24.5, 15.0, 90),
    "C9":  (10.0, 15.0, 90),
    "R40": (12.0, 4.5, 0), "D10": (16.5, 4.5, 180),
    # hub
    "U6":  (76.0, 24.0, 0), "C6": (81.5, 21.5, 90),
    "R20": (63.0, 26.0, 90), "R21": (66.0, 26.0, 90), "R22": (69.0, 26.0, 90),
    # porte: KK in alto a sinistra della fila, Qwiic a seguire (bocca verso il bordo alto)
    "J7":  (29.0, 5.0, 0), "J8": (38.5, 5.0, 0),
    # GPS (bordo destro) e PPS
    "J6":  (101.0, 27.0, 0),
    "R30": (95.0, 37.0, 90), "R31": (92.0, 37.0, 90),
    "U5":  (80.0, 50.0, 0), "C5": (83.5, 50.0, 90), "R32": (80.0, 54.5, 0),
    "D5":  (85.0, 55.5, 90), "J5": (80.0, 66.0, 270),
    "R41": (60.0, 44.0, 0), "D11": (64.5, 44.0, 180),
}
X_IN = {1: 16.0, 2: 32.0, 3: 48.0, 4: 64.0}
for k, x in X_IN.items():
    PLACEMENT[f"J{k}"] = (x, 66.0, 270)     # gomito: frontale verso il bordo, corpo fuori scheda
    PLACEMENT[f"D{k}"] = (x + 5.0, 55.5, 90)
    PLACEMENT[f"R{k}"] = (x - 5.0, 57.0, 90)
    PLACEMENT[f"R1{k}"] = (x, 54.5, 0)
    PLACEMENT[f"U{k}"] = (x, 50.0, 0)
    PLACEMENT[f"C{k}"] = (x + 3.5, 50.0, 90)
X_PORTA = {0: 29.0, 1: 38.5, 2: 50.0, 3: 58.1, 4: 66.2, 5: 74.3, 6: 82.4, 7: 90.5}
for p in range(8):
    x = X_PORTA[p] + (2.54 if p < 2 else 0)            # KK: centro del connettore
    PLACEMENT[f"R5{p}"] = (x - 1.0, 12.5, 90)
    PLACEMENT[f"R6{p}"] = (x + 1.0, 12.5, 90)
for p in PORTE_QW:
    PLACEMENT[f"J{7 + p}"] = (X_PORTA[p], 3.6, 180)
# pad a foro passante di massa collegati pieni al piano (zoccolo del Pico e strip del GPS:
# con le piste vicine le razze termiche non sarebbero tutte collegate)
PAD_PIENI = {"A1", "J6"}
RETI_POTENZA = ("+5V", "+3V3", "+3V3_QW", "GND")
TRACK_POTENZA = 0.4
RIF_VISIBILI = {"H1": False, "H2": False, "H3": False, "H4": False}
RIF_VISIBILI.update({f"R{a}{p}": False for a in (5, 6) for p in range(8)})   # scritte sotto
RIF_POS = {r: (0, 2.7, 0) for r in ("R20", "R21", "R22", "R30", "R31")}
RIF_POS.update({f"C{k}": (1.6, 0, 90) for k in (1, 2, 3, 4, 5, 6)})
RIF_POS.update({f"J{k}": (6.4, -1.5, 0) for k in (1, 2, 3, 4, 5)})
RIF_VISIBILI["A1"] = False                         # sul Pico c'e' la scritta col nome
SCRITTE = [
    ("ACQUISIZIONE", 33.0, 32.0, {"size": 2.0, "bold": True}),
    ("Raspberry Pi Pico 2 (USB verso il Raspberry Pi Zero 2 W)", 33.0, 35.5, {"size": 1.0}),
    ("BARRA 1", 16.0, 60.8, {"size": 1.0}), ("BARRA 2", 32.0, 60.8, {"size": 1.0}),
    ("BARRA 3", 48.0, 60.8, {"size": 1.0}), ("AND", 64.0, 60.8, {"size": 1.0}),
    ("PPS OUT", 80.0, 60.8, {"size": 1.0}),
    ("RIV. 0", 31.5, 9.6, {"size": 0.8}), ("RIV. 1", 41.0, 9.6, {"size": 0.8}),
    ("2", 50.0, 8.6, {"size": 0.8}), ("3", 58.1, 8.6, {"size": 0.8}), ("4", 66.2, 8.6, {"size": 0.8}),
    ("5", 74.3, 8.6, {"size": 0.8}), ("6", 82.4, 8.6, {"size": 0.8}), ("7", 90.5, 8.6, {"size": 0.8}),
    ("pull-up 4k7: R50-R57 (SDA), R60-R67 (SCL)", 62.0, 15.0, {"size": 0.8}),
    ("I2C: KK 1 GND 2 SDA 3 SCL - Qwiic 1 GND 2 3V3 3 SDA 4 SCL", 62.0, 16.6, {"size": 0.8}),
    ("GPS", 101.0, 22.5, {"size": 1.0}),
    ("1 5V 2 3V3 3 GND 4 TX 5 RX 6 PPS", 97.5, 33.4, {"size": 0.8, "rot": 90}),
    ("glacier-elettronica - scatolina di acquisizione rev. A", 52.5, 43.6, {"size": 0.9, "layer": "B"}),
    ("ingressi LEMO: 3,3 V o 5 V, 100k a massa, Schmitt 74LVC1G17", 52.5, 45.1, {"size": 0.9, "layer": "B"}),
    ("hub TCA9548A 0x70 su GP8/GP9 - GPS UART0 GP0/GP1 - PPS GP6", 52.5, 46.6, {"size": 0.9, "layer": "B"}),
]
DNP = set()
CODICI = {
    ("TCA9548APWR", "TSSOP24"): ("TCA9548APWR", "C130026"),
    ("AP2112K-3.3", "SOT235"): ("AP2112K-3.3TRG1", "C51118"),
    ("74LVC1G17", "SOT235"): ("SN74LVC1G17DBVR", "C7836"),
    ("PESD5V0U1BA", "SOD323"): ("PESD5V0U1BA", "C5199862"),
    ("100n", "C0603"): ("CC0603KRX7R9BB104", "C14663"),
    ("1u", "C0603"): ("CL10A105KB8NNNC", "C15849"),
    ("10u", "C1206"): ("CL31B106KOHNNNE", "C47971"),
    ("4k7", "R0603"): ("0603WAF4701T5E", "C23162"),
    ("10k", "R0603"): ("0603WAF1002T5E", "C25804"),
    ("100k", "R0603"): ("0603WAF1003T5E", "C25803"),
    ("100", "R0603"): ("0603WAF1000T5E", "C22775"),
    ("33", "R0603"): ("0603WAF330JT5E", "C23140"),
    ("1k5", "R0603"): ("0603WAF1501T5E", "C22843"),
    ("LED verde", "LED0805"): ("KT-0805G", "C2297"),
    ("Qwiic", "JSTSH4"): ("SM04B-SRSS-TB(LF)(SN)", "C160404"),
}
# montati a mano (foro passante, non da JLCPCB): Pico su strip, LEMO, KK, strip GPS
MANO = {"A1", "J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8"}
DNP = set(MANO)
SCHEMA_FOGLIO = "A3"
SCHEMA = {"A1": (200, 150)}
# posizioni sul foglio A3 (420 x 297 mm), a gruppi
SCHEMA = {"A1": (70, 140),
          "U7": (60, 240), "C7": (40, 245), "C8": (85, 245), "C10": (100, 245), "C9": (25, 245),
          "R40": (120, 245), "D10": (135, 255), "R41": (155, 245), "D11": (170, 255),
          "J6": (150, 205), "R30": (172, 205), "R31": (188, 210), "U5": (212, 205), "C5": (232, 210),
          "R32": (252, 205), "D5": (270, 210), "J5": (292, 205),
          "U6": (330, 120), "C6": (355, 60), "R20": (300, 70), "R21": (312, 70), "R22": (324, 70)}
for k in INGRESSI:
    y = 45 + (k - 1) * 36
    SCHEMA.update({f"J{k}": (150, y), f"D{k}": (172, y + 6), f"R{k}": (188, y + 6),
                   f"R1{k}": (205, y + 6), f"U{k}": (230, y), f"C{k}": (252, y + 6)})
for p in range(8):
    y = 45 + p * 25
    SCHEMA.update({f"R5{p}": (375, y + 4), f"R6{p}": (385, y + 4), f"J{7 + p}": (405, y)})
SCHEMA_TESTI = [
    ("Pico 2: GP2-GP5 ingressi (PIO), GP6 PPS, GP0/GP1 UART0 GPS, GP8/GP9 I2C0, GP7 reset hub, GP15 LED", 20, 280),
    ("Ingressi LEMO: ESD, 100k a massa, 100 ohm, Schmitt 74LVC1G17 a 3,3 V (tollera 5 V)", 140, 30),
    ("Hub I2C TCA9548A 0x70: porte 0-1 KK verso i rivelatori, 2-7 Qwiic (pull-up 4,7k per porta)", 280, 30),
    ("GPS: TX/RX su UART0, PPS su GP6 e sull'uscita LEMO J5", 140, 195),
    ("Alimentazione: +5V dalla USB del Pico; +3V3 dal Pico (300 mA max); +3V3_QW da AP2112K (600 mA)", 20, 230),
]
