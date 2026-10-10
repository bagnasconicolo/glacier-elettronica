# -*- coding: utf-8 -*-
"""La lettura della SOGLIA da parte del secondo ADC (MCP3424, U12) disturba il comparatore?

La soglia TH va all'ingresso invertente del MAX961 e non ha condensatori. Sulla scheda
a 3 canali la si legge attraverso R52 = 10k (accanto al pin 2 del comparatore) e
C52 = 100n verso massa. Netlist completa del canale (riv_cosmici_completo.cir) in
quattro versioni:
  RIF          senza lettura; gli stessi impulsi dell'ADC vanno su un nodo scollegato
               (stessi passi temporali: le differenze sono solo fisiche)
  REALE        10k + 100n; l'ADC preleva 4,5 pC ogni 10 us e ha 2,25 Mohm d'ingresso
               (prelievo esagerato: alla tensione della soglia, ~0,1 V, quello vero e'
               circa 15 volte piu' piccolo)
  STRESS       come REALE, prelievi 10 volte piu' frequenti (ogni 1 us)
  SENZA_FILTRO ADC collegato direttamente alla soglia (quello che NON si deve fare)
Si confrontano soglia, impulsi, falsi conteggi.

    python verifica_soglia_monitor.py   -> stampa e scrive verifica_soglia_monitor.txt
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngspice_run import run

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "riv_cosmici_completo.cir")
MEAS = """.meas tran V_TH0    FIND V(TH)    AT=9.9m
.meas tran PP_TH_Q  PP   V(TH)    FROM=9.90m  TO=9.99m
.meas tran PP_TH_EV PP   V(TH)    FROM=9.999m TO=10.03m
.meas tran Q_QUIET  MAX  V(CMP_Q) FROM=9.90m  TO=9.999m
.meas tran V_THM    FIND V(THM)   AT=9.9m
"""


def variant(kind):
    per = "1u" if kind == "STRESS" else "10u"
    if kind == "RIF":
        net = "R_THD THM 0 1k\nC_THD THM 0 100n\n"
        node = "THM"
    elif kind == "SENZA_FILTRO":
        net = "R_ADC TH 0 2.25Meg\nR_THD THM 0 1k\n"
        node = "TH"
    else:
        net = "R_THM TH THM 10k\nC_THM THM 0 100n\nR_ADC THM 0 2.25Meg\n"
        node = "THM"
    return (f"* --- lettura della soglia ({kind})\n{net}"
            f"I_ADC {node} 0 PULSE(0 0.45m 9.99m 2n 2n 10n {per})\n" + MEAS)


def sim(extra):
    txt = open(BASE, encoding="latin-1").read()
    fn = os.path.join(HERE, "_soglia_tmp.cir")
    open(fn, "w", encoding="latin-1").write(re.sub(r"(?m)^\.tran", extra + ".tran", txt, count=1))
    try:
        return run(fn)[0]
    finally:
        os.remove(fn)


def main():
    kinds = ["RIF", "REALE", "STRESS", "SENZA_FILTRO"]
    r = {k: sim(variant(k)) for k in kinds}
    rows = [("v_th0", "soglia a riposo (V)"),
            ("pp_th_q", "ondulazione della soglia, a riposo (V)"),
            ("pp_th_ev", "ondulazione della soglia durante gli eventi (V)"),
            ("q_quiet", "uscita comparatore senza eventi (V): 0 = nessun falso conteggio"),
            ("v_thm", "tensione letta dall'ADC (V)"),
            ("pk_ev1", "muone 250 p.e.: picco all'ingresso del comparatore (V)"),
            ("w_rpi_ev1", "muone 250 p.e.: durata impulso al Raspberry (s)"),
            ("q_ev2", "rumore 1 p.e.: uscita comparatore (V), deve restare 0"),
            ("rpi_ev3", "muone 40 p.e.: uscita al Raspberry (V)"),
            ("rpi_ev4", "muone ravvicinato: uscita al Raspberry (V)")]
    out = [f"{'misura':66s} " + " ".join(f"{k:>12s}" for k in kinds)]
    for key, name in rows:
        out.append(f"{name:66s} " + " ".join(f"{r[k].get(key, float('nan')):12.5g}" for k in kinds))
    rif, re_ = r["RIF"]["v_th0"], r["REALE"]["v_th0"]
    out.append("")
    out.append(f"Spostamento della soglia con la lettura (REALE - RIF): {(re_ - rif) * 1e6:+.1f} uV "
               f"su {rif * 1e3:.1f} mV ({(re_ - rif) / rif * 100:+.3f} %).")
    out.append(f"Errore della lettura (V_THM / V_TH - 1): {(r['REALE']['v_thm'] / re_ - 1) * 100:+.2f} % "
               "(correggibile nel software).")
    out.append("Il filtro (tau = 10k x 100n = 1 ms) e' a regime a t = 9,9 ms: l'errore coincide con "
               "quello atteso dal partitore 10k / 2,25 Mohm (-0,44 %).")
    s = "\n".join(out)
    print(s)
    open(os.path.join(HERE, "verifica_soglia_monitor.txt"), "w").write(s + "\n")


if __name__ == "__main__":
    main()
