# Acquisizione con Raspberry Pi Pico + Zero 2 W

Il **Pico** cattura gli impulsi della scheda a 3 canali (barre 1–3 e AND) e ne annota
l'istante; lo **Zero 2 W** riceve tutto via USB, salva, legge i sensori I²C (monitor
della scheda e, se c'è, il modulo meteo) e fa girare la dashboard.

Perché due schede: le uscite verso il Raspberry durano 150–220 ns (`sim_3canali`) e non
esiste una misura pubblicata che garantisca che il GPIO del Pi sotto Linux le prenda
tutte; i progetti simili (CosmicWatch v3X con un Pico, QuarkNet e HiSPARC con schede di
acquisizione dedicate, MuonPi con il marcatempo del GPS) tolgono la cattura degli
impulsi a Linux. Fonti nel rapporto `reports/Architettura rivelatori per le scuole.md`.

## Cosa fa il firmware (`main.py`, MicroPython)

- 4 state machine PIO, una per ingresso, partono nello stesso ciclo e guardano il pin
  ogni 2 cicli: **risoluzione 16 ns** (Pico, 125 MHz) o 13,3 ns (Pico 2, 150 MHz),
  stessa scala per i quattro ingressi.
- Nessun impulso perso: coda di 8 posti per ingresso svuotata di continuo dalla CPU; se
  una coda si riempisse, il conteggio "persi" lo dice.
- Una riga per impulso sulla seriale USB: `E <canale> <t_ns>`; una riga di stato al
  secondo: `S <t_ns> <n1> <n2> <n3> <nA> <persi>`. Il LED del Pico lampeggia a ogni AND.

Verifiche fatte senza hardware:
- `python verifica_pio.py`: simulazione ciclo per ciclo del programma PIO (impulsi da
  24 ns a 220 ns, ravvicinati, contatore che passa per zero): errore 0–1 cicli.
- `python verifica_firmware.py`: la parte che gira sulla CPU, con moduli finti, per 10
  minuti di misura (8,7 giri del contatore): istanti esatti, nessun impulso perso.

## Collegamenti (prototipo su millefori)

Per ognuno dei 4 ingressi:

```
LEMO (centrale) ──┬── 74LVC1G17 pin 2 (A)        pin 4 (Y) ── 100 Ω ── GPx del Pico
                 100 kΩ          pin 5 (VCC) = 3V3(OUT) del Pico (pin 36), 100 nF verso massa
                  │              pin 3 (GND) = GND del Pico
LEMO (calza) ─────┴── GND
```

| Ingresso | Uscita della scheda | Pico |
|---|---|---|
| barra 1 | LEMO J104 | GP2 (pin 4) |
| barra 2 | LEMO J204 | GP3 (pin 5) |
| barra 3 | LEMO J304 | GP4 (pin 6) |
| AND | LEMO J5 | GP5 (pin 7) |

- Il **74LVC1G17** (lo stesso buffer delle uscite della scheda) ha gli ingressi che reggono
  5 V: protegge il Pico se un LEMO viene collegato a un'uscita a 5 V. I 100 kΩ tengono
  basso l'ingresso a cavo staccato; i 100 Ω limitano la corrente verso il Pico.
- **Nessuna terminazione a 50 Ω**: le uscite della scheda hanno già 33 Ω in serie
  (adattamento lato sorgente) e vogliono un ingresso ad alta impedenza. Cavi fino a 1–2 m,
  della stessa lunghezza per i tre canali (1 m in più = 5 ns).
- **USB**: dal micro-USB del Pico alla porta **USB dati** dello Zero 2 W (non "PWR IN"),
  con un adattatore OTG. Lo Zero alimenta il Pico (~25 mA).
- L'**I²C** (J6 della scheda) resta collegato allo Zero, come in `PROTOTIPI.md`.

## Installazione

1. Sul Pico: tenere premuto BOOTSEL, collegare l'USB, copiare il file `.uf2` di
   MicroPython (micropython.org, "Raspberry Pi Pico" o "Pico 2").
2. Copiare il firmware: `mpremote cp main.py :main.py` (oppure con Thonny). Al riavvio
   parte da solo.
3. Sullo Zero: `pip install pyserial`, poi `python3 software/acquisizione_pico.py --csv eventi.csv`.
   Ogni 10 s stampa i ritmi e il confronto "triple calcolate dai tempi / AND hardware".
   Senza hardware: `python3 software/acquisizione_pico.py --simula 120`.

## Prova di confronto Pico / GPIO dello Zero (prima prova sui prototipi)

Le uscite dei buffer vanno anche a 4 GPIO dello Zero (per esempio 17, 27, 22, 23, con
100 Ω in serie). Si contano gli stessi impulsi in tre modi: Pico, GPIO dello Zero
(libgpiod), oscilloscopio o contatore. Se lo Zero da solo li conta tutti anche sotto
carico, per le versioni successive si può scegliere; se ne perde, il Pico resta.

## Dopo (fase 2)

GPS con PPS su un quinto ingresso (ora assoluta al µs, coincidenze tra scuole), modulo
meteo e monitor letti dal Pico invece che dallo Zero, tutto in una scatolina con ingressi
LEMO, prese Qwiic e antenna.
