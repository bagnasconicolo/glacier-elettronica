# Variante a 3 canali + coincidenza

Una sola scheda (80 × 165 mm, 2 strati) con **tre front-end completi** del rivelatore
INFN — uno per barra di scintillatore — e la **coincidenza AND** già a bordo.

![PCB](anteprima_pcb_3ch.png)

| File | Contenuto |
|---|---|
| `riv_cosmici_3ch.kicad_pro/.kicad_sch/.kicad_pcb` | progetto KiCad (librerie in `../riv.kicad_sym`, `../rivlib.pretty`) |
| `gerber/`, `riv_cosmici_3ch_gerber.zip` | Gerber + foratura per la produzione |
| `BOM_riv_cosmici_3ch.csv` | distinta completa (anche le parti da montare a mano) |
| `jlcpcb/` | BOM e CPL per il montaggio JLCPCB (stessa procedura di `../jlcpcb/LEGGIMI.md`) |
| `../../docs/schema_riv_cosmici_3canali.pdf` | schema in PDF (A1) |
| `../render3d/out/3ch/` | render 3D della scheda montata |

Tutto è generato da `hardware/generator/` (`netdata3.py`, `gen_sch3.py`, `pcb_data3.py`,
`gen_pcb3.py`, `gen_variante3.py`) a partire dal modello della scheda a 1 canale: il
circuito di ogni canale è **identico** all'originale INFN.

## Com'è fatta

- **Tre strisce da 55 mm**, una per canale, ognuna con lo stesso piazzamento della
  scheda singola: SiPM (J101/J201/J301) a sinistra, uscita LEMO a destra.
- **In comune** (striscia 1): ingresso 5 V (J3), regolatore 3,3 V (U6), boost LT3461
  (U1, alimenta i 3 regolatori di bias, ~8 mA a 41 V), riferimenti 3,6 V (U5 soglie,
  U7 bias).
- **Per canale**: bias del SiPM regolabile (V101/V201/V301), soglia regolabile
  (V102/V202/V302), comparatore MAX961, LED del 555, buffer 74LVC1G17 → LEMO.
- **Riferimenti**: R9 del canale 2 si chiama R209, U3 del canale 3 si chiama U303, ecc.
- **Tolto** il driver TTL a 5 V (MCP1402, J2): le uscite sono LEMO a 3,3 V.

## Uscite LEMO (bordo destro, dall'alto)

| LEMO | Segnale |
|---|---|
| J104 | canale 1 (0–3,3 V, 33 Ω in serie) |
| J204 | canale 2 |
| J5 | **coincidenza AND** dei canali inclusi |
| J304 | canale 3 |

Footprint per **LEMO EPL.00.250.NTN** (presa a gomito da circuito stampato, serie 00):
contatto centrale + 4 piedini di schermo su quadrato 5,08 mm, fori 0,8 mm, frontale
verso l'esterno della scheda. **Prima dell'ordine, appoggia un LEMO vero sul disegno
del PCB in scala 1:1** e verifica fori e distanza dal bordo.

## Coincidenza e jumper JP1–JP3

U10 (74LVC1G11) fa l'AND delle uscite dei tre canali. Ogni ingresso passa da un jumper:

| JP | Chiuso | Aperto |
|---|---|---|
| JP1 | canale 1 nella coincidenza | canale 1 escluso (ingresso tenuto a 1 da R31) |
| JP2 | canale 2 | escluso (R32) |
| JP3 | canale 3 | escluso (R33) |

Tutti chiusi = coincidenza tripla; JP3 aperto = coincidenza doppia 1·2, e così via.
Impulsi dei canali ≥ 84 ns (latch del MAX961): per muoni che attraversano le tre
barre i fronti arrivano entro pochi ns e gli impulsi si sovrappongono.

## Test point per oscilloscopio

| Canale n (TPn01…TPn06, colonna sul bordo destro) | Comuni |
|---|---|
| TPn01 SIG_IN (anodo SiPM) | TP1 VOUT40 (~41 V) |
| TPn02 CMP_IN (ingresso comparatore) | TP2 +5V |
| TPn03 TH (soglia) | TP3 +3V3 |
| TPn04 CMP_Q (uscita comparatore) | TP4 +3V6 |
| TPn05 BIAS (~38 V: attenzione) | TP5 uscita AND |
| TPn06 GND (massa per la pinza della sonda) | TP6 GND |

Fori da 1 mm per anelli Keystone 5000 (rossi) / 5001 (neri, GND) o un filo piegato.

## Montaggio

JLCPCB monta 131 componenti (`jlcpcb/`). **A mano** (non in BOM/CPL):

| Rif. | Parte | Per scheda |
|---|---|---|
| U1 | LT3461 | 1 |
| U103, U203, U303 | MAX961 | 3 |
| U108, U208, U308 | LT1636 | 3 |
| U5, U7 | LP2985AIM5-3.6 | 2 |
| D101, D201, D301 | 1N4148 | 3 |
| J101, J201, J301, J3 | header 1×2 (SiPM, 5 V) | 4 |
| JP1–JP3 | header 1×2 + ponticello | 3 |
| J104, J204, J304, J5 | LEMO EPL.00.250.NTN | 4 |
| TP* | test point | 24 |

Ordine Farnell per 5 schede (con scorta): `ordine_farnell.csv`.

Prima accensione: come per la scheda singola (`../PRIMA_DI_ORDINARE.md`), un canale
alla volta: alimentazioni → U1 → per ogni canale U?08 (regola il bias **senza SiPM**)
→ U?03 (regola la soglia) → SiPM. Per i punti da decidere (R3 = 255k, 2,2 µF su CF4,
CF7, CF9) valgono le stesse note della scheda singola.

## Verifiche fatte

- Schema: netlist riletta dal `.kicad_sch` per geometria = modello dati (0 differenze).
- PCB: autorouter + DRC geometrico + connettività: **0 errori**.
- Non ancora fatto: simulazione SPICE della scheda a 3 canali (il canale è identico a
  quello simulato in `simulation/ltspice/`); ERC/DRC ufficiali in KiCad.
