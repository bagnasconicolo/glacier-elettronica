# -*- coding: utf-8 -*-
"""File per l'ordine di PCB + montaggio su JLCPCB, dal modello dati unico:

  hardware/jlcpcb/BOM_JLCPCB.csv/.xlsx  Comment, Designator, Footprint, JLCPCB Part #
  hardware/jlcpcb/CPL_JLCPCB.csv/.xlsx  Designator, Mid X, Mid Y, Layer, Rotation
  hardware/jlcpcb/MPN_riferimento.csv   codice del produttore per le righe da controllare
  hardware/jlcpcb/riv_cosmici_gerber.zip  (copia dei Gerber)

DNP (non montati da JLCPCB, saldati a mano): vedi DNP qui sotto.

    python gen_jlcpcb.py
"""
import csv, os, re, shutil
from netdata import COMPONENTS
from pcb_data import PLACEMENT, abs_pads, BOARD

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "jlcpcb")
X1, Y1, X2, Y2 = BOARD

# DNP = non montati da JLCPCB, saldati a mano:
#  U1, U3, U8: integrati costosi/critici, comprati da Mouser/Farnell
#  U5, U7 (LP2985AIM5-3.6) e D1 (1N4148 DO-35): esauriti a JLCPCB (verifica 9/10/2026)
#  J1-J4: header non riconosciuti da JLCPCB; si saldano header o fili a mano
DNP = {"U1", "U3", "U8", "U5", "U7", "D1", "J1", "J2", "J3", "J4"}

PKG = {
    "R0805": "0805", "C0805": "0805", "C1206": "1206", "C1210": "1210",
    "L_PWR": "SMD 5x5mm", "DO35": "DO-35", "LED0805": "0805",
    "SOT23": "SOT-23", "SOT23-5": "SOT-23-5", "SOT23-6": "SOT-23-6",
    "SO8": "SOIC-8", "SOT223": "SOT-223", "3296W": "3296W",
    "HDR2": "Header 2.54mm 1x2",
    "SO14": "SOIC-14", "HDR3": "Header 2.54mm 1x3", "KK2": "Molex KK 254 1x2", "KK3": "Molex KK 254 1x3",
}

# (valore, footprint) -> (Comment, JLCPCB Part #, MPN). I codici sono quelli che il
# BOM Tool di JLCPCB ha abbinato al primo caricamento (9/10/2026), dove corretti.
PART = {
    ("22pF", "C0805"):      ("CL21C220JBANNNC", "C1804", "Samsung CL21C220JBANNNC 22pF 50V C0G"),
    ("100pF", "C0805"):     ("CL21C101JBANNNC", "C1790", "Samsung CL21C101JBANNNC 100pF 50V C0G"),
    ("10nF", "C0805"):      ("CL21B103KBANNNC", "C1710", "Samsung CL21B103KBANNNC 10nF 50V X7R"),
    ("10n", "C0805"):       ("CL21B103KBANNNC", "C1710", "Samsung CL21B103KBANNNC 10nF 50V X7R"),
    ("100n", "C0805"):      ("CC0805KRX7R9BB104", "C49678", "Yageo CC0805KRX7R9BB104 100nF 50V X7R"),
    ("100nF", "C0805"):     ("CC0805KRX7R9BB104", "C49678", "Yageo CC0805KRX7R9BB104 100nF 50V X7R"),
    ("1uF", "C0805"):       ("CL21B105KBFNNNE", "C28323", "Samsung CL21B105KBFNNNE 1uF 50V X7R"),
    # uscite dei regolatori (CF4, CF7, CF9): codice JLCPCB da confermare nel BOM Tool
    ("2.2uF", "C0805"):     ("CL21B225KAFNNNE", "", "Samsung CL21B225KAFNNNE 2,2uF 25V X7R"),
    ("100n 100V", "C1206"): ("CC1206KKX7R0BB104", "C107181", "Yageo CC1206KKX7R0BB104 100nF 100V X7R"),
    ("1uF 100V", "C1210"):  ("1210B105K101NT", "C24365", "FH 1210B105K101NT 1uF 100V X7R"),
    ("47uH", "L_PWR"):      ("SRN5040-470M", "C1330294", "Bourns SRN5040-470M 47uH 0.9A"),
    ("1N4148", "DO35"):     ("1N4148", "", "1N4148 DO-35 (a mano)"),
    ("LED rosso", "LED0805"): ("NCD0805R1", "C84256", "NationStar NCD0805R1 LED rosso"),
    ("MMBTH81", "SOT23"):   ("MMBTH81", "C190349", "onsemi MMBTH81"),
    ("BFR93A", "SOT23"):    ("BFR93AE6327HTSA1", "C513260", "Infineon BFR93AE6327HTSA1 (= BFR93A)"),
    ("MCP1402", "SOT23-5"): ("MCP1402T-E/OT", "C128573", "Microchip MCP1402T-E/OT"),
    ("74LVC1G17", "SOT23-5"): ("SN74LVC1G17DBVR", "C7836", "TI SN74LVC1G17DBVR"),
    ("LP2985AIM5-3.6", "SOT23-5"): ("LP2985AIM5-3.6/NOPB", "", "TI LP2985AIM5-3.6/NOPB (a mano)"),
    ("MCP1825S-3302", "SOT223"): ("MCP1825S-3302E/DB", "C148031", "Microchip MCP1825S-3302E/DB"),
    ("TLC555/LMC555", "SO8"): ("TLC555CDR", "C6986", "TI TLC555CDR"),
    ("10k", "3296W"):       ("3296W-1-103LF", "C34846", "Bourns 3296W-1-103LF"),
    ("74LVC1G11", "SOT23-6"): ("SN74LVC1G11DBVR", "C22046", "TI SN74LVC1G11DBVR (AND a 3)"),
    ("MCP3424", "SO14"):    ("MCP3424-E/SL", "C640884", "Microchip MCP3424-E/SL (ADC monitor tensioni)"),
    ("I2C_RPI", "HDR3"):    ("Header 1x3 2.54mm", "", "pin header maschio 1x3 (a mano)"),
    ("I2C_RPI", "KK3"):     ("Molex 22-27-2031", "", "Molex KK 254 3 poli 22-27-2031 (a mano)"),
}
for _v in ("SiPM", "TTL_OUT", "PWR_5V", "LEMO_OUT"):
    PART[(_v, "HDR2")] = ("Header 1x2 2.54mm", "", "pin header maschio 1x2 (a mano)")

# resistori 0805 1%: codice UNI-ROYAL 0805W8F<codice>T5E (serie Basic di JLCPCB,
# es. 10k = 0805W8F1002T5E = C17414). Codice: 3 cifre + n. di zeri; sotto 100 ohm
# la lettera J vale x0,1 (10 ohm = 100J).
R_CODE_CHECKED = {"0805W8F1002T5E": "C17414"}


def ohms(v):
    m = re.fullmatch(r"(\d+)([kKM])(\d*)", v)
    if m:
        a, u, b = m.groups()
        return float(f"{a}.{b or 0}") * (1e3 if u in "kK" else 1e6)
    return float(v.rstrip("R"))


def uniroyal(v):
    r = ohms(v)
    if r < 100:
        code = f"{int(round(r * 10)):03d}J"
    else:
        digits = f"{r:.0f}"
        sig = digits[:3]
        code = sig + str(len(digits) - 3)
    return f"0805W8F{code}T5E"


def comment_for(value, fpk):
    if (value, fpk) in PART:
        return PART[(value, fpk)]
    if fpk == "R0805":
        mpn = uniroyal(value)
        return (mpn, R_CODE_CHECKED.get(mpn, ""), f"UNI-ROYAL {mpn} ({value} 1%)")
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
    bom_hdr = ["Comment", "Designator", "Footprint", "JLCPCB Part #"]
    bom_rows = [r[:4] for r in rows]
    with open(os.path.join(OUT, "BOM_JLCPCB.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(bom_hdr)
        w.writerows(bom_rows)
    write_xlsx(os.path.join(OUT, "BOM_JLCPCB.xlsx"), bom_hdr, bom_rows)
    with open(os.path.join(OUT, "MPN_riferimento.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Comment", "JLCPCB Part #", "MPN"])
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
    src = globals().get("ZIP_SRC", os.path.join(HERE, "..", "riv_cosmici_gerber.zip"))
    shutil.copy(src, os.path.join(OUT, os.path.basename(src)))
    n = sum(len(r[1].split(",")) for r in rows)
    print(f"BOM: {len(rows)} righe, {n} componenti montati; DNP: {sorted(DNP)}")
    print(f"CPL: {n} posizioni")


if __name__ == "__main__":
    main()
