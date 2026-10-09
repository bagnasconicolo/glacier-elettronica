# Alimentazione, rumore e conformità CE: rivelatore di muoni a SiPM per le scuole (scheda 3 canali + Raspberry Pi)

> Nota metodologica: in questa sessione il fetch diretto delle pagine era bloccato dal proxy (raspberrypi.com, docs.broadcom.com, arxiv.org, farnell.com non raggiungibili). Tutti i fatti sotto vengono da risultati di ricerca web (estratti e sintesi dei motori di ricerca). Le URL sono quelle delle fonti primarie restituite, ma i valori numerici vanno ricontrollati sui PDF originali prima di finire in una specifica di progetto. Ho segnato come "Inferenza" i calcoli fatti da me.

## 1. Opzioni per alimentare insieme scheda rivelatore e Raspberry Pi; requisiti ufficiali Pi

### Takeaway
Per Pi 5 la soluzione più semplice e robusta è l'alimentatore ufficiale USB-C PD 27 W (5.1 V / 5 A), da cui si deriva il 5 V per la scheda SiPM con filtro e protezioni. In alternativa, un ingresso unico a 12 V (alimentatore da muro CE, circa 12 €) con buck a bordo, che genera un 5 V/5 A per il Pi e un 5 V "pulito" separato per l'analogico, dà più margine sulla caduta nei cavi, più controllo sul rumore e connettori meno fragili. PoE+ conviene solo se la scuola ha switch PoE; per Pi 4 bastano 5.1 V / 3 A.

### Cited Findings
- **Pi 5 e alimentatori non da 5 A.** Se il Pi 5 non rileva un alimentatore da 5 V / 5 A, il firmware limita le porte USB a 600 mA (invece di 1.6 A), disattiva il boot da USB se non si preme il tasto di accensione e mostra un avviso di alimentazione limitata. Raspberry Pi ammette che con periferiche a basso consumo un alimentatore da 3 A può bastare. — [Raspberry Pi whitepaper "USB Power Delivery on Raspberry Pi 5" (RP-009856-WP)](https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-009856-WP-1-USB%20Power%20delivery%20on%20Raspberry%20Pi%205.pdf)
- **Override del limite USB.** Il flag `usb_max_current_enable=1` in config.txt porta il limite USB a 1.6 A. Il firmware lo imposta da solo quando negozia 5 V / 5 A via PD o quando nella EEPROM è impostato `PSU_MAX_CURRENT=5000`, e questo riabilita anche il boot da USB. È utile se il Pi 5 viene alimentato da un buck a bordo, che non fa negoziazione PD. — [stesso whitepaper](https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-009856-WP-1-USB%20Power%20delivery%20on%20Raspberry%20Pi%205.pdf)
- **Alimentatore ufficiale 27 W.** Fornisce fino a 5.1 V / 5 A; gli altri profili PD sono 9 V / 3 A, 12 V / 2.25 A e 15 V / 1.8 A. — [CanaKit, scheda prodotto](https://canakit.com/official-raspberry-pi-5-power-supply-27w-usb-c.html)
- **Pi 4.** L'alimentatore consigliato è 5.1 V / 3 A USB-C; i 5.1 V servono a compensare la caduta su cavo e connettore. — [raspberry.tips](https://raspberry.tips/en/raspberrypi-einsteiger/best-raspberry-pi-power-supply); [techsparx](https://techsparx.com/linux-sbc/raspberry-pi/pi4-usb-power-limit.html)
- **Soglia di sottotensione.** È circa 4.63 V. Sul Pi 4 il PMIC MxL7704 imposta un flag "sticky" quando l'ingresso scende sotto 4.63 V e il firmware mostra l'icona del fulmine; anche le schede più vecchie usavano la stessa soglia. La fonte è un forum ufficiale ma non la documentazione: da verificare. — [Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?p=1724251)
- Il codice di throttling nel log per la sottotensione è 0x50005. — [Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=270660)
- **Throttling.** Una guida di terze parti afferma che in sottotensione il Pi riduce il clock. Non l'ho verificato su fonte ufficiale. — [pimylifeup](https://pimylifeup.com/raspberry-pi-low-voltage-warning/)
- **Cavi.** Un cavo scadente può far arrivare 4.5 V alla scheda partendo da un alimentatore da 5 V. — [Seeed Studio blog 2025](https://www.seeedstudio.com/blog/2025/12/01/raspberry-pi-power-supply-guide/)
- **Alimentazione dal GPIO (pin 2/4 da 5 V).** È possibile alimentare il Pi così, con 5 V ±5%. In questo caso però si salta il polyfuse/ideal diode di ingresso, e una scheda che retro-alimenta il Pi deve avere un proprio diodo di protezione (o un meccanismo equivalente) nel caso siano presenti entrambe le alimentazioni. Il testo è ripreso dalla vecchia specifica HAT. — [Switch Science wiki (copia della spec HAT)](https://trac.switch-science.com/wiki/Raspberry-HAT); [AB Electronics forum](https://www.abelectronics.co.uk/forums/thread/153/back-powering-the-pi-itself)
- **HAT+.** La specifica HAT+ impone che le schede HAT+ siano compatibili con lo stato STANDBY (5 V presente, 3.3 V spento) su Pi 4/5. — [Raspberry Pi HAT+ specification](https://datasheets.raspberrypi.com/hat/hat-plus-specification.pdf)
- **HAT PoE per Pi 5.** Esistono solo HAT di terze parti:
  - Uctronics PoE+ (802.3af/at, 5 V / 4.5 A): circa 28 £. — [The Pi Hut](https://thepihut.com/products/uctronics-poe-hat-for-raspberry-pi-5-with-active-cooler-802-3af-at)
  - Waveshare PoE HAT (H), 5 V / 5 A. — [Core Electronics](https://core-electronics.com.au/waveshare-poe-hat-for-pi-5-h-variant.html.plain.md)
  - Waveshare PoE HAT (F), 5 V / 4.5 A più un'uscita a 12 V / 2 A per altri dispositivi: circa 19 £. — [The Pi Hut](https://thepihut.com/collections/raspberry-pi-power-supplies/products/poe-hat-for-raspberry-pi-5-with-cooling-fan)
  - Serve un PSE (switch o injector) da almeno 25 W. — [Core Electronics/Uctronics](https://core-electronics.com.au/uctronics-poe-hat-pi-5.html.plain.md)
- **CosmicWatch (MIT/UDel).** È alimentato via USB: assorbe 0.27 W e funziona da qualsiasi porta USB che dia più di 4.5 V. — [Axani et al., arXiv:1801.03029 / Am. J. Phys.](https://arxiv.org/pdf/1801.03029); [AAPT wiki](https://advlabs.aapt.org/wiki/Cosmic_Watch_Muon_Detectors)
- **CosmicWatch v3X (2025).** Ha connettività USB, memoria a bordo, OLED e sensori ambientali; tutto il dispositivo è autonomo e alimentato via USB. — [arXiv:2508.12111](https://arxiv.org/html/2508.12111v2)
- **Precedente con LT3461.** Un progetto DesignSpark di rivelatore a SiPM usa lo stesso schema della nostra scheda: 5 V USB elevati con un LT3461 a circa 30 V. — [RS DesignSpark](https://www.rs-online.com/designspark/building-a-cosmic-ray-detector-part-2-assembly-and-initial-testing)

### Inferences
- **Opzione A: USB-C PD 5 V / 5 A ufficiale, con il Pi a fare da "hub" di alimentazione.**
  - La scheda SiPM si alimenterebbe dai pin 5 V del GPIO del Pi. È la soluzione più economica (circa 12-14 € l'alimentatore) e gli alimentatori USB-C sono già familiari nelle scuole.
  - Contro: il 5 V del Pi è rumoroso (PMIC, carichi digitali, USB). L'LT3461 ha però un buon PSRR intrinseco a valle del regolatore lineare, e il carico è piccolo (100-200 mA).
  - Contro: se l'utente usa un caricatore USB-C qualunque, il Pi 5 resta a 3 A e possono comparire sottotensioni.
- **Opzione B: ingresso unico 12 V (jack 5.5/2.1 o morsetto), con a bordo una "power board"/HAT.**
  - Due buck sincroni: uno 5.1 V / 5 A per il Pi (alimentato via GPIO, con `PSU_MAX_CURRENT=5000`) e uno separato per la scheda SiPM, seguito da LC e LDO.
  - Pro: 12 V tollerano cadute sui cavi lunghi; il rumore digitale si separa alla sorgente; gli alimentatori 12 V CE sono economici. Con un ideal diode/eFuse diventa robusto a inversioni di polarità e hot-plug.
  - Contro: più componenti, e serve una progettazione EMC del buck.
  - È la scelta raccomandata per un prodotto "finito".
- **Opzione C: 24 V.** Non porta vantaggi a questa potenza (meno di 15 W) e restringe la scelta degli alimentatori. Può avere senso solo in ambienti industriali.
- **Opzione D: PoE+.** Un solo cavo per dati e alimentazione su fino a 100 m. Va bene per installazioni fisse (tetto, laboratorio), ma:
  - richiede uno switch/injector PoE+ (le scuole raramente li hanno in aula);
  - aggiunge un convertitore isolato rumoroso;
  - il Pi Zero 2 W non ha Ethernet.
  Da offrire come opzione, non come soluzione di base.
- Con il **Pi Zero 2 W** (consumo molto più basso) l'opzione A con un buon alimentatore micro-USB da 5 V / 2.5 A è sufficiente. Però è il Pi a WiFi che porta in gioco la RED (vedi §5).

### Gaps
- Documentazione ufficiale Raspberry Pi (raspberrypi.com/documentation, sezione "Power supply") non leggibile direttamente: ricontrollare i valori esatti (corrente minima per Zero 2 W, comportamento in sottotensione del Pi 5, alimentazione via GPIO sul Pi 5).
- Non ho trovato la soglia di sottotensione ufficiale per il Pi 5.

## 2. Sensibilità del guadagno SiPM a ripple/rumore di bias e temperatura; requisiti tipici

### Takeaway
Il guadagno dei SiPM è lineare con l'overvoltage (OV). A OV di circa 5.9 V (38.4 - 32.5 V), 1 mV di ripple vale circa 0.017% di guadagno e 10 mV circa 0.17%: per un contatore a soglia di muoni è trascurabile. Domina la temperatura: circa 30 mV/°C di Vbd (Broadcom NUV-MT), cioè circa 0.5%/°C di guadagno senza compensazione. La compensazione con diodo a circa 28 mV/°C è quindi la scelta giusta. I moduli commerciali dichiarano ripple di 0.1-0.2 mVpp, ma è un obiettivo da spettroscopia, non da conteggio.

### Cited Findings
- **Broadcom AFBR-S4N44P014M (stessa tecnologia NUV-MT, microcella da 40 µm, come la 22P014M).** Valori tipici a 12 V di OV e 25 °C:
  - Vbd 32-33 V;
  - coefficiente termico di Vbd 30 mV/°C;
  - guadagno 7.3×10⁶;
  - coefficiente termico del guadagno 1.46×10⁴ /°C (unità da verificare sul PDF).
  — [Datasheet AFBR-S4N44P014M (copia RS)](https://docs.rs-online.com/f847/A700000011180156.pdf); [Broadcom datasheet](https://docs.broadcom.com/doc/AFBR-S4N44P014M-NUV-MT-Silicon-Photomultiplier)
- **AFBR-S4N22P014M.** 2×2 mm, 2464 microcelle da 40 µm, picco a 420 nm, NUV-MT. I listini dei distributori non riportano Vbd né i coefficienti termici. — [Farnell listing](https://no.farnell.com/en-NO/broadcom/afbr-s4n22p014m/silicon-photomultiplier-1-ch-420nm/dp/4351470RL)
- **Application note Broadcom.** Vbd varia con la temperatura, quindi derive termiche esterne o variazioni del rate di conteggio cambiano la temperatura del dispositivo. L'esempio usa passi di 100 mV, che equivalgono a circa 3 °C. — [Broadcom AN300 "Single Photon Measurements"](https://docs.broadcom.com/doc/AFBR-S4NxxPyy4M-Single-Photon-Measurements); [Broadcom AN200 "Working with Broadcom SiPMs"](https://docs.broadcom.com/doc/AFBR-S4XX-Working-with-Broadcom-SiPMs)
- Una presentazione Broadcom definisce i 30 mV/°C un'approssimazione di primo ordine, che dipende dalla profondità della zona di valanga. — [Broadcom PSD13 SiPM overview](https://indico.global/event/1725/contributions/30518/attachments/15506/24700/Broadcom_PSD13_SiPM-Overview.pdf)
- Una caratterizzazione indipendente 2026 degli NUV-MT (AFBR-S4N66P014M, stessa microcella) conferma circa 30 mV/°C. — [arXiv:2608.19156](https://arxiv.org/pdf/2608.19156)
- **Hamamatsu MPPC.** Il guadagno è lineare in OV, con pendenze tra 5.6×10⁵ e 2.5×10⁶ per volt a seconda del dispositivo; il coefficiente di Vbd è 55-60 mV/°C. — [arXiv:1007.2712 (T2K MPPC)](https://arxiv.org/pdf/1007.2712); [arXiv:1606.03727](https://arxiv.org/pdf/1606.03727)
- Senza compensazione, la dipendenza di Vbd dalla temperatura dà una variazione di guadagno di circa 3%/°C (a circa 2 V di OV). Con un alimentatore compensato si scende da 2.8%/°C a 0.3%/°C. — [arXiv:1606.03727 "A novel analog power supply for gain control of the MPPC"](https://arxiv.org/pdf/1606.03727); [arXiv:1403.8104 "Gain stabilization of SiPMs"](https://arxiv.org/pdf/1403.8104)
- Un regolatore per CALICE puntava a una stabilità migliore di 5 mV, meno di 1 mV/°C, e a un guadagno costante entro l'1% su ±5 °C. — [Kvas, Argonne 2014](https://ilcagenda.linearcollider.org/event/6341/contributions/30068/attachments/24894/38393/Kvas-Argonne2014-v5.pdf)
- **Hamamatsu C11204-01.** Ripple 0.1 mVpp tipico e 0.2 mVpp massimo (72 V, senza carico, circuito raccomandato); stabilità ±10 ppm/°C; compensazione termica con sensore esterno. — [Hamamatsu C11204-01 datasheet](https://www.hamamatsu.com/resources/pdf/ssd/c11204-01_kacc1203e.pdf); [manuale](https://confluence.slac.stanford.edu/download/attachments/213887199/K29-B61072Ge_C11204-01MANUAL.pdf?api=v2)
- **CAEN A7585D.** Ripple inferiore a 0.1 mVpp tipico e 0.2 mVpp massimo, rumore inferiore a 300 µV rms, ingresso da 6 a 28 V (o USB nella variante DU), risoluzione di 1 mV. La tabella comparativa CAEN indica invece "< 0.2 mVpp" come tipico, quindi c'è un'incoerenza tra le fonti CAEN. — [CAEN A7585](https://www.caen.it/products/a7585/); [CAEN subfamily](https://caen.it/subfamilies/single-channel-85-v-10-ma-power-supply-module-for-sipm-with-uart-i2c-usb/)
- **Hamamatsu, moduli MPPC non raffreddati.** Usano circuiti di compensazione che aggiustano la tensione inversa al variare della temperatura ambiente. — [Hamamatsu MPPC modules](https://www.hamamatsu.com/resources/pdf/ssd/mppc_modules_kacc9019e.pdf)

### Inferences
- Il guadagno vale G ≈ k·OV, quindi ΔG/G = ΔV/OV. Con OV ≈ 38.4 - 32.5 = 5.9 V:
  - 1 mV corrisponde a 0.017%;
  - 10 mV corrispondono a 0.17%;
  - 1 °C non compensato (30 mV) corrisponde a circa 0.5% di guadagno.
  Anche la PDE dipende dall'OV, ma a circa 6 V è vicina al plateau, quindi è meno sensibile.
- **Escursione termica in aula.** Fra 15 e 30 °C, senza compensazione Vbd si sposta di circa 0.45 V, cioè circa il 7.6% di guadagno: sposta in modo apprezzabile l'efficienza a soglia fissa dei MAX961.
- **Compensazione a 28 mV/°C contro circa 30 mV/°C.** L'errore residuo è di circa 2 mV/°C, cioè circa 0.03%/°C: ottimo, purché il diodo sia termicamente accoppiato ai SiPM. Se il diodo sta sulla scheda e i SiPM sullo scintillatore, la compensazione segue la temperatura sbagliata.
- **Obiettivo realistico per il ripple** sul bias dopo l'LT1636: meno di 1 mVpp nella banda del segnale (fino a 10-100 MHz). È più che sufficiente per il conteggio a soglia. Più importante:
  - tenere bassi i transienti/spike di commutazione dell'LT3461 (circa 1.5 MHz) che si accoppiano capacitivamente sull'ingresso dei comparatori e generano falsi trigger;
  - garantire la stabilità a lungo termine (deriva in mV), verificabile con l'MCP3424.

### Gaps
- Non ho trovato una pendenza ufficiale guadagno-OV né la Vbd specifiche dell'AFBR-S4N22P014M: il PDF Broadcom non era raggiungibile. Il valore di circa 32.5 V va preso dal datasheet o dalla misura del lotto.
- Non ho trovato una specifica Hamamatsu o Broadcom esplicita di "ripple massimo ammissibile" per il bias.

## 3. Buone pratiche: boost + post-regolazione lineare vicino al front-end analogico, isolamento dal rumore del Pi

### Takeaway
Lo schema boost → filtro RC/LC → regolatore lineare → RC per canale, vicino al SiPM, è lo standard usato anche dai progetti accademici. Il Pi va tenuto su un ramo di alimentazione separato (o filtrato con ferrite + LC), con un ritorno di massa che non passa sotto il front-end.

### Cited Findings
- **LT3482 (alternativa all'LT3461).** Boost a frequenza fissa in current-mode pensato per il bias di APD, fino a 90 V. La frequenza fissa rende il rumore d'uscita prevedibile e facile da filtrare; la demo DC975A lavora a 1.1 MHz, programmabile a 650 kHz. — [Analog Devices LT3482](https://www.analog.com/en/products/lt3482.html)
- Un sistema di lettura SiPM universale per missioni X/γ usa l'LT3482: ripple simulato di qualche decina di µV a circa 83 V, con filtri RC aggiuntivi contro transienti di commutazione e ground bounce. — [arXiv:2501.07758](https://arxiv.org/pdf/2501.07758)
- **Usare un LDO come post-regolatore** offre più accuratezza e una risposta ai transitori migliore dei soli filtri passivi. Il PSRR dell'LDO peggiora al ridursi dell'headroom e all'aumentare della corrente: più headroom significa più PSRR ma più dissipazione. — [ADI, "Optimizing LDO headroom control"](https://www.analog.com/en/resources/technical-articles/optimizing-ldo-headroom-control-part-1.html)
- Una rete RC all'ingresso del regolatore lineare migliora il PSRR intrinseco, soprattutto alle alte frequenze. — [ADI, "Improved power-supply rejection for linear regulators"](https://wcm-cce.cldnet.analog.com/media/en/technical-documentation/tech-articles/improved-powersupply-rejection-for-linear-regulators.pdf)
- La resistenza serie del filtro di bias allunga i tempi di recupero, quindi va tenuta piccola se serve un recupero rapido. — [onsemi AND9782](https://www.mouser.lt/pdfDocs/AND9782-D.pdf)
- **Progetto open-source (Pomelo).** Boost poco regolato seguito da LDO ad alta tensione (LT3014B, ingresso fino a 80 V, meno di 10 µA di Iq) per SiPM Broadcom tra 32 e 48 V; il boost lavora in burst per ridurre il consumo. — [Hackaday.io Pomelo](https://hackaday.io/project/194457-pomelo-gamma-spectroscopy-module/log/229126-lower-power-sipm-bias-supply)

### Inferences
Raccomandazioni di progetto (dalla pratica comune; da validare con misure):
- **Ingresso 5 V della scheda SiPM.** Ferrite (600 Ω a 100 MHz, ≥1 A) + 10-22 µF ceramico + bulk 47-100 µF, così l'LT3461 non reinietta rumore a 1.3 MHz verso il Pi e viceversa. Meglio ancora un π-filter (C-L-C, 2.2-10 µH).
- **Uscita del boost (41.7 V).** RC (100 Ω-1 kΩ + 1-4.7 µF/100 V X7R) prima dell'LT1636. Il condensatore va scelto a 100 V per limitare la perdita di capacità con la tensione DC (DC-bias derating).
- **Regolatore per canale.** Headroom di circa 3 V (41.7 → 38.4): sufficiente, ma il PSRR dell'op-amp ad alta frequenza è limitato, quindi è necessario un RC finale sul pin catodo del SiPM: 1-10 kΩ + 100 nF, più 100 nF/10 nF vicino al SiPM per la carica del segnale.
- **Layout.** Separare fisicamente l'induttore e il nodo SW dell'LT3461 dai comparatori MAX961; usare un piano di massa continuo e un unico punto di ritorno verso il Pi (star/ground split a un solo ponte).
- **Comparatori.** Aggiungere un po' di isteresi ai MAX961 contro i retrigger.
- **Pi.** Collegare solo GPIO e I2C (con serie da 33-100 Ω sui GPIO) e la massa comune in un solo punto. Il Pi e il suo PSU sono la sorgente di rumore più forte: se si alimenta la scheda dal 5 V del Pi, aggiungere un LDO 5 V → 4.5 V (o un 3.3 V a basso rumore) per l'analogico.
- **Schermatura.** Un contenitore metallico, o una scatola plastica con vernice conduttiva / foglio di rame sull'area SiPM-comparatori e collegato a GND, aiuta sia contro i falsi conteggi sia in EMC immunità (RF irradiata, EN 61000-4-3).
- **Frequenza del boost.** Se possibile, sincronizzarla o spostarla fuori dalle bande sensibili, e verificare con oscilloscopio (sonda a molla di massa) il ripple sul catodo SiPM.

### Gaps
- Nessuna application note Broadcom specifica sul filtraggio del bias è stata letta per intero (fetch bloccato). La AN200 "Working with Broadcom SiPMs" riporta probabilmente un circuito di polarizzazione consigliato da verificare.

## 4. Protezioni: polarità inversa, TVS/ESD, sovracorrente/eFuse, inrush, brownout, spegnimento sicuro del Pi

### Takeaway
Sull'ingresso servono, in ordine, TVS, ideal diode o eFuse con blocco di inversione, limitazione di corrente/inrush, e un bulk capacitor. Sui connettori esterni (alimentazione e eventuali BNC/USB) servono diodi ESD. La protezione dalla corruzione della SD si ottiene nel modo più economico con rootfs read-only (overlayfs); un HAT a supercondensatori è un'aggiunta opzionale.

### Cited Findings
- **TI TPS25947 (eFuse).**
  - Lavora da 2.7 a 23 V e tollera fino a -15 V in ingresso: protezione da inversione integrata.
  - Comportamento da ideal diode (ORing lineare, corrente inversa quasi nulla), RON 28.3 mΩ.
  - Clamp di sovratensione selezionabile a 3.8, 5.7 o 13.8 V.
  - Limite di corrente regolabile da 0.5 a 6 A, carico fino a 5.5 A.
  — [TI TPS25947 datasheet SLVSFC9](https://www.ti.com/lit/pdf/slvsfc9); [TI product page](https://www.ti.com/product/de-de/TPS25947)
- **Alimentazione via GPIO.** Si salta il fusibile del Pi: un corto su un pin GPIO può danneggiarlo in modo permanente. Le guide di progetto HAT raccomandano fusibile e protezione dall'inversione di polarità sulla HAT che alimenta il Pi. — [AB Electronics forum](https://www.abelectronics.co.uk/forums/thread/153/back-powering-the-pi-itself); [JLCPCB HAT design guide 2026](https://jlcpcb.com/blog/how-to-design-raspberry-pi-hat)
- **Geekworm UPS Scap 5V5A per Pi 5 (ottobre 2026).**
  - Supercondensatori da 22, 60 o 100 F, chip PD che negozia 5 V / 5 A.
  - Il GPIO26 segnala la perdita di rete; sono forniti script di shutdown automatico e riaccensione.
  - Circa 47 $ (versione 100 F).
  — [CNX Software](https://www.cnx-software.com/2026/10/05/geekworm-ups-scap-5v5a-a-supercapacitor-ups-hat-for-raspberry-pi-5/); [Geekworm](https://geekworm.com/products/rpi5-ups-scap-pd5v5a)
- **Waveshare UPS HAT (B).** 2×18650, uscita 5 V fino a 5 A, compatibile Pi 5/4B, circa 23 $. — [Waveshare](https://www.waveshare.com/product/raspberry-pi/hats/interface-power/ups-hat-b.htm?sku=20568)
- **Waveshare UPS HAT (A).** 2.5 A continui, per Pi 4/3B+. — [Waveshare](https://www.waveshare.com/ups-hat.htm?sku=18306)
- **Autonomie stimate** (fonte generica): 10-30 minuti con 18650, meno di 60 secondi con supercondensatori. — [pidiylab](https://pidiylab.com/ups-hat-raspberry-pi/)

### Inferences
Catena d'ingresso consigliata (per l'ingresso a 12 V; per 5 V scalare):
1. **Connettore.** Jack DC bloccante o morsetto a vite. Evitare il header a 2 pin come ingresso esterno: è fragile e permette l'inversione.
2. **TVS.** SMBJ15A per un ingresso a 12 V, SMBJ5.0A per un ingresso a 5 V, verso massa. Copre surge e ESD condotte.
3. **Ideal diode / eFuse.**
   - Per 5 V: TPS25947 (gestisce insieme inversione, sovracorrente, sovratensione e inrush via dV/dt).
   - Per 12 V: in alternativa LM74700-Q1 + N-MOSFET, oppure un semplice P-MOSFET con gate a massa e zener gate-source (costo di qualche decina di centesimi). Il P-MOSFET non limita l'inrush.
4. **Sovracorrente.** Polyfuse (PTC) a valle come backup economico.
5. **ESD sui segnali esterni.** Diodi ESD (es. TPD1E10B06 o simili) su segnali che escono dal contenitore, per superare la IEC 61000-4-2 (richiesta dalle norme EMC di immunità: ±4 kV a contatto e ±8 kV in aria, da verificare sulla norma scelta).
6. **Brownout della scheda SiPM.** Il bias deve salire e scendere in modo controllato. Si può usare un pin di enable dell'LT3461 comandato da un GPIO o da un supervisore, così il bias si attiva solo a Pi avviato. La lettura via MCP3424 permette poi al software di invalidare i dati se il bias è fuori finestra.
7. **Spegnimento sicuro del Pi.**
   - La soluzione di base, a costo zero, è il rootfs read-only (overlayfs, attivabile con raspi-config), con i dati su una partizione separata in journaling o salvati a intervalli con fsync.
   - Il UPS a supercondensatori va considerato opzionale. C'è un report aneddotico secondo cui con Pi 5 i supercap non sempre funzionano ([Reddit, aneddotico](https://lr.us.psf.lt/r/cyberDeck/comments/1fron0d/battery_powered_pi_5/lpn0txk/?context=3)), quindi va testato.

### Gaps
- Prezzi correnti di TPS25947, LM74700 e SMBJ non trovati (vanno presi su Mouser/DigiKey). Come ordine di grandezza dalla mia esperienza: eFuse circa 1-2 €, TVS circa 0.2-0.4 €, P-MOSFET circa 0.2 € in piccoli lotti. Da verificare.
- Livelli precisi di prova ESD/surge nella EN IEC 61326-1: la norma è a pagamento e non è stata letta.

## 5. Percorso regolatorio UE per la vendita alle scuole (CE)

### Takeaway
Se il Pi integrato ha il WiFi/BT attivo, il prodotto finito cade sotto la RED 2014/53/EU, che assorbe EMC e sicurezza. Dal 1 agosto 2025 servono anche i requisiti di cybersecurity (EN 18031-1/-2/-3). Senza radio (o con radio disabilitata in modo permanente) si applicano EMC 2014/30/EU + RoHS, con la LVD esclusa perché si usa un alimentatore esterno a bassa tensione e i 41 V DC interni sono sotto i 75 V DC. La sicurezza resta comunque dovuta (GPSR / EN 62368-1 come riferimento). In Italia servono iscrizione al Registro AEE (RAEE) e marcatura con il bidone barrato. L'alimentatore CE e il Pi CE non rendono automaticamente conforme il prodotto: serve un fascicolo tecnico e una DoC propri.

### Cited Findings
- **LVD.** Si applica tra 50 e 1000 V AC e tra 75 e 1500 V DC (ingresso o uscita); gli adattatori/caricatori sono esplicitamente in scope. L'EMC è trattata separatamente dalla 2014/30/EU. — [TÜV SÜD LVD](https://www.tuvsud.com/en-ae/services/product-certification/ce-low-voltage-directive); [Emitech](https://www.emitech-group.com/en/your-needs/market-access-support/low-voltage-2014-35-ue-directive)
- Il fabbricante dell'apparecchio finale è responsabile che il prodotto finale soddisfi la direttiva EMC e porti la marcatura CE; un adattatore CE da solo non basta. Esempio di DoC: un dispositivo di rete con alimentatore cita EN IEC 62368-1 (LVD) e EN 55032/EN 55035 (EMC). — [Teltonika TSW100 CE](https://wiki.teltonika-networks.com/view/TSW100_CE); [Sentera LVD FAQ](https://www.sentera.eu/en/faq/g/how-does-the-low-voltage-directive-(lvd)-ensure-electrical-safety/1520)
- **EN IEC 61326-1.** Copre gli apparecchi elettrici di misura, controllo e laboratorio alimentati sotto 1000 V AC / 1500 V DC, includendo esplicitamente l'uso "educational". È generalmente considerata prevalente sulle norme EMC generiche. Prevede ambienti "basic", "industrial" e "controlled".
  - Per i sistemi con un PC integrato: dispositivi informatici già conformi alle norme EMC ITE possono essere usati in sistemi in scope 61326 senza test aggiuntivi, se adatti all'ambiente.
  — [DLS EMC, IEC/EN 61326-1](https://www.dlsemc.com/iec-en-61326-1); [BSI](https://knowledge.bsigroup.com/products/electrical-equipment-for-measurement-control-and-laboratory-use-emc-requirements-general-requirements-4)
- **EN 55032 vs EN 61326-1.** La EN 55032 riguarda soprattutto le emissioni RF di apparecchiature IT/multimediali/broadcast, mentre la 61326-1 copre gli strumenti di misura e laboratorio. — [JJR Lab](https://www.jjrlab.com/news/differences-between-en-55032-and-iec61326-1.html)
- **Raspberry Pi e moduli pre-certificati.** RPi fornisce DoC, test report e file grezzi (alcuni sotto NDA) e offre un servizio "Global Market Access" per i prodotti che integrano moduli RPi. Ribadisce però che i fabbricanti restano responsabili della conformità del prodotto finale, e presenta i propri core come "RED-compliant" per ridurre tempi e costi. — [RPi product compliance](https://www.raspberrypi.com/for-industry/compliance/); [RPi news, RED](https://www.raspberrypi.com/news/navigating-the-eus-new-radio-equipment-directive-how-raspberry-pi-provides-an-industrial-advantage/); [RPi Global Market Access PDF](https://pip-assets.raspberrypi.com/categories/1258-marketing-material/documents/RP-009232-MM-1-Raspberry%20Pi%20Global%20Market%20Access.pdf); [RPi Product Compliance PDF](https://pip-assets.raspberrypi.com/categories/1258-marketing-material/documents/RP-008737-MM-3-Raspberry%20Pi%20Product%20Compliance.pdf)
- **DoC UE Raspberry Pi 5.** Esiste ed è scaricabile; quella del CM5 elenca ETSI EN 300 328 V2.2.2 (2.4 GHz), EN 301 893 (5 GHz), EN 301 489-1 V2.2.3 e EN 301 489-17. — [Pi 5 EU DoC (Mouser)](https://www.mouser.com/catalog/additional/Raspberry_Pi_rpi_5_EU_Declaration_of_Conformity_DoC.pdf); [CM5 EU DoC](https://pip-assets.raspberrypi.com/categories/1102-approvals/documents/RP-007496-CF-2-rpi-cm5%20EU%20Declaration%20of%20Conformity%20(DoC).pdf)
- **RED cybersecurity.**
  - Il Regolamento delegato (UE) 2022/30, art. 3(3)(d)(e)(f), si applica dal 1 agosto 2025 (rinvio con il Reg. 2023/2444).
  - Norme armonizzate EN 18031-1 (rete), -2 (privacy/dati personali), -3 (frodi).
  - Con applicazione piena delle EN 18031 è possibile l'autodichiarazione (Modulo A). Se si applicano solo in parte, o certe opzioni (password, controllo parentale, aggiornamenti) restano scoperte, serve un Organismo Notificato.
  — [TÜV SÜD](https://www.tuvsud.com/en/knowledge-hub/technical-updates/consumer-products-and-retail-essentials/european-commission-to-extend-application-of-red-cybersecurity-requirements-to-1-august-2025); [Espressif guide](https://developer.espressif.com/blog/2025/04/esp32-red-da-en18031-compliance-guide/); [In Compliance Magazine](https://incompliancemag.com/reds-cybersecurity-requirements-update-en-18031-x2024/)
- La RED si applica a ciascun prodotto immesso sul mercato; integrare un modulo certificato non elimina gli obblighi RED del prodotto ospite. — [Johner Institute](https://blog.johner-institute.com/regulatory-affairs/radio-equipment-directive-red/)
- **Italia, RAEE.** In base al D.Lgs. 49/2014:
  - chi immette AEE con proprio marchio deve iscriversi al Registro nazionale produttori AEE prima di vendere, tramite la Camera di commercio, su registroaee.it (SPID/CNS);
  - deve scegliere un sistema collettivo o individuale di finanziamento dei RAEE;
  - deve riportare il numero di iscrizione nei documenti commerciali;
  - deve marcare il prodotto con il bidone barrato secondo la CEI EN 50419.
  Il DM 144/2024 integra il registro AEE nel Registro EPR.
  — [InformaImpresa (Unioncamere)](https://informaimpresa.it/item/adempimenti-per-i-produttori-di-apparecchiature-elettriche-ed-elettroniche); [Certifico](https://certifico.com/id/10687)
- **Costi di test EMC.**
  - Uso del laboratorio: 1500-2500 $ al giorno. Per un piccolo prodotto senza RF e con marcatura CE: 2-3 giorni di laboratorio + documentazione, cioè circa 3000-8000 $; sicurezza a parte, da circa 4500 $, in 3-4 settimane. — [electronics-lab forum](https://www.electronics-lab.com/forums/threads/emc-compliance-testing.27689/latest)
  - Stima Altium: circa 4500 $ per la parte CE EMC di un dispositivo semplice alimentato da rete; meno se senza porta AC. — [Altium](https://resources.altium.com/p/emc-certification-and-your-product)
  - Consulenza CE "a forfait": 3800 € per prodotto, test esclusi. — [EcoComply](https://ecocomply.ai/emc-compliance)
  - Pre-compliance aneddotica: circa 300 £ al giorno con un consulente che porta la strumentazione; mezza giornata in camera per test preliminari. — [EEVblog forum](https://www.eevblog.com/forum/beginners/emc-and-emi-certification-cost)

### Inferences
Percorso suggerito:
1. **Versione senza radio.**
   - Usare Pi 4/5 con WiFi/BT disabilitati via device-tree (`dtoverlay=disable-wifi`, `disable-bt`), oppure un modello senza radio come il CM senza wireless.
   - Le direttive diventano EMC + RoHS (+ RAEE). Si applica la EN IEC 61326-1 (ambiente "basic" per le scuole), che vale sia per le emissioni (classe B) sia per l'immunità (ESD, RF irradiata, EFT/surge sulla porta DC se il cavo supera i 3 m).
   - La sicurezza si gestisce con l'alimentatore esterno CE/LVD (es. Mean Well GST, con EN 62368-1 e protezioni) più un'analisi dei rischi del prodotto. La 41 V DC interna è sotto la soglia LVD e sotto il limite ES1/SELV, ma va documentata.
   - Attenzione: disabilitare la radio solo via software potrebbe non bastare per escludere la RED se l'utente può riattivarla. Molti scelgono di dichiarare comunque la RED. È una questione da chiarire con un laboratorio o un consulente.
2. **Versione con WiFi.**
   - DoC sotto la RED: art. 3.1(a) sicurezza con EN 62368-1; art. 3.1(b) EMC con EN 301 489-1/-17 + EN 61326-1; art. 3.2 radio, riusando i report RPi per EN 300 328/301 893 se l'antenna e l'integrazione sono invariate; art. 3.3(d) cyber con EN 18031-1.
   - Prevedere: niente password di default, aggiornamenti sicuri, servizi di rete minimi.
3. **Costi indicativi.**
   - Pre-compliance (mezza o una giornata con LISN + antenna, o un laboratorio locale): 500-1500 €.
   - EMC piena in laboratorio accreditato: 3000-8000 €. La RED con cyber aggiunge costi.
   - Tempi: 3-6 settimane più eventuali iterazioni.
   - Il rischio maggiore di non conformità sono le emissioni irradiate del Pi (clock, HDMI, USB) e del boost, e l'ESD/immunità RF (falsi conteggi). Pianificare scatola, ferriti sui cavi e filtri.

### Gaps
- Non ho letto direttamente i testi EUR-Lex delle direttive né l'elenco OJEU aggiornato delle norme armonizzate (edizioni EN IEC 61326-1:2021 ecc.).
- Non ho trovato prezzi EUR ufficiali per pre-compliance in laboratori italiani: chiedere preventivi.
- Non è stato verificato se la RPi DoC copra già le EN 18031 per Pi 5 / Zero 2 W.
- Non ho approfondito il GPSR (Reg. UE 2023/988) né l'eventuale classificazione come "giocattolo" (esclusa se il prodotto è destinato a uso didattico sotto supervisione, da verificare).

## 6. Componenti consigliati e costi indicativi (EUR)

### Takeaway
Il BOM di alimentazione e protezione aggiunto vale circa 15-30 € per unità, alimentatore da muro incluso. L'alimentatore 12 V Mean Well costa circa 12 €, l'alimentatore ufficiale RPi 27 W circa 12-14 €.

### Cited Findings
- Mean Well GST25E12-P1J (12 V, 2.08 A, 25 W, spina EU): 12.81 € IVA esclusa, 12.04 € da 20 pezzi. — [Alimentatorishop](https://www.alimentatorishop.com/en/external-power-supplies/gst25e12-p1j-meanwell-power-supply-wallmount-25w-12v-input-100-240-vac); [RS UK £13.41](https://uk.rs-online.com/web/p/ac-dc-adapters/1176178)
- Raspberry Pi 27 W USB-C (SC1157, EU): 13.95 € IVA inclusa (11.53 € esclusa) presso un rivenditore NL, 8.63 € presso Novapart. Una pagina Waveshare mostra circa 6 €: è sospetto, va verificato. — [Elektronicavoorjou](https://elektronicavoorjou.nl/en/product/raspberry-pi-27w-usb-c-voeding-zwart/); [Novapart](https://novapart.co/products/SC1157/power-supply-usb-c-51-v-5-a-black-eu-plug/)
- HAT PoE+ per Pi 5: circa 19-29 £. UPS HAT: circa 22-23 $. UPS a supercondensatori: circa 47 $. — vedi fonti in §1 e §4.
- Moduli di bias commerciali di riferimento (CAEN A7585D, Hamamatsu C11204-01): prestazioni da spettroscopia (0.1-0.2 mVpp), ma costo molto superiore (prezzo non trovato), non giustificato per un contatore di muoni. — [CAEN](https://www.caen.it/products/a7585/); [Hamamatsu](https://www.hamamatsu.com/resources/pdf/ssd/c11204-01_kacc1203e.pdf)

### Inferences
BOM di alimentazione consigliato, opzione B a 12 V (prezzi stimati da me, da verificare sui distributori):

| Funzione | Parte suggerita | € indicativi (qty 100) |
|---|---|---|
| Alimentatore da muro | Mean Well GST25E12-P1J (CE, EN 62368-1) | ~12 |
| Connettore | Jack DC 5.5/2.1 da pannello | ~0.5-1 |
| TVS | SMBJ15A | ~0.2 |
| Inversione / inrush | LM74700 + N-FET oppure P-FET + zener | ~0.3-1.5 |
| Fusibile | PTC 2-3 A | ~0.2 |
| Buck 5.1 V / 5 A per il Pi | TPS56637 / TPS54560 / MP2338 (o modulo) | ~2-4 |
| Buck/LDO per l'analogico | Piccolo buck 5 V → 5 V/0.5 A + ferrite + LDO a basso rumore (es. TPS7A20 / LT3042 se serve) | ~1-4 |
| Filtri | Ferriti 0805, induttori 4.7-10 µH, MLCC 100 V | ~1 |
| Protezione ESD sui segnali esterni | TPD1E10B06 o simili | ~0.2 ciascuno |
| Opzionale: UPS | Geekworm UPS Scap o rootfs read-only | 0-45 |

- In alternativa, l'opzione A (USB-C PD 27 W ufficiale + filtro π e TVS sulla scheda SiPM) costa circa 14 € in tutto, ma dipende dal fatto che il cliente usi l'alimentatore giusto.

### Gaps
- Non ho prezzi verificati per eFuse, buck, LDO e TVS in EUR (fetch dei distributori non disponibile): tutti i prezzi in tabella sono stime da verificare su Mouser/DigiKey/Farnell.
