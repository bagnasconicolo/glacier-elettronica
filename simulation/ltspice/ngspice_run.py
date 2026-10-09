# -*- coding: utf-8 -*-
"""Esegue una netlist con ngspice (batch) e restituisce misure .meas e
forme d'onda, senza modificare il file: ne crea una copia temporanea con un
blocco .control che salva il file raw.

    from ngspice_run import run
    meas, wave = run("riv_cosmici_completo.cir")
    wave["v(cmp_q)"], wave["time"]
"""
import os, re, subprocess, tempfile
import numpy as np


def read_raw(fn):
    """lettore minimale per file raw binari di ngspice (reali)."""
    with open(fn, "rb") as f:
        data = f.read()
    hdr_end = data.index(b"Binary:\n") + len(b"Binary:\n")
    hdr = data[:hdr_end].decode("latin-1")
    nvar = int(re.search(r"No\. Variables:\s*(\d+)", hdr).group(1))
    npts = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
    vars_ = re.search(r"Variables:\n(.*?)Binary:", hdr, re.S).group(1)
    names = [ln.split()[1].lower() for ln in vars_.strip().splitlines()]
    arr = np.frombuffer(data[hdr_end:hdr_end + 8 * nvar * npts], dtype="<f8")
    arr = arr.reshape(npts, nvar)
    return {n: arr[:, i] for i, n in enumerate(names)}


def run(cir, params=None, timeout=1200):
    """params: dict di .param da sovrascrivere (es. {'V2_POS': 0.5})"""
    cir = os.path.abspath(cir)
    d = os.path.dirname(cir)
    txt = open(cir, encoding="latin-1").read().replace("\r\n", "\n")
    if params:
        extra = "\n".join(f".param {k}={v}" for k, v in params.items())
        # i .param successivi prevalgono: li metto subito prima di .tran
        txt = re.sub(r"(?m)^\.tran", extra + "\n.tran", txt, count=1)
    fd, raw = tempfile.mkstemp(suffix=".raw")
    os.close(fd)
    ctrl = f".control\nset noaskquit\nrun\nwrite {raw}\n.endc\n"
    txt = re.sub(r"(?mi)^\.end\s*$", ctrl + ".end", txt)
    fd, tmp = tempfile.mkstemp(suffix=".cir", dir=d)
    with os.fdopen(fd, "w") as f:
        f.write(txt)
    try:
        p = subprocess.run(["ngspice", "-b", tmp], cwd=d, capture_output=True,
                           text=True, timeout=timeout)
    finally:
        os.remove(tmp)
    out = p.stdout + p.stderr
    meas = {}
    for m in re.finditer(r"(?m)^([a-z_0-9]+)\s+=\s+([-+0-9.eE]+)", out):
        meas[m.group(1)] = float(m.group(2))
    if "rror" in out and not os.path.getsize(raw):
        raise RuntimeError(out[-3000:])
    wave = read_raw(raw)
    os.remove(raw)
    return meas, wave
