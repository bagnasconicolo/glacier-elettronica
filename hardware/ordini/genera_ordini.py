# -*- coding: utf-8 -*-
"""Pacchetto d'ordine: liste Mouser per N setup (configurazione base + upgrade) e copia dei
file JLCPCB delle schede. Configurazione base = rivelatore a 3 canali + scatolina di
acquisizione, senza GPS, senza modulo meteo; LEMO (prese e cavi) e barre gia' disponibili.

    python3 genera_ordini.py      ->  mouser/*.csv, jlcpcb/<scheda>/*, MuLab_ordini.zip
"""
import csv, os, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)

# (MPN, produttore, quantita' per setup, scorta fissa, descrizione)
BASE = [
    ("LT3461AES6#TRMPBF", "Analog Devices", 1, 1, "Rivelatore U1: boost alta tensione SiPM (SOT-23-6). Fine vita: scorta"),
    ("MAX961ESA+", "Analog Devices", 3, 1, "Rivelatore U103 U203 U303: comparatori (SO-8). Fine vita: scorta"),
    ("LT1636CS8#PBF", "Analog Devices", 3, 1, "Rivelatore U108 U208 U308: op-amp bias (SO-8; NON la versione MSOP). Fine vita: scorta"),
    ("LP2985AIM5-3.6/NOPB", "Texas Instruments", 2, 1, "Rivelatore U5 U7: LDO 3,6 V (SOT-23-5)"),
    ("1N4148-TAP", "Vishay", 3, 4, "Rivelatore D101 D201 D301 (DO-35)"),
    ("61304011121", "Wurth Elektronik", 1, 1, "Rivelatore: strip maschio 1x40 per test point, JP1-JP3, J3"),
    ("M7566-05", "Harwin", 3, 4, "Rivelatore: ponticelli JP1-JP3"),
    ("AFBR-S4N22P014M", "Broadcom", 3, 0, "SiPM, 3 per rivelatore (togliere se gia' disponibili)"),
    ("22-27-2021", "Molex", 3, 1, "Rivelatore J101 J201 J301: header KK 254 2 poli (cavi delle barre)"),
    ("22-01-3027", "Molex", 3, 2, "Connettore KK 254 2 poli lato cavo (barre)"),
    ("22-27-2031", "Molex", 3, 1, "Header KK 254 3 poli: J6 rivelatore + J7 J8 scatolina (I2C)"),
    ("22-01-3037", "Molex", 2, 1, "Connettore KK 254 3 poli lato cavo: cavo I2C rivelatore-scatolina (2 estremi)"),
    ("08-50-0114", "Molex", 12, 6, "Contatti a crimpare KK 254, 22-30 AWG (barre + cavo I2C)"),
    ("SC1631", "Raspberry Pi", 1, 1, "Raspberry Pi Pico 2 (scatolina A1)"),
    ("PPTC201LFBN-RC", "Sullins", 2, 1, "Strip femmina 1x20: zoccolo del Pico"),
    ("PREC006SAAN-RC", "Sullins", 1, 0, "Strip maschio 1x6 J6 scatolina (predisposizione GPS)"),
]
# meteo, opzione A (consigliata per la fase pilota): schedine pronte Adafruit, in catena
UPG_METEO_ADAFRUIT = [
    ("5665", "Adafruit", 1, 0, "Sensore SHT45 temperatura/umidita' STEMMA QT/Qwiic (0x44); versione con PTFE: 6174"),
    ("4633", "Adafruit", 1, 0, "Sensore pressione LPS22 STEMMA QT/Qwiic (0x5D)"),
    ("PRT-14429", "SparkFun", 1, 0, "Cavo Qwiic 500 mm: scatolina -> SHT45"),
    ("4210", "Adafruit", 1, 0, "Cavo STEMMA QT/Qwiic 100 mm: SHT45 -> LPS22"),
]
# meteo, opzione B: il nostro modulo (PCB in jlcpcb/3_modulo_meteo_UPGRADE) + queste parti
UPG_METEO = [
    ("SHT45-AD1B-R2", "Sensirion", 1, 1, "Modulo meteo U1: solo se JLCPCB non lo monta (global sourcing)"),
    ("PRT-14429", "SparkFun", 1, 0, "Cavo Qwiic 500 mm: modulo meteo - scatolina"),
]
UPG_GPS = [
    ("GPS-17285", "SparkFun", 1, 0, "GPS u-blox NEO-M9N con SMA (PPS sul connettore)"),
    ("960", "Adafruit", 1, 0, "Antenna GPS attiva 28 dB, cavo 5 m, SMA"),
    ("266", "Adafruit", 0, 1, "Cavetti femmina-femmina 20 x 75 mm: GPS -> J6"),
]


def scrivi(nome, righe, n):
    p = os.path.join(HERE, "mouser", nome)
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Manufacturer Part Number", "Manufacturer", "Quantity", "Customer Part Number"])
        for mpn, mfr, q, sc, d in righe:
            w.writerow([mpn, mfr, q * n + sc, d])
    return p


def main():
    os.makedirs(os.path.join(HERE, "mouser"), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "mouser")):
        os.remove(os.path.join(HERE, "mouser", f))
    for n in range(2, 7):
        scrivi(f"mouser_base_{n}setup.csv", BASE, n)
        scrivi(f"mouser_upgrade_meteo_adafruit_{n}setup.csv", UPG_METEO_ADAFRUIT, n)
        scrivi(f"mouser_upgrade_meteo_modulo_{n}setup.csv", UPG_METEO, n)
        scrivi(f"mouser_upgrade_gps_{n}setup.csv", UPG_GPS, n)
    # riepilogo: tutte le quantita' in una tabella
    with open(os.path.join(HERE, "mouser", "RIEPILOGO_quantita.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Gruppo", "Manufacturer Part Number", "Manufacturer", "Descrizione"]
                   + [f"{n} setup" for n in range(2, 7)])
        for gruppo, righe in (("BASE", BASE), ("UPGRADE meteo Adafruit", UPG_METEO_ADAFRUIT),
                              ("UPGRADE meteo nostro modulo", UPG_METEO), ("UPGRADE GPS", UPG_GPS)):
            for mpn, mfr, q, sc, d in righe:
                w.writerow([gruppo, mpn, mfr, d] + [q * n + sc for n in range(2, 7)])
    schede = {"1_rivelatore": os.path.join(HW, "variante_3ch", "jlcpcb"),
              "2_scatolina_acquisizione": os.path.join(HW, "moduli", "acquisizione", "jlcpcb"),
              "3_modulo_meteo_UPGRADE": os.path.join(HW, "moduli", "meteo", "jlcpcb")}
    for nome, src in schede.items():
        dst = os.path.join(HERE, "jlcpcb", nome)
        shutil.rmtree(dst, ignore_errors=True)
        os.makedirs(dst)
        for f in os.listdir(src):
            if f.endswith((".csv", ".zip")):
                shutil.copy(os.path.join(src, f), dst)
    z = os.path.join(HERE, "MuLab_ordini.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _d, files in os.walk(HERE):
            for f in files:
                p = os.path.join(root, f)
                if p != z and not f.endswith(".py"):
                    zf.write(p, os.path.relpath(p, HERE))
        pv = os.path.join(HW, "..", "docs", "PREVENTIVO_MuLab.pdf")
        zf.write(pv, "PREVENTIVO_MuLab.pdf")
    print("scritto", z)


if __name__ == "__main__":
    main()
