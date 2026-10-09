# -*- coding: utf-8 -*-
"""File per l'ordine di PCB + montaggio su JLCPCB, dal modello dati unico:

  hardware/jlcpcb/BOM_JLCPCB.csv/.xlsx  Comment, Designator, Footprint, LCSC Part #
  hardware/jlcpcb/CPL_JLCPCB.csv/.xlsx  Designator, Mid X, Mid Y, Layer, Rotation
  hardware/jlcpcb/MPN_riferimento.csv   codice del produttore per le righe da controllare
  hardware/jlcpcb/riv_cosmici_gerber.zip  (copia dei Gerber)

DNP (non montati da JLCPCB, saldati a mano): U1 LT3461, U3 MAX961, U8 LT1636.

    python gen_jlcpcb.py
"""
import csv, os, re, shutil
from netdata import COMPONENTS
from pcb_data import PLACEMENT, abs_pads, BOARD

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "jlcpcb")
X1, Y1, X2, Y2 = BOARD

DNP = {"U1", "U3", "U8"}

PKG = {
    "R0805": "0805", "C0805": "0805", "C1206": "1206", "C1210": "1210",
    "L_PWR": "SMD 5x5mm", "DO35": "DO-35 (THT)", "LED0805": "LED 0805",
    "SOT23": "SOT-23", "SOT23-5": "SOT-23-5", "SOT23-6": "SOT-23-6",
    "SO8": "SOIC-8", "SOT223": "SOT-223", "3296W": "3296W (THT)",
    "HDR2": "Header 2.54mm 1x2 (THT)",
}

# (valore, footprint) -> (Comment per JLCPCB, LCSC #, MPN). LCSC vuoto = lo abbina
# JLCPCB dal Comment/Footprint, oppure si cerca l'MPN nel loro catalogo.
PART = {
    ("100n", "C0805"):      ("100nF 50V X7R", "C49678", "Yageo CC0805KRX7R9BB104"),
    ("100n 100V", "C1206"): ("100nF 100V X7R", "C107181", "Yageo CC1206KKX7R0BB104"),
    ("1uF 100V", "C1210"):  ("1uF 100V X7R", "", "TDK C3225X7R2A105K200AA"),
    ("47uH", "L_PWR"):      ("47uH 0.9A", "C1330294", "Bourns SRN5040-470M"),
    ("1N4148", "DO35"):     ("1N4148", "C14538", "1N4148 DO-35"),
    ("LED rosso", "LED0805"): ("LED rosso", "C84256", "NationStar NCD0805R1"),
    ("MMBTH81", "SOT23"):   ("MMBTH81", "C190349", "onsemi MMBTH81"),
    ("BFR93A", "SOT23"):    ("BFR93A", "", "NXP BFR93A,215 / Infineon BFR93AE6327"),
    ("MCP1402", "SOT23-5"): ("MCP1402T-E/OT", "C128573", "Microchip MCP1402T-E/OT"),
    ("74LVC1G17", "SOT23-5"): ("SN74LVC1G17DBVR", "C7836", "TI SN74LVC1G17DBVR"),
    ("LP2985AIM5-3.6", "SOT23-5"): ("LP2985AIM5-3.6/NOPB", "", "TI LP2985AIM5-3.6/NOPB"),
    ("MCP1825S-3302", "SOT223"): ("MCP1825S-3302E/DB", "C148031", "Microchip MCP1825S-3302E/DB"),
    ("TLC555/LMC555", "SO8"): ("TLC555CDR", "", "TI TLC555CDR (o LMC555CM/NOPB)"),
    ("10k", "3296W"):       ("10k trimmer 3296W", "C34846", "Bourns 3296W-1-103LF"),
    ("SiPM", "HDR2"):       ("Header 1x2 2.54mm", "", "pin header maschio 1x2 2.54"),
    ("TTL_OUT", "HDR2"):    ("Header 1x2 2.54mm", "", "pin header maschio 1x2 2.54"),
    ("PWR_5V", "HDR2"):     ("Header 1x2 2.54mm", "", "pin header maschio 1x2 2.54"),
    ("LEMO_OUT", "HDR2"):   ("Header 1x2 2.54mm", "", "pin header maschio 1x2 2.54"),
}


def comment_for(value, fpk):
    if (value, fpk) in PART:
        return PART[(value, fpk)]
    if fpk == "R0805":            # resistori: JLCPCB abbina dal valore
        v = value[:-1] if re.fullmatch(r"\d+R", value) else value   # 560R -> 560
        v = re.sub(r"^(\d+)k(\d)$", r"\1.\2k", v)                  # 1k2 -> 1.2k
        return (f"{v} 1% 0805", "", "")
    if fpk == "C0805":
        v = value if value.endswith("F") else value + "F"           # 100n -> 100nF
        if v == "100nF":
            return PART[("100n", "C0805")]
        return (f"{v} 50V 0805", "", "")
    raise KeyError((value, fpk))


def ref_key(r):
    m = re.match(r"([A-Z]+)(\d+)", r)
    return (m.group(1), int(m.group(2)))


def centroids():
    acc = {}
    for p in abs_pads():
        acc.setdefault(p["ref"], []).append((p["x"], p["y"]))
    return {r: (sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v))
            for r, v in acc.items()}


def write_xlsx(fn, hdr, rows):
    try:
        import openpyxl
    except ImportError:
        print("openpyxl assente: niente", os.path.basename(fn))
        return
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(hdr)
    for r in rows:
        ws.append(r)
    wb.save(fn)


def main():
    os.makedirs(OUT, exist_ok=True)
    # ---- BOM
    groups = {}
    for ref, (kind, value, fpk, extra) in COMPONENTS.items():
        if ref in DNP:
            continue
        com, lcsc, mpn = comment_for(value, fpk)
        groups.setdefault((com, PKG[fpk], lcsc, mpn), []).append(ref)
    rows = []
    for (com, pkg, lcsc, mpn), refs in groups.items():
        refs.sort(key=ref_key)
        rows.append([com, ",".join(refs), pkg, lcsc, mpn])
    rows.sort(key=lambda r: ref_key(r[1].split(",")[0]))
    # solo le 4 colonne del modello JLCPCB (l'MPN di riferimento e' in LEGGIMI.md)
    bom_hdr = ["Comment", "Designator", "Footprint", "LCSC Part #"]
    bom_rows = [r[:4] for r in rows]
    with open(os.path.join(OUT, "BOM_JLCPCB.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(bom_hdr)
        w.writerows(bom_rows)
    write_xlsx(os.path.join(OUT, "BOM_JLCPCB.xlsx"), bom_hdr, bom_rows)
    with open(os.path.join(OUT, "MPN_riferimento.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Comment", "LCSC Part #", "MPN"])
        w.writerows([[r[1], r[0], r[3], r[4]] for r in rows if r[4]])
    # ---- CPL (origine = angolo in basso a sinistra della scheda, Y verso l'alto)
    cen = centroids()
    cpl_hdr = ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]
    cpl_rows = []
    for ref in sorted(PLACEMENT, key=ref_key):
        if ref in DNP:
            continue
        x, y = cen[ref]
        rot = PLACEMENT[ref][2] % 360
        cpl_rows.append([ref, f"{x - X1:.3f}mm", f"{Y2 - y:.3f}mm", "Top", f"{rot:.0f}"])
    with open(os.path.join(OUT, "CPL_JLCPCB.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cpl_hdr)
        w.writerows(cpl_rows)
    write_xlsx(os.path.join(OUT, "CPL_JLCPCB.xlsx"), cpl_hdr, cpl_rows)
    # ---- Gerber
    shutil.copy(os.path.join(HERE, "..", "riv_cosmici_gerber.zip"),
                os.path.join(OUT, "riv_cosmici_gerber.zip"))
    n = sum(len(r[1].split(",")) for r in rows)
    print(f"BOM: {len(rows)} righe, {n} componenti montati; DNP: {sorted(DNP)}")
    print(f"CPL: {n} posizioni")


if __name__ == "__main__":
    main()
