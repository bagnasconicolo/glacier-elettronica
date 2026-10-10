# -*- coding: utf-8 -*-
"""PCB, Gerber e anteprima della VARIANTE A 3 CANALI.

Riusa il generatore della scheda a 1 canale (gen_pcb: autorouter, pour GND,
DRC, connettivita'; gerber_out; render_pcb) con il modello a 3 canali
(netdata3), il piazzamento didattico a blocchi (pcb_data3) e la serigrafia (silk3).

    python gen_pcb3.py   ->  riv_cosmici_3ch/riv_cosmici_3ch.kicad_pcb, gerber/, pcb_render
"""
import os, runpy, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import netdata3                                    # noqa: E402
sys.modules["netdata"] = netdata3
import pcb_data as PD                              # noqa: E402
import pcb_data3 as P3                             # noqa: E402
PD.BOARD = P3.BOARD
PD.PLACEMENT.clear()
PD.PLACEMENT.update(P3.PLACEMENT)
PD.HV_NETS |= P3.HV_EXTRA
PD.NETCLASS_W.update(P3.WIDTH_EXTRA)
import gen_pcb as GP                               # noqa: E402

OUT = os.path.join(HERE, "riv_cosmici_3ch")
STATE = os.path.join(OUT, "routing_state.json")

# ordine di routing: quello della scheda singola, replicato per canale
SHARED_NETS = netdata3.SHARED_NETS
order = []
for net in list(GP.ROUTE_ORDER):
    if net in SHARED_NETS:
        order.append(net)
    else:
        order += [f"{net}{n}" for n in netdata3.CHANNELS if f"{net}{n}" in netdata3.NETS]
# le connessioni lunghe verso la coincidenza subito dopo le alimentazioni
early = ["BUF_Y1", "BUF_Y2", "BUF_Y3", "AND_IN1", "AND_IN2", "AND_IN3"]
i = order.index("+3V6") + 1
order = [n for n in order[:i] if n not in early] + early + [n for n in order[i:] if n not in early]
order += ["AND_Y", "AND_OUT"]
order += [n for n in netdata3.NETS if n not in order and n != "GND"]
GP.ROUTE_ORDER[:] = order

# corridoio delle uscite verso la coincidenza: piste fisse, aggiunte prima delle
# via GND (che cosi' lo evitano) a ogni tentativo del router
_stubs = GP.add_escape_stubs


def _stubs_and_corridor():
    _stubs()
    t, v = P3.corridor_tracks()
    GP.tracks.extend(t)
    GP.vias.extend(v)


GP.add_escape_stubs = _stubs_and_corridor

# le linee del monitor (MON1..4) non devono passare vicino ai nodi analogici
# sensibili, ne' sullo stesso strato ne' sull'altro (niente incroci sotto l'amplificatore
# e il comparatore, niente tagli nel piano di massa sotto di loro)
SENSITIVE = ("SIG_IN", "Q1B", "Q1C", "Q2E", "Q2C", "CMP_IN", "TH", "TH_W", "TH_HI", "TH_LO",
             "LE", "BIAS", "VSET", "INV")
KEEP_MON = 1.2                                       # mm di distanza minima
_build_obstacles = GP.build_obstacles


def _build_obstacles_mon(net, w):
    obs = _build_obstacles(net, w)
    if net.startswith("MON"):
        from shapely.geometry import LineString
        from shapely.ops import unary_union
        sens = {f"{b}{n}" for b in SENSITIVE for n in netdata3.CHANNELS}
        # i componenti della rete stessa (es. R152 della lettura soglia, con un pad
        # sulla soglia TH1) non contano: la pista deve poter uscire dal loro pad
        own = {p["ref"] for p in GP.pads if p["net"] == net}
        extra = [GP.pad_rect(p, KEEP_MON + w / 2) for p in GP.pads if p["net"] in sens and p["ref"] not in own]
        extra += [LineString(t["pts"]).buffer(t["w"] / 2 + KEEP_MON + w / 2)
                  for t in GP.tracks if t["net"] in sens]
        if extra and own:
            near = unary_union([GP.pad_rect(p, 2.0) for p in GP.pads if p["ref"] in own and p["kind"] == "smd"
                                and p["ref"][0] in "RC"])
            extra = [g.difference(near) for g in extra]
            extra = [g for g in extra if not g.is_empty]
        for L in ("F.Cu", "B.Cu"):
            obs[L] = obs[L] + extra
    return obs


GP.build_obstacles = _build_obstacles_mon

# avanzamento del routing (la scheda a 3 canali richiede parecchi minuti)
import time as _t                                  # noqa: E402
_route_net = GP.route_net
_T0 = _t.time()


def _route_net_log(net):
    ok = _route_net(net)
    print(f"[{_t.time() - _T0:7.1f}s] {net}: {'ok' if ok else 'FALLITO'}", flush=True)
    return ok


GP.route_net = _route_net_log


def solo_serigrafia():
    """riscrive .kicad_pcb, Gerber e anteprima dal routing salvato (senza ri-instradare)"""
    import json
    import silk3
    from shapely.geometry import Polygon
    silk, miss = silk3.build()
    json.dump(silk, open(os.path.join(OUT, "silk.json"), "w"))
    print("serigrafia:", {k: len(v) for k, v in silk.items()}, "riferimenti mancanti:", miss)
    GP.SILK_POLYS = silk
    st = json.load(open(STATE))
    GP.tracks[:] = st["tracks"]
    GP.vias[:] = st["vias"]
    for t in P3.GND_PATCH_TRACKS:                   # isole di massa chiuse (vedi pcb_data3)
        if not any(u["net"] == t["net"] and u["layer"] == t["layer"]
                   and [tuple(p) for p in u["pts"]] == t["pts"] for u in GP.tracks):
            GP.tracks.append(dict(t))
    for v in P3.GND_PATCH_VIAS:
        if not any((u["x"], u["y"]) == (v["x"], v["y"]) for u in GP.vias):
            GP.vias.append(dict(v))
    # piste prolungate fino al centro dei pad, poi DRC e connettivita' sul rame reale
    print("agganci ai pad aggiunti:", GP.snap_to_pads())
    print("isole di massa ricollegate:", GP.fix_gnd_islands())
    pour_keep, _ = GP.gnd_pour()
    errs = GP.drc(pour_keep) + GP.connectivity(pour_keep)
    for e in errs:
        print("ERRORE:", e)
    if errs:
        raise SystemExit("routing salvato non valido: rilanciare gen_pcb3.py senza opzioni")
    st["tracks"], st["vias"] = GP.tracks, GP.vias
    st["pour"] = [list(p.exterior.coords) for p in pour_keep]
    st["pour_holes"] = [[list(h.coords) for h in p.interiors] for p in pour_keep]
    json.dump(st, open(STATE, "w"))
    pour = pour_keep
    GP.write_pcb(os.path.join(OUT, "riv_cosmici_3ch.kicad_pcb"), pour)
    runpy.run_path(os.path.join(HERE, "gerber_out.py"),
                   init_globals={"STATE": STATE, "OUT": os.path.join(OUT, "gerber"),
                                 "NAME": "riv_cosmici_3ch", "SILK": silk})
    runpy.run_path(os.path.join(HERE, "render_pcb.py"),
                   init_globals={"STATE": STATE, "OUTSVG": os.path.join(OUT, "pcb3_render.svg"),
                                 "SILKJSON": os.path.join(OUT, "silk.json")})


if __name__ == "__main__" and "--solo-serigrafia" in sys.argv:
    solo_serigrafia()
elif __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "gerber"), exist_ok=True)
    # serigrafia didattica (blocchi, titoli, test point, riferimenti, legenda sul retro)
    import json
    import silk3
    silk, miss = silk3.build()
    json.dump(silk, open(os.path.join(OUT, "silk.json"), "w"))
    print("serigrafia:", {k: len(v) for k, v in silk.items()}, "riferimenti mancanti:", miss)
    GP.SILK_POLYS = silk
    fails, errs, cerr = GP.main(os.path.join(OUT, "riv_cosmici_3ch.kicad_pcb"), STATE)
    runpy.run_path(os.path.join(HERE, "gerber_out.py"),
                   init_globals={"STATE": STATE, "OUT": os.path.join(OUT, "gerber"),
                                 "NAME": "riv_cosmici_3ch", "SILK": silk})
    runpy.run_path(os.path.join(HERE, "render_pcb.py"),
                   init_globals={"STATE": STATE, "OUTSVG": os.path.join(OUT, "pcb3_render.svg"),
                                 "SILKJSON": os.path.join(OUT, "silk.json")})
    if fails or errs or cerr:
        raise SystemExit(1)
