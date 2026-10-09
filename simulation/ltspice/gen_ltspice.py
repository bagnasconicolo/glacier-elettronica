# -*- coding: utf-8 -*-
"""Genera la simulazione COMPLETA della scheda per LTspice / ngspice dallo
STESSO modello dati dello schema KiCad (hardware/generator/netdata.py):

  riv_cosmici_completo.cir   netlist (LTspice e ngspice)
  riv_cosmici_completo.asc   schema LTspice, a blocchi funzionali
  riv_*.asy                  simboli LTspice usati dallo schema

Ogni componente della scheda compare con il suo riferimento KiCad e ogni
rete con il suo nome KiCad. Nello schema .asc ogni pin e' collegato alla sua
rete con un'etichetta (FLAG) col nome della rete KiCad: due pin con la stessa
etichetta sono collegati.

    python gen_ltspice.py           # genera
    python verifica_ltspice.py      # rilegge l'.asc e lo confronta con la .cir,
                                    # poi simula con ngspice e controlla i numeri
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "hardware", "generator"))
from netdata import COMPONENTS, NETS, NC_PINS  # noqa: E402

# nomi delle reti di alimentazione validi in SPICE
NET_RENAME = {"GND": "0", "+5V": "V5", "+3V3": "V3V3", "+3V6": "V3V6"}

# integrati: sottocircuito in riv_cosmici_modelli.lib e disposizione dei pin
# nel simbolo LTspice (sinistra / destra), per numero di pin del package
IC = {
    "LT3461":  ("LT3461",  [("6", "VIN"), ("4", "SHDN"), ("2", "GND")],
                           [("1", "SW"), ("5", "VOUT"), ("3", "FB")]),
    "LT1636":  ("LT1636",  [("3", "+IN"), ("2", "-IN"), ("1", "NULL"), ("5", "NULL")],
                           [("6", "OUT"), ("7", "V+"), ("4", "V-"), ("8", "SHDN")]),
    "MAX961":  ("MAX961",  [("1", "IN+"), ("2", "IN-"), ("4", "LE"), ("3", "SHDN")],
                           [("6", "Q"), ("7", "QB"), ("8", "VCC"), ("5", "GND")]),
    "MCP1402": ("MCP1402", [("3", "IN"), ("2", "VDD")],
                           [("5", "OUT"), ("1", "GND"), ("4", "GND")]),
    "LP2985":  ("LP2985",  [("1", "VIN"), ("3", "ON"), ("2", "GND")],
                           [("5", "VOUT"), ("4", "BYP")]),
    "MCP1825": ("MCP1825", [("1", "VIN"), ("2", "GND")],
                           [("3", "VOUT"), ("4", "TAB")]),
    "TLC555":  ("TLC555",  [("2", "TRIG"), ("6", "THRES"), ("7", "DISCH"), ("4", "RESET")],
                           [("3", "OUT"), ("8", "VCC"), ("5", "CTRL"), ("1", "GND")]),
    "LVC1G17": ("LVC1G17", [("2", "A"), ("1", "NC")],
                           [("4", "Y"), ("5", "VCC"), ("3", "GND")]),
}

# blocchi funzionali (ordine nella netlist e posizione nello schema .asc)
BLOCKS = [
    ("PWR",   "Alimentazione: J3 5 V -> U6 3,3 V (+ disaccoppiamenti)",
     ["VJ3", "RJ3_CAVO", "U6", "CF8", "CF9", "C22", "CF1", "CF2", "CF3", "CF5"]),
    ("BOOST", "Boost LT3461 -> VOUT40 (~41,7 V)",
     ["U1", "L1", "RL1_DCR", "C2", "C3", "R3", "C1", "R1", "R2", "R22"]),
    ("BIAS",  "Regolatore bias SiPM 38,4 V (LT1636, V1)",
     ["U7", "CF7", "D1", "V1", "R7", "R6", "C4", "U8", "R4", "R5", "R8", "C6"]),
    ("FE",    "SiPM + amplificatore (Q1 BFR93A, Q2 MMBTH81)",
     ["SIPM", "R10", "C7", "R9", "R11", "Q1", "R12", "R13", "Q2", "R14", "C11", "R15"]),
    ("TH",    "Soglia: U5 3,6 V, V2, R17-R19",
     ["U5", "CF4", "R19", "V2", "R18", "R17"]),
    ("CMP",   "Comparatore MAX961 + latch C9/R16",
     ["U3", "R16", "C9"]),
    ("OUT",   "Uscite: MCP1402 -> J2 TTL 5 V ; 74LVC1G17 -> J4 3,3 V -> Raspberry Pi",
     ["U4", "RLJ2", "CLJ2", "U9", "CF10", "R23", "CCAVO", "RSER_RPI", "CRPI", "RRPI"]),
    ("LED",   "Monostabile TLC555 + LED (~11 ms)",
     ["U2", "R20", "C21", "CF6", "R21", "D3"]),
]


def spice_value(v):
    """'1k2'->'1.2k', '560R'->'560', '100n 100V'->'100n', '22pF'->'22p'"""
    v = v.split()[0]
    m = re.fullmatch(r"(\d+)([kKmMR])(\d+)", v)          # 1k2, 4R7
    if m:
        a, u, b = m.groups()
        u = "" if u == "R" else u
        return f"{a}.{b}{u}"
    v = re.sub(r"R$", "", v)                              # 560R -> 560
    v = re.sub(r"(?<=[pnumkM])[FH]$", "", v)              # 22pF -> 22p, 47uH -> 47u
    return v


class El:
    """un elemento SPICE: nome, prefisso, nodi (in ordine SPICE), valore,
    parametri extra, simbolo LTspice e nomi dei pin (in ordine SPICE)"""
    def __init__(self, name, prim, nodes, value, sym, pins, line="", note=""):
        self.name, self.prim, self.nodes = name, prim, nodes
        self.value, self.sym, self.pins, self.line, self.note = value, sym, pins, line, note

    def spice(self):
        nm = self.name if self.name[0].upper() == self.prim else self.prim + self.name
        return " ".join([nm] + self.nodes + [self.value] + ([self.line] if self.line else []))


def build_elements():
    pn = {}
    for net, pins in NETS.items():
        for ref, p in pins:
            pn[(ref, str(p))] = NET_RENAME.get(net, net)

    def n(ref, p):
        p = str(p)
        if (ref, p) in pn:
            return pn[(ref, p)]
        assert (ref, p) in NC_PINS, f"pin {ref}.{p} senza rete"
        return f"NC_{ref}_{p}"

    E = {}
    conn = {}
    for ref, (kind, value, _fp, extra) in COMPONENTS.items():
        if kind == "R":
            E[ref] = El(ref, "R", [n(ref, 1), n(ref, 2)], spice_value(value), "riv_R", ["1", "2"])
        elif kind == "C":
            E[ref] = El(ref, "C", [n(ref, 1), n(ref, 2)], spice_value(value), "riv_C", ["1", "2"])
        elif kind == "L":
            # resistenza serie esplicita (Rser= non e' portabile su ngspice)
            E[ref] = El(ref, "L", [n(ref, 1), f"{ref}_DCR"], spice_value(value), "riv_L", ["1", "2"])
            E[f"R{ref}_DCR"] = El(f"R{ref}_DCR", "R", [f"{ref}_DCR", n(ref, 2)], "0.5",
                                  "riv_R", ["1", "2"], note="DCR di L1")
        elif kind in ("D", "LED"):      # KiCad: 1 = K, 2 = A ; SPICE: A K
            E[ref] = El(ref, "D", [n(ref, 2), n(ref, 1)],
                        "1N4148" if kind == "D" else "LED_ROSSO",
                        "riv_D" if kind == "D" else "riv_LED", ["A", "K"])
        elif kind in ("NPN", "PNP"):    # KiCad SOT-23: 1 = B, 2 = E, 3 = C ; SPICE: C B E
            E[ref] = El(ref, "Q", [n(ref, 3), n(ref, 1), n(ref, 2)], value,
                        "riv_" + kind, ["C", "B", "E"])
        elif kind == "POT":
            pos = "{V1_POS}" if ref == "V1" else "{V2_POS}"
            E[ref] = El(ref, "X", [n(ref, 1), n(ref, 2), n(ref, 3)], "POT", "riv_POT",
                        ["1", "2", "3"], line=f"R=10k POS={pos}")
        elif kind in IC:
            sub, left, right = IC[kind]
            npin = len(left) + len(right)
            E[ref] = El(ref, "X", [n(ref, p) for p in range(1, npin + 1)], sub,
                        "riv_" + sub, [str(p) for p in range(1, npin + 1)])
        elif kind == "CONN2":
            conn[ref] = (n(ref, 1), n(ref, 2))
        else:
            raise ValueError(kind)

    # ---- mondo esterno ai connettori (non sulla scheda)
    a, b = conn["J3"]       # 1 = GND, 2 = +5V
    E["VJ3"] = El("VJ3", "V", ["VIN_EXT", a], "PWL(0 0 100u {VIN})", "riv_V", ["+", "-"],
                  note="J3: alimentatore esterno 5 V, rampa 100 us")
    E["RJ3_CAVO"] = El("RJ3_CAVO", "R", ["VIN_EXT", b], "0.05", "riv_R", ["1", "2"],
                       note="cavo di alimentazione")
    a, b = conn["J1"]       # 1 = anodo/segnale, 2 = catodo/bias (calza)
    E["SIPM"] = El("SIPM", "X", [a, b], "SIPM", "riv_SIPM", ["A", "K"],
                   line="NPE1={NPE_EV1} T1={T_EV1} NPE2={NPE_EV2} T2={T_EV2} "
                        "NPE3={NPE_EV3} T3={T_EV3} NPE4={NPE_EV4} T4={T_EV4} CSIPM={CSIPM}",
                   note="J1: SiPM AFBR-S4N22P014M fuori scheda (cavo Fileca)")
    a, b = conn["J2"]
    E["RLJ2"] = El("RLJ2", "R", [a, b], "10k", "riv_R", ["1", "2"], note="J2: carico TTL")
    E["CLJ2"] = El("CLJ2", "C", [a, b], "30p", "riv_C", ["1", "2"], note="J2: carico TTL")
    a, b = conn["J4"]
    E["CCAVO"] = El("CCAVO", "C", [a, b], "100p", "riv_C", ["1", "2"],
                    note="J4: cavo coassiale ~1 m")
    E["RSER_RPI"] = El("RSER_RPI", "R", [a, "RPI_GPIO"], "330", "riv_R", ["1", "2"],
                       note="330 ohm in serie lato Raspberry Pi (consigliato)")
    E["CRPI"] = El("CRPI", "C", ["RPI_GPIO", b], "5p", "riv_C", ["1", "2"], note="ingresso GPIO")
    E["RRPI"] = El("RRPI", "R", ["RPI_GPIO", b], "50k", "riv_R", ["1", "2"],
                   note="pull-down interno GPIO")
    listed = [r for _k, _t, refs in BLOCKS for r in refs]
    missing = set(E) - set(listed)
    extra = set(listed) - set(E)
    assert not missing and not extra, (missing, extra)
    return E


HEADER = """\
* =====================================================================
* riv_cosmici_completo.cir - SCHEDA COMPLETA "Riv. Cosmici 2024"
* (INFN sez. Torino, S. Gallian - "Amplif, alim, soglie", rev. A)
* + buffer d'uscita 3,3 V verso Raspberry Pi.
*
* GENERATO da gen_ltspice.py a partire da hardware/generator/netdata.py,
* lo stesso modello dati dello schema KiCad: riferimenti e nomi di rete
* sono quelli dello schema (GND = 0, +5V = V5, +3V3 = V3V3, +3V6 = V3V6).
* Non modificare a mano: cambia netdata.py e rigenera.
*
* LTspice : apri riv_cosmici_completo.asc (schema) oppure questo file
*           (File > Open, tipo file: Netlists) e premi Run. Modelli e
*           simboli .asy devono stare nella stessa cartella.
* ngspice : ngspice -b riv_cosmici_completo.cir
*
* Cosa succede nel transitorio (30 ms):
*   0-0,1 ms  la +5V sale (J3), partono i regolatori 3,3 V e 3,6 V
*   0-3 ms    il boost LT3461 carica VOUT40 (~41,7 V), l'LT1636 porta
*             il bias del SiPM (rete BIAS) a ~38,4 V
*   10 ms     EV1..EV4: un muone grande, un dark count (1 p.e., sotto soglia),
*             un muone medio, un muone ravvicinato al terzo
*   Uscite:   CMP_Q/CMP_QB (3,3 V), TTL_OUT (5 V, J2), BUF_OUT (J4 ->
*             GPIO Raspberry Pi, 0-3,3 V), LED D3 acceso ~11 ms dal 555
* =====================================================================
.include riv_cosmici_modelli.lib

* ----------------------------- parametri -----------------------------
.param VIN=5
* V1 (regolazione tensione SiPM): frazione di pista dal pin 1 (lato R7).
*   POS piu' alto = cursore verso D1 = bias piu' alto. 0,76 -> ~38,4 V
.param V1_POS=0.76
* V2 (soglia): frazione di pista dal pin 1 (lato R19, alto) al cursore.
*   soglia ~ 1,286 V * (1 - V2_POS).  0,92 -> ~100 mV (~3 p.e.)
.param V2_POS=0.92
* capacita' terminale del SiPM (dal datasheet del sensore usato): divide la
* carica con l'ingresso dell'amplificatore e cambia i mV per fotoelettrone
.param CSIPM=100p
* eventi nel SiPM: istante [s] e numero di fotoelettroni (0,5 pC/p.e.)
.param T_EV1=10m     NPE_EV1=250
.param T_EV2=10.01m  NPE_EV2=1
.param T_EV3=10.02m  NPE_EV3=40
.param T_EV4=10.0215m NPE_EV4=150
"""

FOOTER = """\
* ----------------------------- analisi -------------------------------
.tran 1u 30m 0 2u
* ---- misure (identiche in LTspice e ngspice; in LTspice i risultati
*      sono in View > SPICE Error Log)
* punto di lavoro a riposo (prima degli eventi)
.meas tran V_3V3     FIND V(V3V3)   AT=9.9m
.meas tran V_3V6     FIND V(V3V6)   AT=9.9m
.meas tran V_REFB    FIND V(VREF_B) AT=9.9m
.meas tran V_OUT40   FIND V(VOUT40) AT=9.9m
.meas tran V_FB      FIND V(FB)     AT=9.9m
.meas tran V_SET     FIND V(VSET)   AT=9.9m
.meas tran V_BIAS    FIND V(BIAS)   AT=9.9m
.meas tran V_TH      FIND V(TH)     AT=9.9m
.meas tran VB_Q1     FIND V(Q1B)    AT=9.9m
.meas tran VC_Q1     FIND V(Q1C)    AT=9.9m
.meas tran VE_Q2     FIND V(Q2E)    AT=9.9m
.meas tran VC_Q2     FIND V(Q2C)    AT=9.9m
.meas tran I_5V      FIND I(VJ3)    AT=9.9m
.meas tran T_BIAS_OK WHEN V(BIAS)=38 RISE=1
* evento 1: muone 250 p.e.
.meas tran PK_EV1    MAX  V(CMP_IN)  FROM=9.999m  TO=10.003m
.meas tran Q_EV1     MAX  V(CMP_Q)   FROM=9.999m  TO=10.003m
.meas tran TTL_EV1   MAX  V(TTL_OUT) FROM=9.999m  TO=10.003m
.meas tran RPI_EV1   MAX  V(RPI_GPIO)  FROM=9.999m  TO=10.003m
.meas tran W_Q_EV1   TRIG V(CMP_Q)   VAL=1.65 RISE=1 TD=9.99m TARG V(CMP_Q)   VAL=1.65 FALL=1 TD=9.99m
.meas tran W_TTL_EV1 TRIG V(TTL_OUT) VAL=2.5  RISE=1 TD=9.99m TARG V(TTL_OUT) VAL=2.5  FALL=1 TD=9.99m
.meas tran W_RPI_EV1 TRIG V(RPI_GPIO)  VAL=1.65 RISE=1 TD=9.99m TARG V(RPI_GPIO)  VAL=1.65  FALL=1 TD=9.99m
.meas tran D_RPI_EV1 TRIG V(CMP_Q)   VAL=1.65 RISE=1 TD=9.99m TARG V(RPI_GPIO)  VAL=1.65  RISE=1 TD=9.99m
* evento 2: dark count 1 p.e. (deve restare sotto soglia)
.meas tran PK_EV2    MAX  V(CMP_IN)  FROM=10.009m TO=10.013m
.meas tran Q_EV2     MAX  V(CMP_Q)   FROM=10.009m TO=10.013m
* evento 3: muone piccolo 40 p.e.
.meas tran PK_EV3    MAX  V(CMP_IN)  FROM=10.019m TO=10.0213m
.meas tran Q_EV3     MAX  V(CMP_Q)   FROM=10.019m TO=10.0213m
.meas tran RPI_EV3   MAX  V(RPI_GPIO)  FROM=10.019m TO=10.0215m
.meas tran W_Q_EV3   TRIG V(CMP_Q)   VAL=1.65 RISE=1 TD=10.019m TARG V(CMP_Q)  VAL=1.65 FALL=1 TD=10.019m
.meas tran W_RPI_EV3 TRIG V(RPI_GPIO)  VAL=1.65  RISE=1 TD=10.019m TARG V(RPI_GPIO) VAL=1.65 FALL=1 TD=10.019m
* evento 4: muone 150 p.e. a 1,5 us dal precedente
.meas tran Q_EV4     MAX  V(CMP_Q)   FROM=10.0215m TO=10.0225m
.meas tran RPI_EV4   MAX  V(RPI_GPIO)  FROM=10.0215m TO=10.0225m
* monostabile 555 + LED
.meas tran VA_LED    MAX  V(LED_A)  FROM=10m TO=12m
.meas tran VK_LED    MAX  V(LED_K)  FROM=10m TO=12m
.meas tran T_LED     TRIG V(LED_A) VAL=1.65 RISE=1 TD=9.99m TARG V(LED_A) VAL=1.65 FALL=1 TD=9.99m
.meas tran V_LED_OFF FIND V(LED_A)  AT=29m
.end
"""



# =============================== netlist .cir ===============================
def write_cir(E, fn):
    L = [HEADER]
    for key, title, refs in BLOCKS:
        L.append(f"* ===================== {title} =====================")
        for r in refs:
            e = E[r]
            if e.note:
                L.append(f"* {e.note}")
            L.append(e.spice())
    L.append(FOOTER)
    with open(fn, "w", newline="\r\n") as f:     # CRLF: piace a LTspice su Windows
        f.write("\n".join(L) + "\n")
    print("scritto", fn)


# =============================== simboli .asy ===============================
# geometria dei simboli in unita' LTspice (griglia 16). Ogni simbolo:
# (pins: [(nome, x, y, lato)], grafica: [righe .asy], larghezza, altezza)
def _two_pin(name, prefix, body, h=96):
    pins = [("1", 16, 0, "TOP"), ("2", 16, h, "BOTTOM")]
    return pins, body, 32, h


SYMBOLS = {}


def _sym(name, prefix, pins, graphics, w, h, descr):
    SYMBOLS[name] = dict(prefix=prefix, pins=pins, gfx=graphics, w=w, h=h, descr=descr)


_sym("riv_R", "R", [("1", 16, 0, "TOP"), ("2", 16, 96, "BOTTOM")],
     ["LINE Normal 16 0 16 16", "LINE Normal 16 80 16 96",
      "LINE Normal 16 16 4 22", "LINE Normal 4 22 28 34", "LINE Normal 28 34 4 46",
      "LINE Normal 4 46 28 58", "LINE Normal 28 58 4 70", "LINE Normal 4 70 16 80"],
     32, 96, "resistore")
_sym("riv_C", "C", [("1", 16, 0, "TOP"), ("2", 16, 64, "BOTTOM")],
     ["LINE Normal 16 0 16 24", "LINE Normal 16 40 16 64",
      "LINE Normal 0 24 32 24", "LINE Normal 0 40 32 40"], 32, 64, "condensatore")
_sym("riv_L", "L", [("1", 16, 0, "TOP"), ("2", 16, 96, "BOTTOM")],
     ["LINE Normal 16 0 16 16", "LINE Normal 16 80 16 96",
      "ARC Normal 0 16 32 32 16 32 16 16", "ARC Normal 0 32 32 48 16 48 16 32",
      "ARC Normal 0 48 32 64 16 64 16 48", "ARC Normal 0 64 32 80 16 80 16 64"],
     32, 96, "induttore")
_sym("riv_D", "D", [("A", 16, 0, "TOP"), ("K", 16, 64, "BOTTOM")],
     ["LINE Normal 16 0 16 24", "LINE Normal 16 40 16 64",
      "LINE Normal 0 24 32 24", "LINE Normal 0 24 16 40", "LINE Normal 32 24 16 40",
      "LINE Normal 0 40 32 40"], 32, 64, "diodo (A in alto, K in basso)")
_sym("riv_LED", "D", [("A", 16, 0, "TOP"), ("K", 16, 64, "BOTTOM")],
     ["LINE Normal 16 0 16 24", "LINE Normal 16 40 16 64",
      "LINE Normal 0 24 32 24", "LINE Normal 0 24 16 40", "LINE Normal 32 24 16 40",
      "LINE Normal 0 40 32 40", "LINE Normal 36 24 48 12", "LINE Normal 36 34 48 22",
      "LINE Normal 48 12 42 14", "LINE Normal 48 22 42 24"], 48, 64, "LED")
_sym("riv_NPN", "Q", [("C", 64, 0, "TOP"), ("B", 0, 48, "LEFT"), ("E", 64, 96, "BOTTOM")],
     ["LINE Normal 0 48 32 48", "LINE Normal 32 24 32 72",
      "LINE Normal 32 40 64 16", "LINE Normal 64 16 64 0",
      "LINE Normal 32 56 64 80", "LINE Normal 64 80 64 96",
      "LINE Normal 64 80 52 78", "LINE Normal 64 80 58 70",
      "CIRCLE Normal 12 16 76 80"], 64, 96, "NPN (C alto, B sx, E basso)")
_sym("riv_PNP", "Q", [("C", 64, 96, "BOTTOM"), ("B", 0, 48, "LEFT"), ("E", 64, 0, "TOP")],
     ["LINE Normal 0 48 32 48", "LINE Normal 32 24 32 72",
      "LINE Normal 32 40 64 16", "LINE Normal 64 16 64 0",
      "LINE Normal 32 56 64 80", "LINE Normal 64 80 64 96",
      "LINE Normal 32 40 42 40", "LINE Normal 32 40 38 30",
      "CIRCLE Normal 12 16 76 80"], 64, 96, "PNP (E alto, B sx, C basso)")
_sym("riv_V", "V", [("+", 16, 0, "TOP"), ("-", 16, 96, "BOTTOM")],
     ["CIRCLE Normal -16 16 48 80", "LINE Normal 16 0 16 16", "LINE Normal 16 80 16 96",
      "LINE Normal 8 36 24 36", "LINE Normal 16 28 16 44", "LINE Normal 8 62 24 62"],
     48, 96, "generatore di tensione")
_sym("riv_POT", "X", [("1", 16, 0, "TOP"), ("2", 64, 48, "RIGHT"), ("3", 16, 96, "BOTTOM")],
     ["LINE Normal 16 0 16 16", "LINE Normal 16 80 16 96",
      "RECTANGLE Normal 4 16 28 80", "LINE Normal 64 48 30 48",
      "LINE Normal 30 48 38 42", "LINE Normal 30 48 38 54"], 64, 96,
     "trimmer 3296W (1 - cursore 2 - 3)")
_sym("riv_SIPM", "X", [("A", 16, 96, "BOTTOM"), ("K", 16, 0, "TOP")],
     ["LINE Normal 16 0 16 40", "LINE Normal 16 56 16 96",
      "LINE Normal 0 56 32 56", "LINE Normal 0 56 16 40", "LINE Normal 32 56 16 40",
      "LINE Normal 0 40 32 40", "RECTANGLE Normal -8 24 40 72",
      "LINE Normal 48 20 36 32", "LINE Normal 56 28 44 40"], 48, 96,
     "SiPM: K in alto (bias), A in basso (segnale)")
for _kind, (_sub, _left, _right) in IC.items():
    _n = max(len(_left), len(_right))
    _w, _h = 128, 32 * (_n + 1)
    _pins = [(p, 0, 32 * (i + 1), "LEFT") for i, (p, _nm) in enumerate(_left)]
    _pins += [(p, _w + 64, 32 * (i + 1), "RIGHT") for i, (p, _nm) in enumerate(_right)]
    _names = {p: nm for p, nm in _left + _right}
    _g = [f"RECTANGLE Normal 32 0 {_w + 32} {_h}"]
    _g += [f"LINE Normal 0 {32 * (i + 1)} 32 {32 * (i + 1)}" for i in range(len(_left))]
    _g += [f"LINE Normal {_w + 32} {32 * (i + 1)} {_w + 64} {32 * (i + 1)}"
           for i in range(len(_right))]
    _g += [f"TEXT {(_w + 64) // 2} {_h // 2} Center 1 {_sub}"]
    _sym("riv_" + _sub, "X", _pins, _g, _w + 64, _h, f"{_sub} (pin = numeri del package)")
    SYMBOLS["riv_" + _sub]["pinnames"] = _names


def write_asy(dirname):
    for name, s in SYMBOLS.items():
        L = ["Version 4", "SymbolType CELL"]
        L += s["gfx"]
        L += ["WINDOW 0 %d -8 Left 2" % (s["w"] + 8), "WINDOW 3 %d 16 Left 2" % (s["w"] + 8)]
        L += [f"SYMATTR Prefix {s['prefix']}", f"SYMATTR Description {s['descr']}"]
        names = s.get("pinnames", {})
        el_pins = PIN_ORDER[name]
        for pname, x, y, side in s["pins"]:
            label = names.get(pname, pname)
            # sui circuiti integrati il nome del pin e' scritto dentro il riquadro
            L.append(f"PIN {x} {y} {side} 40" if names else f"PIN {x} {y} NONE 0")
            L.append(f"PINATTR PinName {label if names else pname}")
            L.append(f"PINATTR SpiceOrder {el_pins.index(pname) + 1}")
        with open(os.path.join(dirname, name + ".asy"), "w", newline="\r\n") as f:
            f.write("\n".join(L) + "\n")


# ordine SPICE dei pin per ogni simbolo (coincide con El.pins)
PIN_ORDER = {
    "riv_R": ["1", "2"], "riv_C": ["1", "2"], "riv_L": ["1", "2"],
    "riv_D": ["A", "K"], "riv_LED": ["A", "K"], "riv_V": ["+", "-"],
    "riv_NPN": ["C", "B", "E"], "riv_PNP": ["C", "B", "E"],
    "riv_POT": ["1", "2", "3"], "riv_SIPM": ["A", "K"],
}
for _kind, (_sub, _left, _right) in IC.items():
    PIN_ORDER["riv_" + _sub] = [str(p) for p in range(1, len(_left) + len(_right) + 1)]


# =============================== schema .asc ===============================
STUB = 32          # lunghezza del filo tra pin ed etichetta
CELL_GAP = 192     # spazio orizzontale tra componenti (per le etichette)
BLOCK_W = 1600     # larghezza di un blocco prima di andare a capo


def _snap(v):
    return int(round(v / 16.0)) * 16


def layout(E):
    """-> lista di (El, x, y) e titoli dei blocchi; due colonne di blocchi"""
    placed, titles = [], []
    col_x = [0, BLOCK_W + 640]
    col_y = [0, 0]
    for bi, (key, title, refs) in enumerate(BLOCKS):
        c = 0 if col_y[0] <= col_y[1] else 1
        bx, by = col_x[c], col_y[c]
        titles.append((bx, by, title))
        x, y, row_h = bx, by + 112, 0
        for r in refs:
            e = E[r]
            s = SYMBOLS[e.sym]
            if x > bx and x + s["w"] > bx + BLOCK_W:
                x, y, row_h = bx, y + row_h + 192, 0
            placed.append((e, _snap(x + 96), _snap(y)))
            x += s["w"] + CELL_GAP + 96
            row_h = max(row_h, s["h"])
        col_y[c] = y + row_h + 320
    return placed, titles


def pin_points(e, x, y):
    """-> {nome_pin: (px, py, lato)} in coordinate del foglio (simboli R0)"""
    return {p: (x + px, y + py, side) for p, px, py, side in SYMBOLS[e.sym]["pins"]}


def write_asc(E, fn):
    placed, titles = layout(E)
    W = max(x for _e, x, _y in placed) + 800
    H = max(y for _e, _x, y in placed) + 600
    L = ["Version 4", f"SHEET 1 {W} {H + 2400}"]
    wires, flags = [], []
    for e, x, y in placed:
        pp = pin_points(e, x, y)
        for pname, net in zip(e.pins, e.nodes):
            px, py, side = pp[pname]
            dx, dy = {"TOP": (0, -STUB), "BOTTOM": (0, STUB),
                      "LEFT": (-STUB, 0), "RIGHT": (STUB, 0)}[side]
            wires.append((px, py, px + dx, py + dy))
            flags.append((px + dx, py + dy, net))
    for x1, y1, x2, y2 in wires:
        L.append(f"WIRE {x1} {y1} {x2} {y2}")
    for x, y, net in flags:
        L.append(f"FLAG {x} {y} {net}")
    for e, x, y in placed:
        L.append(f"SYMBOL {e.sym} {x} {y} R0")
        L.append(f"SYMATTR InstName {e.name}")
        L.append(f"SYMATTR Value {e.value}")
        if e.line:
            L.append(f"SYMATTR SpiceLine {e.line}")
    for bx, by, title in titles:
        L.append(f"TEXT {bx} {by} Left 3 ;{title}")
    # direttive SPICE (una per riga, sotto lo schema)
    ty = H + 64
    L.append(f"TEXT 0 {ty} Left 3 ;Riv. Cosmici 2024 (INFN To) - scheda completa. "
             "Generato da gen_ltspice.py: non modificare a mano.")
    ty += 64
    for ln in (HEADER + FOOTER).splitlines():
        ln = ln.rstrip()
        if not ln:
            continue
        if ln.startswith("*"):
            L.append(f"TEXT 0 {ty} Left 2 ;{ln[1:].strip()}")
        elif ln.startswith("."):
            if ln.lower() == ".end":
                continue
            L.append(f"TEXT 0 {ty} Left 2 !{ln}")
        ty += 32
    with open(fn, "w", newline="\r\n") as f:
        f.write("\n".join(L) + "\n")
    print("scritto", fn, f"({len(placed)} simboli, {len(flags)} etichette)")


if __name__ == "__main__":
    E = build_elements()
    write_cir(E, os.path.join(HERE, "riv_cosmici_completo.cir"))
    write_asy(HERE)
    write_asc(E, os.path.join(HERE, "riv_cosmici_completo.asc"))
