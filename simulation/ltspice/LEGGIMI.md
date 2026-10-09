# Simulazione LTspice della scheda completa

Tutta la scheda — alimentazioni, boost, bias del SiPM, front-end, soglia, comparatore,
driver TTL, monostabile LED, uscita per Raspberry Pi — in un solo schema simulabile.

| File | Cosa contiene |
|---|---|
| `riv_cosmici_completo.asc` | **schema LTspice** (aprilo e premi Run) |
| `riv_*.asy` | simboli usati dallo schema (devono stare nella stessa cartella) |
| `riv_cosmici_completo.cir` | stessa scheda come netlist (LTspice o ngspice) |
| `riv_cosmici_modelli.lib` | modelli: transistor, diodi, SiPM, trimmer e tutti gli integrati |
| `gen_ltspice.py` | genera `.asc`, `.asy` e `.cir` da `hardware/generator/netdata.py` |
| `verifica_ltspice.py` | rilegge l'`.asc`, lo confronta con la `.cir`, simula e controlla |
| `ngspice_run.py` | esegue ngspice e legge le forme d'onda (usato dalla verifica) |

**Lo schema è generato dallo stesso modello dati del KiCad**: riferimenti (R1, U3, …) e
nomi delle reti (CMP_IN, BIAS, …) sono identici. Nell'`.asc` i componenti sono raggruppati
per blocco funzionale; ogni pin ha un'etichetta col nome della rete, e due pin con la
stessa etichetta sono collegati (come le label di KiCad). GND = `0`, +5V = `V5`,
+3V3 = `V3V3`, +3V6 = `V3V6`.

## Uso con LTspice

1. Copia tutta la cartella `simulation/ltspice/` (servono `.asc`, tutti i `.asy` e
   `riv_cosmici_modelli.lib`).
2. Apri `riv_cosmici_completo.asc` e premi **Run**. Il transitorio dura 30 ms; con i
   modelli comportamentali impiega pochi secondi.
3. Sonde utili: `V(BIAS)`, `V(VOUT40)`, `V(CMP_IN)` con `V(TH)`, `V(CMP_Q)`, `V(LE)`,
   `V(TTL_OUT)`, `V(RPI_GPIO)`, `V(LED_A)`.
4. I risultati delle misure `.meas` sono in **View → SPICE Error Log**.

Parametri principali (direttive `.param` in fondo allo schema):

| Parametro | Significato | Default |
|---|---|---|
| `V1_POS` | posizione del trimmer V1 (bias SiPM) | 0,76 → 38,4 V |
| `V2_POS` | posizione del trimmer V2 (soglia) | 0,92 → ~104 mV (~7 p.e.) |
| `VBD`, `G12`, `VOV` | SiPM AFBR-S4N22P014M: breakdown, guadagno a 12 V OV, sovratensione | 32,5 V, 7,3·10⁶, 5,94 V |
| `QPE` | carica per fotoelettrone = q·G12·VOV/12 | ~0,58 pC |
| `CSIPM`, `TAUSIPM` | capacità terminale e recharge del SiPM | 160 pF, 55 ns |
| `T_EVn`, `NPE_EVn` | istante e fotoelettroni dei 4 eventi | muone 250, dark 1, muone 40, muone 150 p.e. |

## Cosa si vede

![simulazione completa](../figures/sim_ltspice_completo.png)

- **Accensione**: +5V in 100 µs; +3V3 e +3V6 subito dopo; il boost carica VOUT40 a
  41,65 V in ~2,4 ms e l'LT1636 porta BIAS a 38,44 V.
- **Muone 250 p.e.**: ~1,13 V all'ingresso del comparatore (saturato), CMP_Q 3,3 V per
  300 ns, TTL 5 V su J2, 3,27 V sul GPIO del Pi con 8 ns di ritardo.
- **Dark count 1 p.e.**: ~10 mV, sotto soglia → nessun impulso.
- **Muone 40 p.e.** e **muone 150 p.e. a 1,5 µs**: due impulsi distinti.
- **LED**: acceso 10,9 ms dal 555 (T = 1,1·R20·C21).

Il SiPM simulato è il Broadcom **AFBR-S4N22P014M** (2×2 mm, 2464 celle, Farnell
4351470), con i valori del datasheet. Per la temperatura usa `.options temp=…` (o
`.temp` in LTspice): la compensazione di D1 tiene la sovratensione a 5,85–5,94 V da
−10 a +50 °C.

## Verifica automatica (ngspice)

```bash
python gen_ltspice.py        # rigenera dopo una modifica a netdata.py
python verifica_ltspice.py   # 1) .asc == .cir  2) tutti i componenti KiCad presenti
                             # 3) 21 controlli numerici PASS/FAIL  4) grafico
```

## Limiti dei modelli (onestamente)

- **Integrati comportamentali** (macromodelli scritti a partire dai datasheet: soglie,
  ritardi, isteresi, limiti di corrente, rail), non i modelli dei produttori. Gli
  utenti LTspice possono sostituire LT3461 e LT1636 con i modelli Analog Devices inclusi
  in LTspice.
- **LT3461 mediato**: regola correttamente la tensione e preleva la potenza dai 5 V
  attraverso L1, ma non simula la commutazione a 1,3 MHz (ripple). Serve per i livelli
  e per la sequenza di accensione, non per il rumore del boost.
- **Stabilità dei LDO** non modellata (vedi `hardware/PRIMA_DI_ORDINARE.md` sui
  condensatori d'uscita).
- I regolatori comportamentali non hanno deriva termica: nelle simulazioni in
  temperatura varia solo ciò che dipende da diodi e transistor (D1, Q1, Q2…).
- Transistor del front-end con parametri tipici (±30% sul guadagno reale); il cavo
  Fileca non è modellato.
