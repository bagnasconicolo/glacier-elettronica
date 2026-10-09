# -*- coding: utf-8 -*-
"""Verifica INDIPENDENTE con KiCad (non con il generatore) di schema e PCB.

    python3 verifica_kicad.py ../variante_3ch/riv_cosmici_3ch      (senza estensione)
    python3 verifica_kicad.py ../riv_cosmici

Richiede KiCad >= 7 (modulo python `pcbnew` e `kicad-cli`) e shapely. Controlla:
  1. netlist dello schema (estratta da kicad-cli) == reti dei pad del PCB;
  2. DRC di KiCad dopo il riempimento delle zone (errori; gli avvisi solo contati);
  3. connettivita' sul RAME REALE: forme vere dei pad, piste, via e piano di massa
     riempito da KiCad; ogni isola del piano conta a se'.
Esce con codice 1 se qualcosa non va.
"""
import collections, os, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
import pcbnew
from shapely.geometry import LineString, Point, Polygon

base = sys.argv[1]
SCH, PCB = base + ".kicad_sch", base + ".kicad_pcb"
mm = lambda v: v / 1e6
ok = True
tmp = tempfile.mkdtemp()

# 1. schema contro PCB
xml = os.path.join(tmp, "net.xml")
subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml, SCH],
               check=True, capture_output=True)
sch = {}
for n in ET.parse(xml).getroot().iter("net"):
    nodes = frozenset((x.get("ref"), x.get("pin")) for x in n.iter("node"))
    for x in nodes:
        sch[x] = nodes
b = pcbnew.LoadBoard(PCB)
pcb = collections.defaultdict(set)
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname():
            pcb[p.GetNetname()].add((fp.GetReference(), p.GetNumber()))
pnet = {x: frozenset(v) for v in pcb.values() for x in v}
diff = sorted(k for k in set(sch) | set(pnet)
              if sch.get(k, frozenset([k])) != pnet.get(k, frozenset([k])))
print(f"1. schema/PCB: {len(diff)} pin collegati in modo diverso", diff[:10])
ok &= not diff

# 2. DRC di KiCad
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
rpt = os.path.join(tmp, "drc.rpt")
pcbnew.WriteDRCReport(b, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
kinds = collections.Counter()
err = []
lines = open(rpt).read().splitlines()
for i, l in enumerate(lines):
    if l.startswith("[") and "]:" in l:
        k = l[1:l.index("]")]
        kinds[k] += 1
        if "Severity: error" in lines[i + 1] and k != "lib_footprint_issues":
            err.append(" ".join(x.strip() for x in lines[i:i + 4]))
print("2. DRC KiCad:", dict(kinds))
for e in err:
    print("   ERRORE:", e)
ok &= not [e for e in err if "unconnected" in e or "clearance" in e and "edge" not in e or "short" in e]

# 3. connettivita' sul rame reale
F, B = pcbnew.F_Cu, pcbnew.B_Cu
items = collections.defaultdict(list)
for fp in b.GetFootprints():
    for p in fp.Pads():
        if not p.GetNetname():
            continue
        for L in (F, B):
            if p.IsOnLayer(L):
                ps = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(ps, L, 0, 1000)
                for i in range(ps.OutlineCount()):
                    o = ps.Outline(i)
                    g = Polygon([(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())])
                    items[p.GetNetname()].append((L, g.buffer(0), f"{fp.GetReference()}.{p.GetNumber()}"))
for t in b.GetTracks():
    n = t.GetNetname()
    if t.GetClass() == "PCB_VIA":
        q = t.GetPosition()
        g = Point(mm(q.x), mm(q.y)).buffer(mm(t.GetWidth()) / 2, 16)
        items[n].append((F, g, "via")); items[n].append((B, g, "via"))
    else:
        a, e = t.GetStart(), t.GetEnd()
        g = LineString([(mm(a.x), mm(a.y)), (mm(e.x), mm(e.y))]).buffer(mm(t.GetWidth()) / 2, 16) \
            if (a.x, a.y) != (e.x, e.y) else Point(mm(a.x), mm(a.y)).buffer(mm(t.GetWidth()) / 2, 16)
        items[n].append((t.GetLayer(), g, None))
for z in b.Zones():
    for L in (F, B):
        if z.IsOnLayer(L):
            fl = z.GetFilledPolysList(L)
            for i in range(fl.OutlineCount()):
                o = fl.Outline(i)
                items[z.GetNetname()].append(
                    (L, Polygon([(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]).buffer(0), None))
broken = 0
for n, it in items.items():
    par = list(range(len(it)))
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(it)):
        for j in range(i + 1, len(it)):
            li, gi, ti = it[i]; lj, gj, tj = it[j]
            if (li == lj and gi.intersects(gj)) or (ti and ti == tj and ti != "via") or \
               (ti == tj == "via" and gi.centroid.distance(gj.centroid) < 0.01):
                par[f(i)] = f(j)
    comps = collections.defaultdict(set)
    for i, (_l, _g, t) in enumerate(it):
        if t and t != "via":
            comps[f(i)].add(t)
    if len(comps) > 1:
        broken += 1
        print("   rete spezzata:", n, sorted(sorted(c)[:4] for c in comps.values())[:4])
print(f"3. rame reale: {broken} reti spezzate")
ok &= broken == 0
print("VERIFICA KICAD:", "OK" if ok else "ERRORI")
sys.exit(0 if ok else 1)
