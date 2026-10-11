# Due prototipi da laboratorio (scheda a 3 canali)

Obiettivo: costruire **2 rivelatori** da usare come prototipi nei laboratori, con le
scuole coinvolte tramite accordi. **Niente marcatura CE, niente piattaforma, niente
GPS**: si spende il minimo e si misura se il circuito funziona davvero. Le scelte "da
prodotto" del rapporto `reports/Architettura rivelatori per le scuole.md` restano per
dopo, se e quando servirà.

## Cosa ordinare

| Voce | Dove | Quantità | Costo (IVA incl.) |
|---|---|---|---|
| PCB 103 × 223,9 mm + montaggio SMD | JLCPCB (`jlcpcb/`) | **5 PCB, montaggio su 2** | ~110–140 € (stima: rifare il preventivo) |
| Chip da saldare a mano, strip, ponticelli, connettori KK | Mouser (`BOM_mouser_2prototipi.csv`) | per 2 schede + 1 chip di scorta | ~127 € |
| SiPM AFBR-S4N22P014M | Mouser (stesso file) | 6 | 125 € (togliere se già disponibili) |
| Raspberry Pi Zero 2 W + scheda SD 16–32 GB | qualsiasi rivenditore | 2 | ~50 € (o Pi già in laboratorio) |
| Raspberry Pi Pico (o Pico 2) + adattatore USB OTG, millefori, 4 buffer per rivelatore | qualsiasi rivenditore; buffer e adattatori nel file Mouser | 2 (+1 di scorta) | ~25 € |
| Alimentatori 5 V | qualsiasi rivenditore | 4 (2 per la scheda, 2 per il Pi) | ~30 € |
| Base in plexiglass, distanziali M3, staffe stampate per le barre | laboratorio | 2 | ~20–40 € |
| LEMO | — | — | già disponibili |
| **Totale** | | | **~490–540 €** (≈ 360–410 € senza SiPM) |

Note sui prezzi:
- **JLCPCB:** il minimo è 5 PCB, ma il montaggio si può chiedere solo su 2 (campo
  "PCBA Qty"). Le 3 schede nude restano come ricambio. Spedizione: scegliere la più
  economica (Global Standard Direct). Il numero va confermato col preventivo reale.
- **Mouser:** sopra 75 € la spedizione è gratuita, con dazi inclusi. MAX961, LT1636 e
  LT3461A sono fine vita e non restituibili: la scorta di un pezzo per tipo serve anche
  a riparare un prototipo.
- **Pico + Zero 2 W.** Il Pico cattura gli impulsi senza perderne e ne annota l'istante
  (16 ns); lo Zero salva, legge l'I²C e fa girare la dashboard. Il Pico costa ~5 € e toglie
  l'unico rischio non verificabile prima dell'ordine: le uscite verso il Raspberry durano
  150–220 ns e non c'è una misura pubblicata che garantisca che il GPIO sotto Linux le
  prenda tutte. È la scelta dei progetti simili (CosmicWatch v3X usa un Pico). Va bene
  anche un Pi 3/4 già presente in laboratorio al posto dello Zero.

## Come montarlo (senza scatola)

- **Una base in plexiglass** (taglio laser) con la scheda e il Pi sopra, su distanziali
  M3 da 10 mm negli 8 fori di fissaggio. Niente involucro chiuso: per un prototipo da
  laboratorio è più comodo per misurare con l'oscilloscopio.
- **Le barre** (già a tenuta di luce) impilate su due staffe stampate in 3D. Cavo dalla
  barra alla scheda: **coassiale RG174 o RG316, fino a 50 cm** (simulato: il segnale cala
  del 10 % e resta 7 volte sopra la soglia), fermato con una fascetta a ogni estremo.
- **Connettore barra → scheda: Molex KK 254 a 2 poli, NON LEMO.** Nel cavo la calza
  porta i +38 V del bias, mentre i LEMO della scheda hanno la carcassa a massa: un
  connettore diverso rende impossibile lo scambio. Sulla scheda, al posto della strip,
  l'header 22-27-2021 (con rampa di aggancio, entra negli stessi fori di J101/J201/J301);
  sul cavo il connettore 22-01-3027 con due contatti 08-50-0114:
  **pin 1 = conduttore centrale (segnale), pin 2 = calza (bias)**, guaina
  termorestringente sulla calza.
- **Il Pi lontano dai SiPM** (dall'altro lato della base), perché scalda.
- **Alimentazione:** due alimentatori separati, uno per la scheda (5 V su J3) e uno per il
  Pi. Costa pochi euro in più e toglie un dubbio: se poi le misure sono pulite, si
  prova con un alimentatore unico.
- **Collegamenti:** uscite dei canali e AND (LEMO) verso il Pico, attraverso 4 buffer di
  protezione su millefori (`firmware/pico_acquisizione/LEGGIMI.md`); Pico allo Zero via USB.
  J6 (I²C, **Molex KK 254 a 3 poli** come i connettori delle barre: header 22-27-2031 sulla
  scheda, connettore 22-01-3037 sul cavo; 1 = GND, 2 = SDA, 3 = SCL) verso i pin 6/3/5 dello Zero.

## Software

- Pico: `firmware/pico_acquisizione/main.py` (MicroPython). Zero:
  `software/acquisizione_pico.py`, salva gli eventi in CSV sulla SD e confronta le triple
  calcolate dai tempi con l'AND hardware.
- `software/monitor_tensioni.py` per i bias e l'alta tensione.
- Ora di rete (NTP): basta per i conteggi.
- Accesso remoto, se serve: Raspberry Pi Connect (gratuito per uso individuale).
- Nessuna piattaforma centrale per ora: i dati si copiano dalla SD o via rete.

## Prime prove (in quest'ordine)

1. Alimentazioni e alta tensione **senza SiPM** (`../PRIMA_DI_ORDINARE.md`); regolare il
   bias con V1 e verificarlo con il monitor delle tensioni.
2. **Conteggio degli impulsi:** in simulazione durano 150–220 ns. Contare gli stessi impulsi
   con il Pico, con i GPIO dello Zero (libgpiod) e con un oscilloscopio o un contatore, anche
   con lo Zero sotto carico. Il Pico deve contarli tutti; il confronto dice se per le
   versioni successive lo Zero da solo basterebbe.
3. **Tenuta alla luce di ogni barra:** conteggio di un singolo canale a luce accesa e
   spenta, torcia lungo il rivestimento.
4. **Disturbi:** con l'oscilloscopio sull'ingresso del comparatore, cercare i picchi del
   survoltore; poi provare il Pi alimentato dalla stessa sorgente della scheda.
5. **Temperatura:** registrare per qualche giorno conteggi, bias e temperatura della
   stanza, per vedere quanto deriva il guadagno.

Quello che si impara da queste prove decide la versione successiva.
