# -*- coding: utf-8 -*-
"""Impronte su misura della libreria 'moduli' (le altre sono copie delle ufficiali KiCad 7.0.11).

RPi_Pico2_Socket: Raspberry Pi Pico / Pico 2 montato su due strip femmina 1x20 (passo
2,54 mm, file distanti 17,78 mm = 0,7"). Numerazione come il Pico: pin 1-20 a sinistra
dall'alto in basso, pin 21-40 a destra dal basso in alto (pin 40 = VBUS in alto a destra).
USB in alto (Y negativa). Contorno del modulo 21 x 51 mm.

    python3 crea_impronte.py
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))


def pico():
    o = ['(footprint "RPi_Pico2_Socket" (version 20221018) (generator crea_impronte) (layer "F.Cu")',
         '  (descr "Raspberry Pi Pico / Pico 2 su due strip femmina 1x20 passo 2,54 mm, file a 17,78 mm; USB in alto")',
         '  (tags "Raspberry Pi Pico 2 RP2350 socket")', '  (attr through_hole)',
         '  (fp_text reference "REF**" (at 0 -27.2) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
         '  (fp_text value "RPi_Pico2" (at 0 27.2) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    # contorno del modulo (serigrafia) e area di ingombro
    o.append('  (fp_rect (start -10.5 -25.5) (end 10.5 25.5) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))')
    o.append('  (fp_rect (start -4 -26.8) (end 4 -25.5) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))')
    o.append('  (fp_text user "USB" (at 0 -23.6) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))')
    o.append('  (fp_rect (start -10.75 -27.05) (end 10.75 25.75) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')
    o.append('  (fp_rect (start -10.5 -25.5) (end 10.5 25.5) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))')
    for k in range(20):
        y = -24.13 + k * 2.54
        for num, x in ((k + 1, -8.89), (40 - k, 8.89)):
            shape = "rect" if num == 1 else "oval"
            o.append(f'  (pad "{num}" thru_hole {shape} (at {x} {round(y, 3)}) (size 1.7 1.7) (drill 1.0) '
                     f'(layers "*.Cu" "*.Mask"))')
    o.append(')')
    open(os.path.join(HERE, "moduli.pretty", "RPi_Pico2_Socket.kicad_mod"), "w").write("\n".join(o) + "\n")


def sht4x_instradabile():
    """Copia dell'impronta ufficiale Sensirion SHT4x (NoCentralPad) con l'area di divieto
    ridotta alla zona centrale tra le due file di pad (x da -0,4 a +0,4 mm): nell'originale
    copre anche il centro dei pad, e un autorouter che si aggancia al centro del pad non
    puo' collegarli. Sotto il sensore continuano a non passare piste ne' piano di rame."""
    import re
    src = os.path.join(HERE, "moduli.pretty", "Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad.kicad_mod")
    s = open(src).read()
    s = s.replace('(footprint "Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad"',
                  '(footprint "Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_KeepoutCentro"', 1)
    s = re.sub(r"\(polygon\s*\(pts.*?\)\s*\)\s*\)", "(polygon (pts (xy -0.4 -0.75) (xy 0.4 -0.75) (xy 0.4 0.75) (xy -0.4 0.75)))",
               s, count=1, flags=re.S)
    open(os.path.join(HERE, "moduli.pretty", "Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_KeepoutCentro.kicad_mod"), "w").write(s)


if __name__ == "__main__":
    pico()
    sht4x_instradabile()
    print("scritte: RPi_Pico2_Socket, Sensirion_DFN-4_..._SHT4x_KeepoutCentro")
