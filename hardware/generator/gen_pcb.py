# -*- coding: utf-8 -*-
"""Genera riv_cosmici.kicad_pcb: piazzamento, escape GND con via,
autorouter a griglia (F.Cu preferito, B.Cu con via), pour GND su B.Cu,
DRC geometrico e verifica connettivita'.
"""
import math, heapq, re, uuid
from shapely.geometry import box, Point, LineString, MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep
import shapely.affinity as aff

from pcb_data import (BOARD, PLACEMENT, COMPONENTS, FP_OF, abs_pads, pad_rect, pad_shape,
                      track_w, CLEARANCE, HV_NETS, HV_CLEAR)
from footprints import FPS
from netdata import NETS

X1, Y1, X2, Y2 = BOARD
GRID = 0.635
VIA_D, VIA_DRILL = 0.8, 0.4
EDGE_CLR = 0.4

pads = abs_pads()
tracks = []   # dict: net, layer, pts [(x,y)..], w
vias = []     # dict: net, x, y

# ---------------- courtyard overlap check ----------------
def courtyards():
    out = []
    for ref, (x, y, rot) in PLACEMENT.items():
        fp = FPS[FP_OF[COMPONENTS[ref][2]]]
        cx1, cy1, cx2, cy2 = fp.courtyard
        b = box(cx1, cy1, cx2, cy2)
        b = aff.rotate(b, -rot, origin=(0, 0))
        b = aff.translate(b, x, y)
        out.append((ref, b))
    return out

def check_courtyards():
    cts = courtyards()
    bad = []
    brd = box(X1, Y1, X2, Y2)
    for i in range(len(cts)):
        if not brd.contains(cts[i][1]):
            bad.append((cts[i][0], "fuori scheda"))
        for j in range(i + 1, len(cts)):
            if cts[i][1].intersects(cts[j][1]):
                a = cts[i][1].intersection(cts[j][1]).area
                if a > 0.01:
                    bad.append((cts[i][0], cts[j][0], round(a, 2)))
    return bad

# ---------------- GND escape vias ----------------
def add_gnd_vias():
    """per ogni pad SMD GND: stub + via verso il pour B.Cu (scelta del punto migliore)."""
    for p in pads:
        if p["net"] != "GND" or p["kind"] != "smd":
            continue
        best = None
        for ang in range(0, 360, 30):
            for dist in (1.3, 1.6, 2.0, 2.4):
                vx = round(p["x"] + dist * math.cos(math.radians(ang)), 3)
                vy = round(p["y"] + dist * math.sin(math.radians(ang)), 3)
                if not (X1 + 1 < vx < X2 - 1 and Y1 + 1 < vy < Y2 - 1):
                    continue
                vgeo = Point(vx, vy).buffer(VIA_D / 2 + CLEARANCE + 0.12)
                stub = LineString([(p["x"], p["y"]), (vx, vy)]).buffer(track_w("GND") / 2 + CLEARANCE + 0.12)
                score = 9e9
                ok = True
                for q in pads:
                    if q is p or q["net"] == "GND":
                        continue
                    qr = pad_rect(q)
                    d = min(qr.distance(vgeo), qr.distance(stub))
                    if qr.intersects(vgeo) or qr.intersects(stub):
                        ok = False; break
                    score = min(score, d)
                if not ok:
                    continue
                for t in tracks:
                    if t["net"] == "GND":
                        continue
                    tg = LineString(t["pts"]).buffer(t["w"] / 2)
                    if tg.intersects(vgeo) or tg.intersects(stub):
                        ok = False; break
                    score = min(score, min(tg.distance(vgeo), tg.distance(stub)))
                if not ok:
                    continue
                for v in vias:
                    if (v["x"] - vx) ** 2 + (v["y"] - vy) ** 2 < (VIA_D + CLEARANCE) ** 2:
                        ok = False; break
                if not ok:
                    continue
                score -= dist * 0.05   # preferisci via vicine
                if best is None or score > best[0]:
                    best = (score, vx, vy)
        if best is None:
            print("!! niente via GND per", p["ref"], p["pin"])
            continue
        _, vx, vy = best
        vias.append(dict(net="GND", x=vx, y=vy))
        tracks.append(dict(net="GND", layer="F.Cu",
                           pts=[(p["x"], p["y"]), (vx, vy)], w=track_w("GND")))

# ---------------- escape stubs (fanout) ----------------
STUBS = {}   # (ref,pin) -> (end_x, end_y)
STUB_DIR_OVERRIDE = {("U1", "4"): (1, 0), ("U7", "1"): (-1, 0)}   # direzione locale forzata
def add_escape_stubs():
    from pcb_data import rot_delta
    for p in pads:
        if p["kind"] != "smd" or p["net"] is None or min(p["w"], p["h"]) >= 0.8:
            continue
        # direzione locale dominante (via dal corpo), poi ruotata
        fpk = COMPONENTS[p["ref"]][2]
        fp = FPS[FP_OF[fpk]]
        px, py, w0, h0, k0, dr0 = fp.pads[p["pin"]]
        if (p["ref"], p["pin"]) in STUB_DIR_OVERRIDE:
            dloc = STUB_DIR_OVERRIDE[(p["ref"], p["pin"])]
            half = (w0 if dloc[0] else h0) / 2 + 0.6
        elif w0 > h0 + 0.2 or (abs(w0 - h0) <= 0.2 and abs(px) >= abs(py)):
            # pad allungato in x (es. SOIC): esce di lato, anche per i pin d'angolo
            dloc = (1 if px > 0 else -1, 0); half = w0 / 2
        else:
            dloc = (0, 1 if py > 0 else -1); half = h0 / 2
        rot = PLACEMENT[p["ref"]][2]
        dx, dy = rot_delta(dloc[0], dloc[1], rot)
        ln = half + 0.8
        ex, ey = p["x"] + dx * ln, p["y"] + dy * ln
        # snap dell'estremo sulla griglia del router (nella direzione di uscita)
        import math as _m
        if abs(dx) > 0.5:
            k = (ex - X1) / GRID
            ex = X1 + (_m.ceil(k) if dx > 0 else _m.floor(k)) * GRID
        if abs(dy) > 0.5:
            k = (ey - Y1) / GRID
            ey = Y1 + (_m.ceil(k) if dy > 0 else _m.floor(k)) * GRID
        ex, ey = round(ex, 3), round(ey, 3)
        tracks.append(dict(net=p["net"], layer="F.Cu",
                           pts=[(p["x"], p["y"]), (ex, ey)], w=0.3))
        STUBS[(p["ref"], p["pin"])] = (ex, ey)

# ---------------- router ----------------
def net_pads(net):
    return [p for p in pads if p["net"] == net]

def geo_of_tracks(net, layer):
    gg = []
    for t in tracks:
        if t["net"] == net and t["layer"] == layer:
            gg.append(LineString(t["pts"]).buffer(t["w"] / 2))
    return gg

DIAG_MARGIN = 0.22

def raw_metal(net):
    """metallo reale altrui per layer (senza buffer)."""
    out = {"F.Cu": [], "B.Cu": []}
    for p in pads:
        if p["net"] == net:
            continue
        g = pad_rect(p)
        if p["kind"] == "smd":
            out["F.Cu"].append(g)
        else:
            out["F.Cu"].append(g); out["B.Cu"].append(g)
    for t in tracks:
        if t["net"] == net:
            continue
        out[t["layer"]].append(LineString(t["pts"]).buffer(t["w"] / 2))
    for v in vias:
        if v["net"] == net:
            continue
        g = Point(v["x"], v["y"]).buffer(VIA_D / 2)
        out["F.Cu"].append(g); out["B.Cu"].append(g)
    return {L: unary_union(gs) if gs else None for L, gs in out.items()}

def validate_path(path, w, raw):
    for a, b in zip(path, path[1:]):
        if a[2] == b[2]:
            g = LineString([a[:2], b[:2]]).buffer(w / 2)
            if raw[a[2]] is not None and raw[a[2]].distance(g) < 0.19:
                return False
        else:
            g = Point(a[0], a[1]).buffer(VIA_D / 2)
            for L in ("F.Cu", "B.Cu"):
                if raw[L] is not None and raw[L].distance(g) < 0.19:
                    return False
    return True

def build_real_obstacles(net, w):
    """metallo reale altrui bufferizzato (per verifiche esatte fuori griglia)."""
    need = w / 2 + CLEARANCE - 0.02
    obs = {"F.Cu": [], "B.Cu": []}
    for p in pads:
        if p["net"] == net:
            continue
        g = pad_rect(p, need)
        if p["kind"] == "smd":
            obs["F.Cu"].append(g)
        else:
            obs["F.Cu"].append(g); obs["B.Cu"].append(g)
    for t in tracks:
        if t["net"] == net:
            continue
        obs[t["layer"]].append(LineString(t["pts"]).buffer(t["w"] / 2 + need))
    for v in vias:
        if v["net"] == net:
            continue
        g = Point(v["x"], v["y"]).buffer(VIA_D / 2 + need)
        obs["F.Cu"].append(g); obs["B.Cu"].append(g)
    return {L: prep(unary_union(gs)) if gs else None for L, gs in obs.items()}

def build_obstacles(net, w):
    """per layer: unione geometrie altre reti, gonfiate di clearance+w/2."""
    obs = {"F.Cu": [], "B.Cu": []}
    for p in pads:
        if p["net"] == net:
            continue
        g = pad_rect(p, CLEARANCE + w / 2 + DIAG_MARGIN)
        if p["kind"] == "smd":
            obs["F.Cu"].append(g)
        else:
            obs["F.Cu"].append(g); obs["B.Cu"].append(g)
    for t in tracks:
        if t["net"] == net:
            continue
        obs[t["layer"]].append(LineString(t["pts"]).buffer(t["w"] / 2 + CLEARANCE + w / 2 + DIAG_MARGIN))
    for v in vias:
        if v["net"] == net:
            continue
        g = Point(v["x"], v["y"]).buffer(VIA_D / 2 + CLEARANCE + w / 2 + DIAG_MARGIN)
        obs["F.Cu"].append(g); obs["B.Cu"].append(g)
    return obs   # liste di geometrie

NX = int((X2 - X1) / GRID) + 1
NY = int((Y2 - Y1) / GRID) + 1

def gxy(i, j):
    return (X1 + i * GRID, Y1 + j * GRID)

def route_net(net):
    ps = net_pads(net)
    if len(ps) < 2:
        return True
    # con piste fisse: si parte da un pad che le tocca (cosi' sono davvero connesse)
    fixed = [LineString(t["pts"]).buffer(t["w"] / 2) for t in tracks if t["net"] == net and t.get("fixed")]
    if fixed:
        fg = unary_union(fixed)
        ps.sort(key=lambda p: 0 if pad_rect(p, 0.01).intersects(fg) else 1)
    w = track_w(net)
    obs = build_obstacles(net, w)
    robs = build_real_obstacles(net, w)
    raw = raw_metal(net)
    blocked = {}
    margin = EDGE_CLR + w / 2
    im_lo = int(math.ceil(margin / GRID)); im_hi = NX - 1 - im_lo
    jm_lo = int(math.ceil(margin / GRID)); jm_hi = NY - 1 - jm_lo
    for L in ("F.Cu", "B.Cu"):
        arr = bytearray(NX * NY)
        for i in range(NX):
            for j in range(NY):
                if i < im_lo or i > im_hi or j < jm_lo or j > jm_hi:
                    arr[i * NY + j] = 1
        for g in obs[L]:
            b = g.bounds
            i0 = max(0, int((b[0] - X1) / GRID)); i1 = min(NX - 1, int(math.ceil((b[2] - X1) / GRID)))
            j0 = max(0, int((b[1] - Y1) / GRID)); j1 = min(NY - 1, int(math.ceil((b[3] - Y1) / GRID)))
            pg = prep(g)
            for i in range(i0, i1 + 1):
                x = X1 + i * GRID
                for j in range(j0, j1 + 1):
                    if not arr[i * NY + j] and pg.intersects(Point(x, Y1 + j * GRID)):
                        arr[i * NY + j] = 1
        blocked[L] = arr

    def pad_layers(p):
        return ("F.Cu",) if p["kind"] == "smd" else ("F.Cu", "B.Cu")

    # geometria della rete gia' connessa, per layer
    conn = {"F.Cu": [], "B.Cu": []}
    for L in pad_layers(ps[0]):
        conn[L].append(pad_rect(ps[0], 0.05))
    # piste pre-instradate a mano ("fixed") della stessa rete: gia' parte della rete
    for t in tracks:
        if t["net"] == net and t.get("fixed"):
            conn[t["layer"]].append(LineString(t["pts"]).buffer(t["w"] / 2))
    for L, g in EXTRA_CONN.get(net, {}).items():      # bersagli extra (isole di massa)
        conn[L].append(g)
    for v in vias:
        if v["net"] == net and v.get("fixed"):
            vg = Point(v["x"], v["y"]).buffer(VIA_D / 2)
            conn["F.Cu"].append(vg); conn["B.Cu"].append(vg)
    st = STUBS.get((ps[0]["ref"], ps[0]["pin"]))
    if st:
        conn["F.Cu"].append(LineString([(ps[0]["x"], ps[0]["y"]), st]).buffer(0.15))
    remaining = list(range(1, len(ps)))
    ok_all = True
    while remaining:
        cgF = unary_union(conn["F.Cu"]) if conn["F.Cu"] else None
        cgB = unary_union(conn["B.Cu"]) if conn["B.Cu"] else None
        allg = unary_union([g for g in (cgF, cgB) if g is not None])
        remaining.sort(key=lambda k: allg.distance(Point(ps[k]["x"], ps[k]["y"])))
        k = remaining.pop(0)
        tgt = ps[k]
        path = astar(tgt, {"F.Cu": cgF, "B.Cu": cgB}, blocked, net, w, robs)
        attempts = 0
        while path is not None and not validate_path(path, w, raw) and attempts < 4:
            attempts += 1
            print(f"!! path scartato (DRC) {net} -> {tgt['ref']}.{tgt['pin']} (tentativo {attempts})")
            # blocca le celle del percorso incriminato e ritenta
            for (px2, py2, L2) in path:
                i2 = int(round((px2 - X1) / GRID)); j2 = int(round((py2 - Y1) / GRID))
                if 0 <= i2 < NX and 0 <= j2 < NY:
                    blocked[L2][i2 * NY + j2] = 1
            path = astar(tgt, {"F.Cu": cgF, "B.Cu": cgB}, blocked, net, w, robs)
            if path is not None and validate_path(path, w, raw):
                break
        if path is not None and not validate_path(path, w, raw):
            path = None
        if path is None:
            print(f"!! routing fallito {net} -> {tgt['ref']}.{tgt['pin']}")
            ok_all = False
            continue
        emit_path(net, w, path)
        # aggiorna geometria connessa per layer (+ via su entrambi)
        for i2 in range(len(path) - 1):
            (xa, ya, La), (xb, yb, Lb) = path[i2], path[i2 + 1]
            if La == Lb:
                conn[La].append(LineString([(xa, ya), (xb, yb)]).buffer(w / 2))
            else:
                vg = Point(xa, ya).buffer(VIA_D / 2)
                conn["F.Cu"].append(vg); conn["B.Cu"].append(vg)
        for L in pad_layers(tgt):
            conn[L].append(pad_rect(tgt, 0.05))
        st = STUBS.get((tgt["ref"], tgt["pin"]))
        if st:
            conn["F.Cu"].append(LineString([(tgt["x"], tgt["y"]), st]).buffer(0.15))
    return ok_all

def astar(tgt, target_geo_by_layer, blocked, net, w, robs=None):
    """A* dal pad tgt verso la geometria esistente (layer-aware)."""
    start_cells = []
    trect = pad_rect(tgt, 0.02)
    ti0 = max(0, int((trect.bounds[0] - X1) / GRID) - 1)
    ti1 = min(NX - 1, int((trect.bounds[2] - X1) / GRID) + 1)
    tj0 = max(0, int((trect.bounds[1] - Y1) / GRID) - 1)
    tj1 = min(NY - 1, int((trect.bounds[3] - Y1) / GRID) + 1)
    slayers = ("F.Cu",) if tgt["kind"] == "smd" else ("F.Cu", "B.Cu")
    for i in range(ti0, ti1 + 1):
        for j in range(tj0, tj1 + 1):
            if trect.contains(Point(gxy(i, j))):
                for L in slayers:
                    start_cells.append((i, j, L))
    st = STUBS.get((tgt["ref"], tgt["pin"]))
    if st:
        i = round((st[0] - X1) / GRID); j = round((st[1] - Y1) / GRID)
        for di2 in (0, 1, -1):
            for dj2 in (0, 1, -1):
                ii, jj = int(i) + di2, int(j) + dj2
                if 0 <= ii < NX and 0 <= jj < NY and                    abs(gxy(ii, jj)[0] - st[0]) <= 0.5 and abs(gxy(ii, jj)[1] - st[1]) <= 0.5:
                    start_cells.append((ii, jj, "F.Cu"))
    if not start_cells:
        i = round((tgt["x"] - X1) / GRID); j = round((tgt["y"] - Y1) / GRID)
        for L in slayers:
            start_cells.append((int(i), int(j), L))
    tprep = {}
    traw = {}
    bounds = None
    for L, g in target_geo_by_layer.items():
        if g is not None:
            traw[L] = g
            tprep[L] = prep(g.buffer(0.45))
            b = g.bounds
            bounds = b if bounds is None else (min(bounds[0], b[0]), min(bounds[1], b[1]),
                                               max(bounds[2], b[2]), max(bounds[3], b[3]))
    if not tprep:
        return None
    tb = bounds
    dist = {}
    pq = []
    for c in start_cells:
        dist[c] = 0
        x, y = gxy(c[0], c[1])
        h = max(abs(x - (tb[0] + tb[2]) / 2), abs(y - (tb[1] + tb[3]) / 2)) / GRID
        heapq.heappush(pq, (h, 0, c, None))
    came = {}
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1),
             (1, 1, 1.42), (1, -1, 1.42), (-1, 1, 1.42), (-1, -1, 1.42)]
    end = None
    visited = set()
    while pq:
        f, g, cur, parent = heapq.heappop(pq)
        if cur in visited:
            continue
        visited.add(cur)
        came[cur] = parent
        i, j, L = cur
        x, y = gxy(i, j)
        if L in tprep and tprep[L].intersects(Point(x, y)):
            end = cur
            break
        for di, dj, cost in moves:
            ni, nj = i + di, j + dj
            if not (0 <= ni < NX and 0 <= nj < NY):
                continue
            nc = (ni, nj, L)
            if nc in visited:
                continue
            if blocked[L][ni * NY + nj]:
                nx2, ny2 = gxy(ni, nj)
                if not (L in tprep and tprep[L].intersects(Point(nx2, ny2))):
                    continue
                if robs and robs[L] is not None and \
                   robs[L].intersects(LineString([gxy(i, j), (nx2, ny2)])):
                    continue
            elif di != 0 and dj != 0:
                if blocked[L][(i + di) * NY + j] or blocked[L][i * NY + (j + dj)]:
                    continue
            ng = g + cost
            if ng < dist.get(nc, 1e9):
                dist[nc] = ng
                nx_, ny_ = gxy(ni, nj)
                h = max(abs(nx_ - (tb[0] + tb[2]) / 2), abs(ny_ - (tb[1] + tb[3]) / 2)) / GRID
                heapq.heappush(pq, (ng + h, ng, nc, cur))
        oL = "B.Cu" if L == "F.Cu" else "F.Cu"
        nc = (i, j, oL)
        if nc not in visited and not blocked[oL][i * NY + j] and not blocked[L][i * NY + j]:
            via_ok = True
            if robs:
                vgeo = Point(x, y).buffer(VIA_D / 2 - w / 2 + 0.03)
                for LL in ("F.Cu", "B.Cu"):
                    if robs[LL] is not None and robs[LL].intersects(vgeo):
                        via_ok = False; break
            if via_ok:
                ng = g + 25
                if ng < dist.get(nc, 1e9):
                    dist[nc] = ng
                    heapq.heappush(pq, (ng, ng, nc, cur))
    if end is None:
        return None
    seq = []
    c = end
    while c is not None:
        seq.append(c)
        c = came[c]
    seq.reverse()
    path = [(round(gxy(i, j)[0], 3), round(gxy(i, j)[1], 3), L) for (i, j, L) in seq]
    px, py = tgt["x"], tgt["y"]
    st2 = STUBS.get((tgt["ref"], tgt["pin"]))
    d_pad = max(abs(path[0][0] - px), abs(path[0][1] - py))
    d_stub = max(abs(path[0][0] - st2[0]), abs(path[0][1] - st2[1])) if st2 else 9e9
    if d_stub <= 0.7 and d_stub <= d_pad:
        if (st2[0], st2[1]) != path[0][:2]:
            path.insert(0, (st2[0], st2[1], path[0][2]))
    elif d_pad <= GRID:
        path.insert(0, (px, py, path[0][2]))
    # attacco esatto alla geometria target (stesso layer dell'ultimo punto)
    from shapely.ops import nearest_points
    lx, ly, lL = path[-1]
    if lL in traw:
        npt = nearest_points(traw[lL], Point(lx, ly))[0]
        ax, ay = round(npt.x, 3), round(npt.y, 3)
        if (ax, ay) != (lx, ly):
            seg = LineString([(lx, ly), (ax, ay)])
            if not (robs and robs[lL] is not None and robs[lL].intersects(seg)):
                path.append((ax, ay, lL))
    # prepend gia' fatto sopra: verifica anche quello
    if len(path) >= 2 and robs:
        L0 = path[0][2]
        seg0 = LineString([path[0][:2], path[1][:2]])
        if robs[L0] is not None and robs[L0].intersects(seg0) and len(path) > 2:
            path.pop(0)
    return path

def emit_path(net, w, path):
    """spezza il path in segmenti per layer + via nei cambi."""
    cur_layer = path[0][2]
    pts = [(path[0][0], path[0][1])]
    for (x, y, L) in path[1:]:
        if L != cur_layer:
            vias.append(dict(net=net, x=pts[-1][0], y=pts[-1][1]))
            if len(pts) > 1:
                tracks.append(dict(net=net, layer=cur_layer, pts=simplify(pts), w=w))
            pts = [pts[-1]]
            cur_layer = L
        if (x, y) != pts[-1]:
            pts.append((x, y))
    if len(pts) > 1:
        tracks.append(dict(net=net, layer=cur_layer, pts=simplify(pts), w=w))

def simplify(pts):
    out = [pts[0]]
    for p in pts[1:-1]:
        a, b = out[-1], p
        # direzione
        pass
    # rimozione collineari
    res = [pts[0]]
    for i in range(1, len(pts) - 1):
        ax, ay = res[-1]; bx, by = pts[i]; cx, cy = pts[i + 1]
        if (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) == 0 and \
           min(ax, cx) <= bx <= max(ax, cx) and min(ay, cy) <= by <= max(ay, cy):
            continue
        res.append(pts[i])
    res.append(pts[-1])
    return res

# ---------------- ordine di routing ----------------
ROUTE_ORDER = [
    "SW", "VOUT40", "FB", "VREG38", "BIAS", "INV",     # boost/HV corti e critici
    "SIG_IN", "Q1B", "Q1C", "Q2E", "Q2C", "CMP_IN",    # catena di segnale
    "+5V", "+3V3", "+3V6",                              # potenza
    "CTL555", "LED_A",                                  # corti, prima di CMP_Q
    "TH", "TH_W", "TH_HI", "TH_LO", "LE", "CMP_Q", "CMP_QB", "TTL_OUT",
    "VSET", "VADJ_HI", "VADJ_LO", "VREF_B",
    "T555", "LED_K",
    "BUF_Y", "BUF_OUT",                                   # buffer d'uscita
]

def route_all():
    global DIAG_MARGIN
    fails = []
    for net in ROUTE_ORDER:
        if not route_net(net):
            fails.append(net)
    if fails:
        print("retry con margine ridotto:", fails)
        DIAG_MARGIN = 0.08
        still = []
        for net in fails:
            if not route_net(net):
                still.append(net)
        DIAG_MARGIN = 0.22
        fails = still
    return fails

# ---------------- pour GND ----------------
def gnd_pour():
    brd = box(X1 + EDGE_CLR, Y1 + EDGE_CLR, X2 - EDGE_CLR, Y2 - EDGE_CLR)
    obs = []
    for p in pads:
        if p["kind"] != "smd" and p["net"] != "GND":
            clr = HV_CLEAR if p["net"] in HV_NETS else 0.3
            obs.append(pad_rect(p, clr))
    for t in tracks:
        if t["layer"] == "B.Cu" and t["net"] != "GND":
            clr = HV_CLEAR if t["net"] in HV_NETS else 0.3
            obs.append(LineString(t["pts"]).buffer(t["w"] / 2 + clr))
    for v in vias:
        if v["net"] != "GND":
            clr = HV_CLEAR if v["net"] in HV_NETS else 0.3
            obs.append(Point(v["x"], v["y"]).buffer(VIA_D / 2 + clr))
    pour = brd.difference(unary_union(obs)) if obs else brd
    # niente colli piu' stretti di 0,3 mm (come il riempimento di KiCad, min_thickness):
    # un collo sottile non e' un collegamento affidabile
    pour = pour.buffer(-0.15).buffer(0.15)
    # tieni solo il componente connesso piu' grande + quelli che toccano GND
    parts = list(pour.geoms) if isinstance(pour, MultiPolygon) else [pour]
    gnd_items = [Point(v["x"], v["y"]) for v in vias if v["net"] == "GND"]
    gnd_items += [pad_rect(p) for p in pads if p["net"] == "GND" and p["kind"] != "smd"]
    keep = []
    for part in parts:
        if any(part.intersects(g) for g in gnd_items):
            keep.append(part)
    return keep, parts

# ---------------- DRC ----------------
def drc(pour_parts):
    err = []
    per_layer_net = {}
    for p in pads:
        layers = ["F.Cu"] if p["kind"] == "smd" else ["F.Cu", "B.Cu"]
        for L in layers:
            per_layer_net.setdefault((L, p["net"]), []).append(pad_rect(p))
    for t in tracks:
        per_layer_net.setdefault((t["layer"], t["net"]), []).append(
            LineString(t["pts"]).buffer(t["w"] / 2))
    for v in vias:
        for L in ("F.Cu", "B.Cu"):
            per_layer_net.setdefault((L, v["net"]), []).append(
                Point(v["x"], v["y"]).buffer(VIA_D / 2))
    for L in ("B.Cu",):
        for part in pour_parts:
            per_layer_net.setdefault((L, "GND"), []).append(part)
    merged = {k: unary_union(v) for k, v in per_layer_net.items()}
    keys = list(merged)
    for a in range(len(keys)):
        for b in range(a + 1, len(keys)):
            (La, na), (Lb, nb) = keys[a], keys[b]
            if La != Lb or na == nb:
                continue
            need = CLEARANCE - 0.03
            d = merged[keys[a]].distance(merged[keys[b]])
            if d < need:
                from shapely.ops import nearest_points
                p1, p2 = nearest_points(merged[keys[a]], merged[keys[b]])
                err.append(f"clearance {La} {na}<->{nb}: {d:.3f} < {need} @ ({p1.x:.1f},{p1.y:.1f})")
    # fori
    holes = [(p["x"], p["y"], p["drill"]) for p in pads if p["kind"] != "smd"]
    holes += [(v["x"], v["y"], VIA_DRILL) for v in vias]
    for i in range(len(holes)):
        for j in range(i + 1, len(holes)):
            dx = holes[i][0] - holes[j][0]; dy = holes[i][1] - holes[j][1]
            dd = math.hypot(dx, dy) - (holes[i][2] + holes[j][2]) / 2
            if dd < 0.3:
                err.append(f"hole-to-hole {dd:.2f} a {holes[i][:2]}")
    return err

# ---------------- connettivita' ----------------
def snap_to_pads():
    """Il router arriva al rettangolo d'ingombro del pad: su un pad tondo, o su un angolo,
    la pista puo' toccarlo appena (o per niente). Ogni estremo di pista che cade
    sull'ingombro di un pad della stessa rete viene prolungato fino al centro del pad."""
    add = []
    have = {(t["net"], t["layer"], tuple(map(tuple, t["pts"]))) for t in tracks}
    for t in tracks:
        for pt in (t["pts"][0], t["pts"][-1]):
            for p in pads:
                if p["net"] != t["net"] or (p["kind"] == "smd" and t["layer"] != "F.Cu"):
                    continue
                c = (p["x"], p["y"])
                if tuple(pt) != c and pad_rect(p, t["w"] / 2 + 0.05).contains(Point(pt)) \
                        and (t["net"], t["layer"], (tuple(pt), c)) not in have:
                    have.add((t["net"], t["layer"], (tuple(pt), c)))
                    add.append(dict(net=t["net"], layer=t["layer"], pts=[tuple(pt), c], w=t["w"]))
    tracks.extend(add)
    return len(add)

EXTRA_CONN = {}

def net_groups(net, pour_parts):
    """gruppi di pad della rete realmente connessi tra loro (rame reale; ogni pezzo
    del piano di massa e' un'isola a se': due pezzi NON sono connessi tra loro)."""
    ps = net_pads(net)
    geos = []
    for p in ps:
        # rame reale, con almeno 0,03 mm di sovrapposizione richiesta
        geos.append(("pad", pad_shape(p, -0.03), ["F.Cu"] if p["kind"] == "smd" else ["F.Cu", "B.Cu"]))
    for t in tracks:
        if t["net"] == net:
            geos.append(("trk", LineString(t["pts"]).buffer(t["w"] / 2 + 0.01), [t["layer"]]))
    for v in vias:
        if v["net"] == net:
            geos.append(("via", Point(v["x"], v["y"]).buffer(VIA_D / 2 + 0.01), ["F.Cu", "B.Cu"]))
    if net == "GND":
        for part in pour_parts or []:
            geos.append(("pour", part.buffer(0.01), ["B.Cu"]))
    n = len(geos)
    parent = list(range(n))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if set(geos[i][2]) & set(geos[j][2]) and geos[i][1].intersects(geos[j][1]):
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    roots = {}
    for i in range(len(ps)):
        roots.setdefault(find(i), []).append(ps[i])
    return list(roots.values())

def connectivity(pour_parts):
    err = []
    for net in list(NETS):
        groups = net_groups(net, pour_parts)
        if len(groups) > 1:
            det = " | ".join(",".join(f"{p['ref']}.{p['pin']}" for p in g) for g in groups)
            err.append(f"rete {net} non connessa: {det}")
    return err

def gnd_island_culprits(pour_parts):
    """reti le cui piste corrono lungo il bordo delle isole di massa isolate"""
    groups = net_groups("GND", pour_parts)
    main = max(groups, key=len)
    big = max(pour_parts, key=lambda g: g.area)
    out = set()
    for g in groups:
        if g is main:
            continue
        pts = [Point(p["x"], p["y"]) for p in g]
        pts += [Point(v["x"], v["y"]) for v in vias if v["net"] == "GND"
                and any(Point(v["x"], v["y"]).distance(q) < 3 for q in pts)]
        isl = [part for part in pour_parts if part is not big and any(part.distance(q) < 0.5 for q in pts)]
        zone = unary_union(isl + [q.buffer(2.0) for q in pts]).buffer(1.0)
        for t in tracks:
            if t["net"] != "GND" and not t.get("fixed") and zone.intersects(LineString(t["pts"])):
                out.add(t["net"])
    return out

def fix_gnd_islands(max_iter=4):
    """pad GND finiti su un'isola del piano di massa chiusa da altre piste: una pista
    di massa li collega al piano principale (o a una pista/pad GND gia' connessi)."""
    global net_pads
    added = 0
    for _ in range(max_iter):
        pk, _pa = gnd_pour()
        groups = net_groups("GND", pk)
        if len(groups) <= 1:
            return added
        main = max(groups, key=len)
        big = max(pk, key=lambda g: g.area)
        geoF = [pad_shape(p, -0.05) for p in main]
        geoF += [Point(v["x"], v["y"]).buffer(VIA_D / 2) for v in vias
                 if v["net"] == "GND" and big.intersects(Point(v["x"], v["y"]))]
        EXTRA_CONN["GND"] = {"B.Cu": big.buffer(-0.3), "F.Cu": unary_union(geoF)}
        orig = net_pads
        for g in groups:
            if g is main:
                continue
            # il primo pad (gia' nel gruppo principale) fa da seme, il secondo e' l'isola
            net_pads = lambda n, a=main[0], b=g[0]: [a, b] if n == "GND" else orig(n)
            try:
                if route_net("GND"):
                    added += 1
            finally:
                net_pads = orig
        EXTRA_CONN.clear()
    return added

# ---------------- writer ----------------
def U():
    return str(uuid.uuid4())


# serigrafia aggiuntiva (variante didattica): {"F.SilkS": [anelli], "B.SilkS": [...]}.
# Se presente, i riferimenti dei footprint vanno su F.Fab (sono gia' nei poligoni)
# e non si scrive il titolo di default.
SILK_POLYS = None

def write_pcb(fn, pour_parts):
    NETIDS = {"": 0}
    for i, net in enumerate(sorted(NETS), 1):
        NETIDS[net] = i
    o = []
    o.append('(kicad_pcb (version 20211014) (generator rivgen)')
    o.append('  (general (thickness 1.6))')
    o.append('  (paper "A4")')
    o.append('  (layers (0 "F.Cu" signal) (31 "B.Cu" signal)'
             ' (34 "B.Paste" user) (35 "F.Paste" user)'
             ' (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")'
             ' (38 "B.Mask" user) (39 "F.Mask" user)'
             ' (44 "Edge.Cuts" user) (46 "B.CrtYd" user "B.Courtyard")'
             ' (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))')
    o.append('  (setup (pad_to_mask_clearance 0.05) (grid_origin 20 20)')
    o.append('    (pcbplotparams (layerselection 0x00010fc_ffffffff) (disableapertmacros false)'
             ' (usegerberextensions false) (usegerberattributes true) (usegerberadvancedattributes true)'
             ' (creategerberjobfile true) (svguseinch false) (svgprecision 6) (excludeedgelayer true)'
             ' (plotframeref false) (viasonmask false) (mode 1) (useauxorigin false)'
             ' (hpglpennumber 1) (hpglpenspeed 20) (hpglpendiameter 15.000000) (dxfpolygonmode true)'
             ' (dxfimperialunits true) (dxfusepcbnewfont true) (psnegative false) (psa4output false)'
             ' (plotreference true) (plotvalue true) (plotinvisibletext false) (sketchpadsonfab false)'
             ' (subtractmaskfromsilk false) (outputformat 1) (mirror false) (drillshape 1)'
             ' (scaleselection 1) (outputdirectory "gerber")))')
    for net, nid in sorted(NETIDS.items(), key=lambda kv: kv[1]):
        o.append(f'  (net {nid} "{net}")')
    # footprints
    for ref, (x, y, rot) in PLACEMENT.items():
        kind0, value, fpk, _ = COMPONENTS[ref]
        fp = FPS[FP_OF[fpk]]
        o.append(f'  (footprint "rivlib:{fp.name}" (layer "F.Cu") (tstamp {U()}) (at {x} {y} {rot})')
        o.append(f'    (descr "{fp.desc}")')
        o.append(f'    (attr {"smd" if all(pp[4]=="smd" for pp in fp.pads.values()) else "through_hole"})')
        o.append(f'    (fp_text reference "{ref}" (at 0 {fp.courtyard[1] - 0.8} {-rot}) '
                 f'(layer "{"F.Fab" if SILK_POLYS else "F.SilkS"}") '
                 '(effects (font (size 0.8 0.8) (thickness 0.13))) (tstamp %s))' % U())
        o.append(f'    (fp_text value "{value}" (at 0 {fp.courtyard[3] + 0.8} {-rot}) (layer "F.Fab") '
                 '(effects (font (size 0.7 0.7) (thickness 0.11))) (tstamp %s))' % U())
        cx1, cy1, cx2, cy2 = fp.courtyard
        o.append(f'    (fp_rect (start {cx1} {cy1}) (end {cx2} {cy2}) (layer "F.CrtYd") '
                 f'(width 0.05) (fill none) (tstamp {U()}))')
        for (sx1, sy1, sx2, sy2) in fp.silk:
            o.append(f'    (fp_line (start {sx1} {sy1}) (end {sx2} {sy2}) (layer "F.SilkS") '
                     f'(width 0.12) (tstamp {U()}))')
        pnmap = {}
        for p in pads:
            if p["ref"] == ref:
                pnmap[p["pin"]] = p["net"]
        for num, (px, py, w, h, k, drill) in fp.pads.items():
            net = pnmap.get(num)
            nets = f' (net {NETIDS[net]} "{net}")' if net else ''
            num = num.split("#")[0]          # pad multipli dello stesso pin
            if k == "smd":
                o.append(f'    (pad "{num}" smd rect (at {px} {py} {rot}) (size {w} {h}) '
                         f'(layers "F.Cu" "F.Paste" "F.Mask"){nets} (tstamp {U()}))')
            else:
                shape = "rect" if k == "tht_rect" else "circle"
                o.append(f'    (pad "{num}" thru_hole {shape} (at {px} {py} {rot}) (size {w} {h}) '
                         f'(drill {drill}) (layers "*.Cu" "*.Mask"){nets} (tstamp {U()}))')
        o.append('  )')
    # tracks & vias
    for t in tracks:
        nid = NETIDS[t["net"]]
        for a, b in zip(t["pts"], t["pts"][1:]):
            o.append(f'  (segment (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (width {t["w"]}) '
                     f'(layer "{t["layer"]}") (net {nid}) (tstamp {U()}))')
    for v in vias:
        o.append(f'  (via (at {v["x"]} {v["y"]}) (size {VIA_D}) (drill {VIA_DRILL}) '
                 f'(layers "F.Cu" "B.Cu") (net {NETIDS[v["net"]]}) (tstamp {U()}))')
    # edge
    o.append(f'  (gr_rect (start {X1} {Y1}) (end {X2} {Y2}) (layer "Edge.Cuts") (width 0.1) (tstamp {U()}))')
    if SILK_POLYS:
        for layer, rings in SILK_POLYS.items():
            for ring in rings:
                pts = " ".join(f"(xy {x} {y})" for x, y in ring[:-1])
                o.append(f'  (gr_poly (pts {pts}) (layer "{layer}") (width 0) (fill solid) (tstamp {U()}))')
    else:
        o.append(f'  (gr_text "Riv.Cosmici 2024 - Amplif alim soglie - ricostruzione" (at {(X1+X2)/2} {Y2 - 2}) '
                 f'(layer "F.SilkS") (tstamp {U()}) (effects (font (size 1 1) (thickness 0.15))))')
    # zona GND
    def fmt_poly(poly):
        pts = " ".join(f"(xy {round(x,3)} {round(y,3)})" for x, y in poly.exterior.coords)
        return pts
    o.append(f'  (zone (net {NETIDS["GND"]}) (net_name "GND") (layer "B.Cu") (tstamp {U()}) '
             '(hatch edge 0.508)')
    o.append('    (connect_pads (clearance 0.3)) (min_thickness 0.25) (filled_areas_thickness no)')
    o.append('    (fill yes (thermal_gap 0.4) (thermal_bridge_width 0.4))')
    o.append(f'    (polygon (pts (xy {X1} {Y1}) (xy {X2} {Y1}) (xy {X2} {Y2}) (xy {X1} {Y2})))')
    for part in pour_parts:
        o.append(f'    (filled_polygon (layer "B.Cu") (island? no)(pts {fmt_poly(part)}))')
    o.append('  )')
    o.append(')')
    txt = "\n".join(o) + "\n"
    txt = txt.replace("(island? no)", "")
    with open(fn, "w") as f:
        f.write(txt)
    print("scritto", fn, f"({len(tracks)} tracce, {len(vias)} via)")

# ---------------- main ----------------
def main(out_pcb="riv_cosmici/riv_cosmici.kicad_pcb", state="routing_state.json"):
    bad = check_courtyards()
    if bad:
        print("COURTYARD:", bad)
    # rip-up & retry: se qualche rete fallisce si riparte da zero
    # instradando per prime le reti fallite (fino a 8 tentativi)
    base_order = list(ROUTE_ORDER)
    first = []
    for attempt in range(8):
        tracks.clear(); vias.clear()
        ROUTE_ORDER[:] = first + [n for n in base_order if n not in first]
        add_escape_stubs()
        add_gnd_vias()
        fails = route_all()
        snap_to_pads()
        fix_gnd_islands()
        if not fails:
            # anche errori di DRC o reti aperte dopo il routing contano come falliti
            _pk, _pa = gnd_pour()
            bad = set()
            for e in drc(_pk) + connectivity(_pk):
                for n in re.findall(r"[A-Z+][A-Z0-9_+]*", str(e)):
                    if n in NETS and n != "GND":
                        bad.add(n)
            # isole del piano di massa: si rifanno per prime le reti che le chiudono
            if len(net_groups("GND", _pk)) > 1:
                bad |= gnd_island_culprits(_pk)
            fails = sorted(bad)
            if not fails:
                break
            print(f"tentativo {attempt + 1}: errori DRC/connettivita' su {fails}")
        print(f"tentativo {attempt + 1}: falliti {fails} -> riprovo con queste reti per prime")
        first = fails + [n for n in first if n not in fails]
    # dedupe (il retry puo' duplicare percorsi identici)
    seen = set(); tt = []
    for t in tracks:
        key = (t["net"], t["layer"], tuple(t["pts"]), t["w"])
        if key not in seen:
            seen.add(key); tt.append(t)
    tracks[:] = tt
    seen = set(); vv = []
    for v in vias:
        key = (v["net"], v["x"], v["y"])
        if key not in seen:
            seen.add(key); vv.append(v)
    vias[:] = vv
    pour_keep, pour_all = gnd_pour()
    errs = drc(pour_keep)
    cerr = connectivity(pour_keep)
    for e in errs[:40]:
        print("DRC:", e)
    for e in cerr:
        print("CONN:", e)
    import json
    json.dump({"tracks": tracks, "vias": vias,
               "pour": [list(p.exterior.coords) for p in pour_keep],
               "pour_holes": [[list(h.coords) for h in p.interiors] for p in pour_keep]},
              open(state, "w"))
    write_pcb(out_pcb, pour_keep)
    print("routing falliti:", fails)
    print("DRC err:", len(errs), " CONN err:", len(cerr))
    return fails, errs, cerr


if __name__ == "__main__":
    main()
