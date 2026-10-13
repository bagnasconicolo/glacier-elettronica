# -*- coding: utf-8 -*-
"""Preventivo in PDF: configurazione base (rivelatore + scatolina di acquisizione, senza GPS,
senza modulo meteo, senza LEMO) per 2 e per 4 setup, e costo degli upgrade (meteo, GPS).

Stime in euro IVA inclusa: listini di ottobre 2026 (Mouser, TME, DigiKey, Adafruit, SparkFun,
listino prototipi JLCPCB) e PROTOTIPI.md; il numero vero esce dai carrelli JLCPCB e Mouser.

    python3 preventivo_pdf.py      ->  docs/PREVENTIVO_MuLab.pdf
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "PREVENTIVO_MuLab.pdf")
INK, ACC, MUTED = "#20374A", "#B26023", "#56616B"

# voce, dove, (min, max) per 2 setup, (min, max) per 4 setup
BASE = [
    ("PCB rivelatore a 3 canali: 5 pezzi, montaggio SMD", "JLCPCB", (110, 140), (145, 185)),
    ("PCB scatolina di acquisizione: 5 pezzi, montaggio SMD", "JLCPCB", (45, 60), (55, 75)),
    ("Spedizione JLCPCB e IVA all'importazione", "JLCPCB", (35, 45), (40, 55)),
    ("Rivelatore: chip saldati a mano, connettori KK, ponticelli (+ scorte)", "Mouser", (117, 117), (215, 215)),
    ("SiPM AFBR-S4N22P014M (3 per rivelatore)", "Mouser", (125, 125), (250, 250)),
    ("Raspberry Pi Pico 2, zoccoli, connettori KK, strip (+ 1 Pico di scorta)", "Mouser", (35, 35), (60, 60)),
    ("Raspberry Pi Zero 2 W + scheda SD", "rivenditore", (50, 50), (100, 100)),
    ("Alimentatori USB 5 V e cavi", "rivenditore", (30, 30), (60, 60)),
    ("Basi, distanziali M3, minuteria", "laboratorio", (20, 40), (40, 80)),
    ("Filamento PETG per scatole e supporti (stampa in proprio)", "laboratorio", (5, 5), (10, 10)),
]
UPGRADE = [
    ("Modulo meteo (SHT45 + LPS22HH, Qwiic)",
     ["PCB 5 pezzi + montaggio (JLCPCB), SHT45 a parte (Mouser), cavo Qwiic 50 cm",
      "nello stesso ordine JLCPCB delle altre schede; ordinato dopo: +30-40 EUR"],
     (60, 70), (85, 100)),
    ("GPS u-blox NEO-M9N + antenna attiva 5 m",
     ["tempo assoluto al microsecondo e PPS: confronto fra stazioni, sciami estesi",
      "il connettore e' gia' sulla scatolina: si aggiunge senza modificare le schede"],
     (220, 220), (440, 440)),
    ("GPS economico ATGM336H con PPS + antenna (alternativa)",
     ["stessa funzione a costo molto minore; verificare il PPS sul modulo acquistato"],
     (30, 30), (60, 60)),
]


def eur(a):
    lo, hi = a
    return f"{lo:,}".replace(",", ".") + (f"-{hi:,}".replace(",", ".") if hi != lo else "") + " EUR"


def tot(col):
    return (sum(r[col][0] for r in BASE), sum(r[col][1] for r in BASE))


def main():
    t2, t4 = tot(2), tot(3)
    with PdfPages(OUT) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.set_xlim(0, 210)
        ax.set_ylim(0, 297)
        T = lambda x, y, s, **k: ax.text(x, y, s, family="DejaVu Sans", va="center", **k)
        T(18, 280, "MuLab - Preventivo", fontsize=20, fontweight="bold", color=INK)
        T(18, 272, "Rivelatore di muoni a 3 barre + scatolina di acquisizione (Pico 2)", fontsize=10.5, color=MUTED)
        T(18, 266.5, "Stime in euro, IVA inclusa - ottobre 2026", fontsize=9, color=MUTED)
        ax.plot([18, 192], [261, 261], color=INK, lw=0.8)

        T(18, 253, "CONFIGURAZIONE BASE", fontsize=10, fontweight="bold", color=ACC)
        T(18, 247, "senza GPS, senza modulo meteo; LEMO (prese e cavi) e barre scintillanti gia' disponibili",
          fontsize=8.5, color=MUTED)
        y = 238
        T(18, y, "Voce", fontsize=8.5, fontweight="bold")
        T(128, y, "Dove", fontsize=8.5, fontweight="bold")
        T(160, y, "2 setup", fontsize=8.5, fontweight="bold", ha="right")
        T(192, y, "4 setup", fontsize=8.5, fontweight="bold", ha="right")
        ax.plot([18, 192], [y - 3, y - 3], color="black", lw=0.5)
        for i, (v, d, a2, a4) in enumerate(BASE):
            yy = y - 9 - i * 7.2
            T(18, yy, v, fontsize=8)
            T(128, yy, d, fontsize=8, color=MUTED)
            T(160, yy, eur(a2), fontsize=8, ha="right")
            T(192, yy, eur(a4), fontsize=8, ha="right")
        yy = y - 9 - len(BASE) * 7.2 + 2.5
        ax.plot([18, 192], [yy, yy], color="black", lw=0.8)
        T(18, yy - 6, "Totale configurazione base", fontsize=9.5, fontweight="bold")
        T(160, yy - 6, eur(t2), fontsize=9.5, fontweight="bold", ha="right")
        T(192, yy - 6, eur(t4), fontsize=9.5, fontweight="bold", ha="right")
        T(18, yy - 13, "Budget consigliato (con ~10% di margine)", fontsize=9.5, fontweight="bold", color=ACC)
        T(160, yy - 13, "~700 EUR", fontsize=9.5, fontweight="bold", ha="right", color=ACC)
        T(192, yy - 13, "~1.200 EUR", fontsize=9.5, fontweight="bold", ha="right", color=ACC)
        T(18, yy - 19.5, "Se i SiPM sono gia' disponibili: -125 EUR (2 setup), -250 EUR (4 setup).", fontsize=8,
          color=MUTED)
        T(18, yy - 24.5, "Per setup: ~290-325 EUR con 2 setup, ~245-275 EUR con 4 (i costi fissi JLCPCB si dividono).",
          fontsize=8, color=MUTED)

        y = yy - 38
        T(18, y, "UPGRADE (da aggiungere quando servono)", fontsize=10, fontweight="bold", color=ACC)
        y -= 9
        T(160, y, "per 2 setup", fontsize=8.5, fontweight="bold", ha="right")
        T(192, y, "per 4 setup", fontsize=8.5, fontweight="bold", ha="right")
        ax.plot([18, 192], [y - 3, y - 3], color="black", lw=0.5)
        y -= 9
        for nome, righe, a2, a4 in UPGRADE:
            T(18, y, nome, fontsize=8.8, fontweight="bold")
            T(160, y, eur(a2), fontsize=8.8, ha="right")
            T(192, y, eur(a4), fontsize=8.8, ha="right")
            for k, r in enumerate(righe):
                T(21, y - 5 - k * 4.4, r, fontsize=7.6, color=MUTED)
            y -= 9 + 4.4 * len(righe) + 2
        T(18, y - 2, "Senza GPS il timing funziona: il Pico marca gli eventi al nanosecondo (coincidenze, intervalli,",
          fontsize=8)
        T(18, y - 6.5, "tassi); data e ora le da' il Raspberry via Internet (NTP, ~ms). Il GPS serve per confrontare",
          fontsize=8)
        T(18, y - 11, "stazioni diverse al microsecondo.", fontsize=8)

        ax.plot([18, 192], [27, 27], color=INK, lw=0.5)
        note = ["Non inclusi: barre scintillanti, prese e cavi LEMO (gia' disponibili), ore di lavoro e stampante 3D.",
                "Le cifre sono stime su listini pubblici: il prezzo definitivo si ottiene caricando BOM e CPL",
                "(cartelle jlcpcb/ delle schede) e le liste Mouser nei carrelli. Un solo ordine per fornitore riduce",
                "spedizioni e costi di avvio del montaggio."]
        for k, n in enumerate(note):
            T(18, 22 - k * 4.4, n, fontsize=7.6, color=MUTED)
        pdf.savefig(fig)
        plt.close(fig)
    print("scritto", os.path.normpath(OUT), "- base 2 setup", t2, ", 4 setup", t4)


if __name__ == "__main__":
    main()
