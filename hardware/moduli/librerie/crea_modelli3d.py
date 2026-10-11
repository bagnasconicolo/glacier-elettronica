# -*- coding: utf-8 -*-
"""Modelli 3D (STEP, con colori) dei componenti che non hanno un modello nella libreria
ufficiale KiCad 7.0.11: Raspberry Pi Pico 2 (sopra gli zoccoli), presa LEMO EPL.00.250.NTN a
gomito, Sensirion SHT4x. Gli altri modelli sono copie della libreria ufficiale (kicad-packages3D).

Quote:
  - Pico 2: scheda 51 x 21 x 1 mm, RP2350 7 x 7 mm, micro-USB (scheda tecnica Raspberry Pi);
    sopra due strip femmina alte 8,5 mm (le strip sono il modello ufficiale PinSocket_1x20)
  - LEMO EPL.00.250.NTN: blocco 7 x 7 x 7,5 mm sopra la scheda, frontale filettato M7
    (diametro 7 mm), lunghezza complessiva 17,5 mm, asse a 4 mm dalla scheda (disegno LEMO)
  - SHT4x: DFN 1,5 x 1,5 x 0,5 mm

    python3 crea_modelli3d.py      ->  3d/glacier.3dshapes/*.step
"""
import os
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Pnt, gp_Ax2, gp_Dir
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "3d", "glacier.3dshapes")


def box(x1, y1, z1, x2, y2, z2):
    return BRepPrimAPI_MakeBox(gp_Pnt(x1, y1, z1), gp_Pnt(x2, y2, z2)).Shape()


def cil(p, d, r, h):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(*p), gp_Dir(*d)), r, h).Shape()


def scrivi(nome, parti):
    """parti: [(forma, (r, g, b))] -> STEP con un colore per parte"""
    doc = TDocStd_Document(TCollection_ExtendedString("MDTV-XCAF"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    for sh, c in parti:                              # una forma (e un colore) per parte
        lab = st.AddShape(sh, False)
        ct.SetColor(lab, Quantity_Color(*c, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    w = STEPCAFControl_Writer()
    w.SetColorMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    os.makedirs(OUT, exist_ok=True)
    w.Write(os.path.join(OUT, nome + ".step"))
    print("scritto", nome)


VERDE, NERO, ARGENTO, ORO, GRIGIO, BIANCO = ((0.05, 0.42, 0.20), (0.08, 0.08, 0.08), (0.78, 0.78, 0.80),
                                              (0.85, 0.68, 0.25), (0.35, 0.35, 0.37), (0.93, 0.93, 0.90))

# Pico 2: coordinate del modello (y verso l'alto = verso il pin 1 e la USB), z = altezza sulla
# scheda madre. La scheda del Pico poggia sulle strip femmina (8,5 mm)
z0 = 8.5
pico = [(box(-10.5, -25.5, z0, 10.5, 25.5, z0 + 1.0), VERDE),
        (box(-3.5, -3.5, z0 + 1.0, 3.5, 3.5, z0 + 1.8), NERO),                 # RP2350
        (box(-1.0, -9.0, z0 + 1.0, 1.0, -7.0, z0 + 1.7), NERO),                # flash
        (box(-4.0, 21.5, z0 + 1.0, 4.0, 26.5, z0 + 3.9), ARGENTO),             # micro-USB
        (box(5.0, 20.0, z0 + 1.0, 8.0, 23.0, z0 + 2.5), BIANCO),               # pulsante BOOTSEL
        (box(-8.0, 18.0, z0 + 1.0, -6.5, 19.0, z0 + 1.6), (0.2, 0.8, 0.2))]   # LED
for k in range(20):                                                        # piazzole dorate
    y = 24.13 - k * 2.54
    for x in (-8.89, 8.89):
        pico.append((cil((x, y, z0 + 1.0), (0, 0, 1), 0.8, 0.03), ORO))
scrivi("RPi_Pico2", pico)

# LEMO EPL.00.250.NTN: origine sul pin centrale, frontale verso +X, asse a 4 mm dalla scheda
lemo = [(box(-3.5, -3.5, 0.0, 3.5, 3.5, 7.5), ARGENTO),
        (cil((3.5, 0, 4.0), (1, 0, 0), 3.5, 10.5), ARGENTO),                  # filetto M7
        (cil((9.0, 0, 4.0), (1, 0, 0), 4.6, 2.0), ARGENTO),                   # dado
        (cil((13.9, 0, 4.0), (1, 0, 0), 1.6, 0.1), (0.9, 0.9, 0.85))]        # isolante PTFE
scrivi("LEMO_EPL.00.250.NTN", lemo)

# Sensirion SHT4x (DFN-4 1,5 x 1,5 mm)
sht = [(box(-0.75, -0.75, 0.0, 0.75, 0.75, 0.5), GRIGIO),
       (box(-0.35, -0.35, 0.5, 0.35, 0.35, 0.51), (0.15, 0.15, 0.15))]       # apertura del sensore
scrivi("Sensirion_SHT4x_DFN-4", sht)
