# -*- coding: utf-8 -*-
"""PDF in scala 1:1 (A4) della scheda a 3 canali, da stampare su carta per
verificare ingombri e fori (es. appoggiando i LEMO veri).

    python stampa_1a1.py  ->  ../variante_3ch/stampa_1a1_riv_cosmici_3ch.pdf
Pagina 1: lato componenti (pad, fori, serigrafia, contorno).
Pagina 2: piste (rame sopra in nero, sotto in grigio) con pad e fori.
Stampare al 100% / "dimensione effettiva": la barra da 50 mm va verificata col righello.
"""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import silk3                                        # imposta netdata3 / pcb_data3
import pcb_data as PD
import cairosvg
from pypdf import PdfWriter, PdfReader

X1, Y1, X2, Y2 = silk3.X1, silk3.Y1, silk3.X2, silk3.Y2
PW, PH = 210.0, 297.0
OX, OY = (PW - (X2 - X1)) / 2 - X1, 50.0 - Y1        # scheda centrata, 50 mm dall'alto... vedi sotto
OY = (PH - (Y2 - Y1)) / 2 + 6 - Y1
st = json.load(open(os.path.join(HERE, "riv_cosmici_3ch", "routing_state.json")))
silk = json.load(open(os.path.join(HERE, "riv_cosmici_3ch", "silk.json")))


def poly(pts, **a):
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in a.items())
    return '<polygon points="' + " ".join(f"{x + OX:.3f},{y + OY:.3f}" for x, y in pts) + f'" {attrs}/>'


def page(title, body):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}mm" height="{PH}mm" viewBox="0 0 {PW} {PH}">',
         f'<rect width="{PW}" height="{PH}" fill="white"/>']
    s += body
    # contorno scheda
    s.append(f'<rect x="{X1 + OX}" y="{Y1 + OY}" width="{X2 - X1}" height="{Y2 - Y1}" fill="none" stroke="black" stroke-width="0.25"/>')
    # testo e barre di scala
    s.append(f'<text x="8" y="9" font-family="DejaVu Sans" font-size="4" font-weight="bold">{title}</text>')
    s.append('<text x="8" y="14" font-family="DejaVu Sans" font-size="2.8">Stampare al 100% ("dimensione effettiva"), NON "adatta alla pagina". '
             'Controllare le barre col righello: 50 mm.</text>')
    yb = PH - 9
    s.append(f'<line x1="8" y1="{yb}" x2="58" y2="{yb}" stroke="black" stroke-width="0.4"/>')
    for x in range(8, 59, 10):
        s.append(f'<line x1="{x}" y1="{yb - 1.5}" x2="{x}" y2="{yb + 1.5}" stroke="black" stroke-width="0.3"/>')
    s.append(f'<text x="60" y="{yb + 1}" font-family="DejaVu Sans" font-size="2.8">50 mm</text>')
    xb = PW - 6
    s.append(f'<line x1="{xb}" y1="{PH - 60}" x2="{xb}" y2="{PH - 10}" stroke="black" stroke-width="0.4"/>')
    for y in range(int(PH - 60), int(PH - 9), 10):
        s.append(f'<line x1="{xb - 1.5}" y1="{y}" x2="{xb + 1.5}" y2="{y}" stroke="black" stroke-width="0.3"/>')
    s.append(f'<text x="{xb - 2}" y="{PH - 62}" font-family="DejaVu Sans" font-size="2.8" text-anchor="end">50 mm</text>')
    s.append("</svg>")
    buf = io.BytesIO()
    cairosvg.svg2pdf(bytestring="\n".join(s).encode(), write_to=buf)
    return buf.getvalue()


def pads_svg(fill):
    out = []
    for p in silk3.PADS:
        out.append(poly(list(PD.pad_rect(p).exterior.coords), fill=fill, stroke="black", stroke_width="0.08"))
    for p in silk3.PADS:
        if p["kind"] != "smd":
            r = p["drill"] / 2
            out.append(f'<circle cx="{p["x"] + OX}" cy="{p["y"] + OY}" r="{r}" fill="white" stroke="black" stroke-width="0.06"/>')
            out.append(f'<path d="M{p["x"] + OX - r} {p["y"] + OY}h{2 * r}M{p["x"] + OX} {p["y"] + OY - r}v{2 * r}" stroke="black" stroke-width="0.04"/>')
    return out


# pagina 1: lato componenti
b1 = [poly(r, fill="#555555") for r in silk["F.SilkS"]]
for ref, c in silk3.COURT.items():
    b1.append(poly(list(c.exterior.coords), fill="none", stroke="#bbbbbb", stroke_width="0.08"))
b1 += pads_svg("#d0d0d0")
p1 = page("Riv. cosmici 3 canali - scala 1:1 - lato componenti", b1)

# pagina 2: piste
b2 = []
for layer, col in (("B.Cu", "#b0b0b0"), ("F.Cu", "#000000")):
    for t in st["tracks"]:
        if t["layer"] == layer:
            pts = " ".join(f"{x + OX:.3f},{y + OY:.3f}" for x, y in t["pts"])
            b2.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{t["w"]}" stroke-linecap="round" stroke-linejoin="round"/>')
for v in st["vias"]:
    b2.append(f'<circle cx="{v["x"] + OX}" cy="{v["y"] + OY}" r="0.4" fill="black"/><circle cx="{v["x"] + OX}" cy="{v["y"] + OY}" r="0.2" fill="white"/>')
b2 += pads_svg("#ffffff")
p2 = page("Riv. cosmici 3 canali - scala 1:1 - piste (nero sopra, grigio sotto)", b2)

w = PdfWriter()
for data in (p1, p2):
    for pg in PdfReader(io.BytesIO(data)).pages:
        w.add_page(pg)
out = os.path.join(HERE, "..", "variante_3ch", "stampa_1a1_riv_cosmici_3ch.pdf")
with open(out, "wb") as f:
    w.write(f)
print("scritto", os.path.normpath(out))
