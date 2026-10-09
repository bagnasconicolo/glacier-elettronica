# Simulazione della catena di segnale

> **Novità: simulazione della scheda COMPLETA** — alimentazioni, boost, bias,
> front-end, comparatore, uscite, 555 — in `ltspice/` (schema LTspice + netlist,
> verificata con ngspice). Vedi la sezione in fondo e `ltspice/LEGGIMI.md`.
> Le sezioni "Buffer d'uscita" e "Treno completo fino ad Arduino" descrivono la
> variante precedente (buffer a 2 transistor a 5 V), sostituita dal 74LVC1G17 a 3,3 V
> per la lettura con Raspberry Pi.


Transitorio non lineare (MNA + backward Euler, BJT Ebers-Moll) dell'intera catena:
impulso SiPM → C7 → Q1 BFR93A → Q2 MMBTH81 → C11 → MAX961 (comportamentale con
isteresi ±2 mV e latch via C9/R16). Impulso SiPM modellato come corrente
esponenziale, τ = 45 ns, 0,5 pC per fotoelettrone (guadagno ~3·10⁶).

## Punto di lavoro DC (Vcc = 3,3 V)

| Nodo | V |
|---|---|
| Base Q1 | 0,60 V |
| Collettore Q1 / base Q2 | 2,48 V |
| Emettitore Q2 | 3,07 V |
| Collettore Q2 (nodo D) | 0,41 V |
| Ic(Q1) / Ic(Q2) | 0,82 mA / 0,41 mA |

Coerente con la topologia: Q1 polarizzato dalla retroazione R11/R9, Q2 in
conduzione debole con degenerazione R13.

## Risposta all'impulso (grafici: `sim_catena.png`, `sim_ampiezze.png`)

- Guadagno di carica: **~35 mV per fotoelettrone** al comparatore (regione lineare).
- Ampiezze al nodo del comparatore: 2 p.e. → 71 mV, 10 p.e. → 386 mV,
  20 p.e. → 811 mV; **clipping a ~1,19 V** oltre ~40 p.e. (saturazione di Q1/Q2).
- Uscita del comparatore: impulsi puliti, larghezza 90–220 ns (cresce con
  l'ampiezza, time-over-threshold), compatibili con il driver MCP1402.
- La rete C9/R16 (100 pF/1 kΩ) produce sul latch-enable un impulso di ~3,3 V con
  τ = 100 ns sul fronte di salita di Q: blocca ri-trigger sul ringing per ~70 ns.
- Range soglia (V2): ~2 mV … 1,29 V ⇒ discriminazione regolabile da **<1 p.e. fino
  a ~40 p.e.**; un muone in scintillatore (centinaia di p.e.) è sempre sopra soglia.
- Monostabile 555: T = 1,1·R20·C21 = 1,1·100k·100n = **11 ms** di lampeggio LED
  per evento (calcolo analitico, non simulato nel transitorio veloce).

## Limiti del modello

- Parametri BJT tipici (IS=50 fA, βF=90/70): il guadagno reale può variare ±30%.
- MAX961 ideale (4,5 ns di ritardo e limiti di slew non modellati).
- Cavo Fileca non modellato (aggiunge ~100 pF/m sul nodo di ingresso: riduce
  leggermente ampiezza e velocità del fronte).
- Per una verifica più accurata: `riv_cosmici_frontend.cir` con ngspice/LTspice,
  sostituendo i modelli BJT con quelli ufficiali NXP/onsemi.

## Come rilanciarla

- Qui: `python3 sim_catena.py` (richiede numpy/matplotlib).
- ngspice: `ngspice riv_cosmici_frontend.cir`
- LTspice: apri il .cir come netlist e premi Run. Parametri in testa al file
  (NPE = fotoelettroni, VTH = soglia).

## Sequenza di muoni (`sim_muoni.py`)

Treno di eventi sul solver circuitale (finestra 200 µs, rate muoni accelerato a
60 kHz per visualizzazione; rate reale ~1,7 Hz su paletta 10×10 cm):

- **Muoni**: arrivi poissoniani, carica ~Landau (Moyal, mediana ~250 p.e., min 80).
- **Dark count SiPM**: 200 kHz a 1–2 p.e.
- **Soglia 100 mV (~3 p.e.)**: tutti i 7 muoni della finestra hanno generato un
  trigger TTL (larghezza 160–224 ns), tutti i ~55 dark count sono stati rigettati.
  Anche due muoni distanti ~1,5 µs sono risolti separatamente.
- Scala reale (`sim_muoni_reale.png`): a 1,7 Hz il LED (11 ms/evento) ha un
  duty di ~2%; probabilità che un secondo muone cada nel tempo morto del
  monostabile: ~1,9% (il trigger TTL su J2 non ne è influenzato: il tempo morto
  della catena veloce è solo ~0,5 µs, dominato dal ritorno sotto soglia).

Grafici: `sim_muoni_treno.png`, `sim_muoni_reale.png`.

## Buffer d'uscita: CMP_Q vs TTL come ingresso (`sim_buffer.py`)

Modello transitorio del buffer a 2 transistor (2N2222) con **carica immagazzinata**
(transit time TF/TR + Cje/Cjc): è quella carica a produrre lo *storage time* che
allunga l'impulso.

**Com'è fatto CMP_Q**: è un'onda quadra 0→3,3 V la cui **larghezza = time-over-threshold**,
cioè quanto il segnale amplificato resta sopra soglia. Non è fissa: muone tipico
(180 p.e.) → **188 ns**, muone grande (500 p.e.) → 231 ns. Il TTL (dopo MCP1402) è
la stessa onda scalata a 0→5 V con ~25 ns di ritardo di propagazione; la **larghezza
si conserva** (il MCP1402 non allunga l'impulso).

**Cosa cambia mettendo il buffer dopo il TTL:**
- Ingresso identico in larghezza (188 ns), ma **5 V invece di 3,3 V** → Q3 riceve più
  corrente di base (4,3 mA vs 2,6 mA) → **satura più a fondo** → immagazzina più carica
  → **storage time maggiore in spegnimento**.
- Uscita da CMP_Q: **174 ns**. Uscita da TTL: **192 ns** → **+18 ns più larga**.
- Il fronte di discesa dell'uscita arriva **+37 ns più tardi** con il TTL (~25 ns di
  ritardo del MCP1402 + ~12 ns di storage time in più).
- In più restano le ragioni già dette: dopo il TTL il buffer è ridondante (il MCP1402
  è già un driver migliore) e le due uscite non sono più indipendenti.

Conclusione: da CMP_Q l'impulso è **più stretto e più fedele** all'originale; dopo il
TTL è **leggermente più largo e più ritardato**. Per contare muoni su Arduino la
differenza (±20 ns) è irrilevante; conta di più l'indipendenza dei rami → **CMP_Q**.

Grafico: `sim_buffer.png`.

## Treno completo end-to-end fino ad Arduino (`sim_treno_completo.py`)

Catena intera muone → SiPM → ampli → comparatore → CMP_Q → **buffer 5 V** → pin
Arduino, con il buffer preso da **CMP_Q** (uscita comparatore) e alimentato a **5 V**
(Arduino Uno/Nano). Il front-end è il solver circuitale non lineare; il buffer è
comportamentale ma calibrato sul modello dettagliato (`sim_buffer.py`): uscita 0→5 V,
salita ~storage-limited (τ≈26 ns), discesa netta (τ≈8 ns).

Finestra 200 µs, rate muoni accelerato a 60 kHz (reale ~1,7 Hz), dark count 200 kHz:

- **7 muoni → 7 impulsi CMP_Q → 7 conteggi Arduino.** I 46 dark count (1–2 p.e.)
  restano tutti sotto soglia: **0 falsi conteggi.**
- Ogni evento: la corrente del SiPM diventa un picco di ~1,2 V al comparatore (i muoni
  grossi saturano), CMP_Q è un'onda quadra 3,3 V larga il time-over-threshold, e il
  buffer la rigenera in un impulso **0→5 V** che l'Arduino conta sul fronte di salita
  (`attachInterrupt(RISING)`, ▼ nel grafico).
- Scala reale (`sim_treno_reale.png`): 60 s a 1,7 Hz → **media 1,68 conteggi/s**,
  fluttuazione poissoniana visibile bar-per-bar.

Grafici: `sim_treno_completo.png` (4 corsie), `sim_treno_zoom.png` (un muone in
dettaglio), `sim_treno_reale.png` (conteggi/s a scala reale).

## Verifica dallo schema: netlist estratta dal .kicad_sch (`verify_from_schematic.py`)

Fino a qui le simulazioni usavano una netlist trascritta a mano (indipendente dal
file KiCad). Questi due script chiudono il buco:

- **`netlist_from_kicad.py`**: legge `riv_cosmici.kicad_sch` ed estrae la netlist
  vera *per geometria* — valori dei componenti, posizione/rotazione/mirror dei
  simboli, fili, giunzioni, etichette e simboli di alimentazione uniti in nodi
  elettrici. La geometria dei pin viene dai `lib_symbols` del file stesso.
- **`verify_from_schematic.py`**: costruisce un solver MNA **generico** dalla
  netlist estratta (R, C, BJT, rail fissi) e simula il front-end partendo da lì.

Risultato: il front-end estratto dallo schema riproduce il simulatore di
riferimento **al millivolt** (punto di lavoro DC di B/C(Q1), E/C(Q2) identico;
picco al comparatore 1188 mV in entrambi).

**Prova che gli errori ora si vedono**: iniettando un errore in una copia dello
schema (R12: 1k → 4k7), il solver legge il nuovo valore e il punto di lavoro del
collettore di Q1 si sposta di **441 mV** → l'errore è rilevato. Lo stesso vale per
un errore di cablaggio: cambierebbe i nodi estratti e quindi il risultato.

Limite residuo: la geometria dei *pin* usa la trasformazione lib→foglio (verificata:
tutti i pin agganciano i fili); gli unici pin "flottanti" segnalati sono i NC
intenzionali (BYP dell'LP2985, ingressi inusati dell'LT1636). Il buffer aggiunto
(Q3/Q4) è nella netlist estratta ma non nel solver del front-end (che si ferma al
comparatore); per simularlo end-to-end si usa `sim_treno_completo.py`.

## Scheda completa: LTspice / ngspice (`ltspice/`)

Netlist e schema LTspice generati da `hardware/generator/netdata.py` (stesso modello
dati del KiCad); integrati con macromodelli dai datasheet, transistor e diodi con
modelli SPICE. Transitorio di 30 ms con accensione e 4 eventi a t = 10 ms
(`python ltspice/verifica_ltspice.py`, 21 controlli tutti superati):

| Grandezza | Simulato |
|---|---|
| +3V3 / +3V6 / riferimento 3,6 V | 3,30 / 3,60 / 3,60 V |
| VOUT40 (boost LT3461) | 41,65 V (calcolo: 1,255 V × 33,2) |
| BIAS SiPM (V1_POS = 0,76) | 38,44 V, raggiunto dopo 2,4 ms |
| Punto di lavoro Q1 B / C, Q2 C | 0,59 / 2,47 / 0,42 V (come `sim_catena.py`) |
| Corrente dai 5 V | 38 mA |
| Muone 250 p.e. al comparatore | 1,14 V (saturato) |
| CMP_Q / TTL J2 / GPIO Pi | 3,28 / 4,99 / 3,27 V |
| Larghezza impulso al GPIO, ritardo | 300 ns, 8 ns |
| Dark count 1 p.e. | ~10 mV → nessun impulso |
| Muoni a 1,5 µs | risolti separatamente |
| LED (555) | 10,9 ms |

SiPM simulato: **Broadcom AFBR-S4N22P014M** (VBD 32,5 V, 160 pF, recharge 55 ns,
guadagno 7,3·10⁶ a 12 V OV → ~3,6·10⁶ e ~0,58 pC/p.e. a 5,9 V OV). Ampiezza al
comparatore: 1 p.e. ≈ 10 mV, 3 p.e. ≈ 40 mV, 5 p.e. ≈ 71 mV, 10 p.e. ≈ 156 mV
(l'amplificatore è leggermente espansivo), muoni saturati a ~1,0–1,2 V. Soglia di
default 104 mV ≈ 7 p.e. Impulso minimo in uscita **~84 ns** (latch C9/R16).

Temperatura (−10…+50 °C): BIAS sale di +28 mV/°C grazie a D1, contro ~30 mV/°C di
VBD → sovratensione costante entro 0,1 V (5,85–5,94 V).

Correzione di ricostruzione emersa dal confronto con l'originale: **V2 è un
potenziometro** (cursore → R17), non un reostato. Il campo della soglia non cambia.
