#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monitor della scheda a 3 canali, letto dal Raspberry Pi: bias, alta tensione, soglie, temperatura.

Collegamento (connettore J6 della scheda, Molex KK 3 poli -> GPIO del Raspberry Pi):
    J6.1 GND -> pin 6 (GND)
    J6.2 SDA -> pin 3 (GPIO2, SDA1)
    J6.3 SCL -> pin 5 (GPIO3, SCL1)
Le resistenze di pull-up sono quelle del Pi (1,8 kohm verso 3,3 V): sulla scheda non ce ne sono.
Abilitare l'I2C:  sudo raspi-config -> Interface Options -> I2C;  poi  pip install smbus2
Verifica:         i2cdetect -y 1   (devono comparire 68 e un secondo indirizzo tra 69 e 6f)

Due ADC MCP3424 sullo stesso bus, in modalita' "one-shot" (convertono solo quando
gli si chiede una lettura; una lettura al secondo non disturba le misure):
  U11 (0x68): CH1..CH3 = bias dei canali 1..3 (VREG38), CH4 = alta tensione.
              Partitore 1 Mohm / 43 kohm: V = V_adc * 1043/43.
  U12 (Adr0 = VDD, Adr1 = GND; il programma ne cerca l'indirizzo):
              CH1..CH3 = soglie dei canali 1..3, lette attraverso 10 kohm + 100 nF:
              l'ingresso dell'ADC (~2,25 Mohm) fa leggere lo 0,44 % in meno, qui corretto.
              CH4 = temperatura della scheda: NTC 10 kohm (B ~ 3900) verso massa,
              22 kohm verso +3,3 V.

    python3 monitor_tensioni.py                 # stampa ogni secondo
    python3 monitor_tensioni.py --csv log.csv   # e salva su file
"""
import argparse, csv, math, time
from smbus2 import SMBus, i2c_msg

ADDR_BIAS = 0x68
RATIO = (1_000_000 + 43_000) / 43_000            # partitore 1M / 43k
TH_CORR = 1 + 10e3 / 2.25e6                      # 10k in serie all'ingresso da ~2,25 Mohm
NTC_R25, NTC_B, R_SERIE, VDD = 10e3, 3900.0, 22e3, 3.3
# taratura: misura col multimetro il test point (BIAS, 41V, SOGLIA) e metti qui il fattore
# V_multimetro / V_letta (1.0 = nessuna correzione); per la temperatura un offset in gradi
CAL = {"bias1": 1.0, "bias2": 1.0, "bias3": 1.0, "hv": 1.0,
       "th1": 1.0, "th2": 1.0, "th3": 1.0, "temp_offset": 0.0}


def leggi(bus, addr, ch):
    """una conversione one-shot a 16 bit (15 campioni/s, guadagno 1): tensione in ingresso all'ADC"""
    cfg = 0x80 | ((ch - 1) << 5) | (0b10 << 2)      # RDY=1 (avvia), canale, one-shot, 16 bit, PGA x1
    bus.write_byte(addr, cfg)
    for _ in range(50):                              # ~67 ms a 16 bit
        time.sleep(0.02)
        msg = i2c_msg.read(addr, 3)
        bus.i2c_rdwr(msg)
        hi, lo, stato = list(msg)
        if not stato & 0x80:                         # RDY = 0: dato pronto
            raw = (hi << 8) | lo
            if raw >= 0x8000:
                raw -= 0x10000
            return raw * 2.048 / 32768               # LSB = 62,5 uV
    raise TimeoutError(f"MCP3424 0x{addr:02x}: canale {ch} non pronto")


def trova_secondo_adc(bus):
    """indirizzo del secondo MCP3424 (U12): il primo che risponde tra 0x69 e 0x6f"""
    for addr in range(0x69, 0x70):
        try:
            bus.read_byte(addr)
            return addr
        except OSError:
            pass
    return None


def temperatura(v):
    """tensione sul partitore 22k / NTC -> gradi Celsius (equazione B)"""
    if not 0.0 < v < VDD:
        return float("nan")
    r = R_SERIE * v / (VDD - v)
    return 1.0 / (1.0 / 298.15 + math.log(r / NTC_R25) / NTC_B) - 273.15 + CAL["temp_offset"]


def leggi_tutto(bus, addr2):
    v = {f"bias{c}": leggi(bus, ADDR_BIAS, c) * RATIO * CAL[f"bias{c}"] for c in (1, 2, 3)}
    v["hv"] = leggi(bus, ADDR_BIAS, 4) * RATIO * CAL["hv"]
    if addr2 is not None:
        for c in (1, 2, 3):
            v[f"th{c}"] = leggi(bus, addr2, c) * TH_CORR * CAL[f"th{c}"]
        v["temp"] = temperatura(leggi(bus, addr2, 4))
    return v


COLONNE = [("bias1", "BIAS ch1 (V)"), ("bias2", "BIAS ch2 (V)"), ("bias3", "BIAS ch3 (V)"),
           ("hv", "alta tensione (V)"), ("th1", "soglia ch1 (V)"), ("th2", "soglia ch2 (V)"),
           ("th3", "soglia ch3 (V)"), ("temp", "temperatura (C)")]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--periodo", type=float, default=1.0, help="secondi tra due giri di letture")
    ap.add_argument("--csv", help="file CSV dove salvare le letture")
    a = ap.parse_args()
    out = None
    with SMBus(1) as bus:
        addr2 = trova_secondo_adc(bus)
        print("ADC soglie/temperatura:", f"0x{addr2:02x}" if addr2 else "non trovato (solo bias e alta tensione)")
        if a.csv:
            f = open(a.csv, "a", newline="")
            out = csv.writer(f)
            out.writerow(["tempo"] + [n for _k, n in COLONNE])
        while True:
            t = time.time()
            v = leggi_tutto(bus, addr2)
            txt = [f"BIAS {v['bias1']:.3f} {v['bias2']:.3f} {v['bias3']:.3f} V", f"HV {v['hv']:.2f} V"]
            if "th1" in v:
                txt += [f"soglie {v['th1'] * 1e3:.1f} {v['th2'] * 1e3:.1f} {v['th3'] * 1e3:.1f} mV",
                        f"T {v['temp']:.1f} C"]
            print(time.strftime("%H:%M:%S"), "  ".join(txt))
            if out:
                out.writerow([f"{t:.1f}"] + [f"{v[k]:.5f}" if k in v else "" for k, _n in COLONNE])
                f.flush()
            time.sleep(max(0.0, a.periodo - (time.time() - t)))


if __name__ == "__main__":
    main()
