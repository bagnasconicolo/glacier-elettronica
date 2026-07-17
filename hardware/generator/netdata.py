# -*- coding: utf-8 -*-
"""
Riv. Cosmici 2024 - "Amplif, alim, soglie" (INFN sez. Torino, S. Gallian, 20/06/2024, rev A)
Trascrizione dello schema (Sheet 1 of 6) - modello dati unico per schema/PCB/BOM.
Refs identici all'originale.
"""

# ---------------------------------------------------------------- components
# fields: ref: (symbol_kind, value, footprint_kind, extra)
COMPONENTS = {
    # Resistori 0805
    "R1":  ("R", "10k",   "R0805", {}),
    "R2":  ("R", "68k",   "R0805", {}),
    "R3":  ("R", "270k",  "R0805", {}),
    "R4":  ("R", "1k2",   "R0805", {}),
    "R5":  ("R", "15k",   "R0805", {}),
    "R6":  ("R", "100k",  "R0805", {}),
    "R7":  ("R", "27k",   "R0805", {}),
    "R8":  ("R", "1k",    "R0805", {}),
    "R9":  ("R", "1k8",   "R0805", {}),
    "R10": ("R", "10k",   "R0805", {}),
    "R11": ("R", "5k6",   "R0805", {}),
    "R12": ("R", "1k",    "R0805", {}),
    "R13": ("R", "560R",  "R0805", {}),
    "R14": ("R", "1k",    "R0805", {}),
    "R15": ("R", "1k",    "R0805", {}),
    "R16": ("R", "1k",    "R0805", {}),
    "R17": ("R", "470R",  "R0805", {}),
    "R18": ("R", "10R",   "R0805", {}),
    "R19": ("R", "18k",   "R0805", {}),
    "R20": ("R", "100k",  "R0805", {}),
    "R21": ("R", "82R",   "R0805", {}),
    "R22": ("R", "220k",  "R0805", {}),
    # Condensatori
    "C1":  ("C", "22pF",       "C0805", {}),
    "C2":  ("C", "1uF 100V",   "C1210", {}),
    "C3":  ("C", "100n 100V",  "C1206", {}),
    "C4":  ("C", "100n",       "C0805", {}),
    "C6":  ("C", "100n 100V",  "C1206", {}),
    "C7":  ("C", "10nF",       "C0805", {}),
    "C9":  ("C", "100pF",      "C0805", {}),
    "C11": ("C", "10n",        "C0805", {}),
    "C21": ("C", "100nF",      "C0805", {}),
    "C22": ("C", "1uF",        "C0805", {}),
    # CF = 100nF 50V (decoupling, nota originale)
    "CF1": ("C", "100n", "C0805", {"note": "decoupling +3V3 amp"}),
    "CF2": ("C", "100n", "C0805", {"note": "decoupling MAX961 VCC"}),
    "CF3": ("C", "100n", "C0805", {"note": "decoupling MCP1402 VDD"}),
    "CF4": ("C", "100n", "C0805", {"note": "out LP2985 +3V6"}),
    "CF5": ("C", "100n", "C0805", {"note": "decoupling TLC555 VCC"}),
    "CF6": ("C", "100n", "C0805", {"note": "TLC555 CTRL"}),
    "CF7": ("C", "100n", "C0805", {"note": "out LP2985 rif. 3V6 (B)"}),
    "CF8": ("C", "100n", "C0805", {"note": "in MCP1825"}),
    "CF9": ("C", "100n", "C0805", {"note": "out MCP1825"}),
    # Induttore
    "L1":  ("L", "47uH", "L_PWR", {"order": "RS 6934344"}),
    # Diodi
    "D1":  ("D", "1N4148", "DO35", {}),
    "D3":  ("LED", "LED rosso", "LED0805", {}),
    # Transistor (SOT-23: 1=B 2=E 3=C)
    "Q1":  ("NPN", "BFR93A",  "SOT23", {"order": "RS 8922365"}),
    "Q2":  ("PNP", "MMBTH81", "SOT23", {"order": "RS 1041196"}),
    # Integrati
    "U1":  ("LT3461",  "LT3461",         "SOT23-6", {"order": "Farnell 4024725"}),
    "U2":  ("TLC555",  "TLC555/LMC555",  "SO8",     {"order": "RS 1962112"}),
    "U3":  ("MAX961",  "MAX961",         "SO8",     {"order": "RS 1899176"}),
    "U4":  ("MCP1402", "MCP1402",        "SOT23-5", {"order": "RS 6684203"}),
    "U5":  ("LP2985",  "LP2985AIM5-3.6", "SOT23-5", {"order": "RS 8122417"}),
    "U6":  ("MCP1825", "MCP1825S-3302",  "SOT223",  {"order": "RS 6695092"}),
    "U7":  ("LP2985",  "LP2985AIM5-3.6", "SOT23-5", {"order": "RS 8122417"}),
    "U8":  ("LT1636",  "LT1636",         "SO8",     {"order": "Farnell 4020771"}),
    # Trimmer (3296W verticale, 3 pin: 1-CCW 2-wiper 3-CW)
    "V1":  ("POT", "10k", "3296W", {"note": "regolazione tensione SiPM"}),
    "V2":  ("POT", "10k", "3296W", {"note": "regolazione soglia"}),
    # Connettori
    "J1":  ("CONN2", "SiPM",    "HDR2", {"note": "cavo Fileca: 1=segnale 2=bias(calza)"}),
    "J2":  ("CONN2", "TTL_OUT", "HDR2", {}),
    "J3":  ("CONN2", "PWR_5V",  "HDR2", {}),
}

# ---------------------------------------------------------------- nets
# net name -> list of (ref, pin)
NETS = {
    "GND": [
        ("R9", "2"), ("R10", "2"), ("R14", "2"), ("R15", "2"), ("R16", "2"),
        ("R18", "2"), ("R7", "2"), ("R4", "2"), ("R6", "2"), ("C4", "2"),
        ("Q1", "2"),
        ("U3", "3"), ("U3", "5"),
        ("U2", "1"),
        ("U1", "2"),
        ("U5", "2"), ("U7", "2"), ("U6", "2"), ("U6", "4"),
        ("U8", "4"),
        ("U4", "1"), ("U4", "4"),
        ("D3", "1"),
        ("C2", "2"), ("C3", "2"), ("C6", "2"), ("C21", "2"), ("C22", "2"),
        ("CF1", "2"), ("CF2", "2"), ("CF3", "2"), ("CF4", "2"), ("CF5", "2"),
        ("CF6", "2"), ("CF7", "2"), ("CF8", "2"), ("CF9", "2"),
        ("J2", "2"), ("J3", "1"),
        ("R1", "2"), ("R2", "2"), ("R22", "2"),
    ],
    "+5V": [
        ("J3", "2"), ("U6", "1"), ("CF8", "1"),
        ("U1", "6"), ("U1", "4"), ("C22", "1"), ("L1", "1"),
        ("U4", "2"), ("CF3", "1"),
        ("U5", "1"), ("U5", "3"),
        ("U7", "1"), ("U7", "3"),
    ],
    "+3V3": [
        ("U6", "3"), ("CF9", "1"),
        ("R12", "2"), ("R13", "2"), ("CF1", "1"),
        ("U3", "8"), ("CF2", "1"),
        ("U2", "8"), ("U2", "4"), ("CF5", "1"),
        ("R20", "2"),
    ],
    "+3V6": [("U5", "5"), ("CF4", "1"), ("R19", "2")],
    # riferimento 3,6V (secondo LP2985) -> D1 -> partitore V1
    "VREF_B": [("U7", "5"), ("CF7", "1"), ("D1", "2")],          # D1 pin2 = A (anodo)
    "VADJ_HI": [("D1", "1"), ("V1", "3")],                        # D1 pin1 = K (catodo)
    "VADJ_LO": [("V1", "1"), ("R7", "1")],
    "VSET": [("V1", "2"), ("U8", "3"), ("C4", "1"), ("R6", "1")],
    # boost 40,2V
    "SW": [("U1", "1"), ("L1", "2")],
    "VOUT40": [("U1", "5"), ("C2", "1"), ("C3", "1"), ("R3", "1"), ("C1", "1"), ("U8", "7")],
    "FB": [("U1", "3"), ("R3", "2"), ("C1", "2"), ("R1", "1"), ("R2", "1"), ("R22", "1")],
    # regolatore lineare 38,4V
    "INV": [("U8", "2"), ("R4", "1"), ("R5", "1")],
    "VREG38": [("U8", "6"), ("R5", "2"), ("R8", "1")],
    "BIAS": [("R8", "2"), ("C6", "1"), ("J1", "2")],
    # front-end
    "SIG_IN": [("J1", "1"), ("R10", "1"), ("C7", "1")],
    "Q1B": [("C7", "2"), ("R9", "1"), ("R11", "1"), ("Q1", "1")],
    "Q1C": [("Q1", "3"), ("R11", "2"), ("R12", "1"), ("Q2", "1")],
    "Q2E": [("Q2", "2"), ("R13", "1")],
    "Q2C": [("Q2", "3"), ("R14", "1"), ("C11", "1")],
    "CMP_IN": [("C11", "2"), ("R15", "1"), ("U3", "1")],
    # soglia
    "TH": [("U3", "2"), ("R17", "1")],
    "TH_W": [("R17", "2"), ("V2", "1"), ("V2", "2"), ("R19", "1")],
    "TH_LO": [("V2", "3"), ("R18", "1")],
    # latch / uscite comparatore
    "LE": [("U3", "4"), ("R16", "1"), ("C9", "1")],
    "CMP_Q": [("U3", "6"), ("C9", "2"), ("U4", "3")],
    "CMP_QB": [("U3", "7"), ("U2", "2")],
    "TTL_OUT": [("U4", "5"), ("J2", "1")],
    # monostabile LED
    "T555": [("U2", "6"), ("U2", "7"), ("R20", "1"), ("C21", "1")],
    "CTL555": [("U2", "5"), ("CF6", "1")],
    "LED_A": [("U2", "3"), ("R21", "1")],
    "LED_K": [("R21", "2"), ("D3", "2")],                          # D3: 1=K 2=A
}

# pin totali attesi per tipo (per il check di completezza)
PIN_COUNT = {
    "R": 2, "C": 2, "L": 2, "D": 2, "LED": 2, "NPN": 3, "PNP": 3, "POT": 3,
    "CONN2": 2,
    "LT3461": 6, "TLC555": 8, "MAX961": 8, "MCP1402": 5, "LP2985": 5,
    "MCP1825": 4, "LT1636": 8,
}
# pin volutamente non connessi
NC_PINS = {("U8", "1"), ("U8", "5"), ("U8", "8"), ("U5", "4"), ("U7", "4")}

def check():
    used = {}
    for net, pins in NETS.items():
        for ref, pin in pins:
            assert ref in COMPONENTS, f"ref sconosciuto {ref}"
            key = (ref, pin)
            assert key not in used, f"pin duplicato {key}: {net} e {used[key]}"
            used[key] = net
    missing = []
    for ref, (kind, *_rest) in COMPONENTS.items():
        n = PIN_COUNT[kind]
        for p in range(1, n + 1):
            key = (ref, str(p))
            if key not in used and key not in NC_PINS:
                missing.append(key)
    assert not missing, f"pin non connessi: {missing}"
    print(f"netlist OK: {len(COMPONENTS)} componenti, {len(NETS)} reti, {len(used)} pin connessi")

if __name__ == "__main__":
    check()
