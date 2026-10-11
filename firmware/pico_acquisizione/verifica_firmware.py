# -*- coding: utf-8 -*-
"""Prova in CPython del firmware del Pico (main.py, gps.py, sensori.py), con moduli finti.

1. Cattura: le code delle state machine vengono riempite con i valori che il PIO
   produrrebbe (formula verificata ciclo per ciclo in verifica_pio.py). Si controlla che
   il firmware scarti il marcatore di partenza, rimetta il tick perso a ogni fronte, conti
   i giri del contatore e dia l'istante giusto in ns, per 4 ingressi + PPS, 10 minuti.
2. GPS: checksum NMEA, data e ora delle frasi RMC (confronto con datetime di Python).
3. Sensori: hub TCA9548A finto con una scheda rivelatore (due MCP3424) sulla porta 0 e un
   modulo meteo (SHT45 + BMP390) sulla porta 3; valori letti = valori messi, CRC,
   formule del BMP390 identiche al driver Adafruit, distacco e ricollegamento a caldo.

    python verifica_firmware.py
"""
import datetime, random, struct, sys, time as time_vero, types

M = 0xFFFFFFFF
FREQ = 150_000_000                                  # Pico 2
stato = {"us": 0}
code = {i: [] for i in range(8)}

# ------------------------------------------------------------------ moduli finti
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
    def __init__(self, *a, **k): self.v = k.get("value", 0)
    def on(self): pass
    def off(self): pass
    def value(self, v=None): self.v = v if v is not None else self.v


class Mem(dict):
    def __getitem__(self, k): return 0
    def __setitem__(self, k, v):
        if k == 0x50200000 and v & 0xF:             # avvio: ogni state machine spinge il marcatore
            for i in range(4): code[i].append(M)
            if v & (1 << 24) and v & (1 << 20):     # e la prima del PIO1 (PPS), nello stesso ciclo
                code[4].append(M)


machine.Pin, machine.mem32 = Pin, Mem()
machine.I2C = machine.UART = object
tm = types.ModuleType("time")
tm.ticks_us = lambda: stato["us"] & ((1 << 30) - 1)
tm.ticks_ms = lambda: (stato["us"] // 1000) & ((1 << 30) - 1)
def ticks_diff(a, b):
    d = (a - b) & ((1 << 30) - 1)
    return d - (1 << 30) if d >= (1 << 29) else d
tm.ticks_diff = ticks_diff
tm.ticks_add = lambda a, b: (a + b) & ((1 << 30) - 1)
for name, mod in (("rp2", rp2), ("machine", machine), ("time", tm), ("select", types.ModuleType("select"))):
    sys.modules[name] = mod
sys.implementation._machine = "Raspberry Pi Pico 2 with RP2350"

import main as fw                                   # noqa: E402
import gps                                          # noqa: E402
import sensori                                      # noqa: E402
sys.modules["time"] = time_vero                     # il firmware resta col suo orologio finto


# ------------------------------------------------------------------ 1. cattura
def prova_cattura():
    r = random.Random(3)
    acq = fw.Acquisizione()
    assert acq.pps and len(acq.sm) == 5
    tick_ns = 2e9 / FREQ
    durata_s, ricevuti = 600, []
    eventi = []
    for i, f in enumerate((2.9, 3.1, 2.7, 0.41)):
        t = 0.0
        while True:
            t += r.expovariate(f)
            if t > durata_s: break
            eventi.append((int(t * 1e9 / tick_ns), i))
    for s in range(1, durata_s):                    # PPS: un impulso al secondo (orologio del Pico +20 ppm)
        eventi.append((int(s * 1.00002 * 1e9 / tick_ns), 4))
    eventi.sort()
    k = [0] * 5
    j, t_us = 0, 0
    while t_us < durata_s * 1e6:
        t_us += r.uniform(100, 20_000)
        stato["us"] = int(t_us)
        while j < len(eventi) and eventi[j][0] * tick_ns / 1000 < t_us:
            tick, i = eventi[j]
            code[i].append((M - (tick - k[i])) & M)
            k[i] += 1; j += 1
        acq.svuota(lambda i, t_ns: ricevuti.append((i, t_ns)))
    attesi = sorted((i, tick * 2_000_000_000 // FREQ) for tick, i in eventi[:j])
    ricevuti.sort()
    assert ricevuti == attesi, (len(ricevuti), len(attesi))
    giri = max(t for _, t in attesi) / (2 ** 32 * 2e9 / FREQ)
    print(f"1. cattura: {len(ricevuti)} impulsi (4 ingressi + {k[4]} PPS) in {durata_s} s, "
          f"{giri:.1f} giri del contatore: tutti esatti")


# ------------------------------------------------------------------ 2. GPS
def nmea(corpo):
    x = 0
    for c in corpo:
        x ^= ord(c)
    return "$%s*%02X\r\n" % (corpo, x)


def prova_gps():
    r = random.Random(5)
    for _ in range(2000):                           # giorni dal 1970 contro datetime
        d = datetime.date(2000, 1, 1) + datetime.timedelta(days=r.randrange(0, 36500))
        assert gps.giorni_da_1970(d.year, d.month, d.day) == (d - datetime.date(1970, 1, 1)).days
    n = gps.NMEA()
    t0 = datetime.datetime(2026, 10, 11, 23, 59, 58, tzinfo=datetime.timezone.utc)
    flusso = b""
    for s in range(4):
        t = t0 + datetime.timedelta(seconds=s)
        flusso += nmea("GNRMC,%s.00,A,4504.1234,N,00740.5678,E,0.01,,%s,,,A,V"
                       % (t.strftime("%H%M%S"), t.strftime("%d%m%y"))).encode()
        flusso += nmea("GNGGA,%s.00,4504.1234,N,00740.5678,E,1,07,1.2,240.0,M,47.0,M,," % t.strftime("%H%M%S")).encode()
    flusso += b"$GNRMC,000000.00,A,,,,,,,121026,,,A,V*00\r\n"           # checksum sbagliato: scartata
    utc = []
    for i in range(0, len(flusso), 7):              # a pezzi, come dalla seriale
        utc += n.dati(flusso[i:i + 7])
    attesi = [int((t0 + datetime.timedelta(seconds=s)).timestamp()) for s in range(4)]
    assert utc == attesi, (utc, attesi)
    assert n.valido and n.satelliti == 7
    print(f"2. GPS: 2000 date controllate, 4 frasi RMC lette (anche a cavallo di mezzanotte), "
          f"una con checksum sbagliato scartata")


# ------------------------------------------------------------------ 3. sensori
def crc8(d):
    return sensori.crc8(d)


class MCP3424:
    def __init__(self, volt): self.v, self.ch = volt, 1
    def write(self, d): self.ch = ((d[0] >> 5) & 3) + 1
    def read(self, n):
        raw = int(round(self.v[self.ch - 1] * 32768 / 2.048))
        return bytes([(raw >> 8) & 0xFF, raw & 0xFF, 0x08])


class SHT45:
    def __init__(self, t, rh):
        self.rt = int(round((t + 45) * 65535 / 175)); self.rh = int(round((rh + 6) * 65535 / 125))
    def write(self, d): assert d == b"\xfd"
    def read(self, n):
        a, b = self.rt.to_bytes(2, "big"), self.rh.to_bytes(2, "big")
        return a + bytes([crc8(a)]) + b + bytes([crc8(b)])


class BMP390:
    def __init__(self, cal, adc_p, adc_t):
        self.reg = {0x00: 0x60, 0x03: 0x60}
        for i, b in enumerate(cal): self.reg[0x31 + i] = b
        for i, b in enumerate(adc_p.to_bytes(3, "little") + adc_t.to_bytes(3, "little")): self.reg[0x04 + i] = b
        self.ptr = 0
    def write(self, d):
        self.ptr = d[0]
        if len(d) > 1: self.reg[d[0]] = d[1]
    def read(self, n): return bytes(self.reg.get(self.ptr + i, 0) for i in range(n))


class BusFinto:
    def __init__(self): self.porte, self.mask = {}, 0
    def _dev(self, a):
        sel = [p for p in range(8) if self.mask >> p & 1]
        if len(sel) != 1 or a not in self.porte.get(sel[0], {}): raise OSError(19)   # ENODEV
        return self.porte[sel[0]][a]
    def writeto(self, a, d):
        if a == 0x70: self.mask = d[0]
        else: self._dev(a).write(bytes(d))
    def readfrom(self, a, n): return self._dev(a).read(n)
    def scan(self):
        sel = [p for p in range(8) if self.mask >> p & 1]
        return [0x70] + (sorted(self.porte.get(sel[0], {})) if len(sel) == 1 else [])


def bmp_adafruit(cal, adc_p, adc_t):
    """riferimento: stesse righe del driver Adafruit CircuitPython BMP3XX"""
    coeff = struct.unpack("<HHbhhbbHHbbhbb", cal)
    T1, T2, T3 = coeff[0] / 2**-8.0, coeff[1] / 2**30.0, coeff[2] / 2**48.0
    P1, P2 = (coeff[3] - 2**14.0) / 2**20.0, (coeff[4] - 2**14.0) / 2**29.0
    P3, P4, P5, P6 = coeff[5] / 2**32.0, coeff[6] / 2**37.0, coeff[7] / 2**-3.0, coeff[8] / 2**6.0
    P7, P8, P9, P10, P11 = coeff[9] / 2**8.0, coeff[10] / 2**15.0, coeff[11] / 2**48.0, coeff[12] / 2**48.0, coeff[13] / 2**65.0
    pd1 = adc_t - T1; pd2 = pd1 * T2
    temperature = pd2 + (pd1 * pd1) * T3
    pd1 = P6 * temperature; pd2 = P7 * temperature**2.0; pd3 = P8 * temperature**3.0
    po1 = P5 + pd1 + pd2 + pd3
    pd1 = P2 * temperature; pd2 = P3 * temperature**2.0; pd3 = P4 * temperature**3.0
    po2 = adc_p * (P1 + pd1 + pd2 + pd3)
    pd1 = adc_p**2.0; pd2 = P9 + P10 * temperature; pd3 = pd1 * pd2; pd4 = pd3 + P11 * adc_p**3.0
    return po1 + po2 + pd4, temperature


def prova_sensori():
    r = random.Random(11)
    bus = BusFinto()
    volt = [0.3171, 0.3170, 0.3172, 1.6245, 0.1035, 0.1031, 0.1040, 1.0711]
    bus.porte[0] = {0x68: MCP3424(volt[:4]), 0x6A: MCP3424(volt[4:])}
    cal = bytes(r.randrange(256) for _ in range(21))
    adc_p, adc_t = 6_700_000 + r.randrange(10000), 8_400_000 + r.randrange(10000)
    bus.porte[3] = {0x44: SHT45(23.37, 48.2), 0x77: BMP390(cal, adc_p, adc_t)}
    righe, ms = [], [0]
    hub = sensori.Hub(bus, reset_pin=Pin())
    gen = sensori.ciclo(hub, bus, righe.append, lambda: ms[0] * 10**6, lambda: ms[0], periodo_ms=5000, scansione_ms=60000)

    def avanza(fino_ms):
        while ms[0] < fino_ms:
            ms[0] += next(gen)

    avanza(2000)                                    # un giro completo di letture
    assert righe[0] == "I 0:68,6a 3:44,77", righe[0]
    m = next(x for x in righe if x.startswith("M")).split()
    letti = [float(x) for x in m[3:]]
    assert m[2] == "0" and len(letti) == 8 and max(abs(a - b) for a, b in zip(letti, volt)) < 6.25e-5
    w = next(x for x in righe if x.startswith("W")).split()
    p_ref, t_ref = bmp_adafruit(cal, adc_p, adc_t)
    assert w[2] == "3" and abs(float(w[3]) - 23.37) < 0.01 and abs(float(w[4]) - 48.2) < 0.01
    assert abs(float(w[5]) - round(p_ref / 100, 3)) < 1e-9 and abs(float(w[6]) - round(t_ref, 2)) < 1e-9
    # distacco del modulo meteo e ricollegamento su un'altra porta
    del bus.porte[3]
    n0 = len(righe); avanza(ms[0] + 6000)
    assert any(x.startswith("X 3") for x in righe[n0:]), righe[n0:]
    assert any(x == "I 0:68,6a" for x in righe[n0:])
    bus.porte[5] = {0x44: SHT45(21.0, 55.0), 0x76: BMP390(cal, adc_p, adc_t)}
    n0 = len(righe); avanza(ms[0] + 70000)
    assert any(x == "I 0:68,6a 5:44,76" for x in righe[n0:]), righe[n0:]
    assert any(x.startswith("W") and x.split()[2] == "5" for x in righe[n0:])
    print("3. sensori: monitor (8 tensioni) e meteo letti giusti; BMP390 identico al driver Adafruit; "
          "modulo staccato -> errore e nuova scansione; ricollegato su un'altra porta -> trovato")


prova_cattura()
prova_gps()
prova_sensori()
print("OK")
