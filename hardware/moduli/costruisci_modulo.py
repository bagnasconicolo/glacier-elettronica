# -*- coding: utf-8 -*-
"""Costruisce un modulo dall'inizio alla fine: schema KiCad, PCB instradato, Gerber,
BOM/CPL JLCPCB, anteprima, verifica indipendente con KiCad.

    python3 costruisci_modulo.py meteo
    python3 costruisci_modulo.py acquisizione
    python3 costruisci_modulo.py meteo --senza-routing     (solo piazzamento, per controllare)

La descrizione della scheda e' in <cartella>/definizione.py (componenti, reti, piazzamento).
"""
import importlib.util, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "generator")
sys.path.insert(0, HERE)
sys.path.insert(0, GEN)
cartella = sys.argv[1]
OUT = os.path.join(HERE, cartella)
spec = importlib.util.spec_from_file_location("definizione", os.path.join(OUT, "definizione.py"))
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
D.check()

# ---------------------------------------------------------------- schema
D.VARIANT = D.NOME                                  # gen_sch non disegna la scheda a 1 canale
sys.modules["netdata"] = D
import gen_sch as G                                   # noqa: E402
from symlib import SYMS                               # noqa: E402
G.FP_MAP.update({k: "moduli:" + v for k, v in D.FP.items()})
G.SYM_MAP.update({k: k for k in ("SHT4X", "LPS22HH", "QWIIC", "SJ2", "SJ3", "TCA9548A", "AP2112K",
                                 "PICO2", "CONN6", "TVSB", "CONN2", "CONN3", "LVC1G17")})
POWER = {"GND", "+5V", "+3V3"}


def stub(ref, x, y, rot=0, length=2.54):
    """simbolo + un filo corto con etichetta (o simbolo di alimentazione) su ogni pin"""
    sym = G.SYM_MAP[D.COMPONENTS[ref][0]]
    G.place(ref, x, y, rot, None, sym)
    pn = {p: n for n, pins in D.NETS.items() for r, p in pins if r == ref}
    for num, (px, py, ang, *_r) in SYMS[sym].pins.items():
        sx, sy = G.pin_sheet_pos(sym, x, y, rot, None, px, py)
        a = (ang + 180 + rot) % 360
        ux, uy = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[a]
        ex, ey = round(sx + ux * length, 3), round(sy + uy * length, 3)
        net = pn.get(num)
        if net is None:
            if (ref, num) in D.NC_PINS:
                G.NCm(sx, sy)
            continue
        G.w(sx, sy, ex, ey)
        if net in POWER:
            G.PW(net, ex, ey, 180 if (net == "GND" and uy < 0) else 0)
        else:
            G.L(net, ex, ey)


for ref, pos in D.SCHEMA.items():
    stub(ref, *pos)
for t in getattr(D, "SCHEMA_TESTI", ()):
    G.T(*t)
G.T(D.TITOLO, 20, 20)
ok = G.check_connectivity()
G.write_sch(os.path.join(OUT, D.NOME + ".kicad_sch"), paper=getattr(D, "SCHEMA_FOGLIO", "A4"), title=D.TITOLO)
if not ok:
    raise SystemExit("schema non coerente con la netlist")

# ---------------------------------------------------------------- PCB
import scheda                                         # noqa: E402
scheda.librerie_progetto(OUT)
pro = open(os.path.join(HERE, "..", "riv_cosmici.kicad_pro")).read().replace("riv_cosmici", D.NOME)
open(os.path.join(OUT, D.NOME + ".kicad_pro"), "w").write(pro)
scheda.costruisci(D, OUT, instrada="--senza-routing" not in sys.argv)
if "--senza-routing" not in sys.argv:
    scheda.fabbricazione(D, OUT)
    r = subprocess.run([sys.executable, os.path.join(GEN, "verifica_kicad.py"), os.path.join(OUT, D.NOME)])
    sys.exit(r.returncode)
