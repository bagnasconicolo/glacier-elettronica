#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monitor delle tensioni della scheda a 3 canali, letto dal Raspberry Pi.

Collegamento (connettore J6 della scheda -> GPIO del Raspberry Pi):
    J6.1 GND -> pin 6 (GND)
    J6.2 SDA -> pin 3 (GPIO2, SDA1)
    J6.3 SCL -> pin 5 (GPIO3, SCL1)
Le resistenze di pull-up sono quelle del Pi (1,8 kohm verso 3,3 V): sulla scheda non ce ne sono.
Abilitare l'I2C:  sudo raspi-config -> Interface Options -> I2C;  poi  pip install smbus2
Verifica:         i2cdetect -y 1   (deve comparire 68)

L'ADC (MCP3424, indirizzo 0x68) lavora in modalita' "one-shot": converte solo quando
gli si chiede una lettura e tra una lettura e l'altra resta fermo. Per non disturbare le
misure basta una lettura al secondo (opzione --periodo).

Ingressi: CH1..CH3 = bias dei canali 1..3 (VREG38, uscita del regolatore),
          CH4 = alta tensione (41 V).  Partitore 1 Mohm / 43 kohm: V = V_adc * 1043/43.

    python3 monitor_tensioni.py                 # stampa ogni secondo
    python3 monitor_tensioni.py --csv log.csv   # e salva su file
"""
import argparse, csv, time
from smbus2 import SMBus, i2c_msg

ADDR = 0x68
RATIO = (1_000_000 + 43_000) / 43_000            # partitore 1M / 43k
# taratura: misura col multimetro il test point BIAS (o 41V) e metti qui il fattore
# V_multimetro / V_letta (1.0 = nessuna correzione)
CAL = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}
NOMI = {1: "BIAS canale 1", 2: "BIAS canale 2", 3: "BIAS canale 3", 4: "Alta tensione"}


def leggi(bus, ch):
    """una conversione one-shot a 16 bit (15 campioni/s, guadagno 1): tensione in ingresso all'ADC"""
    cfg = 0x80 | ((ch - 1) << 5) | (0b10 << 2)      # RDY=1 (avvia), canale, one-shot, 16 bit, PGA x1
    bus.write_byte(ADDR, cfg)
    for _ in range(50):                              # ~67 ms a 16 bit
        time.sleep(0.02)
        msg = i2c_msg.read(ADDR, 3)
        bus.i2c_rdwr(msg)
        hi, lo, stato = list(msg)
        if not stato & 0x80:                         # RDY = 0: dato pronto
            raw = (hi << 8) | lo
            if raw >= 0x8000:
                raw -= 0x10000
            return raw * 2.048 / 32768               # LSB = 62,5 uV
    raise TimeoutError(f"MCP3424: canale {ch} non pronto")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--periodo", type=float, default=1.0, help="secondi tra due giri di letture")
    ap.add_argument("--csv", help="file CSV dove salvare le letture")
    a = ap.parse_args()
    out = None
    if a.csv:
        f = open(a.csv, "a", newline="")
        out = csv.writer(f)
        out.writerow(["tempo"] + [NOMI[c] + " (V)" for c in (1, 2, 3, 4)])
    with SMBus(1) as bus:
        while True:
            t = time.time()
            v = {c: leggi(bus, c) * RATIO * CAL[c] for c in (1, 2, 3, 4)}
            print(time.strftime("%H:%M:%S"), "  ".join(f"{NOMI[c]}: {v[c]:7.3f} V" for c in v))
            if out:
                out.writerow([f"{t:.1f}"] + [f"{v[c]:.4f}" for c in (1, 2, 3, 4)])
                f.flush()
            time.sleep(max(0.0, a.periodo - (time.time() - t)))


if __name__ == "__main__":
    main()
