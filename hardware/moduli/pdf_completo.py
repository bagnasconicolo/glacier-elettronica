# -*- coding: utf-8 -*-
"""PDF unico del sistema: schemi elettrici (rivelatore + moduli), anteprime dei PCB,
preventivo e, in appendice, gli schemi KiCad (quelli usati per la verifica schema = PCB).

    python3 pdf_completo.py      ->  docs/SISTEMA_schemi_PCB_preventivo.pdf

Prima: generator/schema_a4.py (rivelatore), moduli/schemi_a4.py, costruisci_modulo.py.
"""
import os, subprocess, tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
DOCS = os.path.join(ROOT, "docs")
OUT = os.path.join(DOCS, "SISTEMA_schemi_PCB_preventivo.pdf")
RED = "#d00000"

SCHEDE = [  # titolo, immagine, righe
    ("Rivelatore a 3 canali (schema INFN + variante)", os.path.join(ROOT, "hardware/variante_3ch/anteprima_pcb_3ch.png"),
     ["103 x 223,9 mm, 2 strati", "file: hardware/variante_3ch/ (KiCad, Gerber, BOM JLCPCB e Mouser)",
      "verifica KiCad: schema = PCB, DRC senza errori, connettivita' sul rame OK"]),
    ("Scatolina di acquisizione", os.path.join(HERE, "acquisizione/anteprima_scheda_acquisizione.png"),
     ["105 x 70 mm, 2 strati, piano di massa sopra e sotto",
      "file: hardware/moduli/acquisizione/ (KiCad, Gerber, BOM e CPL JLCPCB)",
      "verifica KiCad: schema = PCB, DRC senza errori, connettivita' sul rame OK",
      "LEMO a gomito sul bordo inferiore, porte I2C sul bordo superiore, GPS a destra"]),
    ("Modulo meteo", os.path.join(HERE, "meteo/anteprima_modulo_meteo.png"),
     ["36 x 22 mm, 2 strati; sensore di umidita' su isola con fessure, senza rame sotto",
      "file: hardware/moduli/meteo/ (KiCad, Gerber, BOM e CPL JLCPCB)",
      "verifica KiCad: schema = PCB, DRC senza errori ne' avvisi, connettivita' OK"]),
]

PREVENTIVO = [
    ("Rivelatore: 5 PCB, montaggio SMD su 2", "JLCPCB", "110-140"),
    ("Rivelatore: chip a mano, KK, ponticelli", "Mouser", "~117"),
    ("SiPM AFBR-S4N22P014M (6)", "Mouser", "125 (se mancano)"),
    ("Scatolina: 5 PCB, montaggio su 2", "JLCPCB", "40-50"),
    ("Modulo meteo: 5 PCB, montaggio su 2", "JLCPCB", "35-45"),
    ("Pico 2, zoccoli, KK, strip, cavetti", "Mouser", "~30"),
    ("GPS NEO-M9N SMA (2) + antenne attive 5 m (2)", "Mouser", "~180 (economico ~100)"),
    ("SHT45 a parte, cavi Qwiic, scatole Hammond", "Mouser", "~40"),
    ("Raspberry Pi Zero 2 W + SD (2)", "rivenditore", "~50"),
    ("Alimentatori USB 5 V e cavi", "rivenditore", "~30"),
    ("Base in plexiglass, distanziali", "laboratorio", "20-40"),
]


def pagina(pdf, titolo):
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_xlim(0, 297)
    ax.set_ylim(0, 210)
    ax.add_patch(plt.Rectangle((8, 8), 281, 194, fill=False, lw=1.0))
    ax.text(16, 192, titolo, fontsize=17, fontweight="bold", va="center")
    return fig, ax


def copertina(pdf):
    fig, ax = pagina(pdf, "")
    ax.text(148.5, 150, "Rivelatore di muoni cosmici per le scuole", fontsize=24, ha="center", fontweight="bold")
    ax.text(148.5, 136, "Schemi elettrici, PCB e preventivo del sistema completo", fontsize=15, ha="center")
    ax.text(148.5, 126, "INFN sez. Torino - progetto glacier-elettronica - rev. A - 11/10/2026", fontsize=10,
            ha="center", color="#444")
    idx = ["Architettura del sistema",
           "Rivelatore a 3 canali: 6 fogli A4 (nero = circuito INFN originale, rosso = variante)",
           "Scatolina di acquisizione: ingressi LEMO e PPS; Pico 2, GPS, hub I2C (scheda nuova, in rosso)",
           "Modulo meteo SHT45 + LPS22HH (scheda nuova, in rosso)",
           "Anteprime dei tre PCB",
           "Preventivo per due sistemi completi",
           "Appendice: schemi KiCad (gli stessi file verificati contro i PCB)"]
    for i, t in enumerate(idx):
        ax.text(70, 104 - i * 9, f"{i + 1}.  {t}", fontsize=11)
    ax.text(70, 32, "Colori:", fontsize=10, fontweight="bold")
    ax.text(88, 32, "nero = circuito INFN originale (S. Gallian, 2024)", fontsize=10)
    ax.text(88, 25, "rosso = aggiunto o modificato in questo progetto", fontsize=10, color=RED)
    pdf.savefig(fig)
    plt.close(fig)


def pagine_pcb(pdf):
    for titolo, img, righe in SCHEDE:
        fig, ax = pagina(pdf, "PCB - " + titolo)
        im = plt.imread(img)
        h, w = im.shape[:2]
        bw, bh = 265, 150                               # riquadro dell'immagine (mm)
        s = min(bw / w, bh / h)
        iw, ih = w * s, h * s
        x0, y0 = 148.5 - iw / 2, 30 + (bh - ih) / 2
        ax.imshow(im, extent=(x0, x0 + iw, y0, y0 + ih), zorder=2)
        for i, t in enumerate(righe):
            ax.text(16, 22 - i * 4.6, t, fontsize=9, color=RED if i == 0 else "black")
        if "Rivelatore" not in titolo:
            ax.text(281, 180, "rame sopra (rosso), rame sotto (blu), serigrafia (giallo)", fontsize=8, ha="right",
                    color="#555")
        pdf.savefig(fig)
        plt.close(fig)


def pagina_preventivo(pdf):
    fig, ax = pagina(pdf, "Preventivo - due sistemi completi (stime, euro)")
    ys = 170
    ax.text(16, ys, "Voce", fontsize=10, fontweight="bold")
    ax.text(170, ys, "Dove", fontsize=10, fontweight="bold")
    ax.text(225, ys, "Stima (EUR)", fontsize=10, fontweight="bold")
    ax.plot([16, 281], [ys - 3, ys - 3], color="black", lw=0.8)
    for i, (v, d, c) in enumerate(PREVENTIVO):
        y = ys - 10 - i * 8
        ax.text(16, y, v, fontsize=10)
        ax.text(170, y, d, fontsize=10)
        ax.text(225, y, c, fontsize=10)
    y = ys - 10 - len(PREVENTIVO) * 8
    ax.plot([16, 281], [y + 4, y + 4], color="black", lw=0.8)
    ax.text(16, y - 2, "Totale", fontsize=11, fontweight="bold")
    ax.text(60, y - 2, "~780-850 con SiPM;   ~650-720 senza SiPM;   ~570-640 senza SiPM e col GPS economico",
            fontsize=10, fontweight="bold")
    note = ["Cavi LEMO non inclusi (gia' disponibili). Prese LEMO EPL.00.250.NTN, se mancano: ~18 EUR l'una.",
            "Prezzi stimati sui listini di ottobre 2026 (Mouser, TME, DigiKey, Adafruit, SparkFun, listino prototipi JLCPCB):",
            "il numero vero si ottiene caricando BOM e CPL nei carrelli (dettagli e codici in hardware/PREVENTIVO.md).",
            "JLCPCB: un solo ordine per le tre schede; le parti a foro passante (Pico, LEMO, KK, strip) si saldano a mano."]
    for i, t in enumerate(note):
        ax.text(16, 30 - i * 5, t, fontsize=8.5)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    td = tempfile.mkdtemp()
    parti = os.path.join(td, "parti.pdf")
    with PdfPages(parti) as pdf:
        copertina(pdf)
        pagine_pcb(pdf)
        pagina_preventivo(pdf)
    kicad = []
    for sch in ("hardware/variante_3ch/riv_cosmici_3ch.kicad_sch",
                "hardware/moduli/acquisizione/scheda_acquisizione.kicad_sch",
                "hardware/moduli/meteo/modulo_meteo.kicad_sch"):
        o = os.path.join(td, os.path.basename(sch) + ".pdf")
        subprocess.run(["kicad-cli", "sch", "export", "pdf", "-o", o, os.path.join(ROOT, sch)],
                       check=True, capture_output=True)
        kicad.append(o)
    P = PdfReader(parti)
    MOD = PdfReader(os.path.join(DOCS, "schema_A4_moduli.pdf"))
    RIV = PdfReader(os.path.join(DOCS, "schema_A4_3canali.pdf"))
    w = PdfWriter()
    w.add_page(P.pages[0])                                       # copertina
    w.add_page(MOD.pages[0])                                     # architettura
    for p in RIV.pages:                                          # rivelatore (6 fogli)
        w.add_page(p)
    for p in MOD.pages[1:]:                                      # scatolina, meteo
        w.add_page(p)
    for p in P.pages[1:]:                                        # PCB, preventivo
        w.add_page(p)
    for k in kicad:                                              # appendice
        for p in PdfReader(k).pages:
            w.add_page(p)
    w.write(OUT)
    print("scritto", os.path.relpath(OUT, ROOT), "-", len(w.pages), "pagine")


if __name__ == "__main__":
    main()
