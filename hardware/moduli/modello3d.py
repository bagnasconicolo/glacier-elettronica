# -*- coding: utf-8 -*-
"""Modello 3D (STEP) delle schede montate, con i modelli di librerie/3d.

In una copia temporanea del PCB le variabili dei percorsi (${KICAD7_3DMODEL_DIR},
${KIPRJMOD}/..) diventano percorsi assoluti ai file .step, poi kicad-cli esporta lo STEP.
Il file si apre con FreeCAD, KiCad (visualizzatore 3D) o qualunque CAD meccanico.

    python3 modello3d.py meteo acquisizione     ->  <cartella>/<nome>.step
"""
import glob, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LIB3D = os.path.join(HERE, "librerie", "3d")


def esporta(cartella):
    pcb = glob.glob(os.path.join(HERE, cartella, "*.kicad_pcb"))[0]
    s = open(pcb).read()
    s = re.sub(r'\$\{KICAD[67]_3DMODEL_DIR\}', LIB3D, s)
    s = s.replace("${KIPRJMOD}/../librerie/3d", LIB3D)
    s = re.sub(r'(\(model "[^"]*)\.wrl"', r'\1.step"', s)
    mancanti = sorted({m for m in re.findall(r'\(model "([^"]*)"', s) if not os.path.exists(m)})
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, os.path.basename(pcb))
        open(tmp, "w").write(s)
        out = pcb.replace(".kicad_pcb", ".step")
        r = subprocess.run(["kicad-cli", "pcb", "export", "step", "-f", "-o", out, tmp],
                           capture_output=True, text=True)
    errori = [l for l in (r.stdout + r.stderr).splitlines() if "Could not add" in l]
    print(f"{os.path.relpath(out, HERE)}: {os.path.getsize(out) // 1024} kB, modelli mancanti: {mancanti or 'nessuno'}"
          f"{', errori: ' + str(errori) if errori else ''}")
    return not errori


if __name__ == "__main__":
    ok = all([esporta(c) for c in sys.argv[1:]])
    sys.exit(0 if ok else 1)
