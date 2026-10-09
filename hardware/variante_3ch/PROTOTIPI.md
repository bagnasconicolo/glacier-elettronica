# Due prototipi da laboratorio (scheda a 3 canali)

Obiettivo: costruire **2 rivelatori** da usare come prototipi nei laboratori, con le
scuole coinvolte tramite accordi. **Niente marcatura CE, niente piattaforma, niente
GPS**: si spende il minimo e si misura se il circuito funziona davvero. Le scelte "da
prodotto" del rapporto `reports/Architettura rivelatori per le scuole.md` restano per
dopo, se e quando servirà.

## Cosa ordinare

| Voce | Dove | Quantità | Costo (IVA incl.) |
|---|---|---|---|
| PCB 103 × 215 mm + montaggio SMD | JLCPCB (`jlcpcb/`) | **5 PCB, montaggio su 2** | ~110–140 € (stima: rifare il preventivo) |
| Chip da saldare a mano, strip, ponticelli | Mouser (`BOM_mouser_2prototipi.csv`) | per 2 schede + 1 chip di scorta | 122 € |
| SiPM AFBR-S4N22P014M | Mouser (stesso file) | 6 | 125 € (togliere se già disponibili) |
| Raspberry Pi Zero 2 W + scheda SD 16–32 GB | qualsiasi rivenditore | 2 | ~50 € (o Pi già in laboratorio) |
| Alimentatori 5 V | qualsiasi rivenditore | 4 (2 per la scheda, 2 per il Pi) | ~30 € |
| Base in plexiglass, distanziali M3, staffe stampate per le barre | laboratorio | 2 | ~20–40 € |
| LEMO | — | — | già disponibili |
| **Totale** | | | **~460–510 €** (≈ 335–385 € senza SiPM) |

Note sui prezzi:
- **JLCPCB:** il minimo è 5 PCB, ma il montaggio si può chiedere solo su 2 (campo
  "PCBA Qty"). Le 3 schede nude restano come ricambio. Spedizione: scegliere la più
  economica (Global Standard Direct). Il numero va confermato col preventivo reale.
- **Mouser:** sopra 75 € la spedizione è gratuita, con dazi inclusi. MAX961, LT1636 e
  LT3461A sono fine vita e non restituibili: la scorta di un pezzo per tipo serve anche
  a riparare un prototipo.
- **Pi Zero 2 W** al posto del Pi 5: costa circa un quarto, consuma poco e per contare
  impulsi e leggere l'ADC basta. Va benissimo anche un Pi 3/4 già presente in laboratorio.

## Come montarlo (senza scatola)

- **Una base in plexiglass** (taglio laser) con la scheda e il Pi sopra, su distanziali
  M3 da 10 mm negli 8 fori di fissaggio. Niente involucro chiuso: per un prototipo da
  laboratorio è più comodo per misurare con l'oscilloscopio.
- **Le barre** (già a tenuta di luce) impilate su due staffe stampate in 3D, vicine alla
  scheda: i cavi verso J101/J201/J301 vanno tenuti **corti (10–30 cm)** e fermati con una
  fascetta, così il connettore non si stacca.
- **Il Pi lontano dai SiPM** (dall'altro lato della base), perché scalda.
- **Alimentazione:** due alimentatori separati, uno per la scheda (5 V su J3) e uno per il
  Pi. Costa pochi euro in più e toglie un dubbio: se poi le misure sono pulite, si
  prova con un alimentatore unico.
- **Collegamenti al Pi:** uscite dei canali e AND verso 4 GPIO con cavetti Dupont, J6 (I²C)
  ai pin 3/5/6 per il monitor delle tensioni.

## Software

- Conteggio e tempi degli impulsi con libgpiod (timestamp del kernel), salvataggio in CSV
  sulla SD.
- `software/monitor_tensioni.py` per i bias e l'alta tensione.
- Ora di rete (NTP): basta per i conteggi.
- Accesso remoto, se serve: Raspberry Pi Connect (gratuito per uso individuale).
- Nessuna piattaforma centrale per ora: i dati si copiano dalla SD o via rete.

## Prime prove (in quest'ordine)

1. Alimentazioni e alta tensione **senza SiPM** (`../PRIMA_DI_ORDINARE.md`); regolare il
   bias con V1 e verificarlo con il monitor delle tensioni.
2. **Larghezza degli impulsi al GPIO:** in simulazione sono circa 0,3 µs. Verificare che
   il Pi li conti tutti confrontando il suo conteggio con quello di un oscilloscopio o di
   un contatore. Se ne perde, la correzione è allungare l'impulso (un condensatore).
3. **Tenuta alla luce di ogni barra:** conteggio di un singolo canale a luce accesa e
   spenta, torcia lungo il rivestimento.
4. **Disturbi:** con l'oscilloscopio sull'ingresso del comparatore, cercare i picchi del
   survoltore; poi provare il Pi alimentato dalla stessa sorgente della scheda.
5. **Temperatura:** registrare per qualche giorno conteggi, bias e temperatura della
   stanza, per vedere quanto deriva il guadagno.

Quello che si impara da queste prove decide la versione successiva.
