# Gestione flotta Raspberry Pi per rivelatori nelle scuole: OTA, accesso remoto, monitoraggio, affidabilità storage

Scope: ~10-100 unità Raspberry Pi in scuole italiane, Wi-Fi scolastico dietro NAT/firewall, servizio DAQ (GPIO interrupt + ADC I2C), buffer locale e upload verso server centrale. Ricerca svolta il 2026-10-09.

Nota metodologica: in questa sessione il fetch diretto delle pagine (WebFetch) non funzionava (errore DNS), quindi tutti i dati vengono da risultati di ricerca web che riassumono le pagine indicate. I prezzi vanno ricontrollati sulle pagine ufficiali prima di fare il budget. Le affermazioni senza fonte trovata sono nelle sezioni Inferences o Gaps.

## 1. Sistemi di aggiornamento OTA (Mender, balena, RAUC, SWUpdate, soluzioni Raspberry Pi, apt/Ansible)

### Takeaway
Per ~100 Pi su Raspberry Pi OS ci sono due strade realistiche. (a) Aggiornamenti a pacchetti: un repository apt firmato più un timer pull, con il rootfs reso robusto in altro modo. È il metodo usato da MuonPi, semplice ma senza rollback atomico. (b) A/B atomico: Mender (mender-convert su Raspberry Pi OS, hosted Basic ~34 $/mese ogni 50 dispositivi), oppure il nuovo "Remote Update" di Raspberry Pi Connect, nativo tryboot ma ancora sperimentale (marzo 2026). balenaCloud è il più "chiavi in mano" ma il più costoso (~329 $/mese per il piano Pilot). RAUC e SWUpdate sono solidi ma richiedono di costruirsi immagine e server (Yocto + hawkBit/qbee).

### Cited Findings
**Mender (Northern.tech)**
- Piani hosted a scaglioni fissi, non per singolo dispositivo: Basic 34 $/mese fino a 50 dispositivi; Professional 291 $/mese fino a 250 dispositivi, che aggiunge delta update robusti, deployment pianificati e retry automatici — [Mender plans](https://mender.io/pricing/plans)
- Add-on: Monitor 93 $/mese (fino a 250 dispositivi); Configure 11 $/mese (50 disp.) o 70 $/mese (250 disp.) — [Monitor add-on](https://mender.io/pricing/add-ons/monitor); [Configure add-on](https://mender.io/pricing/add-ons/configure)
- Le cifre sono in conflitto: un post del blog Mender (circa metà 2026) riporta "Starter" a 29 $/mese per 50 dispositivi e Professional a 249 $/mese per 250 — [Mender blog](https://mender.io/blog/the-simplicity-of-menders-pricing-approach); contraddetto dalla pagina piani attuale (34/291 $) — [Mender plans](https://mender.io/pricing/plans). Un listing di terzi indica minimo 50 dispositivi a incrementi di 50 — [FitGap](https://us.fitgap.com/products/014841/mender)
- Per flotte più grandi: contattare le vendite; il calcolatore distingue dispositivi "Micro" (MCU) e "Standard" — [Mender price calculator](https://mender.io/pricing/price-calculator)
- Client open source (Apache 2.0) — [GitHub mendersoftware/mender](https://github.com/mendersoftware/mender)
- Mender richiede un "commit" dopo il primo boot di un aggiornamento riuscito, altrimenti al reboot successivo torna alla partizione precedente. Il delta (xdelta) è solo nei tier commerciali. Mender ha un server di gestione integrato, RAUC no (serve hawkBit, qbee.io ecc.) — [32blog comparison](https://32blog.com/en/yocto/yocto-ota-update-comparison); [Rugix: OTA engines compared (2026)](https://rugix.org/blog/2026-02-28-ota-update-engines-compared/)
- La tabella FOSDEM 2025 (Leon Anavi) indica A/B update e rollback "Yes" per Mender, RAUC e SWUpdate — [FOSDEM 2025 slides](https://archive.fosdem.org/2025/events/attachments/fosdem-2025-6299-exploring-open-source-dual-a-b-update-solutions-for-embedded-linux/slides/237879/leon-anav_pyytRpX.pdf)

**RAUC / SWUpdate / Rugix**
- RAUC e SWUpdate supportano anche layout asimmetrici (recovery) e hook/handler estensibili; RAUC ha l'impronta più piccola e il diff a blocchi ("adaptive updates") — [Rugix blog](https://rugix.org/blog/2026-02-28-ota-update-engines-compared/); [32blog](https://32blog.com/en/yocto/yocto-ota-update-comparison)
- Secondo Rugix (fonte di parte, è un vendor concorrente), Rugix Ctrl è l'unico di questi strumenti a supportare il meccanismo tryboot di Raspberry Pi, cioè il modo ufficiale di fare A/B su hardware Pi. Gli altri tipicamente passano per U-Boot — [Rugix blog](https://rugix.org/blog/2026-02-28-ota-update-engines-compared/)
- Una serie di Interelectronix su CM5 usa rpi-image-gen, un layout rootfs A/B e SWUpdate per l'OTA (blog di terzi, non un'architettura ufficiale) — [Interelectronix CM5 production Linux](https://www.interelectronix.com/building-production-ready-linux-raspberry-pi-compute-module-5.html)

**balenaCloud / openBalena**
- Primi 10 dispositivi gratuiti. Prototype 159 $/mese (30 disp. inclusi, extra 3 $/disp./mese, 1 utente); Pilot 329 $/mese (50–999 disp., 60 inclusi, extra 2 $/disp./mese, 3 utenti); Production 1.439 $/mese (110 inclusi). Annuale: Prototype 1.720 $/anno, Pilot 3.588 $/anno, Production 15.588 $/anno — [balena pricing](https://www.balena.io/pricing)
- In conflitto: una versione cache della pagina indica Prototype 109 $/mese con 20 dispositivi; altri aggregatori riportano Production a 1.299 $/mese — [static.balena.io/pricing](https://static.balena.io/pricing/); [Listicler](https://listicler.com/tools/balenacloud)

**Raspberry Pi (tryboot, rpi-image-gen, Connect Remote Update, rpi-sb-provisioner)**
- Tryboot: `autoboot.txt` con sezione `[all]` (`tryboot_a_b=1`, `boot_partition=`) e sezione `[tryboot]`. Un servizio di update avvia la nuova partizione in modalità tryboot; se l'health check va bene scambia le partizioni, altrimenti al reboot normale il flag tryboot si azzera e si torna alla partizione originale. `autoboot.txt` è limitato a 512 byte — [config.txt docs](https://www.raspberrypi.com/documentation/computers/config_txt.html); [autoboot.adoc](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/computers/config_txt/autoboot.adoc)
- Raspberry Pi Connect "Remote updates" annunciato circa a marzo 2026, ancora **sperimentale**. Due tipi di artefatto: script (creati con `otamaker`, per manutenzione tipo upgrade pacchetti) e A/B boot update (creati con rpi-image-gen, sostituiscono l'intero OS e tornano indietro automaticamente se l'update fallisce). L'A/B richiede di flashare prima il dispositivo con un layout A/B, che le immagini standard non hanno. Si abilita con `rpi-connect ota on` (pacchetti `rpi-connect`, `rpi-connect-ota`) — [RPi news: remote updates](https://www.raspberrypi.com/news/new-remote-updates-on-raspberry-pi-connect/); [Connect docs](https://raspberrypi.com/documentation/services/connect.html); [otamaker](https://github.com/raspberrypi/utils/tree/master/otamaker)
- L'esempio `rpi-image-gen/examples/ota` installa un OS minimo Trixie con Connect Lite e la funzione OTA sperimentale; il default è rpi5, sul Pi 4 va sovrascritto il device layer — [rpi-image-gen examples/ota](https://github.com/raspberrypi/rpi-image-gen/tree/master/examples/ota)
- Problemi segnalati: errore "Failed to open target 'system'" con OTA su sistemi A/B — [rpi-image-gen issue #225](https://github.com/raspberrypi/rpi-image-gen/issues/225); [forum walkthrough](https://forums.raspberrypi.com/viewtopic.php?t=395798)
- rpi-sb-provisioner: provisioning automatico per secure boot e primo boot; dalla v2.3.x accetta artefatti rpi-image-gen (IDP) — [rpi-sb-provisioner](https://github.com/raspberrypi/rpi-sb-provisioner); [releases](https://github.com/raspberrypi/rpi-sb-provisioner/releases)

**Pacchetti Debian via apt (caso MuonPi)**
- MuonPi distribuisce il daemon come `.deb` (es. `muondetector-daemon-2.1.1-raspbian.deb`) tramite un proprio repository apt; il wiki di installazione è dell'era Buster — [MuonPi releases](https://github.com/MuonPi/muondetector/releases); [MuonPi wiki: Raspberry Pi Setup](https://wiki.muonpi.org/index.php?title=Raspberry_Pi_Setup)

### Inferences
- Con 100 dispositivi i costi indicativi per l'OTA sono: Mender Basic ≈ 2 × 34 $ = 68 $/mese (~820 $/anno) se gli scaglioni da 50 si sommano, oppure Professional 291 $/mese (~3.500 $/anno) per i delta; balena Pilot ≈ 329 $ + 40×2 $ = ~409 $/mese (~4.900 $/anno); Raspberry Pi Connect per organizzazioni 0,50 $/disp./mese = ~50 $/mese (~600 $/anno), che include anche shell remota e OTA sperimentale (vedi §2); apt + Ansible/timer ≈ 0 € di licenze, solo un VPS. Sono calcoli miei.
- Il carico DAQ (un solo servizio applicativo) rende ragionevole un approccio ibrido: rootfs stabile e raramente aggiornato (A/B o reflash), mentre il software applicativo passa come `.deb` firmato da un repo apt proprio, con un timer `apt-get install --only-upgrade` e rollout scaglionato (canary su 2-3 scuole). Un Ansible in modalità pull (`ansible-pull`) può gestire la configurazione. Non ho trovato fonti dirette per ansible-pull su flotte Pi.
- Raspberry Pi Connect Remote Update è la via più "nativa" (tryboot) ed economica, ma essendo sperimentale e con bug aperti va valutato con un pilota prima di affidargli 100 unità.

### Gaps
- Non ho potuto verificare direttamente la documentazione di mender-convert né il supporto attuale di Raspberry Pi 5/tryboot in Mender e meta-rauc-community (i fetch erano bloccati).
- Non ho trovato dati di banda per update (dimensione tipica di un artefatto A/B rootfs vs delta). Su Raspberry Pi OS Lite un rootfs compresso pesa probabilmente qualche centinaio di MB: è una stima, non sourced.
- Non ho trovato in questa sessione la residenza dei dati in UE di Mender hosted (Northern.tech è norvegese; esiste un'istanza "eu.hosted.mender.io" secondo conoscenza pregressa, non verificata).

## 2. Accesso remoto dietro NAT/firewall scolastici

### Takeaway
Tailscale (o Headscale self-hosted in UE) è il più robusto nelle reti restrittive, perché ripiega su relay DERP via HTTPS/TCP 443. Raspberry Pi Connect offre una shell remota ufficiale a 0,50 $/dispositivo/mese per le organizzazioni. ZeroTier gratuito è limitato a 10 dispositivi. Un hub WireGuard puro richiede UDP in uscita, che le scuole spesso bloccano.

### Cited Findings
- Tailscale: DERP è il relay di fallback che inoltra pacchetti WireGuard cifrati via HTTPS quando il percorso diretto fallisce; la causa principale delle connessioni relayed è l'UDP bloccato — [Tailscale connection types](https://tailscale.com/docs/reference/connection-types); [Tailscale NAT traversal pt.1](https://tailscale.com/blog/nat-traversal-improvements-pt-1); [Relay server unavailable](https://tailscale.com/docs/reference/messages/client/no-derp-connection)
- Porte: TCP 443 (coordinamento + DERP), UDP 3478 (STUN), UDP 41641 opzionale per connessioni dirette; con solo TCP 443 aperta funziona via DERP, con latenza più alta — [SSD Nodes: relay vs direct](https://www.ssdnodes.com/learn/tailscale-slow-direct-vs-relayed); [SitePoint: Peer Relays](https://www.sitepoint.com/tailscale-peer-relays-nat-traversal-derp/)
- Prezzi Tailscale: il piano Personal è gratuito, con dispositivi utente illimitati, fino a 6 utenti e fino a 50 "tagged resources". I dispositivi posseduti da un tag (server/IoT) contano come risorse taggate — [Tailscale pricing](https://tailscale.com/pricing/); [Pricing FAQ](https://tailscale.com/kb/1251/pricing-faq). Fonti terze indicano che il Personal è per uso non commerciale — [freetier.co](https://freetier.co/directory/products/tailscale)
- Headscale: implementazione open source self-hosted del server di controllo Tailscale, con server DERP embedded (disabilitato di default; richiede UDP 3478 e la configurazione degli IP pubblici). Di default usa i DERP pubblici di Tailscale; abilitando il proprio si elimina l'ultima dipendenza esterna — [Headscale DERP docs](https://headscale.net/stable/ref/derp/); [bitdoze guide](https://www.bitdoze.com/headscale-self-hosted-tailscale-setup/)
- Il self-hosting del derper richiede TCP 80/443 e UDP 3478 — [hub.docker derper](https://hub.docker.com/r/camllia/derper)
- NetBird (azienda tedesca, mesh WireGuard): la Community Edition self-hosted è gratuita, senza limiti di utenti o dispositivi; Commercial Starter a 2.000 €/anno (50 utenti, 500 dispositivi) secondo un rivenditore; esiste hosting gestito in Germania da ~99,90 €/mese — [WZ-IT NetBird licence 2026](https://wz-it.com/en/blog/netbird-self-hosting-license-commercial-starter/); [birdhost](https://birdhost.de/en); [Infralovers: NetBird EU](https://www.infralovers.com/blog/2026-05-13-netbird-eu-zero-trust-vpn/)
- ZeroTier: Personal gratuito con 10 dispositivi, 1 rete, uso non commerciale. Essential 18 $/mese (10 disp., +2 $/disp.); Scale 179 $/mese (100 disp., +1,80 $/disp.); pagina in vigore dal 4 ago 2026 — [ZeroTier pricing](https://www.zerotier.com/pricing.md); [docs pricing](https://docs.zerotier.com/pricing)
- Raspberry Pi Connect: gratuito per uso personale (dispositivi illimitati, screen sharing, remote shell, remote update). Per le organizzazioni costa 0,50 $/dispositivo/mese con utenti illimitati, fatturato sul numero massimo di dispositivi registrati nel mese, e aggiunge ricerca/filtri, tag, provisioning in massa, API di gestione e audit log. Il traffico relay al momento non si paga — [Connect for organisations](https://www.raspberrypi.com/news/raspberry-pi-connect-for-organisations-plus-full-screen-support/); [Connect product page](https://www.raspberrypi.com/connect/)
- Connect ha una console remota "SSH-like" ed è supportato su tutti i modelli — [Hackster](https://hackster.io/news/raspberry-pi-connect-gets-an-ssh-like-remote-console-expands-support-to-all-models-4f1b607d3fb7)

### Inferences
- In reti scolastiche dove spesso è aperto solo 80/443 TCP (tipico con firewall ministeriali o dei provider), le soluzioni con fallback HTTPS (Tailscale/Headscale via DERP, Raspberry Pi Connect, balena, Mender Remote Terminal via websocket) sono più affidabili di WireGuard puro (solo UDP) e di OpenVPN UDP. autossh reverse su porta 443 funziona ma è più fragile da gestire per 100 unità.
- Per 100 Pi su Tailscale servirebbe un piano a pagamento (il gratuito è limitato a 50 risorse taggate ed è non commerciale). Headscale + DERP embedded su un VPS UE (~5-10 €/mese) costa meno e dà residenza dei dati in UE, al prezzo di dover gestire l'operatività.
- Ridondanza consigliata: due canali indipendenti, per esempio Headscale/Tailscale più Raspberry Pi Connect (0,50 $/disp.), così un errore di configurazione di un VPN non rende irraggiungibile la flotta.

### Gaps
- Non ho trovato i prezzi correnti di Tailscale per piano (Starter/Premium per utente, costo per risorsa taggata extra): la pagina non era consultabile direttamente.
- Non ho trovato in questa sessione indicazioni sulla localizzazione UE dei relay di Raspberry Pi Connect né su DPA/GDPR (Raspberry Pi Ltd è nel Regno Unito).
- Nessun dato empirico specifico su quali porte siano aperte nelle reti scolastiche italiane (GARR, reti comunali/provinciali): andrebbe verificato con 2-3 scuole pilota (`tailscale netcheck`).

## 3. Affidabilità dello storage (SD, overlayfs, eMMC, SSD)

### Takeaway
Non ho trovato studi peer-reviewed sui tassi di guasto delle SD nei Pi sul campo; l'evidenza è aneddotica e da test di stress. Le mitigazioni consolidate sono: root in sola lettura con overlay in RAM, dati su una partizione separata, riduzione delle scritture (log in RAM), SD industriali pSLC oppure eMMC (CM4/CM5) o NVMe (Pi 5). La corruzione da perdita di alimentazione nasce soprattutto dalle scritture in cache non ancora completate, non dalla usura.

### Cited Findings
- Causa principale della corruzione alla perdita di alimentazione: le grandi quantità di modifiche al filesystem in cache non ancora scritte, oltre al singolo blocco interrotto — [RPi forum: overlay required?](https://forums.raspberrypi.com/viewtopic.php?t=361461)
- Overlay read-only: la SD è montata in sola lettura e le modifiche vanno in un overlay in RAM, quindi si può spegnere in qualsiasi momento; le modifiche si perdono al reboot, perciò i dati vanno su una partizione o un dispositivo separato in lettura-scrittura (non protetto) — [Core Electronics: Read-Only Raspberry Pi](https://core-electronics.com.au/guides/read-only-raspberry-pi/); [raspi-overlayroot wiki](https://github.com/nils-werner/raspi-overlayroot/wiki); [RPi forum t=294427](https://forums.raspberrypi.com/viewtopic.php?t=294427)
- Un utente con molti Pi sul campo riporta guasti SD "troppo frequenti" anche con root read-only e overlay RAM, e sospetta problemi di segnale del bus al reboot piuttosto che usura — [RPi forum: SD card power failure resilience](https://forums.raspberrypi.com/viewtopic.php?t=253104)
- Test di stress indipendente (133 PB scritti, 351 schede, 3 anni): SanDisk High Endurance 6 guasti su 7 testate; Kingston Industrial 2 guasti su 3, media ~77 giorni e ~141.600 cicli di scrittura completa sotto test continuo — [Tom's Hardware](https://www.tomshardware.com/pc-components/microsd-cards/microsd-card-testing-database-celebrates-third-anniversary-with-133-petabytes-of-data-written-across-4-6-million-cycles-hundreds-of-cards-tested-to-failure-reveal-sandisk-as-the-outlier-with-6-failures-of-the-7-tested)
- Kingston Industrial microSD: pSLC su TLC, fino a 3.840 TBW (dato del vendor), 30K cicli P/E, -40…85 °C — [Kingston datasheet](https://www.kingston.com/datasheets/sdcit2_en.pdf); [Kingston product page](https://www.kingston.com/en/memory-cards/industrial-grade-microsd-uhs-i-u3)
- ATP: una scheda consumer può bastare se resta tra 0 e 70 °C, scrive poco, l'alimentazione è protetta a livello di sistema e la scheda è facile da sostituire; altrimenti servono schede industriali — [ATP: industrial SD factors](https://www.atpinc.com/blog/industrial-sd-cards-factors-requirements-to-consider)
- Le schede muoiono anche con poche scritture per guasto improvviso del controller: conviene ridurre le scritture (log in RAM, root read-only) e prevedere il guasto con backup — [Philosopher's Stone](https://philosophersstone.ee/knowledge/microsd-buying-why-brand-reliability-data-has-limited-predictive-power)
- eMMC contro SD: secondo HiFiBerry l'eMMC ha controller migliori ed è più affidabile, e le scritture si riducono molto con log in RAM e FS read-only; altri ricordano che usa NAND simile e che un'eMMC usurata impone di sostituire tutto il modulo — [HiFiBerry storage comparison](https://www.hifiberry.com/blog/sd-card-vs-usb3-vs-emmc-vs-nvme/); [ClockworkPi forum](https://forum.clockworkpi.com/t/uconsole-cm5-to-emmc-or-not-to-emmc/17969); [Bambu forum](https://forum.bambulab.com/t/microsd-emmc-nand-storage-adapter/166757)
- La cifra "500–2000 TBW per l'eMMC del CM5" pubblicata da un blog di rivenditore è senza fonte primaria e non va usata — [Industrial Monitor Direct](https://industrialmonitordirect.com/blogs/knowledgebase/raspberry-pi-cm5-emmc-vs-pi5-nvme-storage-durability)
- Un blog sostiene che le SD consumer si guastano in genere dopo 6–24 mesi di logging continuo; è un dato non verificato — [Industrial Monitor Direct: edge failures](https://industrialmonitordirect.com/blogs/knowledgebase/raspberry-pi-edge-deployment-failures-root-causes-and-solutions)

### Inferences
- Layout consigliato: partizioni boot e rootfs A/B in sola lettura (o overlayfs via `raspi-config` → Performance → Overlay File System); una partizione `/data` ext4 con `data=journal` o f2fs per il buffer DAQ, scritta a blocchi (es. file orari con fsync) invece di molte scritture piccole; journald in modalità volatile o con log2ram e invio remoto dei log. Le opzioni raspi-config e log2ram vengono da conoscenza pregressa, non da fonti verificate in questa sessione.
- Con un buffer DAQ di pochi MB/giorno l'usura non è il problema principale; lo sono la perdita di alimentazione (scuole che staccano la corrente nei weekend o d'estate) e i guasti del controller. Per questo il root read-only conta più del tipo di scheda, e una scheda industriale pSLC (~15-30 €) è un'assicurazione economica.
- Il CM4/CM5 con eMMC elimina il problema "teacher removes/reseats SD" e i contatti ossidati, ma richiede una carrier board.

### Gaps
- Nessuno studio accademico o case study pubblico trovato con tassi di guasto SD su flotte di Pi (HiSPARC, Cosmic Pi: non trovato materiale sulle stazioni in questa sessione).
- Non ho trovato confronti misurati ext4 contro f2fs per resilienza alla perdita di alimentazione su Pi.
- Non ho trovato la specifica TBW ufficiale dell'eMMC del CM4/CM5.

## 4. Watchdog, recupero automatico, monitoraggio e log remoti

### Takeaway
Il watchdog hardware del SoC (bcm2835_wdt) si gestisce da systemd con `RuntimeWatchdogSec` (≤15 s). Per la telemetria, Grafana Alloy (o node_exporter) con push via `remote_write` verso Grafana Cloud (gratuito fino a 10k serie attive) o verso un Prometheus/VictoriaMetrics self-hosted è la soluzione standard e funziona dietro NAT, perché la connessione è solo in uscita.

### Cited Findings
- Configurazione watchdog: `dtparam=watchdog=on` in config.txt, modulo `bcm2835_wdt` (heartbeat ~14), `RuntimeWatchdogSec=14` in `/etc/systemd/system.conf`; il log mostra "Set hardware watchdog to 10s" — [RPi forum t=258042](https://forums.raspberrypi.com/viewtopic.php?t=258042); [RPi forum t=210974](https://forums.raspberrypi.com/viewtopic.php?t=210974)
- Il timer hardware arriva al massimo a circa 15 s, quindi `RuntimeWatchdogSec` deve essere ≤ 15. Un solo processo può tenere `/dev/watchdog`: se si usa il demone `watchdog`, il valore di systemd va messo a 0 — [RPi forum t=254539](https://forums.raspberrypi.com/viewtopic.php?t=254539); [bends.se HW watchdog](https://bends.se/?page=notebook%2Fsbc%2Fraspberry-pi%2Fhw-watchdog)
- Grafana Cloud free: 10.000 serie metriche attive con retention di 14 giorni, 50 GB/mese di log, 3 utenti; Pro da 19 $/mese più 6,50 $ ogni 1.000 serie — [Grafana tweet](https://x.com/grafana/status/1924516350409752631); [monitoringcost](https://monitoringcost.com/grafana-cloud-pricing)
- Attenzione: le "billable series" possono superare le serie attive (un utente con ~26k billable contro un limite di 10k) — [GitHub issue lentago/drosera#239](https://github.com/lentago/drosera/issues/239)
- Integrazione ufficiale Raspberry Pi di Grafana Cloud: `prometheus.exporter.unix` + relabel `instance=hostname` + `prometheus.remote_write` — [Grafana RPi integration](https://grafana.com/docs/grafana-cloud/monitor-infrastructure/integrations/integration-reference/integration-raspberry-pi-node/)
- Alloy può caricare la configurazione da una sorgente remota HTTP con polling, il che permette di cambiare centralmente la config della flotta — [Alloy remote configuration](https://grafana.com/docs/alloy/latest/configure/load-remote-configuration/)
- `prometheus.remote_write` invia a qualsiasi endpoint compatibile (Mimir, Prometheus con receiver abilitato) — [Alloy: send metrics to Prometheus](https://grafana.com/docs/alloy/latest/tutorials/send-metrics-to-prometheus/)
- MuonPi: il daemon sincronizza i dati con il server centrale via MQTT; la release v2.1.1 ha corretto la riconnessione al broker dopo una perdita di connessione temporanea — [MuonPi releases](https://github.com/MuonPi/muondetector/releases); [detector-network-processor](https://github.com/orgs/MuonPi/repositories)

### Inferences
- 100 Pi × circa 300-500 serie node_exporter fanno 30-50k serie: si supera il free tier di Grafana Cloud. Conviene filtrare le metriche (tenere ~50 serie per Pi: CPU temp, throttling, disco, uptime, Wi-Fi RSSI, metriche DAQ come rate di eventi e backlog upload) oppure ospitare VictoriaMetrics/Prometheus più Grafana sul server centrale (costo solo VPS).
- Il servizio DAQ dovrebbe usare `WatchdogSec=` di systemd con `sd_notify` e `Restart=always`, così un blocco del software (non solo del kernel) porta prima a un riavvio del servizio e poi al reboot. Un health check "heartbeat" lato server (ultimo upload > X ore → alert) è il segnale più utile. È conoscenza generale di systemd, non verificata qui.
- I log remoti si possono raccogliere con Alloy/Promtail → Loki, oppure con journald-remote o rsyslog su TLS.

### Gaps
- Non ho trovato documentazione ufficiale recente di Raspberry Pi sul watchdog per Pi 5 (le fonti sono thread del forum 2017-2020).
- Non ho trovato case study di flotte scolastiche o scientifiche con metriche di uptime.

## 5. Provisioning in scala (immagine, identità, Wi-Fi a cura dei docenti, WPA2-Enterprise)

### Takeaway
Conviene un'immagine unica costruita con rpi-image-gen (o pi-gen), con identità per dispositivo generata al primo boot o in fabbrica (rpi-sb-provisioner per CM/secure boot). Per il Wi-Fi, comitup offre un hotspot con captive portal che i docenti possono usare dal telefono. Per WPA2-Enterprise (PEAP/MSCHAPv2, eduroam) serve NetworkManager, che è il default su Bookworm e Trixie.

### Cited Findings
- comitup: al boot prova le connessioni NetworkManager note; se falliscono crea un hotspot `comitup-<nnn>` con nome persistente e portale su http://10.41.0.1/ che si apre automaticamente su iOS, Android, macOS e Linux; ricorda più reti — [comitup README](https://github.com/davesteele/comitup/blob/main/README.md); [comitup site](http://davesteele.github.io/comitup/); [manpage](https://manpages.ubuntu.com/manpages/jammy/man8/comitup.8.html)
- Personalizzazione del portale comitup: richiesta aperta, nessuna risposta confermata trovata — [comitup issue #73](https://github.com/davesteele/comitup/issues/73)
- WPA2-Enterprise/eduroam: il network manager di default della vecchia desktop non supportava reti enterprise; si passa a NetworkManager (raspi-config → Advanced → Network Config). Configurazione tipica PEAP + MSCHAPv2 con certificato CA dell'istituto; con TLS legacy può servire `nmcli con mod eduroam 802-1x.phase1-auth-flags 32`; cat.eduroam.org genera configurazioni Linux per ogni ente — [OpenFlexure forum](https://openflexure.discourse.group/t/connecting-to-wpa2-enterprise-networks-e-g-eduroam-university-settings/1659); [UCLA network wiki](https://linux.ucla.edu/wiki/ucla-network); [gist eduroam fix](https://gist.github.com/cstanze/bb663ad02884932386d8c58c74c279bd)
- rpi-sb-provisioner: provisioning automatico di secure boot e primo boot per Compute Module, con WebUI e firma degli slot — [rpi-sb-provisioner](https://github.com/raspberrypi/rpi-sb-provisioner); [Interelectronix first boot provisioning](https://www.interelectronix.com/provisioning-automating-first-boot-rpi-sb-provisioner.html)
- Raspberry Pi Connect per organizzazioni include il "bulk provisioning" — [Connect for organisations](https://www.raspberrypi.com/news/raspberry-pi-connect-for-organisations-plus-full-screen-support/)

### Inferences
- Flusso proposto: (1) immagine unica firmata; (2) al primo boot il dispositivo genera una chiave (o usa il serial del SoC) e si registra con un token di enrollment pre-condiviso (Headscale pre-auth key taggata, Mender preauthorize, Connect bulk provisioning); (3) etichetta con QR code che contiene ID dispositivo e link al portale comitup e alla guida; (4) il docente si collega all'hotspot "rivelatore-XXX" e inserisce SSID e password, o le credenziali enterprise. comitup non ha un form EAP pronto all'uso: per WPA2-Enterprise serve un portale personalizzato o un file `.nmconnection` preparato dal team e caricato via USB/boot partition.
- Fallback consigliato: porta Ethernet sempre abilitata (DHCP) per le scuole dove il Wi-Fi è impraticabile, oppure una SIM/router 4G per i casi peggiori.

### Gaps
- Non ho trovato dati su balena WiFi Connect (stato di manutenzione 2025-2026) per un confronto diretto con comitup.
- Non ho trovato esempi documentati di captive portal con supporto 802.1X/EAP pronto all'uso per Pi.
- Nessuna informazione sulle policy delle reti scolastiche italiane (registrazione MAC, portali captive con login, Piano Scuola 4.0).

## 6. Scelta del modello di Raspberry Pi (longevità, consumi, alternative)

### Takeaway
Per un prodotto da mantenere 8-10 anni: Pi 4/CM4 sono garantiti fino ad almeno gennaio 2034; Pi 5/CM5 almeno fino a gennaio 2036 (il blog ufficiale cita 2038 per il Pi 5); Zero 2 W solo fino a gennaio 2030. Il CM4/CM5 con eMMC su una carrier custom (che può integrare ADC, front-end del rivelatore e RTC) è la scelta più "da prodotto". Il Pi 4 con SD industriale e overlay è il compromesso economico. Lo Zero 2 W consuma pochissimo (~0,5 W) ma ha solo Wi-Fi a 2,4 GHz, 512 MB di RAM e la longevità più breve.

### Cited Findings
- Pi 4 Model B "remain in production until at least January 2034" (product brief); CM4 e CM4S fino al 1 gennaio 2034 — [RPi forum: Obsolescence statements](https://forums.raspberrypi.com/viewtopic.php?t=374010); [endoflife.date](https://endoflife.date/raspberry-pi); [Wikipedia Pi 4](https://en.wikipedia.org/wiki/Raspberry_Pi_4)
- Pi 5: il product brief indica almeno gennaio 2036; l'articolo ufficiale sulla longevità indica una data minima garantita di fine produzione a gennaio 2038, con componenti chiave fino al 2042 (conflitto tra fonti, probabilmente l'articolo è più recente); CM5 a gennaio 2036 secondo endoflife.date — [RPi: commitment to longevity](https://www.raspberrypi.com/news/raspberry-pis-commitment-to-longevity-a-sustainable-advantage/); [RPi forum](https://forums.raspberrypi.com/viewtopic.php?t=374010); [endoflife.date](https://endoflife.date/raspberry-pi)
- Zero 2 W: almeno fino a gennaio 2030 — [RPi forum obsolescence](https://forums.raspberrypi.com/viewtopic.php?t=374010); [endoflife.date](https://endoflife.date/raspberry-pi)
- Una vecchia panoramica industriale (ott. 2023) indicava il Pi 4 al 2031: le date sono state riviste nel tempo e sono un minimo garantito — [pi3g](https://pi3g.com/should-industrial-customers-worry-will-pi-5-replace-the-pi-4/)
- Consumi a riposo (dipendono molto dal setup): Pi 5 circa 2,5-3 W headless su Wi-Fi; Pi 4 circa 2,7-2,9 W; Zero 2 W circa 0,4-0,7 W — [Pi Dramble power benchmarks](https://pidramble.com/wiki/benchmarks/power-consumption); [raspberry.tips 2026](https://raspberry.tips/en/raspberrypi-tutorials/raspberry-pi-power-consumption-update-2026-all-models-compared); [André Jacobs Zero 2 W](https://andrejacobs.org/b24/electronics/raspberry-pi-zero-2-w-temperature-and-power-consumption/); [RPi forum Pi 5 idle](https://forums.raspberrypi.com/viewtopic.php?t=360658)
- Connect Remote Update A/B è configurabile su Pi 5 e successivi con boot da EEPROM; l'esempio rpi-image-gen è pensato per rpi5 — [Connect docs](https://raspberrypi.com/documentation/services/connect.html); [rpi-image-gen examples/ota](https://github.com/raspberrypi/rpi-image-gen/tree/master/examples/ota)

### Inferences
- Il carico DAQ (interrupt GPIO + ADC I2C + upload) è leggero: un Pi 4 da 2 GB o un CM4 bastano. Il Pi 5 dà più margine per l'A/B nativo di Connect, NVMe e RTC integrato (utile per timestamp in caso di NTP assente), ma consuma un po' di più e richiede un alimentatore da 5 A per le periferiche. Per il timing preciso degli eventi, un GPS PPS (come MuonPi) è indipendente dal modello.
- Lo Zero 2 W è sconsigliato per un prodotto pluriennale (EOL 2030, solo 2,4 GHz, 512 MB stretti per Alloy + VPN + DAQ), salvo vincoli forti di costo o consumo.
- Alternative industriali (Revolution Pi, Kunbus, Seeed reTerminal, carrier board CM industriali con alimentazione protetta e supercap) non sono state ricercate in dettaglio in questa sessione.

### Gaps
- Non ho trovato prezzi correnti (2026) di CM5 con eMMC, Pi 4 e Pi 5, né dati sulla volatilità dei prezzi LPDDR del 2025-2026.
- Non ho trovato fonti sulle alternative industriali né sui supercap/UPS HAT per lo shutdown pulito.

## Stack raccomandato e costi indicativi (sintesi per il report writer)

### Takeaway
Stack consigliato per ~100 unità, ottimizzato per bassa manutenzione e costi contenuti in UE:
1. **Hardware**: Pi 4 (2 GB) o CM4/CM5 con eMMC su carrier; SD industriale pSLC se si usa il Pi 4; Ethernet come fallback. Longevità 2034+.
2. **OS e storage**: immagine costruita con rpi-image-gen; root read-only (overlay) più `/data` separata per il buffer; journald volatile.
3. **Aggiornamenti**: software DAQ come `.deb` firmato da un repo apt proprio (modello MuonPi) con rollout scaglionato; aggiornamenti dell'OS come A/B (Mender Basic ~68 $/mese per 100 dispositivi, oppure Connect Remote Update quando uscirà dalla fase sperimentale).
4. **Accesso remoto**: Headscale + DERP embedded su VPS UE (€) oppure Tailscale a pagamento; come secondo canale Raspberry Pi Connect per organizzazioni (~50 $/mese per 100 dispositivi).
5. **Monitoraggio**: watchdog hardware via systemd più `WatchdogSec` sul servizio DAQ; Grafana Alloy → VictoriaMetrics/Prometheus + Loki + Grafana self-hosted (o Grafana Cloud filtrando sotto le 10k serie); alert su "nessun upload da N ore".
6. **Provisioning**: comitup per il Wi-Fi a cura dei docenti, QR code sull'etichetta, profili NetworkManager per WPA2-Enterprise.

### Cited Findings
- Vedi le sezioni 1-6 per tutte le fonti (prezzi Mender, balena, Connect, ZeroTier, Grafana Cloud; longevità Raspberry Pi).

### Inferences
- Costo ricorrente annuo stimato (calcoli miei sui prezzi citati): opzione "lean" con apt, Headscale, Connect e monitoraggio self-hosted ≈ 600 $ (Connect) + ~300 € di VPS ≈ 900 €/anno. Opzione con Mender Basic aggiunge ~820 $/anno. Opzione balena (Pilot + 40 dispositivi extra) ≈ 4.900 $/anno, che include OTA, tunnel e dashboard ma meno controllo sui dati.

### Gaps
- Non ho trovato informazioni pubbliche su come HiSPARC e Cosmic Pi gestiscono aggiornamenti e accesso remoto delle stazioni; MuonPi documenta solo il repository apt e MQTT.
