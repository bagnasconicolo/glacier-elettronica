# Prima di ordinare i PCB — stato della revisione A2

Questa revisione (A2) è la scheda INFN "Riv. Cosmici 2024 — Amplif, alim, soglie"
(S. Gallian, rev. A) ricostruita in KiCad, **verificata collegamento per collegamento
contro lo schema originale** e simulata per intero. In più c'è uno stadio d'uscita a
3,3 V per la lettura con un Raspberry Pi.

## Cosa è stato verificato

| Verifica | Come | Esito |
|---|---|---|
| Schema KiCad = schema INFN | confronto pin per pin con `docs/schema_originale_INFN.pdf` | OK, dopo la correzione di V2 (sotto) |
| Netlist del file `.kicad_sch` = modello dati | `simulation/netlist_from_kicad.py` (estrae le reti per geometria) | OK: 0 reti diverse; gli unici pin liberi sono i NC voluti (U5.4, U7.4, U8.1/5/8, U9.1) |
| Piedinature degli integrati | datasheet MAX961, MCP1402, LT3461, LP2985, MCP1825, LT1636, TLC555, 74LVC1G17 | OK |
| Footprint | SOT-23 (1 = B, 2 = E, 3 = C), SOT-23-5/6, SO-8, SOT-223 (tab = GND), 3296W (cursore al centro), LED (pin 1 = catodo) | OK |
| PCB | autorouter del generatore + DRC geometrico + verifica di connettività | 0 errori DRC, 0 reti aperte |
| Funzionamento della scheda intera | `simulation/ltspice/verifica_ltspice.py` (ngspice), 21 controlli | tutti superati (vedi sotto) |

## Cosa è cambiato rispetto alla ricostruzione precedente

1. **V2 (soglia): errore di ricostruzione corretto.** Nell'originale V2 è un
   *potenziometro*: l'estremo alto va a R19 (+3,6 V), il cursore a R17 → TH e l'estremo
   basso a R18. In KiCad il cursore era cortocircuitato all'estremo alto (V2 usato come
   reostato). Ora è come nell'originale. Il campo della soglia resta da ~1 mV a ~1,29 V.
2. **Uscita per il Raspberry Pi (J4).** I GPIO del Pi lavorano a 3,3 V e **non
   tollerano 5 V**. Il vecchio buffer a 2 transistor era alimentato a 5 V e, simulandolo,
   ritardava gli impulsi (~440 ns), li accorciava di ~100 ns e spingeva l'uscita a
   −0,7 V. È stato sostituito da **U9 = 74LVC1G17** (buffer CMOS con trigger di Schmitt,
   alimentato a +3V3) + **R23 = 33 Ω** in serie, adattata al cavo coassiale. Il risultato
   è una copia esatta di CMP_Q a 0–3,3 V, con 8 ns di ritardo.
3. **Libreria `riv.kicad_sym`** rigenerata (contiene il simbolo del 74LVC1G17).
4. **PCB e Gerber** rigenerati, con il buffer finalmente sulla scheda.
5. **BOM** generata dallo stesso modello dati (`hardware/generator/gen_bom.py`).

Nessun valore del circuito originale INFN è stato cambiato.

## Punti da decidere prima del montaggio (non richiedono modifiche al PCB)

1. **LT3461 (U1): uscita del boost oltre il limite assoluto.** Con R3 = 270k e
   R1‖R2‖R22 = 8,39k, VOUT40 = 1,255 V × (1 + 270/8,39) = **41,7 V nominali**.
   Il datasheet LT3461 dà **40 V come massimo assoluto** su VOUT e SW (38 V è l'uscita
   massima dichiarata). La nota INFN indica 40,2 V misurati: la scheda originale
   funziona, ma è al limite. *Consiglio:* **R3 = 255k (1%)** porta VOUT40 a
   **39,4 V**. In simulazione il bias si regola ancora fino a 39 V (38,4 V con
   V1_POS = 0,76). Stesso footprint 0805, cambia solo il valore in BOM.
2. **Condensatori d'uscita dei regolatori.** Il datasheet LP2985 chiede **≥ 2,2 µF**
   in uscita (X7R) e l'MCP1825 **≥ 1 µF**. Nell'originale CF4 e CF7 (uscite LP2985)
   e CF9 (uscita MCP1825) sono da 100 nF. *Consiglio:* montare **2,2 µF X7R 0805
   (≥ 10 V)** su CF4, CF7 e CF9. Stesso footprint, nessuna modifica al PCB.
3. **L1 (47 µH, RS 693-4344)**: il footprint è un 5×5/6×6 mm generico. Controllare le
   dimensioni dei pad sul datasheet della parte che si ordina.
4. **J4**: il footprint è un header 2,54 mm; il LEMO va a pannello e si collega con un
   cavetto. **J2 (TTL_OUT) esce a 5 V: non collegarlo al Raspberry Pi.**
5. **Capacità del SiPM**: dipende dal sensore e decide i mV per fotoelettrone vicino
   alla soglia (da ~32 mV/p.e. senza capacità a ~19 mV/p.e. con 100 pF). I muoni
   (≥ 80 p.e.) saturano comunque a ~1,1 V e vengono sempre contati. La soglia (V2)
   va tarata sulla scheda vera guardando il singolo fotoelettrone all'oscilloscopio.

## Ultimi passi in KiCad (consigliati)

Aprire `hardware/riv_cosmici.kicad_pro` con KiCad ≥ 6, lanciare **ERC** sullo schema,
**riempire le zone** (tasto B) e lanciare il **DRC** sul PCB. Il generatore ha già fatto
un DRC geometrico e la verifica di connettività, ma il DRC ufficiale di KiCad è il
controllo finale. I Gerber pronti sono in `hardware/gerber/` (anche come
`riv_cosmici_gerber.zip`): 2 strati, 80 × 55 mm, foratura PTH in Excellon.

## Collegamento al Raspberry Pi

| Scheda | Raspberry Pi |
|---|---|
| J4 pin 1 (segnale 0–3,3 V) | un GPIO, es. GPIO17 (pin 11), meglio con 330 Ω in serie |
| J4 pin 2 (GND) | GND (es. pin 9) |

Ogni muone produce un impulso positivo di **≥ 84 ns** (minimo garantito dal latch
C9/R16 del MAX961), ~150–270 ns per un muone tipico. Va contato **sul fronte di
salita, a interrupt** (rilevamento dei fronti in hardware del GPIO, es. `libgpiod` con
eventi `RISING_EDGE`): leggere il pin in polling perderebbe impulsi così brevi.
Il rate atteso su una paletta 10×10 cm è ~1,7 eventi/s.
