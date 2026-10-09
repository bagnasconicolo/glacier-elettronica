# -*- coding: utf-8 -*-
"""Variante a 3 CANALI della scheda Riv. Cosmici: modello dati.

Costruito automaticamente da netdata.py (la scheda a 1 canale):
  - parti in comune (boost, 3,3 V, riferimenti 3,6 V) una sola volta, con i
    riferimenti originali;
  - parti di canale replicate 3 volte: R9 del canale 2 -> R209, CF1 -> CF201,
    U3 -> U303 (lettere + n. canale + numero a 2 cifre); reti di canale con
    suffisso: CMP_IN -> CMP_IN1, CMP_IN2, CMP_IN3;
  - tolto il driver TTL a 5 V (U4, CF3, J2): le uscite sono LEMO a 3,3 V;
  - uscita di ogni canale su LEMO 00 (J104, J204, J304);
  - coincidenza: U10 74LVC1G11 (AND a 3) con jumper di esclusione JP1..JP3 e
    pull-up R31..R33 (jumper aperto = canale escluso, ingresso a 1);
    uscita AND su LEMO J5 tramite R30 33 ohm;
  - test point per oscilloscopio (TPn01..TPn06 per canale, TP1..TP6 comuni);
  - monitor delle tensioni: ADC MCP3424 (U11) in I2C su J6 legge i tre bias
    (partitori R?50/R?51 su VREG38n) e l'alta tensione (R40/R41).
"""
import re
from netdata import COMPONENTS as C1, NETS as N1, PIN_COUNT as PC1, NC_PINS as NC1

VARIANT = "3ch"
CHANNELS = (1, 2, 3)

SHARED = {"U1", "L1", "C1", "C2", "C3", "R1", "R2", "R3", "R22", "C22",
          "U5", "CF4", "U6", "CF8", "CF9", "J3", "U7", "CF7"}
DROP = {"U4", "CF3", "J2"}
SHARED_NETS = {"GND", "+5V", "+3V3", "+3V6", "VOUT40", "FB", "SW", "VREF_B"}


def chref(ref, n):
    m = re.fullmatch(r"([A-Z]+)(\d+)", ref)
    return f"{m.group(1)}{n}{int(m.group(2)):02d}"


def _ref(ref, n):
    return ref if ref in SHARED else chref(ref, n)


COMPONENTS = {}
for ref, (kind, value, fpk, extra) in C1.items():
    if ref in DROP:
        continue
    if ref in SHARED:
        COMPONENTS[ref] = (kind, value, fpk, extra)
        continue
    for n in CHANNELS:
        if ref == "J4":
            COMPONENTS[chref(ref, n)] = ("CONN2", f"LEMO_CH{n}", "LEMO00",
                                         {"note": f"uscita canale {n}, LEMO EPL.00.250.NTN"})
        elif ref == "J1":       # cavo della barra: Molex KK 254 (calza = bias, non LEMO)
            COMPONENTS[chref(ref, n)] = ("CONN2", f"SiPM_CH{n}", "KK2",
                                         {"note": "Molex KK 254 22-27-2021; cavo: 1=centrale/segnale 2=calza/bias"})
        else:
            COMPONENTS[chref(ref, n)] = (kind, value, fpk, extra)

NETS = {}
for net, pins in N1.items():
    pins = [(r, p) for r, p in pins if r not in DROP]
    if not pins:
        continue
    if net in SHARED_NETS:
        out = []
        for r, p in pins:
            if r in SHARED:
                out.append((r, p))
            else:
                out += [(chref(r, n), p) for n in CHANNELS]
        NETS[net] = out
    else:
        assert not any(r in SHARED for r, _ in pins), f"rete {net} mista"
        for n in CHANNELS:
            NETS[f"{net}{n}"] = [(chref(r, n), p) for r, p in pins]

# ---- coincidenza
COMPONENTS.update({
    "U10":  ("LVC1G11", "74LVC1G11", "SOT23-6", {"note": "AND a 3 ingressi (coincidenza)"}),
    "CF11": ("C", "100n", "C0805", {"note": "decoupling 74LVC1G11"}),
    "R30":  ("R", "33R", "R0805", {"note": "terminazione serie uscita AND"}),
    "J5":   ("CONN2", "LEMO_AND", "LEMO00", {"note": "uscita coincidenza, LEMO EPL.00.250.NTN"}),
})
AND_PIN = {1: "3", 2: "1", 3: "6"}           # B, A, C del 74LVC1G11 (ingressi equivalenti;
                                             # ordine scelto per piste senza incroci)
for n in CHANNELS:
    COMPONENTS[f"JP{n}"] = ("CONN2", f"INCL_CH{n}", "HDR2",
                            {"note": f"jumper: chiuso = canale {n} nella coincidenza"})
    COMPONENTS[f"R3{n}"] = ("R", "10k", "R0805", {"note": f"pull-up ingresso AND canale {n}"})
    NETS[f"BUF_Y{n}"].append((f"JP{n}", "1"))
    NETS[f"AND_IN{n}"] = [(f"JP{n}", "2"), (f"R3{n}", "1"), ("U10", AND_PIN[n])]
    NETS["+3V3"].append((f"R3{n}", "2"))
NETS["AND_Y"] = [("U10", "4"), ("R30", "1")]
NETS["AND_OUT"] = [("R30", "2"), ("J5", "1")]
NETS["+3V3"] += [("U10", "5"), ("CF11", "1")]
NETS["GND"] += [("U10", "2"), ("CF11", "2"), ("J5", "2")]

# ---- test point per oscilloscopio
TP_CH = ["SIG_IN", "CMP_IN", "TH", "CMP_Q", "BIAS", "GND"]
TP_SHARED = ["VOUT40", "+5V", "+3V3", "+3V6", "AND_OUT", "GND"]
for n in CHANNELS:
    for i, net in enumerate(TP_CH, 1):
        ref = f"TP{n}{i:02d}"
        COMPONENTS[ref] = ("TP", net if net == "GND" else f"{net}{n}", "TP", {"note": "test point"})
        NETS[net if net == "GND" else f"{net}{n}"].append((ref, "1"))
for i, net in enumerate(TP_SHARED, 1):
    ref = f"TP{i}"
    COMPONENTS[ref] = ("TP", net, "TP", {"note": "test point"})
    NETS[net].append((ref, "1"))

# ---- monitor delle tensioni (ADC MCP3424 in I2C verso il Raspberry Pi)
# Partitore 1M / 43k (rapporto 1/24,26) su VREG38n, l'uscita del regolatore del bias:
# e' dentro l'anello di retroazione di U?08, quindi il carico (37 uA) non cambia
# VREG38 ne' BIAS; tra il partitore e il SiPM resta il filtro R8/C6. Condensatore
# da 100n sul punto di misura: assorbe i picchi di campionamento dell'ADC.
MON_DIV = ("1M", "43k")
ADC_CH = {1: ("1", "2"), 2: ("3", "4"), 3: ("11", "12"), 4: ("13", "14")}   # (CH+, CH-)
for n in CHANNELS:
    rt, rb, cm = chref("R50", n), chref("R51", n), chref("C50", n)
    COMPONENTS[rt] = ("R", MON_DIV[0], "R0805", {"note": f"partitore monitor bias canale {n} (alto)"})
    COMPONENTS[rb] = ("R", MON_DIV[1], "R0805", {"note": f"partitore monitor bias canale {n} (basso)"})
    COMPONENTS[cm] = ("C", "100n", "C0805", {"note": f"filtro punto di misura canale {n}"})
    NETS[f"VREG38{n}"].append((rt, "1"))
    NETS[f"MON{n}"] = [(rt, "2"), (rb, "1"), (cm, "1"), ("U11", ADC_CH[n][0])]
    NETS["GND"] += [(rb, "2"), (cm, "2"), ("U11", ADC_CH[n][1])]
COMPONENTS.update({
    "R40":  ("R", MON_DIV[0], "R0805", {"note": "partitore monitor alta tensione (alto)"}),
    "R41":  ("R", MON_DIV[1], "R0805", {"note": "partitore monitor alta tensione (basso)"}),
    "C40":  ("C", "100n", "C0805", {"note": "filtro punto di misura alta tensione"}),
    "U11":  ("MCP3424", "MCP3424", "SO14", {"note": "ADC 18 bit 4 canali I2C, indirizzo 0x68"}),
    "CF12": ("C", "100n", "C0805", {"note": "decoupling MCP3424"}),
    "R42":  ("R", "100R", "R0805", {"note": "serie SDA: fronti piu' lenti, meno disturbi"}),
    "R43":  ("R", "100R", "R0805", {"note": "serie SCL: fronti piu' lenti, meno disturbi"}),
    "J6":   ("CONN3", "I2C_RPI", "HDR3", {"note": "verso Raspberry Pi: 1=GND 2=SDA 3=SCL (pull-up sul Pi)"}),
})
NETS["VOUT40"].append(("R40", "1"))
NETS["MON4"] = [("R40", "2"), ("R41", "1"), ("C40", "1"), ("U11", ADC_CH[4][0])]
NETS["GND"] += [("R41", "2"), ("C40", "2"), ("U11", ADC_CH[4][1]),
                ("U11", "5"), ("U11", "9"), ("U11", "10"), ("CF12", "2"), ("J6", "1")]
NETS["+3V3"] += [("U11", "6"), ("CF12", "1")]
NETS["SDA_ADC"] = [("U11", "7"), ("R42", "1")]
NETS["SCL_ADC"] = [("U11", "8"), ("R43", "1")]
NETS["I2C_SDA"] = [("R42", "2"), ("J6", "2")]
NETS["I2C_SCL"] = [("R43", "2"), ("J6", "3")]

# ---- fori di fissaggio M3 (piazzola a massa)
for k in range(1, 9):
    COMPONENTS[f"MH{k}"] = ("MH", "M3", "MH3", {"note": "foro di fissaggio M3, a massa"})
    NETS["GND"].append((f"MH{k}", "1"))

PIN_COUNT = dict(PC1, LVC1G11=6, TP=1, MCP3424=14, CONN3=3, MH=1)
NC_PINS = set()
for r, p in NC1:
    if r in SHARED:
        NC_PINS.add((r, p))
    else:
        NC_PINS |= {(chref(r, n), p) for n in CHANNELS}


def check():
    used = {}
    for net, pins in NETS.items():
        for ref, pin in pins:
            assert ref in COMPONENTS, f"ref sconosciuto {ref}"
            key = (ref, str(pin))
            assert key not in used, f"pin duplicato {key}: {net} e {used[key]}"
            used[key] = net
    missing = []
    for ref, (kind, *_r) in COMPONENTS.items():
        for p in range(1, PIN_COUNT[kind] + 1):
            if (ref, str(p)) not in used and (ref, str(p)) not in NC_PINS:
                missing.append((ref, p))
    assert not missing, f"pin non connessi: {missing}"
    print(f"netlist 3ch OK: {len(COMPONENTS)} componenti, {len(NETS)} reti, {len(used)} pin connessi")


if __name__ == "__main__":
    check()
