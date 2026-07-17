# -*- coding: utf-8 -*-
"""Estrae la NETLIST (componenti + connessioni) direttamente dal file
riv_cosmici.kicad_sch, per geometria: unisce estremi dei fili, pin dei
componenti, etichette e simboli di alimentazione in nodi elettrici.

Legge TUTTO dal file:
  - valori dei componenti (property Value)
  - posizione/rotazione/mirror di ogni simbolo
  - fili, giunzioni, etichette, simboli di potenza
La geometria dei pin viene dai lib_symbols del file stesso.
Cosi' un errore nello schema (valore o cablaggio) cambia la netlist estratta.
"""
import math
from kiutils.schematic import Schematic

RAILS = {"GND": 0.0, "+5V": 5.0, "+3V3": 3.3, "+3V6": 3.6}

def _pin_abs(inst, px, py):
    """trasformazione lib(Y-up) -> foglio(Y-down) identica a KiCad/gen_sch,
    verificata: aggancia tutti i pin ai fili."""
    x, y = inst.position.X, inst.position.Y
    rot = int(inst.position.angle or 0)
    mir = inst.mirror
    if mir == "x":            # riflessione verticale (attorno ad asse X)
        if rot == 0:   dx, dy = px, py
        elif rot == 90:  dx, dy = -py, px
        elif rot == 180: dx, dy = -px, -py
        else:            dx, dy = py, -px
    elif mir == "y":          # riflessione orizzontale
        if rot == 0:   dx, dy = -px, -py
        elif rot == 90:  dx, dy = py, -px
        elif rot == 180: dx, dy = px, py
        else:            dx, dy = -py, px
    else:
        if rot == 0:   dx, dy = px, -py
        elif rot == 90:  dx, dy = -py, -px
        elif rot == 180: dx, dy = -px, py
        else:            dx, dy = py, px
    return (round(x + dx, 3), round(y + dy, 3))

def extract(path):
    s = Schematic.from_file(path)
    # geometria pin dai lib_symbols del file
    libpins = {}   # lib_id -> {num:(px,py)}
    for lib in s.libSymbols:
        d = {}
        for u in lib.units:
            for p in u.pins:
                d[p.number] = (p.position.X, p.position.Y)
        libpins[lib.entryName] = d

    comps = {}   # ref -> {value, libname, pins:{num:(x,y)}, ptype}
    powerpts = []  # (netname, (x,y))
    for inst in s.schematicSymbols:
        ref = None; value = None
        for pr in inst.properties:
            if pr.key == "Reference": ref = pr.value
            if pr.key == "Value": value = pr.value
        libname = inst.libId.split(":")[-1]
        pins = libpins.get(libname, {})
        abspins = {num: _pin_abs(inst, px, py) for num, (px, py) in pins.items()}
        if libname.startswith("PWR_"):
            net = libname[4:]
            for xy in abspins.values(): powerpts.append((net, xy))
            continue
        if ref and ref.startswith(("#PWR", "#FLG")):
            continue
        comps[ref] = dict(value=value, lib=libname, pins=abspins)

    # nodi: union-find su estremi fili + pin + etichette + potenza
    pts = set()
    segs = []
    for g in s.graphicalItems:
        if type(g).__name__ == "Connection" and getattr(g, "type", "wire") == "wire":
            P = [(round(p.X,3), round(p.Y,3)) for p in g.points]
            for a, b in zip(P, P[1:]):
                segs.append((a, b)); pts.add(a); pts.add(b)
    for c in comps.values():
        for xy in c["pins"].values(): pts.add(xy)
    labels = [(l.text, (round(l.position.X,3), round(l.position.Y,3))) for l in s.labels]
    for _, xy in labels: pts.add(xy)
    for _, xy in powerpts: pts.add(xy)

    parent = {p: p for p in pts}
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    def on_seg(p, a, b):
        if a[0] == b[0]:
            return p[0] == a[0] and min(a[1],b[1]) < p[1] < max(a[1],b[1])
        if a[1] == b[1]:
            return p[1] == a[1] and min(a[0],b[0]) < p[0] < max(a[0],b[0])
        return False
    for a, b in segs:
        union(a, b)
        for p in pts:
            if p != a and p != b and on_seg(p, a, b): union(p, a)

    # nome di ogni gruppo
    name = {}
    for net, xy in powerpts:
        name[find(xy)] = net
    for txt, xy in labels:
        r = find(xy)
        name.setdefault(r, txt)
    anon = [0]
    def netname(r):
        if r not in name:
            anon[0]+=1; name[r] = f"N{anon[0]}"
        return name[r]

    # netlist: net -> [(ref,pin)] ; e per-comp pin->net
    nets = {}
    comp_pin_net = {}
    for ref, c in comps.items():
        for num, xy in c["pins"].items():
            nn = netname(find(xy))
            nets.setdefault(nn, []).append((ref, num))
            comp_pin_net[(ref, num)] = nn
    return comps, nets, comp_pin_net

if __name__ == "__main__":
    comps, nets, cpn = extract("../hardware/riv_cosmici.kicad_sch")
    print(f"{len(comps)} componenti, {len(nets)} reti estratte dal file KiCad")
    # front-end: mostra le reti della catena di segnale
    fe = ["SIG_IN","Q1B","Q1C","Q2E","Q2C","CMP_IN"]
    for ref in ["R9","R10","R11","R12","R13","R14","R15","C7","C11","Q1","Q2"]:
        pins = {n: cpn.get((ref,n)) for n in comps[ref]["pins"]}
        print(f"  {ref:4s} = {comps[ref]['value']:8s}  pin->net: {pins}")
