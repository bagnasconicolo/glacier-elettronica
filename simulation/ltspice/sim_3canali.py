# -*- coding: utf-8 -*-
"""Simulazione della SCHEDA A 3 CANALI intera (ngspice o LTspice).

Netlist generata dal modello dati della scheda a 3 canali
(hardware/generator/netdata3.py, lo stesso del PCB): tre canali completi,
alta tensione, riferimenti e 3,3 V in comune, coincidenza AND (U10 74LVC1G11),
monitor delle tensioni (partitori + ingressi dell'MCP3424).

Domande a cui risponde:
  1. alta tensione e riferimenti condivisi reggono i tre bias? (valori a riposo)
  2. un muone in UN canale disturba gli altri due? (picchi all'ingresso dei
     comparatori dei canali non colpiti, confrontati con la soglia)
  3. la coincidenza scatta solo con tre canali, anche con impulsi piccoli e
     sfasati di qualche ns? quanto dura l'impulso AND?

Eventi (ogni SiPM ha fino a 4 eventi, T in ms, NPE = fotoelettroni):
  10,000  muone attraverso le tre barre: 250 / 150 / 80 p.e., ritardi 0 / 2 / 4 ns
  10,020  muone solo nel canale 1 (250 p.e.)            -> AND non deve scattare
  10,040  muone nei canali 1 e 2 (150 / 150 p.e.)        -> AND non deve scattare
  10,060  tre canali, impulsi piccoli (25 p.e.) e sfasati di 0 / 5 / 10 ns -> AND

    python sim_3canali.py          -> sim_3canali.cir + sim_3canali.txt
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "hardware", "generator"))
import netdata3 as N                                    # noqa: E402
from gen_ltspice import IC, spice_value                 # noqa: E402
from ngspice_run import run                             # noqa: E402

IC = dict(IC)
IC["LVC1G11"] = ("LVC1G11", [], [str(p) for p in range(1, 7)])

RENAME = {"GND": "0", "+5V": "V5", "+3V3": "V3V3", "+3V6": "V3V6"}
EV = {  # canale: [(T ms, NPE), ...]
    1: [(10.000, 250), (10.020, 250), (10.040, 150), (10.060, 25)],
    2: [(10.000002, 150), (10.020, 0), (10.040, 150), (10.060005, 25)],
    3: [(10.000004, 80), (10.020, 0), (10.040, 0), (10.060010, 25)],
}
WIN = [(9.999, 10.0045), (10.019, 10.0245), (10.039, 10.0445), (10.059, 10.0645)]


def netlist():
    pn = {}
    for net, pins in N.NETS.items():
        for ref, p in pins:
            pn[(ref, str(p))] = RENAME.get(net, net)

    def n(ref, p):
        return pn.get((ref, str(p)), f"NC_{ref}_{p}")

    L = []
    for ref, (kind, value, _fp, _e) in N.COMPONENTS.items():
        if kind in ("R", "C"):
            name = ref if ref[0] == kind else f"{kind}_{ref}"
            L.append(f"{name} {n(ref, 1)} {n(ref, 2)} {spice_value(value)}")
        elif kind == "L":
            L += [f"{ref} {n(ref, 1)} {ref}_DCR {spice_value(value)}",
                  f"R{ref}_DCR {ref}_DCR {n(ref, 2)} 0.5"]
        elif kind in ("D", "LED"):
            L.append(f"D{ref} {n(ref, 2)} {n(ref, 1)} {'1N4148' if kind == 'D' else 'LED_ROSSO'}")
        elif kind in ("NPN", "PNP"):
            L.append(f"Q{ref} {n(ref, 3)} {n(ref, 1)} {n(ref, 2)} {value}")
        elif kind == "POT":
            pos = "{V1_POS}" if ref.endswith("01") else "{V2_POS}"   # V101 = V1 del canale 1
            L.append(f"X{ref} {n(ref, 1)} {n(ref, 2)} {n(ref, 3)} POT R=10k POS={pos}")
        elif kind in IC:
            sub, left, right = IC[kind]
            npin = len(left) + len(right)
            L.append(f"X{ref} " + " ".join(n(ref, p) for p in range(1, npin + 1)) + f" {sub}")
        elif kind == "MCP3424":
            # ingressi differenziali: ~2,25 Mohm durante la conversione; il resto scollegato
            for a, b in ((1, 2), (3, 4), (11, 12), (13, 14)):
                L.append(f"R{ref}_IN{a} {n(ref, a)} {n(ref, b)} 2.25Meg")
            for p in (5, 6, 7, 8, 9, 10):
                L.append(f"R{ref}_P{p} {n(ref, p)} 0 1G")
        elif kind in ("TP", "MH", "CONN3"):
            continue
        elif kind == "CONN2":
            a, b = n(ref, 1), n(ref, 2)
            if ref == "J3":           # 1 = GND, 2 = +5V
                L += [f"VJ3 VIN_EXT {a} PWL(0 0 100u {{VIN}})", f"RJ3_CAVO VIN_EXT {b} 0.05"]
            elif ref.startswith("JP"):  # ponticello chiuso: canale incluso nella coincidenza
                L.append(f"R{ref} {a} {b} 0.01")
            elif ref in ("J101", "J201", "J301"):
                c = int(ref[1])
                ev = " ".join(f"NPE{k + 1}={npe} T{k + 1}={t}m" for k, (t, npe) in enumerate(EV[c]))
                L.append(f"XSIPM{c} {a} {b} SIPM {ev} CSIPM={{CSIPM}} QPE={{QPE}} TAU={{TAUSIPM}}")
            else:                     # uscite LEMO (J104/J204/J304, J5): cavo + Raspberry
                L += [f"CCAVO_{ref} {a} {b} 100p", f"RSER_{ref} {a} GPIO_{ref} 330",
                      f"CRPI_{ref} GPIO_{ref} {b} 5p", f"RRPI_{ref} GPIO_{ref} {b} 50k"]
        else:
            raise ValueError((ref, kind))
    return L


def measures():
    M = [".meas tran V_3V3 FIND V(V3V3) AT=9.9m", ".meas tran V_3V6 FIND V(V3V6) AT=9.9m",
         ".meas tran V_REFB FIND V(VREF_B) AT=9.9m", ".meas tran V_OUT40 FIND V(VOUT40) AT=9.9m",
         ".meas tran I_5V FIND I(VJ3) AT=9.9m"]
    for c in (1, 2, 3):
        M += [f".meas tran V_BIAS{c} FIND V(BIAS{c}) AT=9.9m",
              f".meas tran V_TH{c} FIND V(TH{c}) AT=9.9m",
              f".meas tran CMP0_{c} FIND V(CMP_IN{c}) AT=9.99m",
              f".meas tran DBIAS{c} PP V(BIAS{c}) FROM=9.999m TO=10.07m"]
        for k, (a, b) in enumerate(WIN, 1):
            M += [f".meas tran PK{k}_{c} MAX V(CMP_IN{c}) FROM={a}m TO={b}m",
                  f".meas tran MN{k}_{c} MIN V(CMP_IN{c}) FROM={a}m TO={b}m",
                  f".meas tran Q{k}_{c} MAX V(CMP_Q{c}) FROM={a}m TO={b}m",
                  f".meas tran G{k}_{c} MAX V(GPIO_J{c}04) FROM={a}m TO={b}m"]
    for k, (a, b) in enumerate(WIN, 1):
        M += [f".meas tran AND{k} MAX V(GPIO_J5) FROM={a}m TO={b}m",
              f".meas tran WAND{k} TRIG V(GPIO_J5) VAL=1.65 RISE=1 TD={a}m "
              f"TARG V(GPIO_J5) VAL=1.65 FALL=1 TD={a}m",
              f".meas tran WQ{k}_1 TRIG V(CMP_Q1) VAL=1.65 RISE=1 TD={a}m "
              f"TARG V(CMP_Q1) VAL=1.65 FALL=1 TD={a}m",
              f".meas tran DAND{k} TRIG V(CMP_Q1) VAL=1.65 RISE=1 TD={a}m "
              f"TARG V(GPIO_J5) VAL=1.65 RISE=1 TD={a}m"]
    return M


def write(fn):
    txt = ["* sim_3canali.cir - scheda a 3 canali intera (GENERATO da sim_3canali.py)",
           ".include riv_cosmici_modelli.lib",
           ".param VIN=5 V1_POS=0.76 V2_POS=0.92",
           ".param VBD=32.5 G12=7.3Meg VOV=5.94",
           ".param QPE={1.602e-19*G12*VOV/12}",
           ".param CSIPM=160p TAUSIPM=55n"]
    txt += netlist() + measures()
    txt += [".tran 1u 10.07m 0 2u", ".end", ""]
    open(fn, "w").write("\n".join(txt))


def main():
    cir = os.path.join(HERE, "sim_3canali.cir")
    write(cir)
    m, _w = run(cir, timeout=7200)
    g = lambda k: m.get(k.lower(), float("nan"))
    out = []
    p = out.append
    p("SCHEDA A 3 CANALI - simulazione ngspice (sim_3canali.py)\n")
    p("1. Alimentazioni condivise a riposo (t = 9,9 ms)")
    p(f"   +3V3 {g('V_3V3'):.3f} V   +3V6 {g('V_3V6'):.3f} V   VREF_B {g('V_REFB'):.3f} V   "
      f"VOUT40 {g('V_OUT40'):.2f} V   corrente da 5 V {abs(g('I_5V')) * 1e3:.1f} mA")
    for c in (1, 2, 3):
        p(f"   canale {c}: BIAS {g(f'V_BIAS{c}'):.3f} V  soglia TH {g(f'V_TH{c}') * 1e3:.1f} mV  "
          f"ondulazione del bias durante gli eventi {g(f'DBIAS{c}') * 1e3:.2f} mV")
    names = ["muone nelle 3 barre (250/150/80 p.e., 0/2/4 ns)",
             "muone SOLO nel canale 1 (250 p.e.)",
             "muone nei canali 1 e 2 (150/150 p.e.)",
             "3 canali, impulsi piccoli (25 p.e.), 0/5/10 ns"]
    for k, nm in enumerate(names, 1):
        p(f"\nEvento {k}: {nm}")
        for c in (1, 2, 3):
            base = g(f"CMP0_{c}")
            p(f"   canale {c}: ingresso comparatore {base * 1e3:6.1f} mV a riposo, max "
              f"{(g(f'PK{k}_{c}') - base) * 1e3:+7.1f} / min {(g(f'MN{k}_{c}') - base) * 1e3:+6.1f} mV "
              f"(soglia {(g(f'V_TH{c}') - base) * 1e3:.0f} mV sopra il riposo) -> uscita "
              f"{g(f'Q{k}_{c}'):.2f} V, al Raspberry {g(f'G{k}_{c}'):.2f} V")
        a = g(f"AND{k}")
        p(f"   AND (J5, al Raspberry): {a:.2f} V" + (
            f", durata {g(f'WAND{k}') * 1e9:.0f} ns, ritardo dal canale 1 {g(f'DAND{k}') * 1e9:.0f} ns"
            if a > 1.65 else " (non scatta)"))
    p("\nDiafonia: per i canali NON colpiti (evento 2: canali 2 e 3; evento 3: canale 3) il"
      "\nmassimo sopra il riposo va confrontato con la soglia: deve restarne molto sotto.")
    s = "\n".join(out)
    print(s)
    open(os.path.join(HERE, "sim_3canali.txt"), "w").write(s + "\n")


if __name__ == "__main__":
    main()
