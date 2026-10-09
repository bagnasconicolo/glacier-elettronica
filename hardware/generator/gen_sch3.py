# -*- coding: utf-8 -*-
"""Schema della VARIANTE A 3 CANALI (foglio A1).

Riusa il disegno della scheda a 1 canale (gen_sch.build_single): ogni blocco di
canale viene ridisegnato 3 volte, spostato in basso di 180 mm, con riferimenti e
reti rinominati per canale (netdata3.chref: R9 -> R109/R209/R309, CMP_IN ->
CMP_IN1/2/3). Le parti comuni (boost, 3,3 V, riferimenti 3,6 V) sono disegnate
una volta sola a destra; poi coincidenza AND e test point.

    python gen_sch3.py   ->  riv_cosmici_3ch/riv_cosmici_3ch.kicad_sch
"""
import inspect, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import netdata3                                   # noqa: E402
sys.modules["netdata"] = netdata3                 # gen_sch usa il modello a 3 canali
import gen_sch as G                               # noqa: E402
from symlib import SYMS                           # noqa: E402

CH_DY = 180.0                 # passo verticale tra i canali (mm)
SX, SY = 300.0, 0.0           # spostamento delle parti comuni
SHARED_LABELS = {"VOUT40", "VREF_B"}

# ------------------------------------------------- sorgente dei blocchi
SRC = inspect.getsource(G.build_single)
BLOCKS = {}
for m in re.finditer(r"    # ---- blocco (\d+):[^\n]*\n(.*?)(?=    # ---- blocco |\Z)", SRC, re.S):
    BLOCKS[int(m.group(1))] = "\n".join(l[4:] for l in m.group(2).split("\n"))
main_title = re.search(r'\nT\("Riv\. Cosmici 2024[^\n]*', BLOCKS[9])
BLOCKS[9] = BLOCKS[9][:main_title.start()] if main_title else BLOCKS[9]


def cut(text, start, end_incl):
    a = text.index(start)
    b = text.index(end_incl, a) + len(end_incl)
    return text[:a] + text[b:]


# blocco 3 senza U5/CF4 (comuni)
CH3 = cut(BLOCKS[3], "# LP2985 3,6V (U5)", 'T("Rif. soglia 3,6V", 140, 85)')
U5_PART = BLOCKS[3][BLOCKS[3].index("# LP2985 3,6V (U5)"):]
# blocco 7: D1 va all'etichetta VREF_B; CF7/U7 sono comuni
B7 = BLOCKS[7]
i7 = B7.index("path((132.08, 184.15), (137.16, 184.15)")
CH7 = B7[:i7] + ('w(132.08, 184.15, 137.16, 184.15); L("VREF_B", 137.16, 184.15)\n'
                 'T("regolazione tensione (V1)", 112, 190)\n')
U7_PART = ('path((137.16, 184.15), (143.51, 184.15), (144.78, 184.15)); L("VREF_B", 137.16, 184.15)\n'
           + B7[B7.index('place("CF7"'):])
U7_PART = U7_PART.replace('T("regolazione tensione (V1)", 112, 190)\n', "")
# blocco 9: etichetta BUF_Y sull'uscita del buffer (verso il jumper della coincidenza)
CH9 = BLOCKS[9].replace('w(284.48, 160.02, 288.29, 160.02)',
                        'w(284.48, 160.02, 288.29, 160.02); L("BUF_Y", 286.385, 160.02)')
CH9 = CH9.replace('T("Buffer uscita 3,3V -> Raspberry Pi (74LVC1G17)", 262, 136)',
                  'T("Buffer uscita 3,3V (74LVC1G17) -> LEMO", 262, 136)')
# etichetta SIG_IN sul filo J1 -> C7 (serve al test point del canale)
CH1 = BLOCKS[1] + '\nL("SIG_IN", 48.26, 61.27)\n'
CHANNEL_SRC = "\n".join([CH1, BLOCKS[2], CH3, BLOCKS[5], CH7, CH9])
SHARED_SRC = "\n".join([BLOCKS[6], BLOCKS[8], U5_PART, U7_PART])


def run(src, dx, dy, n=None):
    """esegue un blocco con coordinate spostate e (se n) nomi di canale"""
    R = (lambda r: netdata3._ref(r, n)) if n else (lambda r: r)
    Ln = (lambda s: s if (n is None or s in SHARED_LABELS) else f"{s}{n}")
    ns = dict(
        place=lambda ref, x, y, rot=0, mirror=None, sym=None:
            G.place(R(ref), x + dx, y + dy, rot, mirror, sym),
        w=lambda x1, y1, x2, y2: G.w(x1 + dx, y1 + dy, x2 + dx, y2 + dy),
        path=lambda *pts: G.path(*[(x + dx, y + dy) for x, y in pts]),
        J=lambda x, y: G.J(round(x + dx, 3), round(y + dy, 3)),
        L=lambda s, x, y: G.L(Ln(s), round(x + dx, 3), round(y + dy, 3)),
        PW=lambda net, x, y, rot=0: G.PW(net, round(x + dx, 3), round(y + dy, 3), rot),
        NCm=lambda x, y: G.NCm(round(x + dx, 3), round(y + dy, 3)),
        T=lambda s, x, y: G.T(s, x + dx, y + dy),
        FLG=lambda x, y: G.FLG(round(x + dx, 3), round(y + dy, 3)),
    )
    exec(src, ns)


# ------------------------------------------------- piazzamento con "moncherini"
POWER = {"GND", "+5V", "+3V3", "+3V6"}


def stub(ref, x, y, rot=0, sym=None, nets=None, length=2.54):
    """piazza un simbolo e collega ogni pin con un filo corto + etichetta/alimentazione"""
    G.place(ref, x, y, rot, None, sym)
    symname = sym or G.SYM_MAP[netdata3.COMPONENTS[ref][0]]
    for num, (px, py, ang, *_r) in SYMS[symname].pins.items():
        net = (nets or {}).get(num)
        if net is None:
            continue
        sx, sy = G.pin_sheet_pos(symname, x, y, rot, None, px, py)
        # direzione verso l'esterno (opposta al verso del pin), poi rotazione del simbolo
        a = (ang + 180 + rot) % 360
        ux, uy = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[a]
        ex, ey = round(sx + ux * length, 3), round(sy + uy * length, 3)
        G.w(sx, sy, ex, ey)
        if net == "NC":
            G.NCm(sx, sy)
        elif net in POWER:
            G.PW(net, ex, ey, 180 if (net == "GND" and uy < 0) else 0)
        else:
            G.L(net, ex, ey)


def build():
    for n in netdata3.CHANNELS:
        dy = (n - 1) * CH_DY
        run(CHANNEL_SRC, 0, dy, n)
        G.T(f"CANALE {n}", 20, 24 + dy)
        # test point del canale nello spazio libero (dove nella scheda singola c'era il boost)
        for i, net in enumerate(netdata3.TP_CH, 1):
            ref = f"TP{n}{i:02d}"
            stub(ref, 50 + (i - 1) * 10.16, 150 + dy,
                 nets={"1": net if net == "GND" else f"{net}{n}"})
        G.T(f"Test point canale {n}", 48, 142 + dy)
    run(SHARED_SRC, SX, SY)
    G.T("PARTI COMUNI: boost 41,7 V, 3,3 V, riferimenti 3,6 V", 340, 128)
    # ---- coincidenza AND a 3
    cx, cy = 420.0, 260.0
    G.T("COINCIDENZA: AND a 3 canali (jumper aperto = canale escluso)", 360, cy - 30)
    for k, n in enumerate(netdata3.CHANNELS):
        yy = cy - 15 + k * 12.7
        stub(f"JP{n}", 385.0, yy, nets={"1": f"BUF_Y{n}", "2": f"AND_IN{n}"})
        stub(f"R3{n}", 402.0, yy, rot=90, nets={"1": f"AND_IN{n}", "2": "+3V3"})
    stub("U10", cx, cy, nets={"1": "AND_IN1", "3": "AND_IN2", "6": "AND_IN3",
                              "4": "AND_Y", "5": "+3V3", "2": "GND"})
    stub("CF11", cx + 15, cy - 10, nets={"1": "+3V3", "2": "GND"})
    stub("R30", cx + 22, cy + 10, rot=90, nets={"1": "AND_Y", "2": "AND_OUT"})
    stub("J5", cx + 45, cy + 12, nets={"1": "AND_OUT", "2": "GND"})
    G.T("LEMO AND", cx + 40, cy + 4)
    # ---- test point comuni
    G.T("Test point comuni", 360, 330)
    for i, net in enumerate(netdata3.TP_SHARED, 1):
        stub(f"TP{i}", 362 + (i - 1) * 12.7, 342, nets={"1": net})
    G.T("Riv. Cosmici 2024 - VARIANTE 3 CANALI + coincidenza - da INFN sez. Torino (S. Gallian, rev. A)",
        200, 12)


if __name__ == "__main__":
    netdata3.check()
    build()
    ok = G.check_connectivity()
    out = os.path.join(HERE, "riv_cosmici_3ch")
    os.makedirs(out, exist_ok=True)
    G.write_sch(os.path.join(out, "riv_cosmici_3ch.kicad_sch"), paper="A1",
                title="Riv. Cosmici 2024 - 3 canali + coincidenza")
    if not ok:
        raise SystemExit(1)
