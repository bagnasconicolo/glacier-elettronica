# -*- coding: utf-8 -*-
"""Genera la distinta base (BOM) dal modello dati unico (netdata.py):
hardware/bom/BOM_riv_cosmici.csv e .xlsx. Le righe raggruppano i componenti
con stesso valore e package.

    python gen_bom.py
"""
import csv, os, re
from netdata import COMPONENTS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "bom")

PKG = {
    "R0805": "0805", "C0805": "0805", "C1206": "1206", "C1210": "1210",
    "L_PWR": "SMD 5x5/6x6", "DO35": "DO-35", "LED0805": "0805",
    "SOT23": "SOT-23", "SOT23-5": "SOT-23-5", "SOT23-6": "SOT-23-6 (ThinSOT)",
    "SO8": "SO-8", "SOT223": "SOT-223", "3296W": "Trimmer 3296W",
    "HDR2": "Header 2.54 1x2",
}
# codici d'ordine trascritti dal PDF INFN (per valore)
ORDER = {
    "47uH": "RS 693-4344", "BFR93A": "RS 892-2365", "MMBTH81": "RS 104-1196",
    "LT3461": "Farnell 4024725", "TLC555/LMC555": "RS 196-2112 (LMC555CM)",
    "MAX961": "RS 189-9176", "MCP1402": "RS 668-4203",
    "LP2985AIM5-3.6": "RS 812-2417", "MCP1825S-3302": "RS 669-5092",
    "LT1636": "Farnell 4020771",
}
NOTE = {
    "2.2uF": "X7R 0805 >= 10 V, es. Samsung CL21B225KAFNNNE (uscite regolatori; INFN: 100n)",
    "255k": "1% (INFN: 270k): VOUT40 39,4 V, sotto i 40 V max del LT3461",
    "1uF 100V": "dielettrico X7R, 100V (nodo VOUT40 ~41 V)",
    "100n 100V": "X7R 100V (nodi 40V/38,4V)",
    "47uH": "verificare l'ingombro della parte RS effettiva contro il footprint 5x5",
    "1N4148": "assiale DO-35 (o 1N4148W SOD-123 adattando il footprint)",
    "LED rosso": "LED rosso 0805 (pin 1 = catodo)",
    "74LVC1G17": "SN74LVC1G17DBVR (TI) o equivalente; buffer 3,3 V verso Raspberry Pi",
    "33R": "terminazione serie del cavo verso Raspberry Pi",
    "SiPM": "verso scintillatore, cavo Fileca schermato; calza = bias 38,4V",
    "LEMO_OUT": "uscita 0-3,3 V per GPIO Raspberry Pi; footprint header 2.54 -> LEMO a pannello via cavo",
    "TTL_OUT": "uscita 0-5 V (MCP1402): NON collegare ai GPIO del Raspberry Pi",
    "PWR_5V": "pin 1 = GND, pin 2 = +5V",
    "MMBT2222A": "",
}


def ref_key(r):
    m = re.match(r"([A-Z]+)(\d+)", r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)


def rows():
    groups = {}
    for ref, (kind, value, fpk, extra) in COMPONENTS.items():
        key = (kind, value, fpk)
        groups.setdefault(key, []).append(ref)
    out = []
    for (kind, value, fpk), refs in groups.items():
        refs.sort(key=ref_key)
        note = NOTE.get(value, "")
        if kind == "POT":
            note = "Bourns 3296W-1-103LF o equivalente"
        if kind == "C" and value == "100n":
            note = "X7R 50V (CF = disaccoppiamento)"
        out.append([" ".join(refs), len(refs), value, PKG[fpk], ORDER.get(value, ""), note])
    out.sort(key=lambda r: ref_key(r[0].split()[0]))
    out.append(["(fuori scheda)", 1, "SiPM AFBR-S4N22P014M", "-", "Farnell 4351470",
                "montato su PCB separato incollato allo scintillatore"])
    return out


HDR = ["Rif.", "Qta", "Valore/Parte", "Package", "Codice ordine", "Note"]
TITLE = "BOM - Riv. Cosmici 2024 - Amplif, alim, soglie (INFN sez. Torino, rev. A) + buffer 3,3 V per Raspberry Pi"


def main():
    R = rows()
    with open(os.path.join(OUT, "BOM_riv_cosmici.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HDR)
        w.writerows(R)
    try:
        import openpyxl
        from openpyxl.styles import Font
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "BOM"
        ws.append([TITLE])
        ws["A1"].font = Font(bold=True)
        ws.append([])
        ws.append(HDR)
        for c in ws[3]:
            c.font = Font(bold=True)
        for r in R:
            ws.append(r)
        for col, wd in zip("ABCDEF", (28, 6, 24, 20, 26, 70)):
            ws.column_dimensions[col].width = wd
        wb.save(os.path.join(OUT, "BOM_riv_cosmici.xlsx"))
    except ImportError:
        print("openpyxl assente: scritto solo il CSV")
    n = sum(r[1] for r in R if r[0] != "(fuori scheda)")
    print(f"BOM: {len(R)} righe, {n} componenti sulla scheda")


if __name__ == "__main__":
    main()
