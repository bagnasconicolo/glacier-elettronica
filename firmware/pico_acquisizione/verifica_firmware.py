# -*- coding: utf-8 -*-
"""Prova in CPython della parte "CPU" di main.py, con moduli finti al posto del Pico.

Le code delle state machine vengono riempite con i valori che il PIO produrrebbe
(formula verificata ciclo per ciclo in verifica_pio.py). Si controlla che il firmware:
  - scarti il marcatore di partenza;
  - rimetta il tick perso a ogni fronte;
  - conti i giri del contatore (uno ogni ~69 s a 125 MHz) usando l'orologio in us;
  - restituisca l'istante giusto in ns, entro un tick (16 ns), per 10 minuti di misura.

    python verifica_firmware.py
"""
import random, sys, types

M = 0xFFFFFFFF
FREQ = 125_000_000
stato = {"us": 0}
code = {i: [] for i in range(4)}

# --- moduli finti
rp2 = types.ModuleType("rp2")
rp2.PIO = types.SimpleNamespace(JOIN_RX=2)
rp2.asm_pio = lambda **kw: (lambda f: f)
class SM:
    def __init__(self, i, prog, jmp_pin=None):
        self.i = i
        code[i].clear()
    def rx_fifo(self): return len(code[self.i])
    def get(self): return code[self.i].pop(0)
    def active(self, a): pass
    def restart(self): pass
    def exec(self, s): pass
rp2.StateMachine = SM
machine = types.ModuleType("machine")
machine.freq = lambda: FREQ
class Pin:
    IN = OUT = PULL_DOWN = 0
    def __init__(self, *a, **k): pass
    def on(self): pass
    def off(self): pass
class Mem(dict):
    def __getitem__(self, k): return 0
    def __setitem__(self, k, v):
        if k == 0x50200000 and v & 0xF:                # avvio: ogni state machine spinge il marcatore
            for i in range(4): code[i].append(M)
machine.Pin, machine.mem32 = Pin, Mem()
tm = types.ModuleType("time")
tm.ticks_us = lambda: stato["us"] & ((1 << 30) - 1)
tm.ticks_ms = lambda: (stato["us"] // 1000) & ((1 << 30) - 1)
def ticks_diff(a, b):
    d = (a - b) & ((1 << 30) - 1)
    return d - (1 << 30) if d >= (1 << 29) else d
tm.ticks_diff = ticks_diff
tm.ticks_add = lambda a, b: (a + b) & ((1 << 30) - 1)
for name, mod in (("rp2", rp2), ("machine", machine), ("time", tm)):
    sys.modules[name] = mod
sys.modules["select"] = types.ModuleType("select")

import main as fw                                   # noqa: E402


def prova():
    r = random.Random(3)
    acq = fw.Acquisizione()
    tick_ns = 2e9 / FREQ
    durata_s, ricevuti = 600, []
    # eventi veri, in tick dalla partenza: singoli ~3 Hz per barra, AND ~0,4 Hz
    eventi = []
    for i, f in enumerate((2.9, 3.1, 2.7, 0.41)):
        t = 0.0
        while True:
            t += r.expovariate(f)
            if t > durata_s: break
            eventi.append((int(t * 1e9 / tick_ns), i))
    eventi.sort()
    k = [0] * 4
    out = lambda nome, t_ns: ricevuti.append((nome, t_ns))
    j = 0
    # la CPU svuota le code a istanti casuali (ogni 0,1-20 ms)
    t_us = 0
    while t_us < durata_s * 1e6:
        t_us += r.uniform(100, 20_000)
        stato["us"] = int(t_us)
        while j < len(eventi) and eventi[j][0] * tick_ns / 1000 < t_us:
            tick, i = eventi[j]
            code[i].append((M - (tick - k[i])) & M)  # valore spinto dal PIO
            k[i] += 1; j += 1
        acq.svuota(out)
    attesi = [(fw.NOMI[i], tick * 16) for tick, i in eventi[:j]]
    ricevuti.sort(key=lambda e: (e[1], e[0])); attesi.sort(key=lambda e: (e[1], e[0]))
    assert len(ricevuti) == len(attesi), (len(ricevuti), len(attesi))
    err = max(abs(a[1] - b[1]) for a, b in zip(ricevuti, attesi))
    assert all(a[0] == b[0] for a, b in zip(ricevuti, attesi))
    giri = attesi[-1][1] / (2 ** 32 * 16)
    print(f"{len(ricevuti)} impulsi in {durata_s} s ({giri:.1f} giri del contatore): "
          f"errore massimo {err} ns, conteggi {acq.n}")
    assert err == 0
    print("OK: marcatore scartato, tick persi rimessi, giri del contatore contati.")


prova()
