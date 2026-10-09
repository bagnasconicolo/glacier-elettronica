# -*- coding: utf-8 -*-
"""Il monitor delle tensioni disturba le misure? Confronto in simulazione.

Netlist completa del canale (riv_cosmici_completo.cir) in tre versioni:
  RIF    senza monitor; gli stessi impulsi di corrente dell'ADC sono applicati a un nodo
         scollegato, cosi' il simulatore usa gli stessi passi temporali (le differenze
         tra RIF e le altre sono solo fisiche, non numeriche)
  REALE  partitore 1M/43k su VREG38 + 100 nF; ADC che preleva 4,5 pC ogni 10 us
         (= circa 2,2 Mohm di carico medio, come l'MCP3424 durante una conversione)
  STRESS come REALE ma con prelievi 10 volte piu' frequenti (ogni 1 us)
Si confrontano bias del SiPM e risposta agli eventi.

    python verifica_monitor.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngspice_run import run

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "riv_cosmici_completo.cir")
MEAS = """.meas tran V_REG    FIND V(VREG38) AT=9.9m
.meas tran DV_BIAS  PP   V(BIAS)   FROM=9.99m TO=10.03m
.meas tran V_MON    FIND V(MON)    AT=9.9m
"""


def variant(per, connected):
    node = "MON" if connected else "NC_DUMMY"
    div = ("R_MONT VREG38 MON 1Meg\nR_MONB MON 0 43k\nC_MON MON 0 100n\n" if connected
           else "R_DUMMY NC_DUMMY 0 41k\nC_DUMMY NC_DUMMY 0 100n\nR_MONB MON 0 1\n")
    return (f"* --- monitor delle tensioni (verifica_monitor.py)\n{div}"
            f"I_ADC {node} 0 PULSE(0 0.45m 9.99m 2n 2n 10n {per})\n" + MEAS)


def sim(extra):
    txt = open(BASE, encoding="latin-1").read()
    fn = os.path.join(HERE, "_monitor_tmp.cir")
    open(fn, "w", encoding="latin-1").write(re.sub(r"(?m)^\.tran", extra + ".tran", txt, count=1))
    try:
        return run(fn)[0]
    finally:
        os.remove(fn)


def main():
    r = {"RIF": sim(variant("10u", False)), "REALE": sim(variant("10u", True)),
         "STRESS": sim(variant("1u", True))}
    rows = [("v_bias", "bias SiPM a riposo (V)"), ("dv_bias", "ondulazione bias durante gli eventi (V)"),
            ("pk_ev1", "muone 250 p.e.: picco all'ingresso del comparatore (V)"),
            ("w_rpi_ev1", "muone 250 p.e.: durata impulso al Raspberry (s)"),
            ("pk_ev2", "rumore 1 p.e.: picco (V), deve restare sotto soglia"),
            ("q_ev2", "rumore 1 p.e.: uscita comparatore (V), deve restare 0"),
            ("pk_ev3", "muone 40 p.e.: picco (V)"), ("rpi_ev3", "muone 40 p.e.: uscita al Raspberry (V)"),
            ("rpi_ev4", "muone ravvicinato: uscita al Raspberry (V)")]
    print(f"{'misura':55s} {'RIF':>11s} {'REALE':>11s} {'STRESS':>11s}")
    for k, name in rows:
        print(f"{name:55s} " + " ".join(f"{r[v].get(k, float('nan')):11.5g}" for v in r))
    m, vr = r["REALE"]["v_mon"], r["REALE"]["v_reg"]
    print(f"punto di misura a t = 9,9 ms: {m:.4f} V; a regime sara' {vr * 43 / 1043:.4f} V "
          f"(VREG38 {vr:.3f} V x 43/1043). Il filtro 41 kohm x 100 nF ha tau = 4,1 ms: dopo "
          "l'accensione la lettura e' stabile in ~20 ms (qui la simulazione e' ancora nel transitorio).")

if __name__ == "__main__":
    main()
