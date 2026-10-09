# -*- coding: utf-8 -*-
"""Verifica della simulazione LTspice della scheda completa.

1) rilegge riv_cosmici_completo.asc + i simboli riv_*.asy esattamente come
   farebbe LTspice (posizione dei pin, fili, etichette FLAG) e ricostruisce
   la netlist: deve coincidere riga per riga con riv_cosmici_completo.cir;
2) controlla che la .cir contenga tutti i componenti e tutte le reti dello
   schema KiCad (netdata.py);
3) simula la .cir con ngspice e verifica i valori attesi (PASS/FAIL);
4) salva il grafico ../figures/sim_ltspice_completo.png.

    python verifica_ltspice.py
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_ltspice as G
from ngspice_run import run


def parse_asy(fn):
    pins, prefix = [], None
    for ln in open(fn, encoding="latin-1"):
        t = ln.split()
        if not t:
            continue
        if t[0] == "PIN":
            pins.append([int(t[1]), int(t[2]), None, None])
        elif t[0] == "PINATTR" and t[1] == "SpiceOrder":
            pins[-1][3] = int(t[2])
        elif t[0] == "SYMATTR" and t[1] == "Prefix":
            prefix = t[2]
    return prefix, sorted(pins, key=lambda p: p[3])


def asc_to_netlist(fn):
    syms, wires, flags, cur = [], [], [], None
    for ln in open(fn, encoding="latin-1"):
        ln = ln.rstrip("\r\n")
        t = ln.split(" ", 2)
        if t[0] == "SYMBOL":
            a = ln.split()
            assert a[4] == "R0", "solo simboli R0 previsti"
            cur = dict(sym=a[1], x=int(a[2]), y=int(a[3]), attr={})
            syms.append(cur)
        elif t[0] == "SYMATTR":
            cur["attr"][t[1]] = t[2] if len(t) > 2 else ""
        elif t[0] == "WIRE":
            a = list(map(int, ln.split()[1:5]))
            wires.append(((a[0], a[1]), (a[2], a[3])))
        elif t[0] == "FLAG":
            a = ln.split()
            flags.append(((int(a[1]), int(a[2])), a[3]))
    # union-find sui punti (fili + pin + etichette); niente T sui fili qui
    parent = {}
    def find(p):
        parent.setdefault(p, p)
        while parent[p] != p:
            parent[p] = parent[parent[p]]; p = parent[p]
        return p
    def union(a, b):
        parent[find(a)] = find(b)
    for a, b in wires:
        union(a, b)
    name = {}
    for p, n in flags:
        r = find(p)
        assert name.get(r, n) == n, f"due etichette diverse sullo stesso nodo: {n}, {name[r]}"
        name[r] = n
    lines = []
    for s in syms:
        prefix, pins = parse_asy(os.path.join(HERE, s["sym"] + ".asy"))
        nodes = []
        for px, py, _side, _order in pins:
            r = find((s["x"] + px, s["y"] + py))
            assert r in name, f"{s['attr']['InstName']}: pin a ({s['x']+px},{s['y']+py}) scollegato"
            nodes.append(name[r])
        inst = s["attr"]["InstName"]
        nm = inst if inst[0].upper() == prefix else prefix + inst
        extra = [s["attr"].get("Value", "")] + ([s["attr"]["SpiceLine"]] if "SpiceLine" in s["attr"] else [])
        lines.append(" ".join([nm] + nodes + [x for x in extra if x]))
    return lines


def cir_elements(fn):
    out = []
    for ln in open(fn, encoding="latin-1"):
        ln = ln.strip()
        if ln and not ln.startswith(("*", ".", "+")):
            out.append(ln)
    return out


def main():
    ok = True
    cir = os.path.join(HERE, "riv_cosmici_completo.cir")
    asc = os.path.join(HERE, "riv_cosmici_completo.asc")
    # 1) .asc == .cir
    a = sorted(asc_to_netlist(asc)); c = sorted(cir_elements(cir))
    if a == c:
        print(f"[PASS] schema .asc == netlist .cir ({len(a)} elementi)")
    else:
        ok = False
        print("[FAIL] schema .asc diverso dalla netlist .cir")
        for x in sorted(set(a) ^ set(c)):
            print("   ", "asc" if x in a else "cir", x)
    # 2) copertura dello schema KiCad
    E = G.build_elements()
    refs_cir = {l.split()[0].upper() for l in c}
    miss = [r for r, (k, *_x) in G.COMPONENTS.items()
            if k != "CONN2" and r.upper() not in refs_cir and "X" + r.upper() not in refs_cir]
    if miss:
        ok = False; print("[FAIL] componenti KiCad mancanti nella .cir:", miss)
    else:
        n = sum(1 for k, *_x in G.COMPONENTS.values() if k != "CONN2")
        print(f"[PASS] tutti i {n} componenti dello schema KiCad sono nella simulazione "
              f"(+ 4 connettori come carichi/sorgenti esterne)")
    # 3) simulazione
    m, w = run(cir)
    checks = [
        ("+3V3 (U6)",                "v_3v3",    3.2, 3.4, "V"),
        ("+3V6 (U5)",                "v_3v6",    3.5, 3.7, "V"),
        ("rif. 3,6 V (U7)",          "v_refb",   3.5, 3.7, "V"),
        ("VOUT40 (boost U1)",        "v_out40",  40.0, 43.0, "V"),
        ("BIAS SiPM",                "v_bias",   38.0, 38.9, "V"),
        ("soglia TH",                "v_th",     0.08, 0.13, "V"),
        ("base Q1",                  "vb_q1",    0.5, 0.7, "V"),
        ("collettore Q1",            "vc_q1",    2.2, 2.7, "V"),
        ("collettore Q2",            "vc_q2",    0.2, 0.7, "V"),
        ("corrente da J3 (5 V)",     "i_5v",    -0.08, -0.02, "A"),
        ("muone 250 p.e.: picco",    "pk_ev1",   0.8, 1.4, "V"),
        ("muone 250 p.e.: CMP_Q",    "q_ev1",    3.0, 3.4, "V"),
        ("muone 250 p.e.: TTL J2",   "ttl_ev1",  4.5, 5.1, "V"),
        ("muone 250 p.e.: GPIO",     "rpi_ev1",  3.0, 3.35, "V"),
        ("larghezza impulso GPIO",   "w_rpi_ev1", 80e-9, 1e-6, "s"),
        ("ritardo CMP_Q -> GPIO",    "d_rpi_ev1", 0, 30e-9, "s"),
        ("dark count 1 p.e.: CMP_Q", "q_ev2",   -0.1, 0.1, "V"),
        ("muone 40 p.e.: GPIO",      "rpi_ev3",  3.0, 3.35, "V"),
        ("muone a 1,5 us: GPIO",     "rpi_ev4",  3.0, 3.35, "V"),
        ("durata LED (555)",         "t_led",    9e-3, 13e-3, "s"),
        ("LED spento dopo",          "v_led_off", -0.1, 0.1, "V"),
    ]
    for label, k, lo, hi, u in checks:
        v = m.get(k)
        good = v is not None and lo <= v <= hi
        ok &= good
        print(f"[{'PASS' if good else 'FAIL'}] {label:28s} = {v!s:>14} {u}   (atteso {lo} .. {hi})")
    # 4) grafico
    try:
        plot(w)
    except Exception as ex:   # matplotlib assente: non e' un errore della scheda
        print("grafico non generato:", ex)
    print("\nRISULTATO:", "TUTTO OK" if ok else "CI SONO ERRORI")
    return ok


def plot(w):
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = w["time"]
    fig, ax = plt.subplots(3, 2, figsize=(13, 9))
    a = ax[0, 0]
    for k, lab in [("v(v5)", "+5V"), ("v(v3v3)", "+3V3"), ("v(v3v6)", "+3V6")]:
        a.plot(t * 1e3, w[k], label=lab)
    a.set_title("Accensione: alimentazioni"); a.set_xlabel("ms"); a.set_ylabel("V"); a.legend()
    a.set_xlim(0, 5)
    a = ax[0, 1]
    for k, lab in [("v(vout40)", "VOUT40 (boost)"), ("v(vreg38)", "uscita LT1636"), ("v(bias)", "BIAS SiPM")]:
        a.plot(t * 1e3, w[k], label=lab)
    a.set_title("Accensione: alta tensione del SiPM"); a.set_xlabel("ms"); a.set_ylabel("V")
    a.legend(); a.set_xlim(0, 5)
    s = (t > 9.9995e-3) & (t < 10.0235e-3)
    tt = (t[s] - 10e-3) * 1e6
    a = ax[1, 0]
    a.plot(tt, w["v(sig_in)"][s] * 1e3, label="SIG_IN (anodo SiPM)")
    a.plot(tt, w["v(cmp_in)"][s] * 1e3, label="CMP_IN (ingresso comparatore)")
    a.plot(tt, w["v(th)"][s] * 1e3, "--", label="soglia TH")
    a.set_title("4 eventi: muone 250 p.e., dark 1 p.e., muone 40 p.e., muone 150 p.e.")
    a.set_xlabel("us da t = 10 ms"); a.set_ylabel("mV"); a.legend(fontsize=8)
    a = ax[1, 1]
    a.plot(tt, w["v(cmp_q)"][s], label="CMP_Q (MAX961)")
    a.plot(tt, w["v(le)"][s], label="LE (latch C9/R16)")
    a.plot(tt, w["v(ttl_out)"][s], label="TTL_OUT J2 (MCP1402)")
    a.plot(tt, w["v(rpi_gpio)"][s], "--", label="GPIO Raspberry Pi (via J4)")
    a.set_title("Uscite digitali"); a.set_xlabel("us da t = 10 ms"); a.set_ylabel("V")
    a.legend(fontsize=8)
    s2 = (t > 9.995e-3) & (t < 10.0006e-3)
    a = ax[2, 0]
    a.plot((t[s2] - 10e-3) * 1e9, w["v(cmp_q)"][s2], label="CMP_Q")
    a.plot((t[s2] - 10e-3) * 1e9, w["v(buf_y)"][s2], label="74LVC1G17 Y")
    a.plot((t[s2] - 10e-3) * 1e9, w["v(rpi_gpio)"][s2], "--", label="GPIO")
    a.set_xlim(-20, 400)
    a.set_title("Dettaglio primo muone"); a.set_xlabel("ns da t = 10 ms"); a.set_ylabel("V")
    a.legend(fontsize=8)
    a = ax[2, 1]
    a.plot(t * 1e3, w["v(led_a)"], label="uscita 555 (LED_A)")
    a.plot(t * 1e3, w["v(t555)"], label="C21 (temporizzazione)")
    a.plot(t * 1e3, w["v(ctl555)"], "--", label="CTRL (2/3 VCC)")
    a.set_title("Monostabile 555: LED acceso ~11 ms"); a.set_xlabel("ms"); a.set_ylabel("V")
    a.legend(fontsize=8)
    fig.suptitle("Riv. Cosmici 2024 - simulazione della scheda completa (riv_cosmici_completo.cir)")
    fig.tight_layout()
    out = os.path.join(HERE, "..", "figures", "sim_ltspice_completo.png")
    fig.savefig(out, dpi=110)
    print("grafico:", os.path.normpath(out))


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
