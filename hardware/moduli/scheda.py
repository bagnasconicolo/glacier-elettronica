# -*- coding: utf-8 -*-
"""Costruttore dei PCB dei moduli (KiCad 7, script Python di pcbnew).

Da una DESCRIZIONE (modulo Python della scheda: componenti, reti, piazzamento, contorno,
fessure, scritte) produce, nella cartella della scheda:

  <nome>.kicad_pcb       PCB instradato (Freerouting), piani di massa riempiti da KiCad
  gerber/ + <nome>_gerber.zip   Gerber e foratura scritti da KiCad (kicad-cli)
  jlcpcb/BOM_JLCPCB.csv, CPL_JLCPCB.csv   per il montaggio
  anteprima_<nome>.png   rame sopra e sotto, serigrafia, contorno

Le impronte sono quelle della libreria 'moduli' (librerie/moduli.pretty: copie delle
ufficiali KiCad 7.0.11 + RPi_Pico2_Socket + LEMO_EPL00 del rivelatore).

Freerouting (autorouter, Java) si scarica la prima volta in ~/.cache/freerouting.
Il DRC e i controlli schema/PCB li fa ../generator/verifica_kicad.py (stesso del rivelatore).
"""
import csv, os, shutil, subprocess, urllib.request, zipfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _sys
_sys.path.insert(0, os.path.join(HERE, "..", "generator"))
from gen_sch import sym_uuid                                  # noqa: E402  (stesso UUID dello schema)
LIB = os.path.join(HERE, "librerie", "moduli.pretty")
# Freerouting 1.9.0: salva il file .ses ed esce da solo (la 2.0.1 senza interfaccia esce
# prima di aver scritto il risultato). Serve un display: xvfb-run.
FR_URL = "https://github.com/freerouting/freerouting/releases/download/v1.9.0/freerouting-1.9.0.jar"
FR_JAR = os.path.join(os.path.expanduser("~"), ".cache", "freerouting", "freerouting-1.9.0.jar")
mm = pcbnew.FromMM

# regole (dentro le capacita' standard di JLCPCB: 0,127 mm piste/isolamento, foro 0,3 mm)
CLEARANCE = 0.15          # i pad dell'LGA a passo 0,5 mm distano 0,15 mm
TRACK = 0.25
VIA_D, VIA_DRILL = 0.6, 0.3
EDGE = 0.3


NON_MONTATI = ("MH", "SJ2", "SJ3")          # fori e ponticelli a stagno: solo rame, niente da montare


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def _edge(board, pts, closed=True):
    seq = list(pts) + ([pts[0]] if closed else [])
    for a, b in zip(seq, seq[1:]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(V(*a))
        s.SetEnd(V(*b))
        s.SetWidth(mm(0.1))
        board.Add(s)


def _text(board, t, x, y, size=1.0, layer="F", rot=0, bold=False, just="center"):
    layer = {"F": pcbnew.F_SilkS, "B": pcbnew.B_SilkS}.get(layer, layer)
    tx = pcbnew.PCB_TEXT(board)
    tx.SetText(t)
    tx.SetPosition(V(x, y))
    tx.SetLayer(layer)
    tx.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    tx.SetTextThickness(mm(size * (0.2 if bold else 0.15)))
    tx.SetTextAngleDegrees(rot)
    if just == "left":
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    elif just == "right":
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    if layer == pcbnew.B_SilkS:
        tx.SetMirrored(True)
    board.Add(tx)


def _zone(board, net, layer, poly, keepout=False, priority=0):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    if keepout:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(True)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
    else:
        z.SetNet(net)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetMinThickness(mm(0.25))
        z.SetLocalClearance(mm(0.3))
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetAssignedPriority(priority)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in poly:
        ol.Append(mm(x), mm(y))
    board.Add(z)
    return z


def _sexpr(text):
    """lettore minimo di s-espressioni (file .ses di Freerouting)"""
    import re
    tok = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', text)
    st = [[]]
    for t in tok:
        if t == "(":
            st.append([])
        elif t == ")":
            e = st.pop()
            st[-1].append(e)
        else:
            st[-1].append(t.strip('"'))
    return st[0][0]


def importa_ses(board, ses):
    """aggiunge alla scheda piste e via del file .ses (ImportSpecctraSES di KiCad 7
    funziona solo nell'interfaccia grafica). Coordinate in decimi di um, Y rovesciata."""
    s = _sexpr(open(ses).read())
    routes = next(e for e in s if isinstance(e, list) and e and e[0] == "routes")
    res = next(e for e in routes if isinstance(e, list) and e[0] == "resolution")
    k = {"um": 1e-3, "mm": 1.0, "mil": 0.0254}[res[1]] / float(res[2])       # mm per unita'
    pads = {}                                                              # padstack -> (diametro, foro)
    lib = next((e for e in routes if isinstance(e, list) and e[0] == "library_out"), [])
    import re
    for e in lib[1:]:
        if isinstance(e, list) and e[0] == "padstack":
            m = re.search(r"_(\d+):(\d+)_um", e[1])
            if m:
                pads[e[1]] = (int(m.group(1)) / 1000, int(m.group(2)) / 1000)
    nets = {n.GetNetname(): n for n in board.GetNetsByName().values()}
    netout = next(e for e in routes if isinstance(e, list) and e[0] == "network_out")
    nt = nv = 0
    for ne in netout[1:]:
        net = nets[ne[1]]
        for e in ne[2:]:
            if e[0] == "wire":
                path = next(x for x in e[1:] if isinstance(x, list) and x[0] == "path")
                layer = board.GetLayerID(path[1])
                w = float(path[2]) * k
                pts = [(float(path[i]) * k, -float(path[i + 1]) * k) for i in range(3, len(path) - 1, 2)]
                for a, c in zip(pts, pts[1:]):
                    t = pcbnew.PCB_TRACK(board)
                    t.SetStart(V(*a))
                    t.SetEnd(V(*c))
                    t.SetWidth(mm(w))
                    t.SetLayer(layer)
                    t.SetNet(net)
                    board.Add(t)
                    nt += 1
            elif e[0] == "via":
                d, dr = pads.get(e[1], (VIA_D, VIA_DRILL))
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(V(float(e[2]) * k, -float(e[3]) * k))
                v.SetWidth(mm(d))
                v.SetDrill(mm(dr))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNet(net)
                board.Add(v)
                nv += 1
    return nt, nv


def pota_mozziconi(board, senza=("GND",)):
    """accorcia o toglie i tratti di pista con un estremo libero (es. una pista fissa
    oltre il punto dove Freerouting ha messo la via). Le reti in `senza` (quelle col
    piano, che si collega dopo) non si toccano. Ritorna quanti tratti ha toccato."""
    def attacchi(t):
        """punti (sulla pista t) dove si collega qualcos'altro della stessa rete e strato"""
        pts, uid = [], t.m_Uuid.AsString()
        for o in board.GetTracks():                    # (i wrapper SWIG cambiano a ogni lettura:
            if o.m_Uuid.AsString() == uid or o.GetNetCode() != t.GetNetCode():   # confronto per UUID)
                continue
            if o.GetClass() == "PCB_VIA":
                if t.HitTest(o.GetPosition(), 0):
                    pts.append(o.GetPosition())
            elif o.GetLayer() == t.GetLayer():
                for q in (o.GetStart(), o.GetEnd()):
                    if t.HitTest(q, 0):
                        pts.append(q)
                for q in (t.GetStart(), t.GetEnd()):          # a T sul tratto di un'altra pista
                    if o.HitTest(q, 0):
                        pts.append(q)
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.GetNetCode() == t.GetNetCode() and p.IsOnLayer(t.GetLayer()):
                    for q in (t.GetStart(), t.GetEnd()):
                        if p.HitTest(q):
                            pts.append(q)
        return pts

    toccati, cambiato = 0, True
    while cambiato:
        cambiato = False
        for t in list(board.GetTracks()):
            if t.GetClass() != "PCB_TRACK" or t.GetNetname() in senza:
                continue
            att = attacchi(t)
            for fisso, libero, setter in ((t.GetStart(), t.GetEnd(), t.SetEnd),
                                          (t.GetEnd(), t.GetStart(), t.SetStart)):
                if any((q - libero).EuclideanNorm() < 1000 for q in att):
                    continue                                   # estremo collegato
                altri = [q for q in att if (q - fisso).EuclideanNorm() >= 1000]
                if not altri:
                    if any((q - fisso).EuclideanNorm() < 1000 for q in att) or not att:
                        board.Remove(t)                        # mozzicone intero
                else:
                    setter(min(altri, key=lambda q: (q - libero).EuclideanNorm()))
                toccati += 1
                cambiato = True
                break
            if cambiato:
                break
    return toccati


def freerouting():
    if not os.path.exists(FR_JAR):
        os.makedirs(os.path.dirname(FR_JAR), exist_ok=True)
        print("scarico Freerouting ...")
        urllib.request.urlretrieve(FR_URL, FR_JAR)
    return FR_JAR


def costruisci(D, outdir, instrada=True, passate=30):
    """D: modulo di descrizione della scheda. Ritorna il percorso del .kicad_pcb."""
    os.makedirs(outdir, exist_ok=True)
    nome = D.NOME
    pcb_path = os.path.join(outdir, nome + ".kicad_pcb")
    b = pcbnew.BOARD()
    ds = b.GetDesignSettings()
    ds.m_CopperEdgeClearance = mm(EDGE)
    ds.m_MinClearance = mm(0.127)        # minimo assoluto (JLCPCB); la regola normale e' CLEARANCE
    ds.m_TrackMinWidth = mm(0.2)
    ds.m_ViasMinSize = mm(VIA_D)
    ds.m_MinThroughDrill = mm(VIA_DRILL)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(mm(CLEARANCE))
    nc.SetTrackWidth(mm(TRACK))
    nc.SetViaDiameter(mm(VIA_D))
    nc.SetViaDrill(mm(VIA_DRILL))
    # classe "potenza" per le alimentazioni (Freerouting la legge dal DSN)
    pw = pcbnew.NETCLASS("Potenza")
    pw.SetClearance(mm(CLEARANCE))
    pw.SetTrackWidth(mm(getattr(D, "TRACK_POTENZA", 0.4)))
    pw.SetViaDiameter(mm(VIA_D))
    pw.SetViaDrill(mm(VIA_DRILL))
    ds.m_NetSettings.m_NetClasses["Potenza"] = pw

    # contorno e fessure (Edge.Cuts). Attorno alle fessure interne un'area di divieto larga
    # quanto la distanza dal bordo (Freerouting per le fessure usa la distanza tra piste)
    _edge(b, D.CONTORNO)
    from shapely.geometry import Polygon as _P
    for f in getattr(D, "FESSURE", ()):
        _edge(b, f)
        ring = list(_P(f).buffer(EDGE + 0.02, join_style=2).exterior.coords)[:-1]
        z = _zone(b, None, pcbnew.F_Cu, ring, keepout=True)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.F_Cu)
        ls.AddLayer(pcbnew.B_Cu)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowCopperPour(False)
    # reti
    nets = {}
    for n in D.NETS:
        ni = pcbnew.NETINFO_ITEM(b, n)
        b.Add(ni)
        nets[n] = ni
        if n in getattr(D, "RETI_POTENZA", ()):
            ni.SetNetClass(ds.m_NetSettings.m_NetClasses["Potenza"])
    pin_net = {(r, str(p)): n for n, pins in D.NETS.items() for r, p in pins}
    # componenti
    for ref, (kind, value, fpk, extra) in D.COMPONENTS.items():
        x, y, rot = D.PLACEMENT[ref][:3]
        lato = D.PLACEMENT[ref][3] if len(D.PLACEMENT[ref]) > 3 else "F"
        fp = pcbnew.FootprintLoad(LIB, D.FP[fpk])
        if fp is None:
            raise SystemExit(f"impronta mancante: {D.FP[fpk]}")
        fp.SetFPID(pcbnew.LIB_ID("moduli", D.FP[fpk]))
        fp.SetPath(pcbnew.KIID_PATH("/" + sym_uuid(ref)))      # abbina simbolo e impronta in KiCad
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPosition(V(x, y))
        b.Add(fp)
        if lato == "B":
            fp.Flip(V(x, y), False)
        fp.SetOrientationDegrees(rot)
        if ref in getattr(D, "CLEARANCE_LOCALE", {}):          # es. LGA a passo fine: disegno del costruttore
            fp.SetLocalClearance(mm(D.CLEARANCE_LOCALE[ref]))
        for p in fp.Pads():
            n = pin_net.get((ref, p.GetNumber()))
            if n:
                p.SetNet(nets[n])
                if ref in getattr(D, "PAD_PIENI", ()) and n == "GND":
                    p.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        rt = fp.Reference()
        rt.SetVisible(getattr(D, "RIF_VISIBILI", {}).get(ref, True))
        rt.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        rt.SetTextThickness(mm(0.13))
        if ref in getattr(D, "RIF_POS", {}):                     # posizione scelta a mano
            dx, dy = D.RIF_POS[ref][:2]
            rt.SetPosition(V(x + dx, y + dy))
            rt.SetTextAngleDegrees(D.RIF_POS[ref][2] if len(D.RIF_POS[ref]) > 2 else 0)
            rt.SetKeepUpright(True)
        fp.Value().SetVisible(False)
    # scritte
    for t in getattr(D, "SCRITTE", ()):
        _text(b, *t[:3], **(t[3] if len(t) > 3 else {}))
    # piste tracciate a mano (bloccate: Freerouting le tiene e instrada il resto)
    for net, larg, pts in getattr(D, "PISTE_FISSE", ()):
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(V(*a))
            t.SetEnd(V(*c))
            t.SetWidth(mm(larg))
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(nets[net])
            t.SetLocked(True)
            b.Add(t)
    b.Save(pcb_path)

    if instrada:
        dsn = os.path.join(outdir, nome + ".dsn")
        ses = os.path.join(outdir, nome + ".ses")
        if not pcbnew.ExportSpecctraDSN(b, dsn):
            raise SystemExit("esportazione DSN fallita")
        if os.path.exists(ses):
            os.remove(ses)
        # ottimizzazione su un solo thread: quella multi-thread puo' creare violazioni di
        # distanza (avviso del programma stesso)
        cmd = ["xvfb-run", "-a", "java", "-jar", freerouting(), "-de", dsn, "-do", ses,
               "-mp", str(passate), "-mt", "1"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        log = (r.stdout + r.stderr)
        open(os.path.join(outdir, "freerouting.log"), "w").write(log)
        if not os.path.exists(ses) or os.path.getsize(ses) == 0:
            raise SystemExit("Freerouting non ha prodotto il file .ses (vedi freerouting.log)")
        nt, nv = importa_ses(b, ses)
        # il .ses riporta anche le piste fisse: tolgo i doppioni
        visti, doppi = set(), []
        for t in b.GetTracks():
            if t.GetClass() != "PCB_TRACK":
                continue
            a, c = sorted([(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)])
            key = (a, c, t.GetLayer(), t.GetNetname())
            if key in visti:
                doppi.append(t)
            visti.add(key)
        for t in doppi:
            b.Remove(t)
        nt -= len(doppi)
        print(f"Freerouting: {nt} tratti di pista, {nv} via; mozziconi potati: {pota_mozziconi(b)}")
        for f in (dsn, ses):
            os.remove(f)
    b.Save(pcb_path)
    # piani di massa su entrambi i lati: sulla scheda ricaricata da file (riempire le zone
    # di una scheda costruita in memoria manda in crash pcbnew 7)
    b = pcbnew.LoadBoard(pcb_path)
    gnd = b.FindNet("GND")
    if gnd is not None:
        for L in (pcbnew.F_Cu, pcbnew.B_Cu):
            _zone(b, gnd, L, D.CONTORNO)
    # aree senza piano (es. sotto il sensore di umidita'): aggiunte DOPO il routing, perche'
    # nel DSN KiCad le esporta come divieto anche per le piste
    for poly in getattr(D, "SENZA_RAME", ()):
        for L in (pcbnew.F_Cu, pcbnew.B_Cu):
            _zone(b, None, L, poly, keepout=True)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(pcb_path)
    return pcb_path


def fabbricazione(D, outdir):
    """Gerber + foratura (kicad-cli), anteprima, BOM/CPL JLCPCB"""
    nome = D.NOME
    pcb = os.path.join(outdir, nome + ".kicad_pcb")
    g = os.path.join(outdir, "gerber")
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(g)
    layers = "F.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
    subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "-o", g + "/", "-l", layers,
                    "--subtract-soldermask", pcb], check=True, capture_output=True)
    subprocess.run(["kicad-cli", "pcb", "export", "drill", "-o", g + "/", "--format", "excellon",
                    "--drill-origin", "absolute", "--excellon-separate-th", "-u", "mm", pcb],
                   check=True, capture_output=True)
    z = os.path.join(outdir, nome + "_gerber.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(g)):
            zf.write(os.path.join(g, f), f)
    # anteprima: rame sopra/sotto, serigrafia, contorno
    svg = os.path.join(outdir, "anteprima.svg")
    subprocess.run(["kicad-cli", "pcb", "export", "svg", "-o", svg, "--page-size-mode", "2",
                    "--exclude-drawing-sheet", "-l", "B.Cu,F.Cu,F.Silkscreen,Edge.Cuts", pcb],
                   check=True, capture_output=True)
    try:
        import cairosvg
        cairosvg.svg2png(url=svg, write_to=os.path.join(outdir, f"anteprima_{nome}.png"),
                         output_width=getattr(D, "ANTEPRIMA_PX", 1600), background_color="white")
        os.remove(svg)
    except Exception as e:                                       # noqa: BLE001
        print("anteprima PNG non creata:", e)
    # BOM e CPL per JLCPCB
    b = pcbnew.LoadBoard(pcb)
    jd = os.path.join(outdir, "jlcpcb")
    os.makedirs(jd, exist_ok=True)
    groups = {}
    for ref, (kind, value, fpk, extra) in D.COMPONENTS.items():
        if ref in D.DNP or kind in NON_MONTATI:
            continue
        mpn, lcsc = D.CODICI.get((value, fpk), ("", ""))
        groups.setdefault((value, D.FP[fpk], mpn, lcsc), []).append(ref)
    with open(os.path.join(jd, "BOM_JLCPCB.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "JLCPCB Part #"])
        for (value, fp, mpn, lcsc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
            w.writerow([mpn or value, ",".join(sorted(refs)), fp, lcsc])
    x0 = pcbnew.ToMM(b.GetBoardEdgesBoundingBox().GetX())
    y1 = pcbnew.ToMM(b.GetBoardEdgesBoundingBox().GetBottom())
    with open(os.path.join(jd, "CPL_JLCPCB.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for fp in sorted(b.GetFootprints(), key=lambda fp: fp.GetReference()):
            ref = fp.GetReference()
            if ref in D.DNP or D.COMPONENTS[ref][0] in NON_MONTATI:
                continue
            p = fp.GetPosition()
            w.writerow([ref, f"{pcbnew.ToMM(p.x) - x0:.3f}mm", f"{y1 - pcbnew.ToMM(p.y):.3f}mm",
                        "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom",
                        f"{fp.GetOrientationDegrees() % 360:.0f}"])
    shutil.copy(z, os.path.join(jd, os.path.basename(z)))
    return z


def librerie_progetto(outdir):
    """sym-lib-table e fp-lib-table del progetto KiCad della scheda"""
    rel_lib = os.path.relpath(LIB, outdir)
    rel_sym = os.path.relpath(os.path.join(HERE, "..", "riv.kicad_sym"), outdir)
    open(os.path.join(outdir, "fp-lib-table"), "w").write(
        f'(fp_lib_table\n  (lib (name "moduli")(type "KiCad")(uri "${{KIPRJMOD}}/{rel_lib}")(options "")(descr ""))\n)\n')
    open(os.path.join(outdir, "sym-lib-table"), "w").write(
        f'(sym_lib_table\n  (lib (name "riv")(type "KiCad")(uri "${{KIPRJMOD}}/{rel_sym}")(options "")(descr ""))\n)\n')
