# Moduli del sistema: scatolina di acquisizione e modulo meteo

Due schede nuove si affiancano al rivelatore a 3 canali (`hardware/variante_3ch`). Sono fatte con
KiCad 7 e verificate con KiCad stesso: lo schema corrisponde al PCB, il DRC non dà errori e la
connettività è controllata sul rame reale.

| Cartella | Scheda | Dimensioni |
|---|---|---|
| `acquisizione/` | Pico 2 su zoccolo, 4 ingressi LEMO con buffer di Schmitt, uscita PPS LEMO, GPS, hub I2C TCA9548A a 8 porte (2 KK verso i rivelatori, 6 Qwiic) | 105 × 70 mm |
| `meteo/` | SHT45 (temperatura e umidità) + LPS22HH (pressione), due prese Qwiic, sensore su isola con fessure | 36 × 22 mm |

Ogni cartella contiene:

| File | Contenuto |
|---|---|
| `definizione.py` | componenti, reti, piazzamento e codici (unica sorgente) |
| `*.kicad_sch`, `*.kicad_pcb`, `*.kicad_pro` | progetto KiCad |
| `gerber/`, `*_gerber.zip` | file di produzione |
| `jlcpcb/` | BOM e CPL per il montaggio |
| `anteprima_*.png` | anteprima del PCB |
| `*.step` | modello 3D della scheda montata |

## Schemi leggibili

Gli schemi A4 sono in `docs/schema_A4_moduli.pdf`, generati da `schemi_a4.py`. Ogni valore
e ogni pin disegnato viene controllato contro `definizione.py`.

Il PDF completo del sistema è `docs/SISTEMA_schemi_PCB_preventivo.pdf`, generato da
`pdf_completo.py`.

## Rigenerare

```
python3 costruisci_modulo.py meteo           # schema, PCB, routing (Freerouting 1.9), Gerber, BOM/CPL, verifica
python3 costruisci_modulo.py acquisizione
python3 schemi_a4.py                         # schemi A4
python3 pdf_completo.py                      # PDF unico
python3 modello3d.py meteo acquisizione      # STEP
```

## Note di progetto

- **Ingressi della scatolina.** Ogni ingresso ha il diodo ESD PESD5V0U1BA, 100k a massa,
  100 Ω in serie e un 74LVC1G17 a 3,3 V. L'ingresso del 74LVC1G17 tollera 5,5 V, quindi va
  bene anche con il vecchio TTL a 5 V. I buffer vanno a GP2–GP5 (PIO).
- **GPS.** UART0 su GP0/GP1, PPS su GP6, e lo stesso PPS esce bufferizzato su LEMO (J5).
- **Hub I2C.** Il TCA9548A (0x70) è sul bus I2C0 (GP8/GP9) e il suo reset su GP7. Ogni porta
  ha i suoi pull-up da 4,7k. Le porte Qwiic sono alimentate da un AP2112K-3.3 (600 mA)
  preso dalla USB.
- **Modulo meteo.** L'LPS22HH sostituisce il BMP390, per la stessa classe di rumore e la
  disponibilità da JLCPCB. SHT41 o SHT40 si possono montare al posto dell'SHT45. JP1 chiude
  i pull-up (aperto di fabbrica), JP2 sceglie l'indirizzo 0x5D o 0x5C.
- **LEMO.** Prese a gomito EPL.00.250.NTN sul bordo: il corpo sporge dalla scheda e attraversa
  la parete della scatola.
- **Preventivo e ordini.** Vedi `hardware/PREVENTIVO.md` e `BOM_mouser_moduli_2sistemi.csv`.
