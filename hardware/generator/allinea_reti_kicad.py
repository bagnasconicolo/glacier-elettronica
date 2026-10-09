# -*- coding: utf-8 -*-
"""Dà alle reti del PCB gli stessi nomi che KiCad ricava dallo schema
("/CMP_IN1" per le etichette locali, "Net-(Q101-C)" per le reti senza etichetta,
"unconnected-(...)" per i pin liberi), come farebbe "Aggiorna PCB dallo schema" (F8).
Senza questo passo il DRC di KiCad con --schematic-parity segnala net_conflict
(solo nomi: i collegamenti sono identici, e lo script lo verifica prima di rinominare).

    python3 allinea_reti_kicad.py ../variante_3ch/riv_cosmici_3ch      (senza estensione)

Richiede KiCad >= 7 (pcbnew + kicad-cli).
"""
import os, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
import pcbnew

base = sys.argv[1]
xml = os.path.join(tempfile.mkdtemp(), "net.xml")
subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml,
                base + ".kicad_sch"], check=True, capture_output=True)
sch = {}
for n in ET.parse(xml).getroot().iter("net"):
    for x in n.iter("node"):
        sch[(x.get("ref"), x.get("pin"))] = n.get("name")

b = pcbnew.LoadBoard(base + ".kicad_pcb")
old2new, loose = {}, []
for fp in b.GetFootprints():
    for p in fp.Pads():
        k = (fp.GetReference(), p.GetNumber())
        if k not in sch:
            continue
        if p.GetNetCode() > 0:
            o = p.GetNetname()
            if old2new.setdefault(o, sch[k]) != sch[k]:
                sys.exit(f"collegamenti diversi tra schema e PCB su {k}: {o}")
        else:
            loose.append((p, sch[k]))
if len(set(old2new.values())) != len(old2new):
    sys.exit("due reti del PCB finirebbero nella stessa rete dello schema")
nets = b.GetNetInfo()
for o, n in old2new.items():
    nets.GetNetItem(o).SetNetname(n)
for p, n in loose:                                   # pin liberi: rete "unconnected-(...)"
    ni = pcbnew.NETINFO_ITEM(b, n)
    b.Add(ni)
    p.SetNet(ni)
b.Save(base + ".kicad_pcb")
print(f"reti rinominate: {sum(o != n for o, n in old2new.items())}, pin liberi: {len(loose)}")
