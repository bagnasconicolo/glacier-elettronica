#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legge gli impulsi dal Raspberry Pi Pico (firmware/pico_acquisizione) e li salva, sullo Zero 2 W.

Il Pico manda una riga per impulso con l'istante in ns (risoluzione 16 ns, stessa scala
per i quattro ingressi). Questo programma:
  - converte gli istanti in ora UTC usando l'orologio dello Zero (NTP, errore ~ms);
  - salva gli eventi in CSV (ora UTC, t_ns del Pico, canale);
  - conta le coincidenze triple anche "in software", dai tempi delle tre barre, e le
    confronta con l'AND fatto in hardware dalla scheda: devono quasi coincidere;
  - stampa ogni 10 s i ritmi dei canali.

Collegamento: Pico -> porta USB "dati" dello Zero 2 W (adattatore OTG micro-USB).
    pip install pyserial
    python3 acquisizione_pico.py                       # porta /dev/ttyACM0
    python3 acquisizione_pico.py --csv eventi.csv
    python3 acquisizione_pico.py --simula 120           # prova senza hardware (120 s simulati)
"""
import argparse, csv, datetime, random, sys, time
from collections import deque

CANALI = ("1", "2", "3", "A")


class Orologio:
    """ora UTC di un istante del Pico: offset = ora_Zero - t_Pico, preso col ritardo USB minimo
    tra le ultime righe di stato (il ritardo USB puo' solo aggiungere tempo)"""
    def __init__(self):
        self.campioni = deque(maxlen=120)

    def stato(self, t_pico_ns, ora_zero):
        self.campioni.append(ora_zero - t_pico_ns / 1e9)

    def utc(self, t_ns):
        if not self.campioni:
            return None
        return min(self.campioni) + t_ns / 1e9


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
    ~30 ns), righe di stato ogni secondo, ritardo USB 1-8 ms. Tempo accelerato."""
    r = random.Random(seme)
    t0 = time.time()
    ev = []
    for ch, f in (("1", 2.5), ("2", 2.7), ("3", 2.3)):          # singoli non da muone
        t = 0.0
        while t < durata_s:
            t += r.expovariate(f)
            ev.append((int(t * 1e9), ch))
    t = 0.0
    while t < durata_s:                                         # muoni: tutte e tre le barre e l'AND
        t += r.expovariate(0.41)
        base = int(t * 1e9)
        for ch, d in (("1", 0), ("2", 2), ("3", 4)):
            ev.append((base + d + r.randint(0, 3) * 16, ch))
        ev.append((base + 20, "A"))
    ev = sorted(e for e in ev if e[0] < durata_s * 1e9)
    n = {c: 0 for c in CANALI}
    yield "H pico_acquisizione 1.0 125000000", t0
    s = 1
    for t_ns, ch in ev:
        while t_ns > s * 1e9:
            yield "S %d %d %d %d %d 0" % ((s * 10 ** 9,) + tuple(n[c] for c in CANALI)), t0 + s + r.uniform(.001, .008)
            s += 1
        n[ch] += 1
        yield "E %s %d" % (ch, t_ns), t0 + t_ns / 1e9 + r.uniform(.001, .008)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--porta", default="/dev/ttyACM0")
    ap.add_argument("--csv", help="file CSV degli eventi")
    ap.add_argument("--finestra-ns", type=int, default=1000, help="finestra delle triple in software")
    ap.add_argument("--simula", type=float, metavar="SECONDI", help="prova senza hardware")
    a = ap.parse_args()
    sorgente = righe_simulate(a.simula) if a.simula else righe_porta(a.porta)
    orol, coinc = Orologio(), Coincidenze(a.finestra_ns)
    n = {c: 0 for c in CANALI}
    persi, attesa, ultimo_rapporto, t_pico = 0, [], None, 0
    f = w = None
    if a.csv:
        f = open(a.csv, "a", newline="")
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["utc", "t_ns_pico", "canale"])

    def salva(t_ns, ch):
        if w:
            u = orol.utc(t_ns)
            w.writerow([datetime.datetime.fromtimestamp(u, datetime.timezone.utc).isoformat(timespec="microseconds"), t_ns, ch])

    def rapporto(t_ns):
        dt = t_ns / 1e9
        if dt <= 0:
            return
        print(f"{dt:7.0f} s  " + "  ".join(f"{'barra ' + c if c != 'A' else 'AND':8s} {n[c] / dt:5.2f}/s" for c in CANALI)
              + f"   triple software {coinc.n} / AND {n['A']}   persi {persi}")

    for riga, ora in sorgente:
        p = riga.split()
        if not p:
            continue
        if p[0] == "H":
            print("Pico:", riga)
        elif p[0] == "E" and len(p) == 3:
            ch, t_ns = p[1], int(p[2])
            n[ch] = n.get(ch, 0) + 1
            coinc.impulso(ch, t_ns)
            t_pico = max(t_pico, t_ns)
            if orol.campioni:
                salva(t_ns, ch)
            else:
                attesa.append((t_ns, ch))            # prima riga di stato non ancora arrivata
        elif p[0] == "S" and len(p) == 7:
            t_s = int(p[1])
            orol.stato(t_s, ora)
            persi = int(p[6])
            for e in attesa:
                salva(*e)
            attesa.clear()
            if f:
                f.flush()
            if ultimo_rapporto is None or t_s - ultimo_rapporto >= 10e9:
                ultimo_rapporto = t_s
                rapporto(t_s)
    rapporto(t_pico)
    if f:
        f.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
