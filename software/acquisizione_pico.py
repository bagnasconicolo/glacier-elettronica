#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Riceve tutto dal Raspberry Pi Pico 2 (firmware/pico_acquisizione) e lo salva, sullo Zero 2 W.

Dal Pico arrivano, in righe di testo:
  - gli impulsi delle tre barre e dell'AND, con l'istante in ns (risoluzione 13-16 ns);
  - il PPS del GPS con la sua ora UTC: ogni evento prende cosi' l'ora assoluta al
    microsecondo (senza GPS si usa l'orologio dello Zero, NTP, errore ~ms);
  - le letture dei sensori dietro l'hub I2C: monitor della scheda rivelatore (bias,
    alta tensione, soglie, temperatura) e modulo meteo (temperatura, umidita', pressione).

Questo programma:
  - salva gli eventi in CSV (ora UTC, fonte dell'ora, t_ns del Pico, canale);
  - salva i sensori in un secondo CSV (ambiente);
  - conta le coincidenze triple anche "in software", dai tempi delle tre barre, e le
    confronta con l'AND fatto in hardware dalla scheda: devono quasi coincidere;
  - stampa ogni 10 s ritmi, stato del GPS, ultime letture.

Collegamento: Pico 2 -> porta USB "dati" dello Zero 2 W (adattatore OTG micro-USB).
    pip install pyserial
    python3 acquisizione_pico.py --csv eventi.csv --ambiente ambiente.csv
    python3 acquisizione_pico.py --simula 120           # prova senza hardware (120 s simulati)
"""
import argparse, csv, datetime, os, random, sys, time
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monitor_tensioni as MT                         # stesse formule del monitor (partitori, NTC)

CANALI = ("1", "2", "3", "A")


class Orologio:
    """ora UTC di un istante del Pico.
    Con il GPS: dall'ultimo PPS battezzato, con la frequenza vera del quarzo del Pico
    misurata tra due PPS (il quarzo sbaglia di decine di ppm). Senza GPS: ora dello Zero
    meno il ritardo USB minimo tra le ultime righe di stato."""
    def __init__(self):
        self.ntp = deque(maxlen=120)
        self.pps = deque(maxlen=4)                     # (t_pps_ns, utc_s) con posizione valida

    def stato(self, t_pico_ns, ora_zero):
        self.ntp.append(ora_zero - t_pico_ns / 1e9)

    def gps(self, t_pps_ns, utc_s, valido):
        if valido:
            if self.pps and t_pps_ns - self.pps[-1][0] > 1.5e9:   # PPS saltati: niente stima vecchia
                self.pps.clear()
            self.pps.append((t_pps_ns, utc_s))

    def gps_ok(self, t_ns):
        return bool(self.pps) and abs(t_ns - self.pps[-1][0]) < 5e9

    def utc(self, t_ns):
        if self.gps_ok(t_ns):
            t0, u0 = self.pps[-1]
            scala = 1.0
            if len(self.pps) >= 2:
                (ta, ua), (tb, ub) = self.pps[0], self.pps[-1]
                scala = (ub - ua) * 1e9 / (tb - ta)            # secondi veri per secondo del Pico
            return u0 + (t_ns - t0) / 1e9 * scala, "gps"
        if self.ntp:
            return min(self.ntp) + t_ns / 1e9, "ntp"
        return None, "-"


class Coincidenze:
    """triple in software: un impulso per barra entro la finestra (le barre arrivano in
    ordine qualunque; ogni impulso si usa una sola volta)"""
    def __init__(self, finestra_ns):
        self.f = finestra_ns
        self.ultimo = {"1": None, "2": None, "3": None}
        self.n = 0

    def impulso(self, ch, t):
        if ch not in self.ultimo:
            return False
        self.ultimo[ch] = t
        tt = list(self.ultimo.values())
        if None in tt or max(tt) - min(tt) > self.f:
            return False
        self.n += 1
        self.ultimo = {k: None for k in self.ultimo}
        return True


def monitor(v):
    """tensioni agli ingressi degli ADC -> grandezze fisiche (come monitor_tensioni.py)"""
    d = {f"bias{c}": v[c - 1] * MT.RATIO * MT.CAL[f"bias{c}"] for c in (1, 2, 3)}
    d["hv"] = v[3] * MT.RATIO * MT.CAL["hv"]
    if len(v) >= 8:
        for c in (1, 2, 3):
            d[f"th{c}"] = v[3 + c] * MT.TH_CORR * MT.CAL[f"th{c}"]
        d["temp_scheda"] = MT.temperatura(v[7])
    return d


def righe_porta(porta):
    import serial                                    # pyserial
    with serial.Serial(porta, 115200, timeout=1) as s:
        s.write(b"?")                                # chiede l'intestazione
        while True:
            r = s.readline()
            if r:
                yield r.decode("ascii", "replace").strip(), time.time()


def righe_simulate(durata_s, seme=1):
    """stessa forma del Pico: singoli ~3 Hz per barra, muoni ~0,4 Hz (3 barre + AND entro
    ~30 ns), PPS ogni secondo (quarzo del Pico +25 ppm), sensori ogni 5 s, ritardo USB
    1-8 ms. Tempo accelerato."""
    r = random.Random(seme)
    t0 = time.time()
    utc0 = int(t0) + 1
    ev = []
    for ch, f in (("1", 2.5), ("2", 2.7), ("3", 2.3)):          # singoli non da muone
        t = 0.0
        while t < durata_s:
            t += r.expovariate(f)
            ev.append((int(t * 1e9), "E %s %d" % (ch, int(t * 1e9))))
    t = 0.0
    while t < durata_s:                                         # muoni: tre barre e AND
        t += r.expovariate(0.41)
        base = int(t * 1e9)
        for ch, d in (("1", 0), ("2", 2), ("3", 4)):
            tt = base + d + r.randint(0, 3) * 16
            ev.append((tt, "E %s %d" % (ch, tt)))
        ev.append((base + 20, "E A %d" % (base + 20)))
    for s in range(1, int(durata_s)):                           # GPS
        tp = int(s * 1e9 / 1.000025)
        ev.append((tp, "P %d" % tp))
        ev.append((tp + 300_000_000, "G %d %d A 9" % (tp, utc0 + s)))
    for s in range(0, int(durata_s), 5):                        # sensori
        ts = s * 10 ** 9 + 2 * 10 ** 8
        v = [0.3171, 0.3170, 0.3172, 1.6245, 0.1035, 0.1031, 0.1040, 1.0711]
        v = [x + r.gauss(0, 3e-5) for x in v]
        ev.append((ts, "M %d 0 " % ts + " ".join("%.6f" % x for x in v)))
        ev.append((ts + 10 ** 8, "W %d 3 %.3f %.2f %.3f %.2f" % (ts + 10 ** 8, 22.8 + r.gauss(0, .02),
                   47.5 + r.gauss(0, .1), 1012.84 + r.gauss(0, .02), 23.1)))
    ev.sort()
    yield "H pico_acquisizione 2.0 150000000 pps", t0
    yield "I 0:68,6a 3:44,77", t0
    n = {c: 0 for c in CANALI}
    s = 1
    for t_ns, riga in ev:
        if t_ns >= durata_s * 1e9:
            break
        while t_ns > s * 1e9:
            yield "S %d %d %d %d %d 0" % ((s * 10 ** 9,) + tuple(n[c] for c in CANALI)), t0 + s + r.uniform(.001, .008)
            s += 1
        if riga[0] == "E":
            n[riga.split()[1]] += 1
        yield riga, t0 + t_ns / 1e9 + r.uniform(.001, .008)


def iso(u):
    return datetime.datetime.fromtimestamp(u, datetime.timezone.utc).isoformat(timespec="microseconds")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--porta", default="/dev/ttyACM0")
    ap.add_argument("--csv", help="file CSV degli eventi")
    ap.add_argument("--ambiente", help="file CSV dei sensori (monitor e meteo)")
    ap.add_argument("--finestra-ns", type=int, default=1000, help="finestra delle triple in software")
    ap.add_argument("--simula", type=float, metavar="SECONDI", help="prova senza hardware")
    a = ap.parse_args()
    sorgente = righe_simulate(a.simula) if a.simula else righe_porta(a.porta)
    orol, coinc = Orologio(), Coincidenze(a.finestra_ns)
    n = {c: 0 for c in CANALI}
    st = {"persi": 0, "t_pico": 0, "gps": "-", "meteo": None, "monitor": None, "porte": ""}
    attesa, ultimo_rapporto = [], None
    fe = we = fa = wa = None
    if a.csv:
        fe = open(a.csv, "a", newline=""); we = csv.writer(fe)
        if fe.tell() == 0:
            we.writerow(["utc", "fonte_ora", "t_ns_pico", "canale"])
    if a.ambiente:
        fa = open(a.ambiente, "a", newline=""); wa = csv.writer(fa)
        if fa.tell() == 0:
            wa.writerow(["utc", "porta", "grandezza", "valore"])

    def salva(t_ns, ch):
        if we:
            u, fonte = orol.utc(t_ns)
            we.writerow([iso(u), fonte, t_ns, ch])

    def ambiente(t_ns, porta, valori):
        u, _ = orol.utc(t_ns)
        if wa and u is not None:                     # prima del primo riferimento d'ora: si salta
            for k, v in valori.items():
                if v is not None:
                    wa.writerow([iso(u), porta, k, "%.6g" % v])

    def rapporto(t_ns):
        dt = t_ns / 1e9
        if dt <= 0:
            return
        txt = (f"{dt:6.0f} s  " + "  ".join(f"{'b' + c if c != 'A' else 'AND'} {n[c] / dt:4.2f}/s" for c in CANALI)
               + f"  triple sw {coinc.n}/AND {n['A']}  persi {st['persi']}  ora: {orol.utc(t_ns)[1]}")
        if st["meteo"]:
            m = st["meteo"]
            txt += f"  {m.get('T', float('nan')):.1f} C {m.get('UR', float('nan')):.0f}% {m.get('P', float('nan')):.2f} hPa"
        if st["monitor"]:
            txt += f"  bias {st['monitor']['bias1']:.2f} V"
        print(txt)

    for riga, ora in sorgente:
        p = riga.split()
        if not p:
            continue
        k = p[0]
        if k == "H":
            print("Pico:", riga)
        elif k == "E" and len(p) == 3:
            ch, t_ns = p[1], int(p[2])
            n[ch] = n.get(ch, 0) + 1
            coinc.impulso(ch, t_ns)
            st["t_pico"] = max(st["t_pico"], t_ns)
            if orol.ntp or orol.pps:
                salva(t_ns, ch)
            else:
                attesa.append((t_ns, ch))            # nessun riferimento d'ora ancora arrivato
        elif k == "G" and len(p) == 5:
            orol.gps(int(p[1]), int(p[2]), p[3] == "A")
        elif k == "M" and len(p) >= 7:
            d = monitor([float(x) for x in p[3:]])
            st["monitor"] = d
            ambiente(int(p[1]), int(p[2]), d)
        elif k == "W" and len(p) == 7:
            f = lambda x: None if x == "-" else float(x)
            d = {"T": f(p[3]), "UR": f(p[4]), "P": f(p[5]), "T_baro": f(p[6])}
            st["meteo"] = d
            ambiente(int(p[1]), int(p[2]), d)
        elif k == "I":
            if riga != st["porte"]:
                print("Hub I2C:", riga[2:] or "nessun sensore")
                st["porte"] = riga
        elif k == "X":
            print("Sensori:", riga[2:])
        elif k == "S" and len(p) == 7:
            t_s = int(p[1])
            orol.stato(t_s, ora)
            st["persi"] = int(p[6])
            for e in attesa:
                salva(*e)
            attesa.clear()
            for fh in (fe, fa):
                if fh:
                    fh.flush()
            if ultimo_rapporto is None or t_s - ultimo_rapporto >= 10e9:
                ultimo_rapporto = t_s
                rapporto(t_s)
    rapporto(st["t_pico"])
    for fh in (fe, fa):
        if fh:
            fh.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
