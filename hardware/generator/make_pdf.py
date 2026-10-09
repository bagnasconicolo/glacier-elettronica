# -*- coding: utf-8 -*-
"""Schemi elettrici in PDF (vettoriali, a grandezza reale del foglio):

  docs/schema_riv_cosmici_1canale.pdf   (A3)
  docs/schema_riv_cosmici_3canali.pdf   (A1)
  docs/schemi_riv_cosmici.pdf           (entrambi)

Disegnati dagli stessi dati dei file .kicad_sch (gen_sch / gen_sch3).
I file KiCad restano il riferimento: questo e' il formato da stampare/condividere.

    python make_pdf.py
"""
import datetime, os, runpy, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "docs")
os.makedirs(OUT, exist_ok=True)
TODAY = datetime.date.today().isoformat()


def frame(w, h, title, sub, rev, sheet):
    """cornice + cartiglio in basso a destra (coordinate in mm del foglio)"""
    m = 8
    e = [f'<rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}" fill="none" stroke="#800000" stroke-width="0.35"/>']
    bw, bh = 150, 32
    x0, y0 = w - m - bw, h - m - bh
    e.append(f'<rect x="{x0}" y="{y0}" width="{bw}" height="{bh}" fill="white" stroke="#800000" stroke-width="0.35"/>')
    for yy in (y0 + 12, y0 + 22):
        e.append(f'<line x1="{x0}" y1="{yy}" x2="{x0 + bw}" y2="{yy}" stroke="#800000" stroke-width="0.25"/>')
    e.append(f'<line x1="{x0 + 100}" y1="{y0 + 12}" x2="{x0 + 100}" y2="{y0 + bh}" stroke="#800000" stroke-width="0.25"/>')
    t = lambda s, x, y, sz=2.6, wgt="normal": (
        f'<text x="{x}" y="{y}" font-family="DejaVu Sans, Arial" font-size="{sz}" '
        f'font-weight="{wgt}" fill="#202020">{s}</text>')
    e += [t(title, x0 + 3, y0 + 6.5, 4.2, "bold"), t(sub, x0 + 3, y0 + 10.5, 2.4),
          t("Progetto originale: INFN sez. Torino, S. Gallian (rev. A, 2024)", x0 + 3, y0 + 17.5, 2.3),
          t("Licenza CERN-OHL-W-2.0 - github.com/bagnasconicolo/glacier-elettronica", x0 + 3, y0 + 20.5, 2.0),
          t(f"Rev. {rev}   Data {TODAY}", x0 + 3, y0 + 28, 2.6),
          t(f"Foglio {sheet}", x0 + 103, y0 + 18, 2.6), t("Formato " + ("A3" if w < 500 else "A1"), x0 + 103, y0 + 28, 2.6)]
    return e


def render(variant):
    """lancia il generatore dello schema in un processo separato e ne fa il PDF"""
    code = f'''
import os, sys, runpy
sys.path.insert(0, {HERE!r}); os.chdir({HERE!r})
sys.argv = ["x"]
variant = {variant!r}
if variant == "3ch":
    runpy.run_path("gen_sch3.py", run_name="__main__")
import make_pdf as M
if variant == "3ch":
    view = (0, 0, 841, 594); extra = M.frame(841, 594, "Riv. Cosmici 2024 - 3 canali + coincidenza",
        "3 front-end SiPM, boost/bias in comune, AND 74LVC1G11 con esclusione, uscite LEMO 00", "B1", "1/1")
    out = "schema_riv_cosmici_3canali"
else:
    view = (0, 0, 420, 297); extra = M.frame(420, 297, "Riv. Cosmici 2024 - 1 canale",
        "Amplif, alim, soglie + uscita 3,3 V per Raspberry Pi (74LVC1G17)", "A2", "1/1")
    out = "schema_riv_cosmici_1canale"
svg = os.path.join(M.OUT, out + ".svg")
runpy.run_path("render_sch.py", init_globals={{"VIEW": view, "OUTSVG": svg, "MM": True, "EXTRA": extra}})
import cairosvg
cairosvg.svg2pdf(url=svg, write_to=os.path.join(M.OUT, out + ".pdf"))
os.remove(svg)
print("scritto", out + ".pdf")
'''
    subprocess.run([sys.executable, "-c", code], check=True)


if __name__ == "__main__":
    render("1ch")
    render("3ch")
    from pypdf import PdfWriter
    w = PdfWriter()
    for f in ("schema_riv_cosmici_1canale.pdf", "schema_riv_cosmici_3canali.pdf"):
        w.append(os.path.join(OUT, f))
    w.write(os.path.join(OUT, "schemi_riv_cosmici.pdf"))
    print("scritto schemi_riv_cosmici.pdf")
