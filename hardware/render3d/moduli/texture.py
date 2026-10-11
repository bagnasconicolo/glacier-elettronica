# -*- coding: utf-8 -*-
"""Texture della faccia superiore (maschera verde, rame sotto maschera, pad stagnati, serigrafia)
da kicad-cli: uno strato alla volta in bianco e nero, poi composti con i colori.
    python3 texture.py scheda.kicad_pcb uscita.png [definizione.py]
Con la definizione del modulo, le fessure (FESSURE) diventano trasparenti."""
import io, os, subprocess, sys, tempfile
import cairosvg
from PIL import Image, ImageChops

pcb, out = sys.argv[1], sys.argv[2]
PX = 24                                            # pixel per mm


def strato(layers, td, nome):
    svg = os.path.join(td, nome + ".svg")
    subprocess.run(["kicad-cli", "pcb", "export", "svg", "-o", svg, "--page-size-mode", "2", "--black-and-white",
                    "--exclude-drawing-sheet", "-l", layers, pcb], check=True, capture_output=True)
    return svg


with tempfile.TemporaryDirectory() as td:
    # contorno per misurare la scheda (stesso riquadro per tutti gli strati: Edge.Cuts sempre incluso)
    files = {k: strato(l + ",Edge.Cuts", td, k) for k, l in
             (("cu", "F.Cu"), ("mask", "F.Mask"), ("silk", "F.Silkscreen"), ("edge", "Edge.Cuts"))}
    import re
    vb = re.search(r'width="([\d.]+)mm"', open(files["edge"]).read())
    wmm = float(vb.group(1))
    W = int(wmm * PX)
    img = {k: Image.open(io.BytesIO(cairosvg.svg2png(url=f, output_width=W, background_color="white"))).convert("L")
           for k, f in files.items()}
size = img["edge"].size
edge = img["edge"].point(lambda v: 255 if v < 128 else 0)          # linee del contorno
inv = lambda im: im.point(lambda v: 255 if v < 128 else 0)          # nero = disegnato -> maschera
cu = ImageChops.subtract(inv(img["cu"]), edge)
mask = ImageChops.subtract(inv(img["mask"]), edge)                  # aperture della maschera = pad
silk = ImageChops.subtract(inv(img["silk"]), edge)
base = Image.new("RGB", size, (24, 96, 52))                         # maschera verde
base.paste((44, 128, 72), mask=cu)                                  # rame sotto la maschera
base.paste((212, 208, 196), mask=mask)                              # pad stagnati (HASL)
base.paste((240, 240, 232), mask=ImageChops.subtract(silk, mask))   # serigrafia (non sui pad)
if len(sys.argv) > 3:                                              # fessure trasparenti
    import importlib.util
    from PIL import ImageDraw
    spec = importlib.util.spec_from_file_location("d", sys.argv[3])
    D = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(D)
    k = size[0] / wmm
    alpha = Image.new("L", size, 255)
    for f in getattr(D, "FESSURE", ()):
        ImageDraw.Draw(alpha).polygon([(x * k, y * k) for x, y in f], fill=0)
    base.putalpha(alpha)
base.save(out)
print("scritto", out, size)
