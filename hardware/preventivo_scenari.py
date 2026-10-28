# -*- coding: utf-8 -*-
"""Preventivo a scenari per 2-6 rivelatori MuLab (configurazione base, IVA inclusa), con e
senza SiPM, e in appendice i carrelli Mouser reali (docs/preventivi/Mouser_carrello_*.pdf).

Configurazione base: rivelatore a 3 canali + scatolina di acquisizione (Pico 2) + Raspberry
Pi Zero 2 W; esclusi GPS, modulo meteo, LEMO (prese e cavi) e barre scintillanti.
Mouser: carrelli reali del 28/10/2026 per 2, 4 e 6 setup; 3 e 5 dagli stessi prezzi unitari.
Zoccoli e pin del Pico: Amazon. JLCPCB e il resto: stime (listino prototipi, PROTOTIPI.md).

    python3 preventivo_scenari.py      ->  docs/PREVENTIVO_scenari_MuLab.pdf
"""
import os, tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs")
OUT = os.path.join(DOCS, "PREVENTIVO_scenari_MuLab.pdf")
CARRELLI = {2: "Mouser_carrello_2setup_2026-10-28.pdf", 4: "Mouser_carrello_4setup_2026-10-28.pdf",
            6: "Mouser_carrello_6setup_2026-10-28.pdf"}
IVA = 1.22
INK, ACC, MUTED, LIGHT = "#20374A", "#B26023", "#56616B", "#EEF2F5"
NS = (2, 3, 4, 5, 6)

# Mouser, merce IVA esclusa (senza zoccoli e pin del Pico): carrelli reali per 2, 4, 6
MOUSER = {2: 269.74, 4: 418.39, 6: 612.55}
SIPM = {2: 128.46, 4: 204.60, 6: 306.90}          # riga SiPM nei carrelli
# 3 e 5 setup: stessi prezzi unitari dei carrelli (soglia di prezzo a 10 pezzi)
U = {"LT3461": (5.73, 5.73), "MAX961": (7.62, 5.90), "LT1636": (5.77, 4.42), "LP2985": (0.619, 0.619),
     "1N4148": (0.096, 0.096), "strip": (1.32, 1.32), "jumper": (0.341, 0.341), "SiPM": (21.41, 17.05),
     "KK2h": (0.198, 0.167), "KK2c": (0.095, 0.08), "KK3h": (0.198, 0.195), "KK3c": (0.095, 0.095),
     "crimp": (0.067, 0.067), "Pico": (4.30, 4.30)}
Q = {"LT3461": (1, 1), "MAX961": (3, 1), "LT1636": (3, 1), "LP2985": (2, 1), "1N4148": (3, 4), "strip": (1, 1),
     "jumper": (3, 4), "SiPM": (3, 0), "KK2h": (3, 1), "KK2c": (3, 2), "KK3h": (3, 1), "KK3c": (2, 1),
     "crimp": (12, 6), "Pico": (1, 1)}
for n in (3, 5):
    tot = 0
    for k, (a, b) in Q.items():
        q = a * n + b
        u = U[k][0] if q < 10 else U[k][1]
        tot += q * u
        if k == "SiPM":
            SIPM[n] = q * u
    MOUSER[n] = tot


def jlc_riv(n):
    """JLCPCB, solo rivelatore, DHL DDP (dazi e IVA compresi). Carrelli reali del 28/10/2026:
    5 PCB + 5 montati = 335,37 EUR; 10 PCB + 10 montati = 507,91 EUR. Dai due carrelli:
    PCB 5 pz 16,07; montaggio = 121 fissi (avvio, stencil, parti Extended) + 19,6 a scheda;
    spedizione 33,4 (5 pz) / 65,6 (10 pz); IVA 22% su merce + spedizione; 7,42 di diritti."""
    if n <= 5:
        v = (16.07 + 121 + 19.6 * n + 33.4) * 1.22 + 7.42
    else:
        v = (27.47 + 121 + 19.6 * n + 50) * 1.22 + 7.42
    esatto = n == 5
    return (v, v) if esatto else (v * 0.97, v * 1.05)


def jlc_box(n):
    """JLCPCB, scatolina (Economic). Carrelli reali a se' stanti del 28/10/2026: 5 PCB + 5 montati
    = merce 56,61 (totale DDP 110,62); 10 + 10 = merce 75,17 (totale 133,46) -> 38,2 fissi +
    3,7 a scheda. Nello stesso ordine del rivelatore spedizione e diritti si pagano una volta:
    si aggiunge la merce con IVA, piu' 0-8 EUR di spedizione per il peso in piu'."""
    m = 38.2 + 3.7 * n
    return (m * 1.22, (m + 8) * 1.22)


def righe(n):
    """(voce, dove, min, max, fonte) IVA inclusa"""
    m = MOUSER[n] * IVA
    s = SIPM[n] * IVA
    j, b = jlc_riv(n), jlc_box(n)
    return [
        ("PCB rivelatore + montaggio, DHL DDP", "JLCPCB", j[0], j[1],
         "carrello" if n == 5 else "dai carrelli 5 e 10 pz"),
        ("PCB scatolina + montaggio (stesso ordine)", "JLCPCB", b[0], b[1], "dai carrelli 5 e 10 pz"),
        ("Chip, connettori, Pico 2", "Mouser", m - s, m - s,
         "carrello" if n in CARRELLI else "prezzi del carrello"),
        ("SiPM (3 per rivelatore)", "Mouser", s, s, "carrello" if n in CARRELLI else "prezzi del carrello"),
        ("Zoccoli e pin Pico, strip 1x6", "Amazon", 2 * n + 4, 3 * n + 6, "stima"),
        ("Raspberry Pi Zero 2 W + microSD", "rivenditore", 25 * n, 30 * n, "stima"),
        ("Alimentatori 5 V, cavi USB e OTG", "rivenditore", 15 * n, 20 * n, "stima"),
        ("Basi, viti, distanziali, PETG", "laboratorio", 12 * n, 22 * n, "stima"),
        ("Una tantum: crimpatrice KK, cavi", "rivenditore", 40, 60, "stima"),
    ]


def totali(n):
    r = righe(n)
    lo, hi = sum(x[2] for x in r), sum(x[3] for x in r)
    s = SIPM[n] * IVA
    return lo, hi, lo - s, hi - s


def eur(x):
    return f"{x:,.0f}".replace(",", ".") + " €"


def rng(a, b):
    a, b = 5 * round(a / 5), 5 * round(b / 5)
    return eur(a) if a == b else f"{a:,.0f}–{b:,.0f} €".replace(",", ".")


def pagina():
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_xlim(0, 210)
    ax.set_ylim(0, 297)
    T = lambda x, y, s, **k: ax.text(x, y, s, family="DejaVu Sans", va="center", **k)
    return fig, ax, T


def intestazione(T, ax, titolo, sotto):
    T(18, 280, titolo, fontsize=19, fontweight="bold", color=INK)
    T(18, 272, sotto, fontsize=9.5, color=MUTED)
    ax.plot([18, 192], [266, 266], color=INK, lw=0.8)


def pag_scenari(pdf):
    fig, ax, T = pagina()
    intestazione(T, ax, "MuLab - Preventivo a scenari",
                 "Rivelatore a 3 barre + scatolina di acquisizione + Raspberry Pi Zero 2 W  -  euro, IVA inclusa  -  28/10/2026")
    T(18, 257, "Configurazione base: senza GPS e senza modulo meteo (upgrade successivi, gia' previsti dall'elettronica);",
      fontsize=8.3, color=MUTED)
    T(18, 252.5, "esclusi prese e cavi LEMO e barre scintillanti (gia' disponibili).", fontsize=8.3, color=MUTED)
    # tabella riassuntiva
    y0 = 240
    cols = [18, 62, 104, 146, 192]
    hdr = ["Rivelatori", "Con SiPM", "Senza SiPM", "Budget con SiPM\n(+10% margine)", "Per rivelatore\n(con SiPM)"]
    ax.add_patch(plt.Rectangle((16, y0 - 5), 178, 10, color=INK))
    xs = [18, 82, 124, 166, 192]
    for i, h in enumerate(hdr):
        T(xs[i], y0, h, fontsize=8.3, color="white", fontweight="bold", ha="left" if i == 0 else "right")
    for k, n in enumerate(NS):
        lo, hi, lo2, hi2 = totali(n)
        y = y0 - 13 - k * 11
        if k % 2 == 0:
            ax.add_patch(plt.Rectangle((16, y - 5.5), 178, 11, color=LIGHT))
        T(18, y, f"{n} rivelatori", fontsize=10, fontweight="bold", color=INK)
        T(82, y, rng(lo, hi), fontsize=9.5, ha="right")
        T(124, y, rng(lo2, hi2), fontsize=9.5, ha="right")
        T(166, y, "~" + eur(5 * round(hi * 1.1 / 5)), fontsize=10, fontweight="bold", color=ACC, ha="right")
        T(192, y, rng(lo / n, hi / n), fontsize=9, ha="right", color=MUTED)
    y = y0 - 13 - len(NS) * 11 - 4
    note = ["Mouser: carrelli reali del 28/10/2026 per 2, 4 e 6 rivelatori (in appendice); 3 e 5 calcolati con gli stessi",
            "prezzi unitari. Le scorte dei chip fuori produzione (LT3461, MAX961, LT1636) sono comprese.",
            "JLCPCB rivelatore: carrelli reali (5 e 10 schede montate, DHL DDP con dazi e IVA); altri numeri interpolati.",
            "JLCPCB scatolina: carrelli reali (5 e 10, totale a se' stante 110,62 e 133,46 EUR), qui sommata allo stesso ordine.",
            "Raspberry, alimentatori e minuteria: stime.",
            "IVA calcolata al 22%: i carrelli Mouser riportano il 20%, verificare i dati di fatturazione.",
            "Da 4 rivelatori in su i SiPM superano i 10 pezzi e scendono da 21,41 a 17,05 € (IVA esclusa) l'uno.",
            "Oltre 5 rivelatori servono 10 PCB per tipo (lotto minimo JLCPCB = 5)."]
    for i, t in enumerate(note):
        T(18, y - i * 4.6, t, fontsize=7.6, color=MUTED)
    # upgrade
    y -= len(note) * 4.6 + 8
    T(18, y, "UPGRADE SUCCESSIVI (non inclusi)", fontsize=10, fontweight="bold", color=ACC)
    up = [("Meteo, schedine pronte Adafruit SHT45 + LPS22 + cavi Qwiic", 30, "a rivelatore"),
          ("Meteo, nostro modulo (PCB JLCPCB nello stesso ordine)", 25, "a rivelatore"),
          ("GPS u-blox NEO-M9N + antenna attiva 5 m", 110, "a rivelatore"),
          ("GPS economico ATGM336H con PPS + antenna", 15, "a rivelatore")]
    for i, (v, c, u) in enumerate(up):
        yy = y - 8 - i * 6
        T(18, yy, v, fontsize=8.5)
        T(192, yy, f"~{c} € {u}", fontsize=8.5, ha="right")
    T(18, y - 8 - len(up) * 6 - 2, "Il GPS si collega al connettore J6 gia' presente sulla scatolina (UART GP0/GP1, PPS su GP6 e LEMO J5).",
      fontsize=7.6, color=MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def pag_dettaglio(pdf):
    fig, ax, T = pagina()
    intestazione(T, ax, "Dettaglio delle voci", "euro, IVA inclusa; con SiPM")
    y = 256
    xs = [18, 108, 131, 151, 171, 192]
    T(18, y, "Voce", fontsize=8, fontweight="bold")
    xcol = [100, 123, 146, 169, 192]
    for i, n in enumerate(NS):
        T(xcol[i], y, f"{n} riv.", fontsize=8, fontweight="bold", ha="right")
    ax.plot([18, 192], [y - 3, y - 3], color="black", lw=0.5)
    rr = {n: righe(n) for n in NS}
    for k in range(len(rr[2])):
        yy = y - 11 - k * 13
        v, d, *_ = rr[2][k]
        voce = v if n != 2 else v
        T(18, yy + 2, v, fontsize=7.6)
        T(18, yy - 2.6, f"{d}  ·  {rr[2][k][4]}", fontsize=6.6, color=MUTED)
        for i, n in enumerate(NS):
            r = rr[n][k]
            T(xcol[i], yy, rng(r[2], r[3]), fontsize=7.2, ha="right")
    yy = y - 11 - len(rr[2]) * 13 + 4
    ax.plot([18, 192], [yy, yy], color="black", lw=0.8)
    T(18, yy - 6, "Totale con SiPM", fontsize=8.5, fontweight="bold")
    T(18, yy - 13, "Totale senza SiPM", fontsize=8.5, fontweight="bold")
    for i, n in enumerate(NS):
        lo, hi, lo2, hi2 = totali(n)
        T(xcol[i], yy - 6, rng(lo, hi), fontsize=7.6, ha="right", fontweight="bold")
        T(xcol[i], yy - 13, rng(lo2, hi2), fontsize=7.6, ha="right", fontweight="bold")
    T(18, yy - 20, "(La riga SiPM e' per 3 SiPM a rivelatore: 6, 9, 12, 15, 18 pezzi.)", fontsize=7, color=MUTED)
    y2 = yy - 34
    T(18, y2, "MOUSER: CARRELLI REALI (28/10/2026, merce IVA esclusa)", fontsize=10, fontweight="bold", color=ACC)
    for i, n in enumerate((2, 4, 6)):
        T(18, y2 - 8 - i * 6, f"{n} rivelatori: merce {MOUSER[n]:.2f} €, di cui SiPM {SIPM[n]:.2f} €; spedizione gratuita"
          .replace(".", ","), fontsize=8.3)
    T(18, y2 - 8 - 3 * 6 - 2, "Zoccoli 1x20, pin del Pico e strip 1x6 non sono nei carrelli: si comprano su Amazon (voce a parte).",
      fontsize=7.6, color=MUTED)
    T(18, y2 - 8 - 3 * 6 - 7, "Elenchi per il BOM Tool Mouser: hardware/ordini/mouser/mouser_base_Nsetup.csv",
      fontsize=7.6, color=MUTED)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    tmp = os.path.join(tempfile.mkdtemp(), "p.pdf")
    with PdfPages(tmp) as pdf:
        pag_scenari(pdf)
        pag_dettaglio(pdf)
    w = PdfWriter()
    for p in PdfReader(tmp).pages:
        w.add_page(p)
    for n, f in CARRELLI.items():
        r = PdfReader(os.path.join(DOCS, "preventivi", f))
        for p in r.pages:
            w.add_page(p)
    # carrelli JLCPCB (screenshot)
    tmp2 = os.path.join(os.path.dirname(tmp), "j.pdf")
    with PdfPages(tmp2) as pdf:
        for f, t in (("JLCPCB_carrello_rivelatore_5pz.png", "JLCPCB - rivelatore, 5 PCB + 5 montati (carrello)"),
                     ("JLCPCB_checkout_rivelatore_5pz.png", "JLCPCB - rivelatore, 5 + 5: totale con DHL DDP"),
                     ("JLCPCB_carrello_rivelatore_10pz.png", "JLCPCB - rivelatore, 10 PCB + 10 montati (carrello)"),
                     ("JLCPCB_checkout_rivelatore_10pz.png", "JLCPCB - rivelatore, 10 + 10: totale con DHL DDP")):
            fig = plt.figure(figsize=(11.69, 8.27))
            fig.text(0.04, 0.95, t, fontsize=14, fontweight="bold", color=INK, family="DejaVu Sans")
            a = fig.add_axes([0.04, 0.04, 0.92, 0.86])
            a.imshow(plt.imread(os.path.join(DOCS, "preventivi", f)))
            a.set_axis_off()
            pdf.savefig(fig)
            plt.close(fig)
    for p in PdfReader(tmp2).pages:
        w.add_page(p)
    w.write(OUT)
    for n in NS:
        lo, hi, lo2, hi2 = totali(n)
        print(n, rng(lo, hi), rng(lo2, hi2), "budget", round(hi * 1.1))
    print("scritto", os.path.normpath(OUT), len(w.pages), "pagine")


if __name__ == "__main__":
    main()
