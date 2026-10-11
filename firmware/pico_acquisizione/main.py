# -*- coding: utf-8 -*-
"""Acquisizione degli impulsi del rivelatore a 3 canali con un Raspberry Pi Pico (MicroPython).

Il Pico NON perde impulsi e ne annota l'istante: quattro state machine PIO (una per
ingresso) guardano il proprio pin a ogni coppia di cicli di clock (16 ns a 125 MHz,
13,3 ns su Pico 2 a 150 MHz) e, a ogni fronte di salita, mettono in coda il valore di un
contatore. Le quattro state machine partono nello stesso ciclo, quindi i tempi dei
quattro ingressi sono sulla stessa scala. La CPU svuota le code e manda tutto allo
Zero 2 W via USB, una riga per evento. Verifica della formula: verifica_pio.py.

Ingressi (attraverso il buffer di protezione, vedi LEGGIMI.md):
    GP2 = barra 1    GP3 = barra 2    GP4 = barra 3    GP5 = AND (coincidenza)

Righe inviate sulla seriale USB (testo, separato da spazi):
    H pico_acquisizione <versione> <frequenza_Hz>      intestazione (all'avvio e con "?")
    E <canale> <t_ns>                                  un impulso; canale = 1, 2, 3 oppure A;
                                                       t_ns = nanosecondi dalla partenza
    S <t_ns> <n1> <n2> <n3> <nA> <persi>               stato, una volta al secondo: conteggi
                                                       totali e impulsi persi (coda piena)
Comandi accettati dalla seriale:  "?" ripete l'intestazione,  "R" riparte da zero.

Installazione: MicroPython sul Pico, poi copiare questo file come main.py
(per esempio con Thonny o con  mpremote cp main.py :main.py).
"""
import rp2, machine, time, sys, select
from machine import Pin, mem32

VERSIONE = "1.0"
PIN_INGRESSI = (2, 3, 4, 5)
NOMI = ("1", "2", "3", "A")
M = 0xFFFFFFFF
PIO0_BASE = 0x50200000            # stesso indirizzo su RP2040 e RP2350
PIO_CTRL, PIO_FDEBUG = PIO0_BASE + 0x000, PIO0_BASE + 0x008


@rp2.asm_pio(fifo_join=rp2.PIO.JOIN_RX)
def fronti():
    # x scende di 1 ogni 2 cicli. A ogni fronte di salita mov + push costano un
    # decremento: il firmware lo rimette (variabile k). Ordine e conti in verifica_pio.py.
    label("rise")
    mov(isr, x)                   # istante del fronte
    push(noblock)                 # in coda (8 posti); se la coda e' piena si segna in FDEBUG
    label("high")
    jmp(x_dec, "hchk")            # attesa della discesa, contando
    label("hchk")
    jmp(pin, "high")
    wrap_target()
    jmp(x_dec, "lchk")            # attesa della salita, contando
    label("lchk")
    jmp(pin, "rise")
    wrap()


class Acquisizione:
    def __init__(self):
        self.freq = machine.freq()
        self.pin = [Pin(p, Pin.IN, Pin.PULL_DOWN) for p in PIN_INGRESSI]
        self.sm = []
        self.riparti()

    def riparti(self):
        for sm in self.sm:
            sm.active(0)
        self.sm = []
        for i, pin in enumerate(self.pin):
            # (ri)creata da capo: parte dall'istruzione 0, con la coda vuota
            sm = rp2.StateMachine(i, fronti, jmp_pin=pin)    # divisore 1: clock di sistema
            while sm.rx_fifo():
                sm.get()
            sm.restart()
            sm.exec("mov(x, invert(null))")                  # x = 0xFFFFFFFF
            self.sm.append(sm)
        self.primo = [True] * 4                              # il primo valore e' il marcatore di partenza
        self.k = [0] * 4
        self.n = [0] * 4
        self.persi = 0
        mem32[PIO_FDEBUG] = 0xF                              # azzera i segnali di coda piena
        self.t_us, self.ultimo = 0, time.ticks_us()
        mem32[PIO_CTRL] = 0xFFF                              # avvio delle 4 state machine nello stesso ciclo

    def orologio_ns(self):
        """tempo grossolano (risoluzione 1 us) dalla partenza, senza giri del contatore"""
        ora = time.ticks_us()
        self.t_us += time.ticks_diff(ora, self.ultimo)
        self.ultimo = ora
        return self.t_us * 1000

    def svuota(self, uscita):
        grezzo = self.orologio_ns() * self.freq // 2_000_000_000   # stesso istante, in tick
        for i, sm in enumerate(self.sm):
            while sm.rx_fifo():
                v = sm.get()
                if self.primo[i]:
                    self.primo[i] = False
                    continue
                t = ((M - v) + self.k[i]) & M                # tick dalla partenza, modulo 2^32
                self.k[i] += 1
                t += ((grezzo - t + (1 << 31)) >> 32) << 32  # il contatore fa un giro ogni ~69 s
                self.n[i] += 1
                uscita(NOMI[i], t * 2_000_000_000 // self.freq)
        st = mem32[PIO_FDEBUG] & 0xF
        if st:
            self.persi += 1
            mem32[PIO_FDEBUG] = st


def main():
    led = Pin("LED", Pin.OUT)
    acq = Acquisizione()
    scrivi = sys.stdout.write
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)
    led_off = [0]

    def intestazione():
        scrivi("H pico_acquisizione %s %d\n" % (VERSIONE, acq.freq))

    def evento(nome, t_ns):
        scrivi("E %s %d\n" % (nome, t_ns))
        if nome == "A":                                      # un muone: lampeggio del LED
            led.on()
            led_off[0] = time.ticks_add(time.ticks_ms(), 40)

    intestazione()
    prossimo = time.ticks_add(time.ticks_ms(), 1000)
    while True:
        acq.svuota(evento)
        ora = time.ticks_ms()
        if led_off[0] and time.ticks_diff(ora, led_off[0]) >= 0:
            led.off()
            led_off[0] = 0
        if time.ticks_diff(ora, prossimo) >= 0:
            prossimo = time.ticks_add(prossimo, 1000)
            scrivi("S %d %d %d %d %d %d\n" % ((acq.orologio_ns(),) + tuple(acq.n) + (acq.persi,)))
        if poll.poll(0):
            c = sys.stdin.read(1)
            if c == "?":
                intestazione()
            elif c == "R":
                acq.riparti()
                intestazione()


if __name__ == "__main__":
    main()
