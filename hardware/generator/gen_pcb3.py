# -*- coding: utf-8 -*-
"""PCB, Gerber e anteprima della VARIANTE A 3 CANALI.

Riusa il generatore della scheda a 1 canale (gen_pcb: autorouter, pour GND,
DRC, connettivita'; gerber_out; render_pcb) con il modello a 3 canali
(netdata3) e il piazzamento a tre strisce (pcb_data3).

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
order += ["AND_IN1", "AND_IN2", "AND_IN3", "AND_Y", "AND_OUT"]
order += [n for n in netdata3.NETS if n not in order and n != "GND"]
GP.ROUTE_ORDER[:] = order

# avanzamento del routing (la scheda a 3 canali richiede parecchi minuti)
import time as _t                                  # noqa: E402
_route_net = GP.route_net
_T0 = _t.time()


def _route_net_log(net):
    ok = _route_net(net)
    print(f"[{_t.time() - _T0:7.1f}s] {net}: {'ok' if ok else 'FALLITO'}", flush=True)
    return ok


GP.route_net = _route_net_log


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "gerber"), exist_ok=True)
    fails, errs, cerr = GP.main(os.path.join(OUT, "riv_cosmici_3ch.kicad_pcb"), STATE)
    runpy.run_path(os.path.join(HERE, "gerber_out.py"),
                   init_globals={"STATE": STATE, "OUT": os.path.join(OUT, "gerber"),
                                 "NAME": "riv_cosmici_3ch"})
    runpy.run_path(os.path.join(HERE, "render_pcb.py"),
                   init_globals={"STATE": STATE, "OUTSVG": os.path.join(OUT, "pcb3_render.svg")})
    if fails or errs or cerr:
        raise SystemExit(1)
