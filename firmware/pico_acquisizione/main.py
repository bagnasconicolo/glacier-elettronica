# -*- coding: utf-8 -*-
"""Acquisizione del rivelatore a 3 canali con un Raspberry Pi Pico 2 (MicroPython).

Il Pico NON perde impulsi e ne annota l'istante: una state machine PIO per ingresso
guarda il proprio pin a ogni coppia di cicli di clock (13,3 ns su Pico 2 a 150 MHz,
16 ns su Pico a 125 MHz) e, a ogni fronte di salita, mette in coda il valore di un
contatore. Le state machine partono nello stesso ciclo, quindi i tempi sono tutti sulla
stessa scala. Formula verificata ciclo per ciclo in verifica_pio.py.

In piu' il Pico:
  - annota allo stesso modo il PPS del GPS e gli da' un nome (ora UTC) con le frasi
    NMEA (gps.py): ogni evento ha cosi' l'ora assoluta al microsecondo;
  - legge i sensori I2C dietro l'hub TCA9548A (sensori.py): monitor della scheda
    rivelatore, modulo meteo, altro in futuro.

Collegamenti (vedi LEGGIMI.md):
    GP2 barra 1   GP3 barra 2   GP4 barra 3   GP5 AND        (attraverso i buffer)
    GP6 PPS del GPS   GP0/GP1 seriale del GPS (TX/RX)
    GP8/GP9 I2C (SDA/SCL) verso l'hub   GP7 RESET dell'hub

Righe inviate allo Zero sulla seriale USB (testo):
    H pico_acquisizione <versione> <frequenza_Hz> <pps|no_pps>
    E <canale> <t_ns>                 impulso; canale 1, 2, 3 oppure A; ns dalla partenza
    P <t_ns>                          PPS del GPS
    G <t_ns_pps> <utc_s> <A|V> <sat>  ora UTC del PPS appena annotato (A = posizione valida)
    S <t_ns> <n1> <n2> <n3> <nA> <persi>   stato, ogni secondo
    I / M / W / X                     sensori I2C (sensori.py)
Comandi dalla seriale:  "?" ripete l'intestazione,  "R" riparte da zero.

Installazione: MicroPython per Pico 2, poi copiare main.py, gps.py e sensori.py
(per esempio  mpremote cp main.py gps.py sensori.py :).
"""
import rp2, machine, time, sys, select
from machine import Pin, mem32, I2C, UART
import gps, sensori

VERSIONE = "2.0"
PIN_INGRESSI = (2, 3, 4, 5)
NOMI = ("1", "2", "3", "A")
PIN_PPS = 6
BAUD_GPS = 9600                   # u-blox M8 di fabbrica; NEO-F10T: 38400
PERIODO_SENSORI_MS = 5000
M = 0xFFFFFFFF
PIO0, PIO1 = 0x50200000, 0x50300000   # RP2040 e RP2350 (pico-sdk, addressmap.h)
CTRL, FDEBUG = 0x000, 0x008
RP2350 = "RP2350" in sys.implementation._machine


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
        # PPS: solo su RP2350, che avvia nello stesso ciclo anche le state machine del PIO1
        self.pps = RP2350
        if self.pps:
            self.pin.append(Pin(PIN_PPS, Pin.IN, Pin.PULL_DOWN))
        self.sm = []
        self.riparti()

    def riparti(self):
        for sm in self.sm:
            sm.active(0)
        self.sm = []
        for i, pin in enumerate(self.pin):
            # (ri)creata da capo: parte dall'istruzione 0, con la coda vuota.
            # Ingressi: state machine 0-3 (PIO0). PPS: 4 (la prima del PIO1).
            sm = rp2.StateMachine(i, fronti, jmp_pin=pin)    # divisore 1: clock di sistema
            while sm.rx_fifo():
                sm.get()
            sm.restart()
            sm.exec("mov(x, invert(null))")                  # x = 0xFFFFFFFF
            self.sm.append(sm)
        n = len(self.sm)
        self.primo = [True] * n                              # il primo valore e' il marcatore di partenza
        self.k = [0] * n
        self.n = [0] * n
        self.persi = 0
        mem32[PIO0 + FDEBUG] = 0xF                           # azzera i segnali di coda piena
        mem32[PIO1 + FDEBUG] = 0xF
        self.t_us, self.ultimo = 0, time.ticks_us()
        avvio = 0xFFF                                        # PIO0: abilita, riavvia, riallinea i divisori
        if self.pps:
            # stessa scrittura: abilita e riallinea anche la state machine 0 del PIO1
            # (NEXT_PIO_MASK bit 20, NEXTPREV_SM_ENABLE bit 24, NEXTPREV_CLKDIV_RESTART bit 26)
            avvio |= (1 << 20) | (1 << 24) | (1 << 26)
        mem32[PIO0 + CTRL] = avvio

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
                t += ((grezzo - t + (1 << 31)) >> 32) << 32  # il contatore fa un giro ogni ~57 s (Pico 2)
                self.n[i] += 1
                uscita(i, t * 2_000_000_000 // self.freq)
        for base in (PIO0, PIO1):
            st = mem32[base + FDEBUG] & 0xF
            if st:
                self.persi += 1
                mem32[base + FDEBUG] = st


def main():
    led = Pin("LED", Pin.OUT)
    acq = Acquisizione()
    scrivi = sys.stdout.write
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)
    led_off = [0]
    pps = [None]                                             # istante dell'ultimo PPS non ancora battezzato

    uart = UART(0, BAUD_GPS, tx=Pin(0), rx=Pin(1))
    nmea = gps.NMEA()
    i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=100_000)
    hub = sensori.Hub(i2c, reset_pin=Pin(7, Pin.OUT, value=1))
    riga = lambda s: scrivi(s + "\n")
    nuovo_ciclo = lambda: sensori.ciclo(hub, i2c, riga, acq.orologio_ns, time.ticks_ms, PERIODO_SENSORI_MS)
    sens = nuovo_ciclo()
    sens_prossimo = time.ticks_ms()

    def intestazione():
        scrivi("H pico_acquisizione %s %d %s\n" % (VERSIONE, acq.freq, "pps" if acq.pps else "no_pps"))

    def evento(i, t_ns):
        if i == 4:                                           # PPS
            scrivi("P %d\n" % t_ns)
            pps[0] = t_ns
            return
        scrivi("E %s %d\n" % (NOMI[i], t_ns))
        if i == 3:                                           # AND: un muone, lampeggio del LED
            led.on()
            led_off[0] = time.ticks_add(time.ticks_ms(), 40)

    intestazione()
    prossimo = time.ticks_add(time.ticks_ms(), 1000)
    while True:
        acq.svuota(evento)
        ora = time.ticks_ms()
        if uart.any():
            for utc in nmea.dati(uart.read()):
                # l'RMC arriva entro ~0,5 s dal PPS del secondo che descrive
                if pps[0] is not None and acq.orologio_ns() - pps[0] < 900_000_000:
                    scrivi("G %d %d %s %d\n" % (pps[0], utc, "A" if nmea.valido else "V", nmea.satelliti))
                pps[0] = None
        if time.ticks_diff(ora, sens_prossimo) >= 0:
            try:
                sens_prossimo = time.ticks_add(ora, next(sens))
            except Exception as e:                           # bus bloccato o altro: si riparte col ciclo
                riga("X - %s" % e)
                hub.sblocca()
                sens = nuovo_ciclo()
                sens_prossimo = time.ticks_add(ora, 1000)
        if led_off[0] and time.ticks_diff(ora, led_off[0]) >= 0:
            led.off()
            led_off[0] = 0
        if time.ticks_diff(ora, prossimo) >= 0:
            prossimo = time.ticks_add(prossimo, 1000)
            scrivi("S %d %d %d %d %d %d\n" % ((acq.orologio_ns(),) + tuple(acq.n[:4]) + (acq.persi,)))
        if poll.poll(0):
            c = sys.stdin.read(1)
            if c == "?":
                intestazione()
            elif c == "R":
                acq.riparti()
                intestazione()


if __name__ == "__main__":
    main()
