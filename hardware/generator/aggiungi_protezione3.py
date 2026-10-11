# -*- coding: utf-8 -*-
"""Scheda a 3 canali: aggiunge al routing salvato la PROTEZIONE DELL'ALIMENTAZIONE
(USB-C J7, fusibile F1, TVS D5, MOSFET P Q4, C60, LED D6) senza toccare il resto.

  - tiene tutte le piste e via delle altre reti;
  - del +5V tiene solo i tratti d'uscita dai pad dei componenti esistenti (il +5V ora
    parte dal source di Q4 e non piu' da J3, quindi va ri-instradato);
  - via di massa e tratti d'uscita solo per i pad dei componenti nuovi;
  - instrada le reti nuove e il +5V, poi agganci, isole di massa, piano, DRC e
    connettivita' sul rame reale; salva lo stato.

    python3 aggiungi_protezione3.py
    python3 gen_pcb3.py --solo-serigrafia          # riscrive PCB, Gerber, anteprime
"""
import inspect, json, sys
sys.argv = sys.argv[:1]
import gen_pcb3                                    # noqa: E402  (configura gen_pcb per i 3 canali)
import gen_pcb as GP                               # noqa: E402

NEW = {"J7", "R60", "R61", "F1", "D5", "Q4", "R62", "C60", "R63", "D6"}
NETS = ["VIN_RAW", "CC1", "CC2", "VIN_F", "Q4_G", "LED_PWR", "+5V"]

st = json.load(open(gen_pcb3.STATE))
stub_of = {(round(p["x"], 3), round(p["y"], 3)): (p["ref"], p["pin"])
           for p in GP.pads if p["net"] == "+5V" and p["ref"] not in NEW and p["kind"] == "smd"}
tracks, kept_stubs = [], 0
for t in st["tracks"]:
    t = dict(t, pts=[tuple(p) for p in t["pts"]])
    if t["net"] in NETS:
        a = (round(t["pts"][0][0], 3), round(t["pts"][0][1], 3))
        if t["net"] == "+5V" and len(t["pts"]) == 2 and a in stub_of and abs(t["w"] - 0.3) < 1e-6:
            tracks.append(t)                        # tratto d'uscita di un pad esistente
            GP.STUBS[stub_of[a]] = t["pts"][1]
            kept_stubs += 1
        continue
    tracks.append(t)
GP.tracks[:] = tracks
GP.vias[:] = [v for v in st["vias"] if v["net"] not in NETS]
print(f"tenute {len(GP.tracks)} piste (di cui {kept_stubs} uscite del +5V), {len(GP.vias)} via")


def solo_nuovi(fn, cond):
    """esegue una funzione di gen_pcb limitando il ciclo principale sui pad ai componenti nuovi"""
    src = inspect.getsource(fn)
    src = src.replace(cond, cond.replace("for p in pads:", "for p in [q for q in pads if q['ref'] in NEW]:"), 1)
    ns = dict(vars(GP))
    ns["NEW"] = NEW
    exec(src, ns)
    ns[fn.__name__]()


solo_nuovi(GP.add_gnd_vias, "for p in pads:\n        if p[\"net\"] != \"GND\"")
solo_nuovi(gen_pcb3._stubs, "for p in pads:\n        if p[\"kind\"] != \"smd\" or p[\"net\"] is None")
print("via di massa e uscite aggiunte per:", sorted(NEW))

for n in NETS:
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
