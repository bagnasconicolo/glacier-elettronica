# Ordine su JLCPCB — PCB + montaggio

Tre file da caricare su [jlcpcb.com](https://jlcpcb.com) → *Order now*:

| File | A cosa serve |
|---|---|
| `riv_cosmici_gerber.zip` | Gerber + foratura: il circuito stampato |
| `BOM_JLCPCB.xlsx` (o `.csv`) | distinta dei componenti da montare (33 righe, 53 componenti) |
| `CPL_JLCPCB.xlsx` (o `.csv`) | posizione e rotazione di ogni componente |
| `MPN_riferimento.csv` | solo per te: il codice del produttore delle righe da controllare |

Generati da `hardware/generator/gen_jlcpcb.py` (stesso modello dati di schema e PCB).

**Non montati da JLCPCB (DNP), da saldare a mano** (non sono nella BOM né nel CPL; le
piazzole restano sulla scheda):

| Rif. | Parte | Perché a mano |
|---|---|---|
| U1, U3, U8 | LT3461, MAX961, LT1636 | costosi / poco disponibili: si comprano a listino |
| U5, U7 | LP2985AIM5-3.6 (SOT-23-5) | esauriti a JLCPCB al 9/10/2026 |
| D1 | 1N4148 (DO-35, foro passante) | esaurito a JLCPCB al 9/10/2026 |
| J1–J4 | header 1×2 passo 2,54 mm (o fili) | non riconosciuti dal BOM Tool |

Nella BOM ogni riga ha il **JLCPCB Part #** oppure, come Comment, il **codice del
produttore** (i resistori sono UNI-ROYAL `0805W8F…T5E`, la serie standard di JLCPCB):
così il BOM Tool trova il pezzo esatto invece di indovinarlo dalla descrizione.

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

## 2. Montaggio: dove si caricano BOM e CPL

Il prezzo che compare dopo il Gerber (~$11) è **solo il PCB nudo**. Il montaggio si
aggiunge così:

1. Nella stessa pagina scorri in fondo fino a **PCB Assembly** e attivalo.
2. Imposta: PCBA Type **Economic** (se segnala i componenti a foro passante, passa a
   **Standard**), Assembly Side **Top Side**, PCBA Qty **10**, Tooling holes
   **Added by JLCPCB**, Confirm Parts Placement **Yes**.
3. Premi **NEXT** (a destra): appare l'anteprima del PCB → di nuovo **NEXT**.
4. Solo adesso compaiono i due pulsanti **Add BOM File** e **Add CPL File**: carica
   `BOM_JLCPCB.xlsx` e `CPL_JLCPCB.xlsx` (vanno bene anche i `.csv`) → **Process BOM & CPL**.
5. Pagina dei componenti (controlli al punto 3) → **NEXT** → anteprima del piazzamento →
   **NEXT** → il prezzo totale con il montaggio.

Se un caricamento dà errore, annota il messaggio esatto: di solito indica la colonna
o la riga che non va.

## 3. Controlli nella pagina dei componenti

- Tutte le righe dovrebbero risultare abbinate. Se un resistore resta "No matches" o
  "Unconfirmed", cerca nel loro catalogo il valore in 0805 1% e scegli una parte
  **Basic** (costa meno: niente tassa per parti fuori libreria).
- Se una parte risulta **senza stock** ("0 JLCPCB"), sceglila in alternativa con stesso
  valore e package, oppure toglila e aggiungila alla lista da saldare a mano.
- **Rotazioni**: nell'anteprima controlla il **pin 1** di U2, U4, U6, U9 e l'orientamento
  di Q1, Q2 e D3 (catodo = lato con la barra sul silkscreen). Le convenzioni di rotazione
  cambiano tra programmi: se un componente è girato, correggilo lì (90°/180°).
- **PCBA Qty**: nel tuo primo tentativo risultava 15. Mettila a 10 (o al minimo che
  accettano) se non ti servono schede in più.

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
| U5, U7 | LP2985AIM5-3.6/NOPB (SOT-23-5) | 24 |
| D1 | 1N4148 DO-35 | 12 |
| J1–J4 | pin header maschio 1×2 passo 2,54 mm (o una strip da tagliare) | 45 |
| — | SiPM Broadcom AFBR-S4N22P014M (Farnell 4351470) | 10 |

## 6. Prima accensione

Prima salda J1–J4, U5, U7 e D1 (servono alle alimentazioni e ai riferimenti), poi i tre
chip uno alla volta, controllando le tensioni passo per passo; la sequenza è in
`hardware/PRIMA_DI_ORDINARE.md`. In breve: 5 V → 3,3/3,6 V → U1 (VOUT40) → U8, regola
V1 a 38,4 V **senza SiPM** → U3, regola la soglia con V2 → collega il SiPM.
