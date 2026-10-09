# -*- coding: utf-8 -*-
"""Raccoglie la VARIANTE A 3 CANALI in hardware/variante_3ch/: schema e PCB
KiCad, Gerber (+ zip), anteprime, BOM e file JLCPCB (BOM/CPL).
Da lanciare dopo gen_sch3.py e gen_pcb3.py.

    python gen_variante3.py
"""
import csv, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import netdata3                                    # noqa: E402
sys.modules["netdata"] = netdata3
import pcb_data as PD                              # noqa: E402
import pcb_data3 as P3                             # noqa: E402
PD.BOARD = P3.BOARD
PD.PLACEMENT.clear()
PD.PLACEMENT.update(P3.PLACEMENT)

SRC = os.path.join(HERE, "riv_cosmici_3ch")
DST = os.path.join(HERE, "..", "variante_3ch")
os.makedirs(os.path.join(DST, "gerber"), exist_ok=True)
os.makedirs(os.path.join(DST, "jlcpcb"), exist_ok=True)

# ---- KiCad
for f in ("riv_cosmici_3ch.kicad_sch", "riv_cosmici_3ch.kicad_pcb"):
    shutil.copy(os.path.join(SRC, f), DST)
pro = open(os.path.join(HERE, "..", "riv_cosmici.kicad_pro")).read().replace("riv_cosmici", "riv_cosmici_3ch")
open(os.path.join(DST, "riv_cosmici_3ch.kicad_pro"), "w").write(pro)
open(os.path.join(DST, "sym-lib-table"), "w").write(
    '(sym_lib_table\n  (lib (name "riv")(type "KiCad")(uri "${KIPRJMOD}/../riv.kicad_sym")(options "")(descr ""))\n)\n')
open(os.path.join(DST, "fp-lib-table"), "w").write(
    '(fp_lib_table\n  (lib (name "rivlib")(type "KiCad")(uri "${KIPRJMOD}/../rivlib.pretty")(options "")(descr ""))\n)\n')
# ---- Gerber
gz = os.path.join(DST, "riv_cosmici_3ch_gerber.zip")
with zipfile.ZipFile(gz, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(os.path.join(SRC, "gerber"))):
        shutil.copy(os.path.join(SRC, "gerber", f), os.path.join(DST, "gerber", f))
        z.write(os.path.join(SRC, "gerber", f), f)
# ---- anteprime
import cairosvg                                    # noqa: E402
cairosvg.svg2png(url=os.path.join(SRC, "pcb3_render.svg"),
                 write_to=os.path.join(DST, "anteprima_pcb_3ch.png"), output_width=1400)

# ---- BOM completa (tutti i componenti, anche quelli da saldare a mano)
import gen_bom                                     # noqa: E402
gen_bom.COMPONENTS = netdata3.COMPONENTS
gen_bom.PKG.update({"LEMO00": "LEMO 00 (EPL.00.250.NTN)", "TP": "test point THT",
                    "SO14": "SOIC-14", "HDR3": "header 1x3 2,54"})
gen_bom.NOTE.update({"74LVC1G11": "SN74LVC1G11DBVR, AND a 3 ingressi (coincidenza)",
                     "MCP3424": "MCP3424-E/SL, ADC I2C del monitor tensioni (LCSC C640884)",
                     "1M": "partitore monitor (alto)", "43k": "partitore monitor (basso)",
                     "10k": ""})
rows = []
groups = {}
for ref, (kind, value, fpk, extra) in netdata3.COMPONENTS.items():
    if kind == "MH":                                # fori di fissaggio: non sono componenti
        continue
    key = ("TP", "TP") if kind == "TP" else \
          (("LEMO", fpk) if fpk == "LEMO00" else (value, fpk))
    groups.setdefault(key, []).append(ref)
for (value, fpk), refs in groups.items():
    refs.sort(key=gen_bom.ref_key)
    note = gen_bom.NOTE.get(value, "")
    if fpk == "3296W":
        note = "Bourns 3296W-1-103LF o equivalente"
    if value == "100n":
        note = "X7R 50V (CF = disaccoppiamento)"
    if value == "TP":
        value, note = "test point", "pin di strip header 2,54 (o anello Keystone 5000 rosso / 5001 nero)"
    if value == "LEMO":
        value, note = "LEMO EPL.00.250.NTN", "presa a gomito da circuito stampato (gia' disponibili)"
    rows.append([" ".join(refs), len(refs), value, gen_bom.PKG[fpk], gen_bom.ORDER.get(value, ""), note])
rows.sort(key=lambda r: gen_bom.ref_key(r[0].split()[0]))
rows.append(["(fuori scheda)", 3, "SiPM AFBR-S4N22P014M", "-", "Farnell 4351470",
             "uno per canale, su PCB separato incollato allo scintillatore"])
with open(os.path.join(DST, "BOM_riv_cosmici_3ch.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(gen_bom.HDR)
    w.writerows(rows)

# ---- JLCPCB: BOM e CPL (montaggio solo delle parti comuni e reperibili)
import gen_jlcpcb as GJ                            # noqa: E402
DNP = {"U1", "U5", "U7", "J3", "J5", "J6", "JP1", "JP2", "JP3"}
for n in netdata3.CHANNELS:
    DNP |= {netdata3.chref(r, n) for r in ("U3", "U8", "D1", "J1", "J4")}
DNP |= {r for r in netdata3.COMPONENTS if r.startswith("TP") or r.startswith("MH")}
GJ.DNP = DNP
GJ.OUT = os.path.join(DST, "jlcpcb")
GJ.ZIP_SRC = gz
GJ.main()
print("variante a 3 canali in", os.path.normpath(DST))
print("DNP (a mano):", len(DNP), "componenti")
