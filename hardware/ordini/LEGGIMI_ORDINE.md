# MuLab: come fare gli ordini (JLCPCB + Mouser)

Questo pacchetto copre la **configurazione base**: rivelatore a 3 canali e scatolina di
acquisizione con Pico 2, senza GPS e senza modulo meteo. Le prese LEMO, i cavi LEMO e le
barre scintillanti si danno per già disponibili. Meteo e GPS sono **upgrade** con file
separati. Costi stimati: `PREVENTIVO_MuLab.pdf`.

Gli ordini sono due:
- **JLCPCB**: circuiti stampati e montaggio dei componenti SMD;
- **Mouser**: chip da saldare a mano, connettori, SiPM, Pico 2.

```
jlcpcb/1_rivelatore/              Gerber zip, BOM, CPL (+ MPN_riferimento.csv, solo consultazione)
jlcpcb/2_scatolina_acquisizione/  Gerber zip, BOM, CPL
jlcpcb/3_modulo_meteo_UPGRADE/    Gerber zip, BOM, CPL  (solo se si ordina anche il meteo)
mouser/mouser_base_2setup.csv     lista Mouser per 2 setup (con scorte)
mouser/mouser_base_4setup.csv     lista Mouser per 4 setup
mouser/mouser_upgrade_meteo_*.csv / mouser_upgrade_gps_*.csv
```

---

## 1. JLCPCB (jlcpcb.com → Order now)

Si fa **un solo ordine con le schede tutte insieme**: una scheda alla volta, ognuna
aggiunta al carrello ("Save to cart"), poi si paga tutto insieme. Spedizione e IVA si
pagano una volta sola.

### 1a. Opzioni del circuito stampato (per ogni scheda)

Caricare lo zip dei Gerber ("Add gerber file"); dimensioni e strati li legge da solo.

| Opzione | Rivelatore | Scatolina | Meteo (upgrade) |
|---|---|---|---|
| Dimensioni (lette dal Gerber) | 103 × 223,9 mm | 105 × 70 mm | 36 × 22 mm |
| Layers | 2 | 2 | 2 |
| PCB Qty | 5 (minimo) | 5 | 5 |
| PCB Thickness | 1,6 mm | 1,6 mm | 1,6 mm |
| PCB Color | **Red** | **Red** | **Red** |
| Surface Finish | HASL lead-free | HASL lead-free | HASL lead-free |
| Outer Copper Weight | 1 oz | 1 oz | 1 oz |
| Mark on PCB | Remove mark (facoltativo) | idem | idem |
| Tutto il resto | default | default | default |

Il modulo meteo ha distanze fino a 0,127 mm vicino al sensore di pressione: rientrano
nelle capacità standard.

### 1b. Montaggio (PCB Assembly)

1. Nella stessa pagina, in fondo, attivare **PCB Assembly**.
2. Impostare:
   - **PCBA Type**: **Standard** per il rivelatore (ha trimmer e USB-C con piedini passanti); **Economic** va bene per scatolina e meteo;
   - **Assembly Side**: Top;
   - **PCBA Qty**: **2** (o **4**), cioè quanti setup si costruiscono; le altre schede restano nude come ricambio;
   - **Tooling holes**: Added by JLCPCB;
   - **Confirm Parts Placement**: **Yes**.
3. Premere NEXT → NEXT. Compaiono **Add BOM File** e **Add CPL File**: caricare
   `BOM_JLCPCB.csv` e `CPL_JLCPCB.csv` della cartella della scheda → **Process BOM & CPL**.
4. Nella pagina dei componenti, per ogni riga:
   - deve risultare abbinata e **in stock**;
   - nel rivelatore alcuni resistori hanno solo il codice del produttore (UNI-ROYAL
     `0805W8F…T5E`, colonna Comment): se restano "No match", cercare valore + 0805 + 1%
     e scegliere una parte **Basic**;
   - **SHT45-AD1B-R2** (meteo) non ha codice: scegliere **Global Sourcing** oppure
     toglierlo e comprarlo da Mouser (riga nel file upgrade meteo);
   - se una parte è a stock zero, sostituirla con lo stesso valore e package, o toglierla
     e saldarla a mano.
5. **Anteprima del piazzamento: controllare rotazioni e pin 1.** È il punto in cui si
   sbaglia più spesso, perché ogni programma ha la sua convenzione.
   - Rivelatore: integrati SO-8 e SOT-23, diodi, LED, USB-C.
   - Scatolina: U1–U5 74LVC1G17, U6 TCA9548A (pin 1 = puntino), U7 AP2112K, diodi D1–D5, LED, prese Qwiic con l'apertura verso il bordo.
   - Meteo: U1 SHT45, U2 LPS22HH, prese Qwiic.

   Se un pezzo è girato, correggerlo lì (90° o 180°) e annotarlo.
6. NEXT → prezzo totale con montaggio → Save to cart.

**Non montati da JLCPCB, da saldare a mano.** Non sono in BOM/CPL; arrivano dall'ordine
Mouser o sono già disponibili.

| Scheda | Parti a mano |
|---|---|
| Rivelatore | U1 LT3461, U103/203/303 MAX961, U108/208/308 LT1636, U5 U7 LP2985, D101/201/301 1N4148, J101/201/301 e J6 KK, J3 + JP1–JP3 + test point (strip 1x40), J104/204/304 e J5 LEMO |
| Scatolina | A1 Pico 2 (su 2 strip femmina 1x20), J1–J5 LEMO, J6 strip 1x6 (GPS), J7 J8 KK |
| Meteo | nulla (JP1, JP2 sono ponticelli a stagno sul circuito) |

---

## 2. Mouser (mouser.it)

1. Accedere a mouser.it → menu **BOM** (strumento "BOM Tool" o "Carica BOM").
2. **Upload**: `mouser/mouser_base_2setup.csv` (o `_4setup`). Abbinare le colonne:
   Manufacturer Part Number → *Mfr. Part #*, Manufacturer → *Manufacturer*,
   Quantity → *Quantity*, Customer Part Number → *Customer #*. La descrizione finisce
   sull'etichetta di ogni bustina.
3. Controllare **disponibilità** e **quantità minime**. LT3461, MAX961 e LT1636 sono
   fine vita: se uno è esaurito, segnalarlo e non sostituirlo a caso, perché pinout e
   versione contano (LT1636 in SO-8, **non** MSOP).
4. Togliere la riga dei **SiPM** se sono già disponibili.
5. **Add to cart**. Sopra 50 € la spedizione è gratuita, dazi inclusi.
6. Upgrade, quando servono: aggiungere `mouser_upgrade_meteo_*.csv` e/o
   `mouser_upgrade_gps_*.csv` (stessa procedura).

Quantità (scorte comprese):

| Parte | 2 setup | 4 setup |
|---|---|---|
| LT3461 / MAX961 / LT1636 | 3 / 7 / 7 | 5 / 13 / 13 |
| LP2985-3.6 | 5 | 9 |
| SiPM AFBR-S4N22P014M | 6 | 12 |
| Pico 2 | 3 | 5 |
| Connettori KK, contatti, strip, ponticelli | vedi CSV | vedi CSV |

---

## 3. Da comprare altrove o già disponibili

- Raspberry Pi Zero 2 W + microSD 16–32 GB, uno per setup (qualsiasi rivenditore).
- Alimentatori USB 5 V e cavi: un USB-C per il rivelatore, un micro-USB per lo Zero; il cavo USB tra Zero e Pico.
- Prese LEMO EPL.00.250.NTN (9 per setup) e cavi LEMO: già disponibili.
- Barre scintillanti: già disponibili.
- Scatola della scatolina e supporti: stampati in 3D (PETG).
- Cavo I2C rivelatore → scatolina: si crimpa con i connettori KK 3 poli e i contatti della lista Mouser.

---

## 4. Dopo l'ordine

- Le BOM e i CPL nascono da `hardware/generator/gen_jlcpcb.py` (rivelatore) e da
  `hardware/moduli/costruisci_modulo.py` (scatolina, meteo). Se cambia una scheda,
  rigenerarli e rilanciare `python3 hardware/ordini/genera_ordini.py`.
- Primo collaudo del rivelatore: `hardware/variante_3ch/LEGGIMI.md` (sezione Montaggio)
  e `NOTA_PER_TECNICO_INFN.txt`.
