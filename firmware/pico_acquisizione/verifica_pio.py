# -*- coding: utf-8 -*-
"""Simulatore ciclo per ciclo del programma PIO di main.py (cattura dei fronti di salita).

Controlla, senza hardware, la formula usata dal firmware per ricostruire l'istante di
ogni impulso:   tick = (0xFFFFFFFF - x) + k        (k = impulsi precedenti dello stesso
canale; ogni fronte "costa" un tick perche' mov + push non decrementano x)
e che l'errore resti entro un tick (2 cicli di clock = 16 ns a 125 MHz), anche quando il
contatore x passa per zero e riparte da 0xFFFFFFFF.

Programma (stesso ordine di main.py; lo state machine parte dall'istruzione 0):
  0 rise:  mov isr, x
  1        push noblock
  2 high:  jmp x-- 3
  3        jmp pin 2
  4 (wrap_target) jmp x-- 5
  5        jmp pin 0      (wrap -> 4)

    python verifica_pio.py
"""
import random

M = 0xFFFFFFFF


def simula(impulsi, n_cicli, x0=M):
    """impulsi: lista di (inizio, fine) in cicli (il pin e' gia' sincronizzato).
    Restituisce i valori spinti nella FIFO con il ciclo in cui avviene il push."""
    def pin(c):
        return any(a <= c < b for a, b in impulsi)
    pc, x, isr, out = 0, x0, 0, []
    for c in range(n_cicli):
        if pc == 0:
            isr = x; pc = 1
        elif pc == 1:
            out.append((c, isr)); pc = 2
        elif pc in (2, 4):                      # jmp x--: salta se x != 0, decrementa sempre
            x = (x - 1) & M
            pc += 1                             # bersaglio = istruzione successiva in entrambi i casi
        elif pc == 3:
            pc = 2 if pin(c) else 4
        elif pc == 5:
            pc = 0 if pin(c) else 4             # wrap
    return out


def ricostruisci(out):
    """come main.py: scarta il marcatore di partenza, applica tick = (M - x) + k"""
    ev = []
    for k, (_c, v) in enumerate(out[1:]):
        ev.append(((M - v) + k) & M)
    return ev


def prova(nome, impulsi, n, x0=M, tick_ciclo=2):
    out = simula(impulsi, n, x0)
    assert out[0][1] == x0, "manca il marcatore di partenza"
    rec = ricostruisci(out)
    assert len(rec) == len(impulsi), (len(rec), len(impulsi))
    off = (M - x0)
    err = []
    for (a, _b), t in zip(impulsi, rec):
        cic = ((t - off) & M) * tick_ciclo               # istante ricostruito (mod 2^32 tick), in cicli
        err.append(a - cic)
    lo, hi = min(err), max(err)
    print(f"{nome:44s} impulsi {len(impulsi):4d}  errore da {lo:+d} a {hi:+d} cicli")
    return lo, hi


def main():
    r = random.Random(1)
    risultati = []
    # 1. impulsi da 150-220 ns (19-28 cicli a 125 MHz) a caso, anche ravvicinati
    t, imp = 50, []
    while t < 400_000:
        w = r.randint(19, 28); imp.append((t, t + w)); t += w + r.randint(3, 3000)
    risultati.append(prova("impulsi casuali 150-220 ns", imp, 401_000))
    # 2. impulsi minimi (3 cicli = 24 ns) e pause minime
    imp = [(100 + 7 * i, 103 + 7 * i) for i in range(200)]
    risultati.append(prova("impulsi da 24 ns, ogni 56 ns", imp, 2000))
    # 3. passaggio del contatore per zero (x parte vicino a 0)
    imp = [(40 + 61 * i, 60 + 61 * i) for i in range(300)]
    risultati.append(prova("contatore che passa per zero", imp, 20_000, x0=5000))
    lo = min(a for a, _ in risultati); hi = max(b for _, b in risultati)
    print(f"\nErrore complessivo: da {lo:+d} a {hi:+d} cicli (un tick = 2 cicli = 16 ns a 125 MHz).")
    assert 0 <= lo and hi <= 2, "formula sbagliata"
    print("OK: l'istante di ogni fronte e' ricostruito con un ritardo di 0-2 cicli "
          "(uguale per tutti i canali, quindi irrilevante nelle differenze di tempo).")


if __name__ == "__main__":
    main()
