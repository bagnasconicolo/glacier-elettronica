# Rivelatore di particelle alpha con BPW21 — versione minima

Un solo integrato (**MCP6022**, doppio op-amp rail-to-rail), 5 V presi
dall'Arduino, una decina di componenti passivi. Ogni alpha che colpisce il
fotodiodo produce un impulso 0 → 5 V che lo sketch
[`firmware/conta_muoni/conta_muoni.ino`](../../firmware/conta_muoni/conta_muoni.ino)
conta **senza modifiche** (interrupt su D2).

## ⚠️ Prima di tutto: la finestra del BPW21 va tolta

Il BPW21 è in un contenitore metallico TO-5 con **finestra di vetro** (che fa
anche da filtro). Un alpha da 5 MeV si ferma in ~25 µm di vetro e in ~4 cm d'aria:
**con la finestra il circuito non vedrà mai un alpha.**

- Rimuovi il cappuccio limando con cura il bordo del TO-5 (o con un tagliatubi
  piccolo) e sollevalo: il chip resta scoperto. Non toccare il chip né i fili
  di bonding.
- Il chip scoperto è **sensibilissimo alla luce**: tutto il rivelatore va in una
  scatola metallica chiusa e buia (una scatoletta di latta va benissimo, e fa
  anche da schermo contro i disturbi). Collega la scatola a GND.
- Sorgente tipica: l'Am-241 di un vecchio rivelatore di fumo (~37 kBq), messa
  a **pochi mm** dal chip. Non aprire né grattare la sorgente.

## Schema

```
 +5V ── R1 100k ──┬── VTH ── R2 2,2k ──┬── VREF ── R3 100k ── GND
                  │                    │
                C1 1µF               C2 1µF
                  │                    │
                 GND                  GND

                           Cf 1 pF
                       ┌─────||─────┐
                       ├── Rf 22M ──┤
          BPW21        │            │
   GND ────▶|──────────┴──┤− U1A    │           C3 1µF         U1B
          A     K         │   ──────┴── CSA ─────||──────┬──────┤+
                  VREF ───┤+                             │      │   ──────┬──▶ Arduino D2
                                                         │  VTH─┤−        │
                                               VREF ── R4 10k             │
                                                         └──── R5 10M ────┘
```

In parole (piedinatura MCP6022 DIP-8: 1 = OUTA, 2 = −INA, 3 = +INA, 4 = GND,
5 = +INB, 6 = −INB, 7 = OUTB, 8 = +5 V):

| Collegamento | Note |
|---|---|
| +5 V → R1 100k → **VTH** → R2 2,2k → **VREF** → R3 100k → GND | partitore unico: riferimento + soglia |
| C1 1 µF da VTH a GND, C2 1 µF da VREF a GND | filtro dei riferimenti |
| VREF → pin 3 (+INA) | |
| BPW21: **catodo → pin 2** (−INA), **anodo → GND** | il fotodiodo lavora a ~2,5 V inversi (max 10 V) |
| Cf 1 pF e Rf 22 MΩ in parallelo tra pin 2 e pin 1 | preamplificatore di carica, τ = 22 µs |
| pin 1 → C3 1 µF → pin 5 (+INB) | accoppiamento AC: la corrente di buio non sposta la soglia |
| R4 10k da pin 5 a VREF | |
| R5 10 MΩ da pin 7 a pin 5 | ~5 mV di isteresi: un impulso = un solo conteggio |
| VTH → pin 6 (−INB) | soglia del comparatore |
| pin 7 (OUTB) → Arduino **D2** | impulso 0/5 V, già pronto per l'interrupt |
| 100 nF tra pin 8 e pin 4, vicino all'integrato | disaccoppiamento |

Facoltativo: un LED con 1 kΩ da pin 7 a GND lampeggia (debolmente, gli impulsi
durano ~50 µs) a ogni alpha; per un "click" udibile basta un buzzer piezo
passivo sullo stesso pin.

## Come funziona

1. **Carica.** Un alpha di ~4 MeV che si ferma nel silicio crea
   4 MeV / 3,6 eV ≈ 1,1 milioni di coppie elettrone-lacuna → **Q ≈ 180 fC**.
2. **Preamplificatore di carica (U1A).** La carica finisce su Cf = 1 pF: l'uscita
   sale di Q/Cf ≈ 170 mV e torna giù con τ = Rf·Cf = 22 µs. La grande capacità
   del BPW21 (~270 pF a 2,5 V) non conta: con un CSA l'ampiezza dipende solo da Cf.
3. **Comparatore (U1B).** Lo scalino passa attraverso C3 (così la corrente di
   buio, che sposta la linea di base di Idark·Rf, viene ignorata) e viene
   confrontato con la soglia di ~57 mV, equivalente a **~1,4 MeV**.
4. **Selettività.** Un beta o un gamma lascia nel sottile strato svuotato del
   BPW21 al massimo qualche decina di keV (≈ 1–3 mV all'uscita del CSA), molto
   sotto soglia: **il circuito conta solo gli alpha** (e la luce, se la scatola
   non è buia).

## Simulazione

`alpha_bpw21.cir` è la netlist ngspice del circuito qui sopra (op-amp
comportamentale con GBW 10 MHz e uscita rail-to-rail):

```bash
ngspice -b alpha_bpw21.cir
```

| Evento | Uscita CSA (picco sopra la base) | Uscita D2 |
|---|---|---|
| alpha 4 MeV (178 fC) | +167 mV | impulso 0→5 V di 73 µs |
| alpha 2 MeV (89 fC) | ~+80 mV | impulso 0→5 V di 36 µs |
| gamma 60 keV (2,7 fC) | < 3 mV | nessun impulso |
| corrente di buio 2 nA → 30 nA | la base si sposta di +0,6 V | nessun effetto sulla soglia |

## Distinta base

| Rif. | Valore | Note |
|---|---|---|
| D1 | BPW21 | finestra rimossa (vedi sopra) |
| U1 | MCP6022 (DIP-8) | va bene anche un altro doppio op-amp CMOS rail-to-rail a 5 V con GBW ≥ 5 MHz (es. MCP6292, TLV2372) |
| Rf | 22 MΩ | |
| Cf | 1 pF C0G | su breadboard la capacità parassita aggiunge ~0,5 pF: gli impulsi calano un po' ma restano ben sopra soglia |
| R1, R3 | 100 kΩ | |
| R2 | 2,2 kΩ | soglia: 1,5 kΩ → più sensibile, 3,3 kΩ → meno |
| R4 | 10 kΩ | |
| R5 | 10 MΩ | |
| C1, C2, C3 | 1 µF ceramico | |
| — | 100 nF ceramico | disaccoppiamento |

## Consigli pratici

- Collegamenti tra fotodiodo e pin 2 **cortissimi**: quel nodo è ad alta
  impedenza e capta tutto (rete 50 Hz, telefono, alimentatore USB rumoroso).
- Se conti impulsi anche **senza sorgente**: c'è luce che entra o il 50 Hz che
  passa. Chiudi bene la scatola, accorcia i fili, prova ad alimentare l'Arduino
  da batteria/power bank.
- Il rate dipende moltissimo dalla distanza sorgente–chip (l'aria frena gli
  alpha): con un Am-241 da rivelatore di fumo a 2–3 mm aspettati da qualche
  conteggio a qualche decina al secondo; a 3–4 cm cala a zero. È un bell'esperimento
  per misurare il **range degli alpha in aria**.
