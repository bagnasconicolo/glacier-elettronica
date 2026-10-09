# -*- coding: utf-8 -*-
"""Cavo tra barra (SiPM) e scheda: quanto conta la lunghezza?

Il SiPM viene spostato in fondo a un cavo coassiale tipo RG174/RG316 (circa
100 pF/m e 250 nH/m; modello a parametri concentrati in 2 celle LC per metro):
conduttore centrale = segnale (anodo), calza = bias (catodo), come nello schema
INFN. Si confrontano 0 / 0,5 / 1 / 2 m.

    python verifica_cavo.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngspice_run import run

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = open(os.path.join(HERE, "riv_cosmici_completo.cir"), encoding="latin-1").read()


def sim(m):
    txt = BASE
    if m > 0:
        txt = re.sub(r"(?m)^XSIPM SIG_IN BIAS ", "XSIPM SIG_FAR BIAS_FAR ", txt, count=1)
        n = max(1, int(round(2 * m)))                      # celle LC
        L, C = 250e-9 * m / n, 100e-12 * m / n
        nodes = ["SIG_FAR"] + [f"SIG_C{k}" for k in range(1, n)] + ["SIG_IN"]
        line = f"* cavo coassiale {m} m ({n} celle LC)\nR_FAR1 SIG_FAR 0 1G\nV_SHIELD BIAS_FAR BIAS 0\n"
        for k in range(n):
            line += f"L_C{k} {nodes[k]} {nodes[k]}_L {L:.4g}\nR_C{k} {nodes[k]}_L {nodes[k + 1]} 0.05\n"
            line += f"C_C{k} {nodes[k + 1]} BIAS {C:.4g}\n"
        txt = re.sub(r"(?m)^\.tran", line + ".tran", txt, count=1)
    fn = os.path.join(HERE, "_cavo_tmp.cir")
    open(fn, "w", encoding="latin-1").write(txt)
    try:
        return run(fn)[0]
    finally:
        os.remove(fn)


def main():
    L = [0, 0.5, 1.0, 2.0]
    r = {m: sim(m) for m in L}
    rows = [("pk_ev1", "muone 250 p.e.: picco ingresso comparatore (V)"),
            ("rpi_ev1", "muone 250 p.e.: uscita al Raspberry (V)"),
            ("pk_ev3", "muone 40 p.e.: picco (V)"),
            ("rpi_ev3", "muone 40 p.e.: uscita al Raspberry (V)"),
            ("pk_ev2", "rumore 1 p.e.: picco (V)"),
            ("q_ev2", "rumore 1 p.e.: uscita comparatore (V), deve restare ~0"),
            ("v_th", "soglia (V)")]
    print(f"{'misura':50s}" + "".join(f"{str(m) + ' m':>10s}" for m in L))
    for k, name in rows:
        print(f"{name:50s}" + "".join(f"{r[m].get(k, float('nan')):10.4g}" for m in L))


if __name__ == "__main__":
    main()
