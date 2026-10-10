# -*- coding: utf-8 -*-
"""Scheda a 3 canali: ri-instrada SOLO le reti indicate (dopo aver spostato un
componente), tenendo il resto del routing salvato. Poi DRC e connettivita'.

    python3 reinstrada_reti3.py I2C_SDA I2C_SCL
    python3 gen_pcb3.py --solo-serigrafia          # riscrive PCB, Gerber, anteprime
"""
import json, sys
nets = sys.argv[1:]
sys.argv = sys.argv[:1]
import gen_pcb3                                    # noqa: E402  (configura gen_pcb per i 3 canali)
import gen_pcb as GP                               # noqa: E402
st = json.load(open(gen_pcb3.STATE))
GP.tracks[:] = [dict(t, pts=[tuple(p) for p in t["pts"]]) for t in st["tracks"] if t["net"] not in nets]
GP.vias[:] = [v for v in st["vias"] if v["net"] not in nets]
for t in gen_pcb3.P3.GND_PATCH_TRACKS:
    if not any(u["net"] == t["net"] and [tuple(p) for p in u["pts"]] == t["pts"] for u in GP.tracks):
        GP.tracks.append(dict(t))
for n in nets:
    if not GP.route_net(n):
        sys.exit(f"routing fallito: {n}")
print("agganci:", GP.snap_to_pads(), " isole di massa ricollegate:", GP.fix_gnd_islands())
pk, _ = GP.gnd_pour()
errs = GP.drc(pk) + GP.connectivity(pk)
for e in errs:
    print("ERRORE:", e)
if errs:
    sys.exit(1)
st.update(tracks=GP.tracks, vias=GP.vias,
          pour=[list(p.exterior.coords) for p in pk],
          pour_holes=[[list(h.coords) for h in p.interiors] for p in pk])
json.dump(st, open(gen_pcb3.STATE, "w"))
print("OK: DRC 0, connettivita' OK")
