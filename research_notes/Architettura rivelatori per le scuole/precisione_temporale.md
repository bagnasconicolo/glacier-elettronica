# Precisione temporale dei timestamp per un rivelatore di muoni basato su Raspberry Pi (quando serve GPS/PPS)

> Note di ricerca (ottobre 2026). Nota metodologica: durante questa ricerca il proxy di rete bloccava il recupero diretto dei testi completi (arxiv.org, muonpi.org, pos.sissa.it, abyz.me.uk restituivano errori di connessione). I risultati qui sotto vengono quindi dai riassunti/estratti dei motori di ricerca delle pagine citate, non da una lettura completa dei PDF. Le cifre vanno ricontrollate sulla fonte primaria prima di citarle in un documento finale. Le cifre "a memoria" non verificate sono indicate esplicitamente come tali (nelle sezioni Inferences/Gaps).

## 1. Precisione/jitter dei timestamp ottenibile sul Raspberry Pi (libgpiod, pigpio, PREEMPT_RT, RP1/PIO, Pico PIO, TDC)

### Takeaway
Con Linux puro (interrupt GPIO, timestamp preso dal kernel) le misure pubblicate parlano di jitter dell'ordine del µs (≈0,2–7 µs a seconda della configurazione) su Pi 4. PREEMPT_RT "così com'è" peggiora il timestamp, perché sposta il gestore dell'interrupt in un thread. Per arrivare a 5–20 ns servono un front-end hardware: un contatore in un microcontrollore o in un PIO (Pico/RP2040: 8–16 ns per tick), il "timemark" del ricevitore GNSS (MuonPi, alcune decine di ns) oppure un TDC (TDC7200: risoluzione 55 ps).

### Cited Findings
**Linux / libgpiod**
- Lo strumento `gpiomon` di libgpiod v2 permette di scegliere il clock dei timestamp degli edge event con `-E/--event-clock`: i valori sono `monotonic` (il default), `realtime` e `hte`. `realtime` viene formattato come UTC. — [libgpiod docs, gpiomon](https://libgpiod.readthedocs.io/en/master/gpiomon.html); [man gpiomon (Debian)](https://manpages.debian.org/testing/gpiod/gpiomon.1.en.html)
- Nell'API C/GLib il clock degli eventi si imposta per singola linea (`GPIODGLIB_LINE_CLOCK_MONOTONIC / _REALTIME / _HTE`). — [libgpiod docs, get_event_clock](https://libgpiod.readthedocs.io/en/master/Gpiodglib-1.0/method.LineInfo.get_event_clock.html)
- Il supporto HTE (Hardware Timestamping Engine) è entrato in libgpiod v2 nel 2022. Da Linux 5.19 la uAPI GPIO espone un flag che rende l'HTE la sorgente dei timestamp, ma solo se il driver dell'hardware fornisce un HTE. — [patch libgpiod HTE (Linaro patchwork)](https://patches.linaro.org/patch/608734)
- Il timestamp di un edge event viene preso dal kernel nel gestore dell'interrupt, non quando il processo utente si sveglia. Lo stesso vale per pps-gpio. Con PREEMPT_RT i gestori vengono forzati in thread, quindi il timestamp arriva dopo la latenza di wake-up del thread e non più sull'edge elettrico. — [Cuckoo Escapement, kernel README](https://git.supported.systems/warehack.ing/cuckoo-escapement/src/branch/main/kernel/README.md)
- Misure su un singolo Pi 4 con GPS (field report autopubblicato, un solo Pi e un solo modulo GPS):
  - offset RMS di chrony: baseline 823 ns; con filtro mediano e `prefer` sul refclock PPS 440 ns; con PREEMPT_RT standard 2468 ns (peggio); con PREEMPT_RT più la patch IRQF_NO_THREAD 199 ns.
  - jitter grezzo del PPS: 2134 ns con chrony ottimizzato, 6947 ns con PREEMPT_RT (PPS in thread), 2568 ns con la patch IRQF_NO_THREAD.

  — [Cuckoo Escapement README](https://git.supported.systems/warehack.ing/cuckoo-escapement/raw/branch/main/README.md); [patch pps-gpio IRQF_NO_THREAD](https://git.supported.systems/warehack.ing/cuckoo-escapement/src/branch/main/kernel/0001-pps-gpio-keep-timestamp-in-hard-irq-under-PREEMPT_RT.patch)
- Sul kernel standard del Pi 4 non si può spostare l'interrupt GPIO su un altro core: scrivere `smp_affinity` dà "Operation not permitted", perché le linee GPIO sono demultiplexate da pinctrl-bcm2835. — [Cuckoo Escapement kernel README](https://git.supported.systems/warehack.ing/cuckoo-escapement/src/branch/main/kernel/README.md)
- Eventi persi sotto carico (aneddotico): un utente che contava impulsi di 5–100 µs con gpio su Orange Pi Zero ne perdeva alcuni, in corrispondenza di picchi di CPU. Lo stesso approccio risultava affidabile su un Raspberry Pi. — [Armbian forum](https://forum.armbian.com/topic/8171-opi-zero-gpio-libs-miss-edges)
- Contare in hardware gli edge persi è un concetto previsto in un RFC del kernel (contatore di "missed edges"), ma per hardware Intel, non per il Pi. — [LKML RFC gpiolib event count](https://lkml.iu.edu/2108.3/00810.html)

**pigpio**
- pigpio campiona e marca temporalmente i GPIO 0–31 fino a 1.000.000 campioni/s, cioè con risoluzione di 1 µs. Le callback di cambio stato (`gpioSetAlertFunc`) riportano un tick in µs. — [pigpio (directory secondaria)](https://www.neura.market/ai-tools-directory/all/joan2937-pigpio); esempio con sample rate di 2 µs: [freq_count_1.c](https://docs.ros.org/en/api/cob_hand_bridge/html/freq__count__1_8c_source.html)
- Il tick è un contatore a 32 bit in µs che va in overflow, quindi il codice deve gestire il wrap. — [pigpio_ffi docs](https://www.rubydoc.info/gems/pigpio_ffi/PiGPIO); [hall.c](https://docs.ros.org/en/api/cob_hand_bridge/html/hall_8c_source.html)

**Raspberry Pi 5 / RP1 / PIO**
- Su Pi 5 i GPIO sono gestiti dal chip RP1, collegato al BCM2712 via PCIe. RP1 contiene un blocco PIO, controllabile da userspace con PIOLib. La maggior parte delle chiamate PIOLib passa per il firmware di RP1 e richiede ≥10 µs. La documentazione ufficiale avverte che i compiti che richiedono uno stretto accoppiamento tra state machine e software sono a rischio, mentre lo streaming di dati va bene. — [Raspberry Pi news, piolib](https://www.raspberrypi.com/news/piolib-a-userspace-library-for-pio-control/)
- Con la libreria Gpio5 su Pi 5 sono stati generati impulsi fino a 24 ns. Si tratta di output, non di timestamp in ingresso. — [i-programmer, Pi 5 Gpio5](https://www.i-programmer.info/programming/148-hardware/17934-raspberry-pi-5-iot-in-c-gpio5.html?start=3)

**Pico (RP2040) PIO come co-processore di timestamp**
- PicoPET (timestamper su Pico): conta i cicli di clock tra fronti di salita e invia i timemark via seriale/USB. Risoluzione 16 ns a 125 MHz con PLL interno, ~166 ns usando il quarzo a 12 MHz. Il numero di canali è limitato dalla memoria PIO. — [GitHub dorsic/PicoPET](https://github.com/dorsic/PicoPET)
- Hui, Kyle, Edwards (Columbia) usano i PIO dell'RP2040, che sono co-processori cycle-accurate, per realizzare periferiche di timestamp (input capture / output compare). — [Timestamp Peripherals for Precise Real-Time Programming (copia scribd)](https://www.scribd.com/document/747987033/Timestamp-Peripherals-for-Precise-Real-Time-Programming)
- Timestamper "da 5 $" su STM32G431 a 170 MHz con input capture sul PPS GPS: risoluzione ~6 ns (1 tick), con obiettivo dichiarato di 184 ps. — [time-nuts, feb 2021](https://febo.com/pipermail/time-nuts_lists.febo.com/2021-February/102892.html)
- Un progetto ha portato CosmicWatch su un STM32F446 a 180 MHz con GPS, usando contatori interni per timestamp di scala ns e un timer agganciato al GPS. Gli autori notano che in pratica il jitter era peggiore dei ~10 ns attesi dal GPS. — [arXiv 1908.11288 (CREDO portable detectors)](https://arxiv.org/pdf/1908.11288)

**TDC dedicati**
- TI TDC7200: risoluzione 55 ps, deviazione standard 35 ps; 1 START e fino a 5 STOP; range 12–500 ns (modo 1) e 250 ns–8 ms (modo 2); alimentazione 2–3,6 V; interfaccia SPI. — [TI TDC7200 product page](https://www.ti.com/product/tdc7200)
- Prezzo TDC7200PW ≈3,16 $; scheda EVM ≈238,80 $ (listino DigiKey, datato 2015). — [DigiKey TDC7200](https://www.digikey.com/es/product-highlight/t/texas-instruments/tdc7200-time-to-digital-converter)
- Su time-nuts c'è un esempio di TDC esterno pilotato da un Pi Pico in MicroPython (minimo start-stop 12 ns, serve un riferimento a 10 MHz stabile). — [time-nuts / febo thread](https://lists.febo.com/empathy/thread/RBI3244CDGI5FIVJQLCRR6ZLARP3J2FY)
- TDC in FPGA (ring oscillator / tapped delay line) arrivano a decine di ps (applicazione: ToF in muografia). — [arXiv 1310.4281](https://arxiv.org/pdf/1310.4281)

### Inferences
- Per le coincidenze software tra canali della stessa scheda (uso b), il limite pratico con libgpiod v2 sono i timestamp kernel con jitter di qualche µs su Pi 4. La finestra di coincidenza software andrebbe quindi impostata a ~5–10 µs. Con rate di muoni di singolo canale dell'ordine di Hz–decine di Hz le coincidenze accidentali restano trascurabili: R_acc ≈ 2·τ·R1·R2, che con τ = 10 µs e R = 10 Hz dà ~2·10⁻³ Hz. È un'inferenza da calcolo, non da fonte. Conviene comunque tenere la coincidenza hardware come trigger principale.
- `CLOCK_REALTIME` (UTC) ha senso solo se l'orologio di sistema è disciplinato (NTP/PPS). Per misure di intervalli locali conviene `CLOCK_MONOTONIC`, che non salta in caso di aggiustamenti. Non ho trovato evidenza che i Raspberry Pi (BCM2711/BCM2712/RP1) espongano un provider HTE: verosimilmente `-E hte` non è disponibile su Pi. Da verificare con `gpiomon -E hte`.
- Su un kernel PREEMPT_RT bisogna assicurarsi che il gestore GPIO non sia threaded (cfr. patch IRQF_NO_THREAD), altrimenti i timestamp peggiorano invece di migliorare.
- Il ToF tra barre (uso d, ns) è fuori portata per Linux/pigpio (µs). Sarebbe possibile solo con un front-end PIO/MCU (risoluzione 6–16 ns per tick, ancora troppo grossolana per ToF su ~10 cm, dove la luce impiega ~0,3 ns) oppure con un TDC (55 ps). In pratica il ToF tra barre a distanza di cm/dm richiede TDC e discriminatori a soglia costante, non i semplici comparatori digitali.

### Gaps
- Non ho trovato benchmark pubblicati (paper o blog con istogrammi) di latenza/jitter degli edge event libgpiod su Pi 4/Pi 5 misurati con un generatore esterno. L'unico dato quantitativo trovato è il jitter PPS su Pi 4 (field report di un singolo autore).
- Non ho trovato misure di timestamp in ingresso tramite il PIO di RP1 (Pi 5), né la frequenza di clock del PIO di RP1 da una fonte verificata.
- Dati ScioSense TDC-GPX2 (risoluzione ~20 ps, prezzo) non trovati nei risultati: da verificare sul datasheet ScioSense.
- Il campionamento di default di pigpio (comunemente 5 µs, `gpioCfgClock`) è una conoscenza generale non confermata da fonte, perché la documentazione abyz.me.uk non era raggiungibile. pigpio inoltre non supporta Pi 5 (anche questo non verificato in questa sessione).

## 2. Rate massimi, eventi persi e larghezza minima degli impulsi (100–300 ns)

### Takeaway
Non ho trovato una fonte che quantifichi la larghezza minima di impulso rilevata dagli interrupt GPIO del Pi. Il rischio concreto è nella perdita di eventi sotto carico (code userspace) e nel campionamento: pigpio con campionamento a ≥1 µs può perdere impulsi di 100 ns per costruzione. Conviene allungare gli impulsi (≥1–5 µs) o mettere un front-end MCU/PIO.

### Cited Findings
- pigpio campiona i livelli a una frequenza massima di 1 MHz (1 µs). Un impulso più breve del periodo di campionamento può quindi non essere visto. Questa conclusione è una deduzione dal principio di campionamento; il valore di 1 MHz è citato in [pigpio feature list (secondaria)](https://www.neura.market/ai-tools-directory/all/joan2937-pigpio).
- Su Orange Pi Zero si perdevano impulsi di 5–100 µs durante i picchi di CPU, mentre il conteggio era affidabile su Raspberry Pi. — [Armbian forum](https://forum.armbian.com/topic/8171-opi-zero-gpio-libs-miss-edges)
- CosmicWatch (Arduino) calcola il dead time misurando in µs la durata dei comandi. Il dead time è "particolarmente importante" per la lentezza dell'Arduino. — [arXiv 1908.00146](https://arxiv.org/pdf/1908.00146)
- CosmicWatch v3X: trigger hardware, logica analogica di coincidenza (accidentali ridotte di quasi due ordini di grandezza), CPU dual-core con il processing sul secondo core (dead time medio ridotto di ~2 ordini di grandezza). — [arXiv 2508.12111](https://arxiv.org/html/2508.12111v2)
- Un riassunto secondario riporta per v3X una finestra di coincidenza di 2,3 µs e ~0,32 eventi/s per due rivelatori sovrapposti in coincidenza. Non verificato sulla fonte primaria. — [ElectronicsForU](https://www.electronicsforu.com/?p=202781)

### Inferences
- Nei SoC Broadcom la rilevazione di edge per gli interrupt GPIO è fatta da logica hardware sincrona (registri di event-detect), quindi un impulso di 100–300 ns ha buone probabilità di essere agganciato. Però se l'impulso è più corto di un ciclo del clock di campionamento interno, oppure se salita e discesa arrivano prima che il driver legga lo stato, si può perdere un edge o leggere il livello sbagliato. È un'inferenza non verificata da fonte. La scelta prudente è un monostabile o pulse stretcher (es. 74HC123/74LVC1G123) a ~2–10 µs, oppure catturare gli impulsi con un MCU/PIO che campiona a 125+ MHz (8 ns).
- Per i rate di muoni attesi (~1 /cm²/min, cioè pochi Hz–decine di Hz per barra), la sola latenza software non è un problema di throughput. Il rischio riguarda la coda di eventi persa sotto carico (rete, scrittura su SD) e il rumore dei SiPM (dark count fino a kHz–MHz sui canali singoli se la soglia è bassa). Per questo è importante usare la coincidenza hardware come trigger e contare i singoli canali in hardware.

### Gaps
- Nessuna misura pubblicata trovata sulla larghezza minima di impulso rilevabile via interrupt su BCM2711/BCM2712/RP1, né sul massimo rate di edge event libgpiod prima di perdite.
- La dimensione della coda kernel degli edge event (libgpiod v2 `event_buffer_size`) e il comportamento in overflow non sono stati verificati in questa ricerca.

## 3. Tempo assoluto: NTP su Wi-Fi, chrony, GPS PPS, PTP, antenna GPS nelle scuole

### Takeaway
Solo NTP su Wi-Fi scolastico dà precisioni da qualche ms a decine di ms: basta per conteggi e rate, non per coincidenze di sciami tra scuole (finestre µs). Un GPS con PPS letto da chrony su Pi porta a sub-µs (≈0,2–1 µs RMS secondo misure di hobbisti). Il PPS stesso di un modulo timing u-blox è ≤20 ns a cielo aperto ma ~500 ns indoor. L'antenna deve stare a una finestra o all'esterno.

### Cited Findings
- NTP su Internet: incertezza pratica di "qualche decina di ms". Il tratto Wi-Fi locale è stimato almeno 10 volte peggiore del tratto Internet e domina l'errore. — [time-nuts 2017, wifi with time sync](https://www.febo.com/pipermail/time-nuts/2017-January/103352.html)
- Su un Pi 4 su Wi-Fi è stato misurato un jitter NTP di qualche ms (preliminare). — [time-nuts 2019](https://febo.com/pipermail/time-nuts_lists.febo.com/2019-December/098503.html)
- Su Wi-Fi a 2,4 GHz (ESP8266) la latenza UDP è spesso di decine di ms e raramente costante. — [time-nuts 2019 (thread)](https://lists.febo.com/pipermail/time-nuts_lists.febo.com/2019-December/098503.html)
- Rivelatori sincronizzati via Internet (derivati da CosmicWatch): misurata una differenza di tempo di 2,03 ms; gli autori stanno passando al GPS. — [Kearns, St. Vincent College](https://www.stvincent.edu/assets/docs/academic-conference/academic-conference-201/Phys_Kearns_Synchronization_of_Muon_Detectors.pdf)
- Un GPS USB senza PPS dà accuratezza dell'ordine del ms (±10 ms). — [Austin's Nerdy Things 2025](https://austinsnerdythings.com/2025/02/14/revisiting-microsecond-accurate-ntp-for-raspberry-pi-with-gps-pps-in-2025/)
- Con GPS+PPS e chrony su Pi: il Pi resta abitualmente "a singole cifre" di ns rispetto al riferimento secondo le statistiche di chrony (un picco "fortunato" a 1 ns). Una lettura PPS singola era a 684 ns dal tempo GPS in un post precedente. La configurazione tipica è `refclock SHM 0 refid NMEA` più `refclock PPS /dev/pps0 lock NMEA`. La sentenza NMEA arriva ~200–325 ms dopo il PPS ed è usata solo per numerare il secondo. — [Austin's Nerdy Things 2025](https://austinsnerdythings.com/2025/02/14/revisiting-microsecond-accurate-ntp-for-raspberry-pi-with-gps-pps-in-2025/)
  - Attenzione: le "singole cifre di ns" sono l'offset stimato da chrony stesso rispetto al PPS. Non sono una misura indipendente con un oscilloscopio. Il field report Cuckoo Escapement su Pi 4 misura un offset RMS di 199–823 ns e un jitter grezzo del PPS di 2–7 µs. I due dati non sono in contraddizione diretta, perché misurano grandezze diverse, ma indicano che l'accuratezza reale sull'evento è dell'ordine di 0,2–2 µs. — [Cuckoo Escapement](https://git.supported.systems/warehack.ing/cuckoo-escapement/raw/branch/main/README.md)
- Il PPS GPS è allineato in hardware al secondo GPS entro decine di ns. chrony usa NMEA per sapere "che ora è" e PPS per sapere "quando inizia il secondo". — [Hackster, Ben Leikin stratum-1](https://www.hackster.io/news/got-the-time-ben-leikin-does-thanks-to-a-stratum-1-time-server-built-from-a-raspberry-pi-755764618216)
- Il Pi 5 supporta PTP con timestamp hardware, con sincronizzazione fino a decine di ns. Il Pi 3 è svantaggiato perché la sua Ethernet passa via USB. — [Austin's Nerdy Things 2025](https://austinsnerdythings.com/2025/02/14/revisiting-microsecond-accurate-ntp-for-raspberry-pi-with-gps-pps-in-2025/)
- u-blox NEO-M8T (modulo timing): accuratezza del PPS ≤20 ns a cielo aperto, ≤500 ns indoor, jitter ±11 ns (scheda di un rivenditore che riprende la spec u-blox). La sensibilità di −157 dBm permette l'avvio anche in strutture con vista del cielo limitata. Esiste una HAT Waveshare NEO-M8T per Raspberry Pi. — [Waveshare NEO-M8T HAT](https://www.waveshare.com/product/neo-m8t-gnss-timing-hat.htm); [Electronic Specifier](https://electronicspecifier.com/wireless/gnss-timing-modules-offer-accuracy-of-less-than-20ns)
- Nei rivelatori scolastici (QuarkNet) l'antenna deve stare vicino a una finestra. I cavi lunghi verso la DAQ attenuano il segnale, e questo ha motivato soluzioni wireless. — [QuarkNet poster](https://new.quarknet.org/sites/default/files/BUITRAGO_D_poster.pdf); [QuarkNet wireless GPS](https://quarknet.org/sites/default/files/Developing%20a%20wireless%20GPS%20data%20collection%20system%20for%20cosmic%20ray%20timing.pdf)
- Una scheda QuarkNet più vecchia, con GPS low-cost, marcava i trigger con accuratezza di ~50 ns in UTC tra siti lontani. — [arXiv physics/0311060 / QuarkNet DAQ](https://arxiv.org/pdf/physics/0311060)
- Su ESP32, NMEA più 1PPS dà ±5 µs, contro circa ±10 ms con il solo NMEA (progetto cosmic-ray "kurikintons"). — [kurikintons release notes](https://kurikintons.readthedocs.io/latest/releases/v1.16.3/)

### Inferences
- Per la coincidenza tra scuole serve tempo assoluto con errore ≪ finestra: almeno µs. Solo NTP (ms) è insufficiente di tre ordini di grandezza.
- Un GPS PPS su GPIO con chrony (tier 2) dà sub-µs sull'orologio di sistema. L'errore sul timestamp dell'evento muonico, letto anch'esso via GPIO, sarà però dominato dalla latenza/jitter di interrupt (µs), quindi in totale si stima ~1–5 µs. Basta per finestre di coincidenza tra stazioni di 10–100 µs, non per la ricostruzione di direzione.
- Antenna indoor o dietro vetri metallizzati: rischio di fix intermittente e di PPS degradato (centinaia di ns). Con un front-end a contatore disciplinato dal PPS (tier 3) l'errore residuo resta comunque ≪ µs. Conviene usare antenne attive con cavo verso una finestra o il tetto, e moduli "timing" (NEO-M8T, ZED-F9T) con modalità stazionaria/survey-in.

### Gaps
- Nessuna misura sistematica trovata di NTP/chrony su reti Wi-Fi scolastiche (con proxy/firewall che bloccano spesso UDP 123). I dati sono aneddotici (time-nuts).
- Prezzi aggiornati (2026) di Adafruit Ultimate GPS HAT, Uputronics GPS HAT, NEO-M9N/ZED-F9T non recuperati in questa sessione.
- Precisione PTP su Wi-Fi: non trovata. Probabilmente non è applicabile in modo utile, perché il timestamp hardware PTP del Pi 5 è sull'Ethernet.

## 4. Cosa usano i progetti reali e che precisione serve per coincidenze di sciami e ricostruzione direzionale

### Takeaway
Tutti i network che correlano stazioni distanti usano GPS con PPS e un contatore hardware (HiSPARC: contatore a 200 MHz, 5 ns, latched al PPS; EEE: TDC resettato dal PPS; MuonPi: timemark del u-blox, alcune decine di ns). Per la sola coincidenza tra stazioni bastano µs (HiSPARC usa ±2 µs). Per la direzione degli sciami servono ~10–20 ns (offset HiSPARC tra stazioni σ ≈ 19 ns).

### Cited Findings
**MuonPi**
- Rivelatore low-cost: scintillatore plastico più SiPM, su Raspberry Pi con scheda add-on custom. Il timestamp sfrutta la funzione "timemark" del u-blox NEO-M8N. Il Pi controlla la scheda via I2C, UART e GPIO. — [MuonPi wiki](https://wiki.muonpi.org/); [muonpi.org muondetector](https://muonpi.org/muondetector.html)
- Accuratezza del timestamp: "fino a 20 ns" secondo il README GitHub, "alcune decine di ns" secondo sito e wiki. Le cifre sono discordanti. — [GitHub MuonPi/muondetector](https://github.com/MuonPi/muondetector); [muonpi.org](https://muonpi.org/muondetector.html)
- Primi risultati: due rivelatori sovrapposti, distribuzione delle differenze di tempo gaussiana con σ ≈ 50 ns. — [MuonPi first results](https://muonpi.org/first_results.html)
- Meccanismo del timemark: probabilmente un capture register sul contatore libero del ricevitore, attivato dai fronti di salita e discesa (ipotesi da mailing list; non esiste documentazione ufficiale dettagliata). — [NTPsec devel, u-blox LKM Timemark driver](https://lists.ntpsec.org/pipermail/devel/2018-August/006519.html)
- Non ho trovato evidenza di un chip TDC sulla scheda MuonPi.

**HiSPARC**
- Il costruttore dell'elettronica GPS specifica un'accuratezza di 15 ns (1σ). — [HiSPARC Experiment, arXiv 1908.01622](https://arxiv.org/pdf/1908.01622)
- Offset tra stazioni (circa 100 coppie, Amsterdam Science Park): gaussiana con μ = 2,7 ns e σ = 18,9 ns. La larghezza cresce con la distanza tra stazioni. — [arXiv 1908.01622](https://arxiv.org/pdf/1908.01622); [poster HiSPARC](https://www.hisparc.nl/oud/fileadmin/HiSPARC/documenten/Posters/140817_ISVHECRI.pdf)
- Il tempo dell'evento si ricava da un contatore a 200 MHz (passo 5 ns) latched al PPS GPS. — [HiSPARC firmware docs](https://docs.hisparc.nl/firmware/messages.html)
- ADC con campionamento a 2,5 ns. — [poster HiSPARC Nikhef](https://www.hisparc.nl/oud/fileadmin/HiSPARC/documenten/Posters/120101_Nikhef.pdf)
- Le coincidenze tra stazioni si cercano con una finestra di 2 µs sui timestamp GPS. — [HiSPARC news 2014](https://www.hisparc.nl/oud/en/news/newsitem/article/translate-to-english-coincidenties-showers-gemeten-door-meerdere-stations/cache/925fcbc3137c1ee163a593068b48bfb6/)
- La simulazione SAPPHIRE assume un offset di timing di stazione con σ ≈ 16 ns. — [SAPPHIRE docs, detector simulations](https://docs.hisparc.nl/sapphire/simulations/detector.html)

**EEE (Extreme Energy Events)**
- Rete di telescopi MRPC nelle scuole. Ogni telescopio ha un'unità di trigger e un ricevitore GPS. Il timestamp assoluto è il tempo UTC dal GPS più un offset misurato da un TDC relativo al PPS; il PPS resetta i TDC. Sono state osservate coincidenze di sciami tra telescopi distanti fino a centinaia di km. — [PoS ICRC2019 358/389](https://pos.sissa.it/358/389/pdf); [EEE trigger (Centro Fermi)](https://agenda.centrofermi.it/event/91/contributions/606/attachments/348/535/EEE_trigger_v1.pdf)
- Un articolo del 2021 nota che i ricevitori GPS di EEE non sono calibrati e propone una sincronizzazione White Rabbit su fibra con UTC(IT). — [GPS Solutions 2021](https://link.springer.com/10.1007/s10291-021-01152-9)

**CosmicWatch / CREDO / altri**
- CosmicWatch: Arduino; coincidenza tra due rivelatori via cavo (v2), oppure con logica analogica e finestra hardware (v3X). — [arXiv 1908.00146](https://arxiv.org/pdf/1908.00146); [arXiv 2508.12111](https://arxiv.org/html/2508.12111v2)
- Rivelatori CREDO/CosmicWatch portati su STM32 a 180 MHz con GPS, per timestamp di scala ns. — [arXiv 1908.11288](https://arxiv.org/pdf/1908.11288)
- SCROD: hit latched su un oscillatore a 100 MHz resettato ogni secondo dal PPS. La precisione era limitata a ~40 ns dal fronte del PPS. — [arXiv hep-ex/0106002](https://arxiv.org/pdf/hep-ex/0106002)
- QuarkNet: ~50 ns in UTC tra siti distanti con GPS low-cost. — [arXiv physics/0311060](https://arxiv.org/pdf/physics/0311060)
- Cosmic Pi: non ho trovato fonti tecniche specifiche (GPS più Arduino Due/STM32) nei risultati.

### Inferences
- Coincidenza tra scuole a km di distanza: la luce percorre 1 km in ~3,3 µs, quindi lo sciame può arrivare a stazioni a distanza d con Δt ≤ d/c. Per d = 1–10 km la finestra fisica è ~3–33 µs. HiSPARC usa 2 µs per stazioni vicine (centinaia di m). Un errore di sincronizzazione di ~1–5 µs (tier 2) è quindi accettabile per finestre di 10–50 µs, ma allarga le accidentali. Con rate singoli di pochi Hz per stazione le accidentali restano comunque basse (stima: 2·50 µs·1 Hz·1 Hz ≈ 10⁻⁴ Hz ≈ 9 /giorno). È un calcolo indicativo, non da fonte. Sciami estesi rilevabili da due stazioni a km di distanza con piccole aree (~0,1 m²) sono comunque eventi rarissimi (energie ≳10¹⁷–10¹⁸ eV): stima generale, da verificare con un altro filone di ricerca.
- Ricostruzione direzionale: con base L = 10 m–1 km, una risoluzione angolare di qualche grado richiede σ_t ≲ L·Δθ/c. Per L = 100 m e Δθ = 5° si ottiene ≈ 29 ns. Il riferimento sono quindi i ~15–20 ns di HiSPARC, che richiedono tier 3–4 (contatore o timemark disciplinato dal PPS), non il timestamp GPIO di Linux.

### Gaps
- Non ho trovato nel testo completo i valori della finestra di coincidenza tra telescopi EEE né la risoluzione GPS raggiunta in ns, perché il full text era inaccessibile.
- Per Cosmic Pi non sono stati trovati dati tecnici.
- Per CREDO non sono stati trovati dati sulla precisione temporale degli smartphone e dei rivelatori dedicati.

## 5. Raccomandazioni a livelli (con costi indicativi)

### Takeaway
Tier 1 (NTP) per conteggi e rate. Tier 2 (GPS PPS più chrony, ~30–100 €) per coincidenze tra scuole con finestre di decine di µs. Tier 3 (Pico/MCU timestamper disciplinato dal PPS, ~5–15 € in più) per 10–20 ns e direzione. Tier 4 (TDC) solo per il ToF tra barre.

### Cited Findings
- Tier 1, NTP: errore di ms–decine di ms su Wi-Fi. — [time-nuts 2017](https://www.febo.com/pipermail/time-nuts/2017-January/103352.html); [time-nuts 2019](https://febo.com/pipermail/time-nuts_lists.febo.com/2019-December/098503.html)
- Tier 2, GPS PPS con chrony su GPIO: sub-µs sull'orologio di sistema, con jitter di interrupt di 2–7 µs su Pi 4 (misure di un singolo autore). Un modulo di timing aggiunge ≤20 ns a cielo aperto (500 ns indoor). — [Austin's Nerdy Things](https://austinsnerdythings.com/2025/02/14/revisiting-microsecond-accurate-ntp-for-raspberry-pi-with-gps-pps-in-2025/); [Cuckoo Escapement](https://git.supported.systems/warehack.ing/cuckoo-escapement/raw/branch/main/README.md); [Waveshare NEO-M8T HAT](https://www.waveshare.com/product/neo-m8t-gnss-timing-hat.htm)
- Tier 3, timestamper con contatore: Pico PIO 16 ns a 125 MHz (PicoPET); STM32 a 170 MHz ~6 ns; HiSPARC con contatore a 200 MHz (5 ns) latched al PPS; MuonPi con il timemark u-blox (decine di ns). — [PicoPET](https://github.com/dorsic/PicoPET); [time-nuts STM32](https://febo.com/pipermail/time-nuts_lists.febo.com/2021-February/102892.html); [HiSPARC firmware](https://docs.hisparc.nl/firmware/messages.html); [MuonPi](https://wiki.muonpi.org/)
- Tier 4, TDC: TDC7200 con 55 ps di risoluzione, ~3 $ il chip e ~239 $ l'EVM. Usato da EEE (TDC resettato dal PPS). — [TI](https://www.ti.com/product/tdc7200); [DigiKey](https://www.digikey.com/es/product-highlight/t/texas-instruments/tdc7200-time-to-digital-converter); [PoS EEE](https://pos.sissa.it/358/389/pdf)

### Inferences
- **Architettura consigliata per le scuole**: tenere la coincidenza triplice in hardware come trigger. Mandare l'uscita AND, eventualmente allungata a qualche µs, sia a un GPIO del Pi (conteggio e timestamp grossolano) sia a un Pico (RP2040/RP2350, ~5 €). Il Pico conta i cicli tra il PPS del GPS e ciascun evento (≈8 ns/tick a 125 MHz, ~6,7 ns a 150 MHz su RP2350) e invia "secondo GPS più contatore" via USB/UART al Pi. Il Pi riceve NMEA/PPS anche per chrony (orologio di sistema) e numera il secondo. Si ottiene un timestamp assoluto di ~20–50 ns, comparabile a MuonPi/HiSPARC, a un costo marginale basso. Il PIO del Pi 5/RP1 sarebbe un'alternativa senza Pico, ma mancano misure e documentazione verificate per i timestamp in ingresso.
- Moduli GNSS: per il tier 2 basta un modulo navigazione con PPS (NEO-M8N/M9N, Adafruit Ultimate GPS). Per i tier 3–4 è meglio un modulo timing (NEO-M8T, ZED-F9T), che offre la correzione del sawtooth del PPS (qErr) e la modalità a posizione fissa. Prezzi indicativi non verificati in questa ricerca (vedi Gaps).
- Il ToF tra barre (uso d) resta fuori scopo. Richiederebbe discriminatori veloci (CFD o leading-edge con correzione time-walk) più un TDC (TDC7200 o TDC-GPX2) o un FPGA, e ha una complessità sproporzionata per l'uso scolastico.

### Gaps
- Costi aggiornati al 2026 di Adafruit Ultimate GPS HAT, Uputronics GPS/RTC HAT, Waveshare NEO-M8T HAT, moduli ZED-F9T e TDC-GPX2: non recuperati, perché il fetch diretto delle pagine era bloccato in questa sessione.
- Nessuna fonte verificata sulla correzione qErr (sawtooth) del PPS u-blox e sul suo guadagno (tipicamente da ~±10–20 ns a pochi ns): da verificare nel manuale u-blox Timing.
