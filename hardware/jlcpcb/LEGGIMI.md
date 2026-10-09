# Ordine su JLCPCB — PCB + montaggio

Tre file da caricare su [jlcpcb.com](https://jlcpcb.com) → *Order now*:

| File | A cosa serve |
|---|---|
| `riv_cosmici_gerber.zip` | Gerber + foratura: il circuito stampato |
| `BOM_JLCPCB.csv` | distinta dei componenti da montare (36 righe, 60 componenti) |
| `CPL_JLCPCB.csv` | posizione e rotazione di ogni componente |

Generati da `hardware/generator/gen_jlcpcb.py` (stesso modello dati di schema e PCB).

**Non montati da JLCPCB (DNP), da saldare a mano:** U1 LT3461, U3 MAX961, U8 LT1636.
Non sono nella BOM né nel CPL; le piazzole restano sulla scheda.

## 1. Opzioni del PCB

| Opzione | Valore |
|---|---|
| Base material | FR-4 |
| Layers | 2 |
| Dimensions | 80 × 55 mm (le legge dal Gerber) |
| PCB Qty | 10 |
| PCB Thickness | 1.6 mm |
| PCB Color | a scelta (verde = più economico) |
| Surface Finish | HASL lead-free (o ENIG) |
| Outer Copper Weight | 1 oz |
| Via covering | Tented |
| Min via hole / diameter | 0.4 / 0.8 mm (rientra nello standard) |
| Mark on PCB | Remove mark (opzionale, costa poco) |
| Il resto | default |

Regole del progetto: piste ≥ 0,3 mm, isolamento ≥ 0,22 mm (0,4 mm attorno alle reti a
40 V), fori ≥ 0,4 mm: tutto dentro le capacità standard di JLCPCB.

## 2. Opzioni del montaggio (PCB Assembly: ON)

| Opzione | Valore |
|---|---|
| PCBA Type | Economic (se accetta i componenti a foro passante; altrimenti Standard) |
| Assembly Side | Top Side |
| PCBA Qty | 10 |
| Tooling holes | Added by JLCPCB |
| Confirm Parts Placement | **Yes** (fanno vedere le rotazioni prima di montare) |

Poi carica `BOM_JLCPCB.csv` e `CPL_JLCPCB.csv`.

## 3. Controlli nella pagina dei componenti

- **Righe con "LCSC Part #" vuoto** (passivi comuni, BFR93A, LP2985, TLC555, condensatore
  da 1 µF 100 V, header): JLCPCB le abbina dal Comment/Footprint. Controlla che proponga:
  - **C2**: 1 µF **100 V** X7R 1210 (es. TDK C3225X7R2A105K200AA). Il nodo è a ~41 V: niente 50 V.
  - **C1, C9** (22 pF, 100 pF): dielettrico C0G/NP0.
  - **Q1**: BFR93A in SOT-23 (NXP BFR93A,215 o Infineon BFR93AE6327). Se non c'è,
    rimuovilo dalla BOM e saldalo a mano.
  - **U5, U7**: LP2985AIM5-**3.6** (non 3.3!).
  - **U2**: TLC555CDR o LMC555CM/NOPB, in **SOIC-8** (non VSSOP/MSOP).
  - **Resistori**: 0805, 1%.
- **Header J1–J4**: se preferisci saldare tu fili o connettori, togli quella riga.
- **Rotazioni**: nell'anteprima 3D controlla il **pin 1** di U2, U4, U5, U6, U7, U9 e
  l'orientamento di Q1, Q2, D1 (banda = catodo = pin quadrato) e D3 (catodo = lato con la
  barra sul silkscreen). Le convenzioni di rotazione cambiano tra programmi: se un
  componente è girato, correggilo lì (90°/180°).

## 4. Varianti consigliate (vedi `hardware/PRIMA_DI_ORDINARE.md`)

Stesso PCB, cambia solo la BOM:

| Rif. | Valore INFN | Consigliato | Perché |
|---|---|---|---|
| R3 | 270k | **255k 1%** | boost a 39,4 V invece di 41,7 V (max assoluto LT3461: 40 V) |
| CF4, CF7, CF9 | 100 nF | **2,2 µF X7R 0805 ≥10 V** | uscita LP2985 ≥ 2,2 µF, MCP1825 ≥ 1 µF da datasheet |

Se le adotti, modifica le righe nel CSV prima di caricarlo (CF4, CF7, CF9 diventano
una riga separata).

## 5. Da comprare a parte (Mouser / Farnell / DigiKey)

| Rif. | Parte | Qta (con scorta) |
|---|---|---|
| U1 | LT3461ES6#TRMPBF (SOT-23-6) | 12 |
| U3 | MAX961ESA+ (SOIC-8) | 12 |
| U8 | LT1636CS8#PBF (SOIC-8) | 12 |
| — | SiPM Broadcom AFBR-S4N22P014M (Farnell 4351470) | 10 |

## 6. Prima accensione

Monta i tre chip uno alla volta e controlla le tensioni passo per passo; la sequenza è
in `hardware/PRIMA_DI_ORDINARE.md`. In breve: 5 V → 3,3/3,6 V → U1 (VOUT40) → U8, regola
V1 a 38,4 V **senza SiPM** → U3, regola la soglia con V2 → collega il SiPM.
