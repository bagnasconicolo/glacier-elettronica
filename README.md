# glacier-elettronica — Rivelatore di raggi cosmici

Front-end di lettura per un **rivelatore di muoni cosmici** basato su SiPM +
scintillatore: amplificatore veloce, discriminatore a soglia regolabile,
generazione del bias del SiPM, uscita TTL e **buffer d'uscita verso Arduino**.

Ricostruzione completa in KiCad — dal solo PDF scansionato dello schema originale
INFN sez. Torino ("Riv. Cosmici 2024 — Amplif, alim, soglie", S. Gallian) —
accompagnata da simulazioni circuitali non lineari, un verificatore che gira
**direttamente dallo schema**, un sito didattico interattivo e il firmware Arduino
per il conteggio.

![Licenza](https://img.shields.io/badge/licence-CERN--OHL--W--2.0-blue)
![KiCad](https://img.shields.io/badge/KiCad-6%2F7%2F8%2F9-green)

## Come funziona il circuito

Un muone attraversa lo scintillatore e produce un lampo di luce; il **SiPM**
(AFBR-S4N22P014M, polarizzato a ~38,4 V generati a bordo) lo converte in un
impulso di corrente. Due transistor — **BFR93A** (Q1) e **MMBTH81** (Q2) —
amplificano di ~28×. Il comparatore **MAX961** confronta con la soglia impostata
dal trimmer V2 e produce l'impulso digitale **CMP_Q**; una rete C9/R16 (latch)
evita i doppi conteggi. Da qui il segnale va al driver **MCP1402** (uscita TTL su
J2) e al **buffer** discreto (2× MMBT2222A) che lo rigenera a 0–5 V verso il
connettore LEMO/J4, pronto per un Arduino. Un timer **555** accende un LED per
11 ms a ogni evento.

Rate reale su una paletta 10×10 cm a livello del mare: **~1,7 muoni/s**.

| Schema | PCB |
|---|---|
| ![schema](hardware/previews/anteprima_schema.png) | ![pcb](hardware/previews/anteprima_pcb.png) |

## Struttura del repository

```
hardware/          progetto KiCad (schema, PCB, librerie, Gerber, BOM)
  riv_cosmici.kicad_pro/.kicad_sch/.kicad_pcb
  riv.kicad_sym, rivlib.pretty/        librerie simboli e footprint del progetto
  gerber/                              Gerber RS-274X + Excellon (pronti per il fab)
  bom/                                 distinta base (.xlsx e .csv) con codici Farnell/RS
  previews/                            anteprime PNG
  generator/                           script Python che GENERANO lo hardware (sorgente)
simulation/        modelli circuitali non lineari + verifica dallo schema
  sim_catena.py        catena di segnale (SiPM -> ampli -> comparatore)
  sim_muoni.py         treno di muoni (Poisson + Landau) + dark count
  sim_buffer.py        buffer d'uscita: CMP_Q vs TTL, storage time
  sim_treno_completo.py catena END-TO-END fino al pin Arduino
  netlist_from_kicad.py   estrae la netlist dal .kicad_sch
  verify_from_schematic.py simula DALLA netlist estratta (front-end + buffer)
  make_recap.py        genera il PDF di recap
  riv_cosmici_frontend.cir  netlist SPICE per LTspice/ngspice
  figures/             grafici generati
web/               sito didattico interattivo (single-file, offline)
firmware/          sketch Arduino per il conteggio dei muoni
docs/              RECAP_progetto.pdf  +  schema_originale_INFN.pdf (scansione di partenza)
```

## Hardware (KiCad)

Apri `hardware/riv_cosmici.kicad_pro` con **KiCad 6 o successivo**. Le librerie di
progetto (`riv.kicad_sym`, `rivlib.pretty`) sono già referenziate da `sym-lib-table`
e `fp-lib-table` con percorso `${KIPRJMOD}`. I Gerber in `hardware/gerber/` sono
pronti per la produzione (2 layer, 80×55 mm; DRC geometrico e connettività a zero
errori). La BOM in `hardware/bom/` riporta i codici d'ordine Farnell/RS trascritti
dal progetto originale.

### ⚠ Da verificare prima di produrre

- **MCP1402 (U4)**: piedinatura come da disegno INFN — confrontare col datasheet
  Microchip DS20002052 prima dell'ordine.
- **L1 (47 µH, RS 693-4344)**: footprint generico 5×5/6×6 mm — verificare l'ingombro
  reale.
- **J4 (LEMO)**: footprint provvisorio (header 2,54); sostituire con quello LEMO
  (es. EPL.00.250.NTN) prima del layout. Il buffer non è ancora nel PCB/Gerber.
- Rifare il fill delle zone e lanciare ERC/DRC ufficiali in KiCad.

## Simulazioni

Tutto in Python puro (nessun SPICE richiesto): un solver MNA + Newton con transistor
Ebers-Moll. Installa le dipendenze e lancia gli script da `simulation/`:

```bash
pip install -r requirements.txt
cd simulation
python sim_catena.py          # risposta della catena, punto di lavoro DC
python sim_muoni.py           # treno di muoni + dark count, reiezione
python sim_buffer.py          # buffer: CMP_Q vs TTL, storage time
python sim_treno_completo.py  # end-to-end fino al pin Arduino
```

Risultati principali (dettaglio in `simulation/RISULTATI_SIMULAZIONE.md`):
guadagno ~35 mV/fotoelettrone, saturazione oltre ~40 p.e.; soglia regolabile da
~2 mV a ~1,3 V; 7 muoni → 7 conteggi con 46 dark count rigettati; rate medio
1,68 conteggi/s a scala reale.

Per LTspice/ngspice: `simulation/riv_cosmici_frontend.cir` (parametri NPE e VTH in
testa al file).

### Verifica DIRETTA dallo schema

Le simulazioni normali usano una netlist trascritta a mano. Per legare la verifica
allo schema vero:

```bash
cd simulation
python verify_from_schematic.py            # front-end letto dal .kicad_sch
python verify_from_schematic.py --buffer   # buffer letto dal .kicad_sch
```

`netlist_from_kicad.py` estrae la netlist per geometria direttamente dal file
`hardware/riv_cosmici.kicad_sch` (valori, fili, etichette, alimentazioni) e
`verify_from_schematic.py` la simula: il punto di lavoro coincide col riferimento al
millivolt, e un errore introdotto nello schema (valore o cablaggio) cambia il
risultato — così la simulazione diventa una vera verifica dello schema.

Il **PDF di recap** con tutti i grafici e i numeri si rigenera con:
`python make_recap.py` → `docs/RECAP_progetto.pdf`.

## Sito didattico

In `web/` ci sono pagine HTML autonome (funzionano offline, senza librerie
esterne), con dentro lo **stesso solver circuitale** portato in JavaScript:

- `schematico_interattivo.html` — lo schema elettrico "vivo": lancia un muone al
  rallentatore, sonde sui nodi, componenti cliccabili, trimmer della soglia
  trascinabile, oscilloscopio.
- `viaggio_del_muone.html` — la catena stadio per stadio, con i grafici ricalcolati
  in tempo reale.
- `rivelatore_cosmici.html` — cruscotto con muoni animati e conteggio.

## Firmware Arduino

`firmware/conta_muoni/conta_muoni.ino` conta i muoni via interrupt hardware e
stampa i conteggi/s sul monitor seriale. Collega **J4 → D2** (con 330 Ω in serie)
e **GND → GND**. Solo per Arduino a **5 V** (Uno/Nano/Mega); per board a 3,3 V
alimentare il buffer a 3,3 V o prendere da CMP_Q per non danneggiare il pin.

## Rigenerare lo hardware

Gli script in `hardware/generator/` sono il "sorgente" da cui sono stati generati
schema, PCB e Gerber (via codice, per costruzione riproducibile). Per rigenerare:
`python gen_sch.py`, `python gen_pcb.py`, `python gerber_out.py`.

## Crediti e licenza

Progetto originale: **INFN sezione di Torino**, "Riv. Cosmici 2024 — Amplif, alim,
soglie" (S. Gallian, 2024). Ricostruzione KiCad, buffer, simulazioni, verifica e
materiale didattico: questo repository.

Rilasciato sotto **CERN Open Hardware Licence Version 2 — Weakly Reciprocal**
(CERN-OHL-W-2.0): vedi `LICENSE` e `LICENSE.CERN-OHL-W-2.0.txt`. Il software di
supporto (script Python/JS, firmware) è distribuito con lo stesso spirito.
