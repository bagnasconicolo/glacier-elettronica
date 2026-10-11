# Preventivo: due sistemi completi

Per due sistemi completi: rivelatore a 3 canali, scatolina di acquisizione, modulo meteo,
Raspberry Pi Zero 2 W e GPS. Prezzi in euro, **stimati** sui listini dell'ottobre 2026:
Mouser, TME, DigiKey, Adafruit, SparkFun e il listino JLCPCB per i prototipi. Il sito Mouser
e quello di JLCPCB non sono raggiungibili da qui, quindi il numero vero esce caricando i file
nei due carrelli (vedi sotto). Mouser: IVA esclusa, spedizione gratuita sopra 75 €.
JLCPCB: le tre schede in un solo ordine, una sola spedizione.

| Voce | Dove | File | Stima |
|---|---|---|---|
| Rivelatore: 5 PCB, montaggio SMD su 2 | JLCPCB | `variante_3ch/jlcpcb/` | 110–140 € |
| Rivelatore: chip a mano, connettori KK, ponticelli | Mouser | `variante_3ch/BOM_mouser_2prototipi.csv` | ~117 € |
| SiPM AFBR-S4N22P014M (6) | Mouser | stesso file | 125 € (togliere se già disponibili) |
| Scatolina: 5 PCB 105 × 70 mm, montaggio SMD su 2 | JLCPCB | `moduli/acquisizione/jlcpcb/` | 40–50 € |
| Modulo meteo: 5 PCB 36 × 22 mm, montaggio su 2 | JLCPCB | `moduli/meteo/jlcpcb/` | 35–45 € |
| Pico 2, zoccoli, KK, strip GPS, cavetti | Mouser | `moduli/BOM_mouser_moduli_2sistemi.csv` | ~30 € |
| GPS NEO-M9N SMA (2) + antenne attive 5 m (2) | Mouser (SparkFun, Adafruit) | stesso file | ~180 € (con Adafruit 746 al posto del NEO-M9N: ~100 €) |
| SHT45 a parte, cavi Qwiic, scatole Hammond | Mouser | stesso file | ~40 € |
| Raspberry Pi Zero 2 W + scheda SD | qualsiasi rivenditore | — | ~50 € |
| Alimentatori USB 5 V e cavi | qualsiasi rivenditore | — | ~30 € |
| Base in plexiglass, distanziali M3 | laboratorio | — | 20–40 € |
| **Totale** | | | **~780–850 €** con i SiPM; **~650–720 €** senza; **~570–640 €** senza SiPM e col GPS economico |

**Non inclusi i cavi LEMO: ci sono già (confermato).** Le prese LEMO sulle schede, se mancano, si
aggiungono queste voci:
- prese EPL.00.250.NTN: ~18 € l'una, 5 per scatolina e 4 per rivelatore;
- cavi LEMO 00–00 da 1 m: ~68 € l'uno (FFA-FFA00250CTAC29 100CM), 4 per sistema.

Cavi compatibili LEMO 00 RG174 si trovano a ~8–12 €, ma la qualità del connettore va
verificata.

## Ordine JLCPCB (tre schede insieme)

Per ognuna delle tre schede:
1. Carica lo zip dei Gerber.
2. Imposta 2 strati, 1,6 mm, HASL senza piombo. Per il rivelatore vedi la sua nota.
3. Attiva "PCB Assembly", lato superiore, con "PCBA Qty" = 2.
4. Carica `BOM_JLCPCB.csv` e `CPL_JLCPCB.csv` dalla cartella `jlcpcb/`.

Le parti a foro passante si saldano a mano e non sono nelle BOM JLCPCB: Pico (su strip),
LEMO, KK e strip del GPS. Anche i ponticelli a stagno non sono componenti.

Il SHT45-AD1B-R2 non ha un codice JLCPCB verificato: nella BOM del modulo meteo ha il campo
vuoto. Al caricamento JLCPCB offre il "global sourcing" (lo compra lui, qualche giorno in
più); altrimenti si ordina da Mouser (riga nel file dei moduli) e lo monta un laboratorio
con forno o aria calda. È un DFN da 1,5 mm: non si salda col saldatore.

## Codici JLCPCB/LCSC usati

| Parte | Codice |
|---|---|
| TCA9548APWR | C130026 |
| AP2112K-3.3TRG1 | C51118 |
| SN74LVC1G17DBVR | C7836 |
| PESD5V0U1BA | C5199862 |
| LPS22HHTR | C2827824 |
| SM04B-SRSS-TB (Qwiic) | C160404 |
| LED verde 0805 KT-0805G | C2297 |
| 100 nF 0603 | C14663 |
| 1 µF 0603 | C15849 |
| 10 µF 1206 | C47971 |
| 4,7k 0603 | C23162 |
| 10k 0603 | C25804 |
| 100k 0603 | C25803 |
| 100 Ω 0603 | C22775 |
| 33 Ω 0603 | C23140 |
| 1,5k 0603 | C22843 |

I primi sei e il LED sono verificati sulle pagine LCSC indicizzate. Per i passivi
"basic" i codici sono quelli standard UNI-ROYAL e Samsung: JLCPCB segnala comunque ogni
codice che non trova al caricamento della BOM.
