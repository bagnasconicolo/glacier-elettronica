# -*- coding: utf-8 -*-
"""Scheda a 1 canale: aggancia le piste salvate al centro dei pad (vedi gen_pcb.snap_to_pads),
ricontrolla DRC e connettivita' sul rame reale e riscrive .kicad_pcb e Gerber
senza ri-instradare.   python fix_agganci.py"""
import json, os, runpy, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE); sys.path.insert(0, HERE)
import gen_pcb as GP
STATE = "routing_state.json"
st = json.load(open(STATE))
GP.tracks[:] = [dict(t, pts=[tuple(p) for p in t["pts"]]) for t in st["tracks"]]
GP.vias[:] = st["vias"]
print("agganci ai pad aggiunti:", GP.snap_to_pads())
print("isole di massa ricollegate:", GP.fix_gnd_islands())
pk, _ = GP.gnd_pour()
errs = GP.drc(pk) + GP.connectivity(pk)
for e in errs:
    print("ERRORE:", e)
if errs:
    raise SystemExit(1)
json.dump({"tracks": GP.tracks, "vias": GP.vias,
           "pour": [list(p.exterior.coords) for p in pk],
           "pour_holes": [[list(h.coords) for h in p.interiors] for p in pk]}, open(STATE, "w"))
GP.write_pcb("riv_cosmici/riv_cosmici.kicad_pcb", pk)
runpy.run_path("gerber_out.py", init_globals={"STATE": STATE})
print("DRC 0, connettivita' OK")
