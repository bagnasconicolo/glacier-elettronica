# Piattaforma dati e rete per una rete di rivelatori di raggi cosmici nelle scuole

> Nota di metodo: in questa sessione il proxy di uscita bloccava il recupero completo delle pagine (arxiv.org, pos.sissa.it, docs.hisparc.nl e muonpi.org davano DNS/403). I risultati qui sotto si basano quindi sugli estratti dei motori di ricerca dalle pagine citate, non sulla lettura completa dei testi. Le affermazioni che vengono solo da conoscenze generali sono marcate come inferenze o gap.

## 1. Come le reti reali (HiSPARC, EEE, CREDO, Cosmic Pi, MuonPi, QuarkNet) gestiscono upload, archiviazione, accesso e buffering

### Takeaway
Tutte le reti studiate usano lo stesso schema: **buffer locale sulla stazione, upload in uscita e asincrono verso un server centrale, ricostruzione e riassunto notturni o quasi online, poi accesso pubblico in sola lettura via web/API**. HiSPARC (buffer MySQL locale, upload HTTP, archivio HDF5, Django public DB, OpenVPN e Nagios) è il riferimento più maturo e documentato. MuonPi è l'esempio più vicino al nostro hardware: un daemon su Raspberry Pi pubblica su MQTT e un servizio centrale calcola le coincidenze. EEE usa una sincronizzazione di file verso INFN-CNAF (cloud OpenStack) con DQM web.

### Cited Findings
**HiSPARC (Nikhef, Paesi Bassi)**
- Ogni stazione è un PC Windows in una rete scolastica, con l'elettronica collegata via USB e un GPS per posizione e tempo. Il software di stazione gestisce il flusso dati, l'event building e l'invio al database centrale — [HiSPARC experiment, arXiv:1908.01622](https://arxiv.org/pdf/1908.01622)
- Il software di stazione comprende un run-time LabVIEW, servizi di controllo e monitoraggio remoti, script Python e un **buffer locale**. La DAQ fa zero suppression e calcola baseline, pulse height e integrale. Dati e prime analisi vanno in un **database MySQL locale**, e un programma Python carica i dati a intervalli regolari sul datastore di Nikhef — [ICALEPCS 2013, THPPC064](https://accelconf.web.cern.ch/ICALEPCS2013/papers/thppc064.pdf)
- Monitoraggio: Nagios sorveglia hardware e DAQ di ogni stazione e manda e-mail al responsabile in caso di guasto. L'accesso remoto e gli aggiornamenti software passano da una **rete OpenVPN** — [ICALEPCS 2013](https://accelconf.web.cern.ch/ICALEPCS2013/papers/thppc064.pdf); [HiSPARC software downloads](https://www.hisparc.nl/oud/en/downloads/software/)
- Datastore centrale: un'applicazione **WSGI** riceve gli upload (oggetti pickled) e li mette in coda. Un processo "writer" svuota la coda e scrive in file **HDF5 con PyTables** — [docs.hisparc.nl datastore writer](https://docs.hisparc.nl/datastore/writer.html)
- Accesso pubblico: download con form web (file .tsv per stazione e intervallo di date), HTTP GET su `https://data.hisparc.nl/data/<station>/events`, il pacchetto Python SAPPHiRE, le web app jSparc e un'API per i metadati — [Data access, HiSPARC publicdb](https://docs.hisparc.nl/publicdb/data_access.html); [SAPPHiRE](https://docs.hisparc.nl/sapphire/); [jSparc data retrieval](https://docs.hisparc.nl/jsparc/data_retrieval.html)
- Ogni notte un'applicazione **Django** preprocessa i dati grezzi e genera l'**Event Summary Data (ESD)**: pulse height, timestamp, posizione dei rivelatori e offset temporali. La tabella eventi ha i campi `timestamp` (uint32) + `nanoseconds` (uint32), t1–t4 e zenith/azimuth — [SAPPHiRE ESD](https://docs.hisparc.nl/sapphire/esd.html)
- Dal 1° gennaio 2018 sono supportate solo installazioni Windows 10 — [HiSPARC software](https://www.hisparc.nl/oud/en/downloads/software/)
- Esiste un mirror del Public Database all'Università dello Utah, con pagine di stato per stazione — [hisparc-data.chpc.utah.edu](https://hisparc-data.chpc.utah.edu/show/stations/7/status)

**EEE – Extreme Energy Events (Centro Fermi / INFN)**
- I telescopi MRPC sono in gran parte installati nelle scuole superiori e gestiti da studenti e docenti. La risoluzione temporale degli MRPC è circa 100 ps — [Abbrescia, slide CF mar 2018](https://agenda.centrofermi.it/event/54/contributions/355/attachments/277/380/AbbresciaCFMar18.pdf)
- Dal 2014 EEE usa il cloud **OpenStack (IaaS) di INFN-CNAF** per raccogliere, monitorare e ricostruire i dati di tutte le stazioni. La sincronizzazione stazioni→CNAF usava **BitTorrent Sync** (peer-to-peer gratuito) — [PoS ICRC2017 (301) 478](https://pos.sissa.it/301/478/pdf)
- Monitor in tempo reale su eee.centrofermi.it/monitor e cnaf.infn.it/eee/monitor; DQM "run by run" e "day by day"; due e-log e report automatici dei turnisti — [EEE Erice 2018](https://agenda.centrofermi.it/event/89/contributions/602/attachments/344/515/EEE_Erice_2018.pdf)
- La ricostruzione con controlli di qualità web è "quasi online" (poche ore). Gli studenti controllano ogni giorno le prestazioni del telescopio — [Gnesi, SIF 2016](https://agenda.centrofermi.it/event/4/contributions/220/attachments/154/183/Gnesi-EEE-SIF2016_pre.pdf)
- Scala: 49 telescopi collegati a CNAF nel 2018. Oltre 48 miliardi di tracce raccolte dall'autunno 2014 al 2017 — [EEE Erice 2018](https://agenda.centrofermi.it/event/89/contributions/602/attachments/344/515/EEE_Erice_2018.pdf); [PoS 301/478](https://pos.sissa.it/301/478/pdf)
- Luglio 2026: a CNAF ci sono una VM per l'analisi automatica standard (produzione DST, plot), una VM per l'analisi dei ricercatori e una VM di test su AlmaLinux 10. Lo strumento "rEEEmote" è installato su 24 PC (21 nel 2025) — [EEE meeting 2026-07-01](https://agenda.centrofermi.it/event/353/contributions/2299/attachments/1035/1556/eee_meeting_20260701.pdf)

**MuonPi (Giessen)**
- Rete IoT distribuita di rivelatori a basso costo basati su Raspberry Pi (scintillatore plastico + SiPM). Timestamp di qualche decina di ns grazie alla funzione "timemark" del GNSS u-blox NEO-M8N — [wiki.muonpi.org](https://wiki.muonpi.org/); [muonpi.org](https://muonpi.org)
- Il daemon gira come servizio systemd e invia i dati al server centrale in tempo reale. Un LED indica lo stato del **link MQTT** verso il server. La libreria è Paho MQTT C++. Un programma di login autentica l'utente sul servizio MQTT, e uno stesso account può gestire più stazioni con station-id distinti — [GitHub MuonPi/muondetector](https://github.com/MuonPi/muondetector); [package list archive.muonpi.org](https://archive.muonpi.org/2.0.0/raspbian/dists/buster/main/binary-armhf/Packages); [release v1.1.2](https://muonpi.org/release_v112.html)
- Il servizio "detector-network-processor" si collega a un broker MQTT, calcola le coincidenze e le scrive su un database o le inoltra a un altro broker MQTT — [GitHub MuonPi (listing)](https://gitblind.noratr.app/MuonPi)

**CREDO**
- Ogni rilevamento viene prima salvato sul dispositivo e poi trasferito a un repository centrale. Il repository espone un'API dedicata (servizi REST conformi a **OpenAPI**, principi FAIR) e i dati sono pubblici — [CREDO, arXiv:2010.08351 / Symmetry 2020](https://arxiv.org/pdf/2010.08351); [Symmetry DOI 10.3390/sym12111802](https://api.crossref.org/works/10.3390%2FSYM12111802)
- L'accesso pubblico ai rilevamenti avviene tramite api.credo.science — [IPPOG CREDO](https://ippog.web.cern.ch/node/253)

**Cosmic Pi e reti analoghe**
- Cosmic Pi ha una dashboard pubblica con le unità connesse e i dati aggregati, condivisione opzionale della posizione GPS e supporto Grafana — [3dtested news](https://www.3dtested.com/news/raspberry-pi-cosmicpi). La fonte è giornalistica e non indica il protocollo.
- Rete ArduSiPM: broker **Mosquitto** su server Linux, un plugin Python che scrive su MySQL e un web service con app HTML5 — [arXiv:1703.09843](https://arxiv.org/pdf/1703.09843)
- DAQ modulare per reti di raggi cosmici: dati lenti e operativi via MQTT, cache in memoria per il monitoraggio online, persistenza SQL per l'offline, server in container replicabili — [arXiv:2203.05608](https://arxiv.org/pdf/2203.05608)

**QuarkNet e-Lab (Fermilab)**
- Il software Java EQUIP gira sul PC collegato al DAQ via USB/seriale e i dati sono file di testo. Lo studente **carica i file a mano** sull'e-Lab web e poi usa gli strumenti performance, flux e shower. La geometria va inserita a parte nell'e-Lab — [How to use EQUIP](https://new.quarknet.org/sites/default/files/HowtouseEQUIP.pdf); [Cosmic Ray Workshop agenda](https://quarknet.org/node/1060)
- Tra le richieste di supporto ci sono "upload failures". Nel 2020 risultavano 106.000 file CRMD archiviati nell'e-Lab — [QuarkNet Monthly Report 2023](https://new.quarknet.org/sites/default/files/MonthlyReport_JanFeb_2023%20%281%29.pdf); [Fermilab e-Lab paper cs/0502089](https://web3.arxiv.org/pdf/cs/0502089)

### Inferences
- Lo schema da copiare è: buffer persistente locale (SQLite/file) → upload in uscita autenticato e idempotente → coda/ingest centrale → archivio grezzo immutabile (file HDF5/Parquet) + database riassuntivo → API pubblica e dashboard.
- L'upload manuale di QuarkNet porta a errori ("upload failures"). L'upload automatico di HiSPARC e MuonPi è preferibile.
- Il VPN di HiSPARC per la manutenzione remota è un punto di forza operativo. Oggi lo stesso risultato si ottiene con WireGuard/Tailscale/Headscale (vedi sezione 6).

### Gaps
- Non è stato possibile leggere i testi completi del NIM/arXiv HiSPARC e del PoS EEE. Mancano quindi il formato esatto dei payload HiSPARC e la versione corrente del trasferimento EEE (BitTorrent Sync/Resilio è confermato solo nel 2017).
- Non ho trovato un paper peer-reviewed su MuonPi, né la documentazione dei topic MQTT o dello schema DB (repo detector-network-processor non leggibile in questa sessione).
- Non ho trovato fonti su come IceCube/Pierre Auger outreach (es. Auger Open Data) gestiscono l'accesso: non cercato per limite di tool call.

## 2. Scelta del protocollo: MQTT/TLS, HTTPS batch, WebSocket; proxy e firewall; store-and-forward; volume dati

### Takeaway
Per le scuole italiane la scelta più robusta è **tutto in uscita su TCP 443**. Si può fare con MQTT over WebSocket+TLS (wss://…:443) per lo stato e i dati in tempo reale, oppure con **upload HTTPS batch** idempotenti dal buffer locale come canale primario o di riserva. La porta 8883 (MQTT/TLS nativo) va tenuta come opzione ma spesso è filtrata. Il buffering affidabile va fatto **sul dispositivo** (spool su disco), non affidato alla coda del broker. Il volume dati è piccolo: ~100–200 mila eventi/giorno per rivelatore.

### Cited Findings
- WebSocket su porta 443 attraversa la maggior parte dei firewall — [Alibaba Cloud IoT docs](https://www.alibabacloud.com/help/doc-detail/63656.html)
- Mosquitto supporta listener `protocol websockets` con le stesse opzioni TLS dei listener MQTT, incluso `require_certificate` per mTLS — [DEV: TLS in Mosquitto](https://dev.to/sheng_chen_5979882122c747/configuring-tls-in-the-mosquitto-mqtt-broker-3jnb)
- HiveMQ: il binding sulla porta 443 può richiedere privilegi o port mapping (es. Docker) — [HiveMQ CE secure websocket](https://mintlify.com/hivemq/hivemq-community-edition/mqtt/transports/secure-websocket)
- I client non-browser (Python, Node, Java) possono usare mTLS anche su WSS, mentre i client browser di norma non presentano certificati client — [ThingsBoard MQTT over WS](https://thingsboard.io/docs/mqtt-broker/pe/user-guide/mqtt-over-ws/)
- Mosquitto: `max_queued_messages` limita i messaggi QoS1/2 accodati per ogni client offline con sessione persistente. Oltre il limite i nuovi messaggi vengono **scartati**. Esistono anche `max_queued_bytes` e `queue_qos0_messages`. Le code stanno in RAM — [Eclipse mosquitto-dev](https://www.eclipse.org/lists/mosquitto-dev/msg00755.html); [Cedalo persistent queue](https://docs.cedalo.com/mosquitto/2.9/broker/Mosquitto%20Manual/mosquitto-persistent-queue); [mosquitto.conf example](https://code.nicolabs.net/nicolabs/mosquitto/raw/commit/99fa50f30e325609394c324c8ff71cfbbe95d8ab/mosquitto.conf)
- La sessione persistente richiede clean session disattivata, un client ID stabile e QoS ≥1 — [Node-RED forum](https://discourse.nodered.org/t/issues-in-persisting-messages-in-mqtt-broker-using-nodered-mqtt-nodes/4666)
- Precedenti: HiSPARC usa upload HTTP periodici da un buffer locale MySQL ([ICALEPCS 2013](https://accelconf.web.cern.ch/ICALEPCS2013/papers/thppc064.pdf)); MuonPi usa MQTT in tempo reale ([muonpi.org release](https://muonpi.org/release_v112.html)); EEE usa la sincronizzazione di file P2P ([PoS 301/478](https://pos.sissa.it/301/478/pdf)).

### Inferences
- **Stima del volume** (calcolo proprio):
  - 1–2 µ/s per rivelatore danno 86.400–172.800 eventi/giorno.
  - Con un record binario di ~32–64 B (timestamp ns a 64 bit, maschera dei canali, tre tempi o ToT, flag) sono 3–11 MB/giorno. In JSON (~150–200 B per evento) sono ~15–35 MB/giorno. Compresso (zstd/gzip) circa 3–5 volte meno.
  - Per 100 rivelatori: ≤3,5 GB/giorno non compressi, ~1 TB/anno nel caso peggiore, molto meno compresso (~0,1–0,3 TB/anno in Parquet).
  - Lo slow control (tensioni bias, temperatura ogni 10–60 s) è trascurabile.
  - Sono numeri gestibili da un singolo server modesto.
- Architettura consigliata sul Pi:
  1. L'acquisizione scrive su uno **spool locale** (SQLite in WAL o file orari Parquet/CSV.gz con checksum).
  2. Un uploader separato invia batch (es. ogni 1–5 min o ogni N eventi) via **HTTPS POST** con ID di batch idempotente e aspetta un ACK con hash.
  3. Cancella il batch solo dopo l'ACK e lo conserva per X giorni.
  4. In parallelo, MQTT/WSS:443 trasporta heartbeat, rate e slow control per la dashboard live, con LWT (Last Will) per lo stato online/offline.
  5. Con la scheda SD si possono bufferizzare settimane di dati (~10 MB/giorno).
- Alternativa: solo MQTT 5 su WSS:443 con QoS1 e spool locale lato client (es. Paho con persistenza su file), come MuonPi. È più semplice ma meno idempotente dell'HTTPS batch.
- Proxy HTTP espliciti con autenticazione o ispezione TLS (proxy con MITM) rompono mTLS e possono rompere WebSocket. Un fallback HTTPS puro con token per dispositivo e la possibilità di configurare `HTTPS_PROXY` aumentano la robustezza.
- Captive portal: un Pi headless non può completare un login web. Servono una whitelist MAC dal tecnico della scuola o una rete o SSID dedicato. Per 802.1X (PEAP/MSCHAPv2) NetworkManager/wpa_supplicant su Raspberry Pi OS funziona, con certificato CA della rete — [UNIBS guida eduroam Linux](https://www.unibs.it/sites/default/files/2026-09/Guida_Eduroam_Debian_Ubuntu_EN.pdf); [AC Training Lab RPi WPA2-Enterprise](https://ac-training-lab.readthedocs.io/en/latest/raspberry-pi-wpa2-enterprise.html); [USQ RPi eduroam](https://makerresources.unisq.edu.au/wp-content/uploads/2021/02/How-to-set-up-a-Raspberry-Pi-with-Eduroam-at-USQ.pdf)
- Fallback hardware: un router o chiavetta 4G con SIM IoT per le scuole con reti ostili (inferenza, nessun costo verificato).

### Gaps
- Non ho trovato statistiche su quanto spesso le reti scolastiche italiane bloccano la porta 8883 o usano proxy con ispezione TLS. Va verificato con un sondaggio sulle scuole pilota.
- Le fonti non trattano in dettaglio il comportamento dei proxy con WebSocket.
- Non ho trovato fonti su strumenti headless per captive portal.

## 3. Storage: database time-series, object storage, retention, open data

### Takeaway
Per ~10–100 rivelatori conviene **PostgreSQL + TimescaleDB**: SQL, continuous aggregates, compressione, RLS per la multi-tenancy e un ecosistema unico. A fianco serve un **archivio grezzo immutabile** (file giornalieri per stazione in HDF5 o Parquet su object storage S3-compatibile EU). Per la pubblicazione aperta si usano release periodiche su **Zenodo** con DOI. InfluxDB 3 Core ha limiti di retention e numero di database nella versione open.

### Cited Findings
- TimescaleDB ha continuous aggregates nativi con refresh automatico e compressione columnstore fino a 90%+. Eredita l'ecosistema PostgreSQL — [TigerData compare](https://www.tigerdata.com/compare/influxdb) (fonte del vendor)
- InfluxDB 3.0 non ha continuous aggregates o materialized views nativi. InfluxDB 3 Core ha limiti, ad esempio 72 h di retention e 5 database — [QuestDB comparison](https://questdb.com/blog/comparing-influxdb-timescaledb-questdb-time-series-databases) (fonte di un concorrente, da verificare sulla documentazione Influx)
- Tesi OST 2024 (neutrale): InfluxDB usa meno disco e ha query migliori di default. TimescaleDB recupera con continuous aggregates, indici e policy di compressione — [OST thesis](https://orix.ost.ch/bitstreams/a7a62e90-5515-4c46-ab95-3ff53ad9f417/download)
- Precedente: HiSPARC tiene i grezzi in HDF5 (PyTables) e un ESD riassuntivo notturno con download in TSV — [datastore writer](https://docs.hisparc.nl/datastore/writer.html); [ESD](https://docs.hisparc.nl/sapphire/esd.html)
- Precedente: CREDO pubblica i dati via API REST/OpenAPI secondo FAIR — [arXiv:2010.08351](https://arxiv.org/pdf/2010.08351)

### Inferences
- Modello dati consigliato:
  - hypertable `events(station_id, t_ns BIGINT o timestamptz+ns, channel_mask, t1,t2,t3, flags)`
  - hypertable `slowcontrol(station_id, t, vbias1..3, temp, ...)`
  - continuous aggregates per rate di 1 min/1 h per canale e coincidenze
  - tabelle relazionali per scuole, stazioni, utenti e calibrazioni
- Retention:
  - eventi singoli nel DB "caldo" per 1–2 anni, compressi dopo 7 giorni
  - aggregati per sempre
  - file grezzi per sempre su object storage
- Open data: file giornalieri o mensili per stazione in **HDF5 o Parquet + CSV** per gli studenti, con README e metadati (posizione arrotondata della scuola, geometria, calibrazioni), release annuali su Zenodo (CERN, server UE) con DOI e licenza CC-BY 4.0.
- QuestDB è un'alternativa veloce per l'ingest ma non serve a questi volumi.

### Gaps
- Le fonti sui database time-series sono quasi tutte di vendor. Manca un benchmark indipendente con questo volume (basso).
- Policy di Zenodo e limiti di dimensione non verificati in questa sessione.

## 4. Dashboard e multi-tenancy (Grafana vs app custom), autenticazione, ruoli, pagine pubbliche

### Takeaway
Grafana OSS va bene per il team di progetto e per dashboard rapide. Però **non filtra le righe** e le "variabili" non sono un confine di sicurezza, quindi l'isolamento per scuola va imposto nel DB (**PostgreSQL RLS** o viste per tenant) oppure in un'API. Per l'esperienza scuola (docente/studente, didattica, export) è meglio una **web app custom** (Django o FastAPI + frontend) con **OIDC via Keycloak**, che può incorporare pannelli Grafana. Le pagine pubbliche si fanno sull'esempio di HiSPARC e jSparc.

### Cited Findings
- Grafana non offre row-level security per i datasource SQL. L'approccio raccomandato è RLS in PostgreSQL o viste ristrette. Le variabili delle dashboard non sono un confine di sicurezza — [Grafana community: PostgreSQL row level access](https://community.grafana.com/t/postgresql-row-level-access-in-grafana/163838); [community thread variabili per team](https://community.grafana.com/t/different-value-of-variables-for-users-from-different-teams/68827)
- Le Organizations di Grafana sono tenant isolati (dashboard, datasource, utenti e team propri). Un utente vede una sola org alla volta — [OneUptime: Grafana organizations multi-tenancy](https://oneuptime.com/blog/post/2026-02-09-grafana-organizations-multi-tenancy/view)
- Nella versione OSS i ruoli fissi non sono estendibili. I permessi sui datasource e LBAC/RBAC avanzati sono funzioni Enterprise/Cloud — [classmethod: Grafana tenant separation](https://dev.classmethod.jp/articles/grafana-tenant-separation-team-organization/); [Grafana blog: teams & roles](https://grafana.com/blog/managing-access-in-grafana-a-single-stack-journey-with-teams-roles-and-real-world-patterns/?pg=blog)
- Precedenti: HiSPARC ha un public DB Django con pagine di stato per stazione e jSparc per la didattica ([publicdb](https://docs.hisparc.nl/publicdb/)). EEE ha un monitor pubblico e DQM ([EEE Erice 2018](https://agenda.centrofermi.it/event/89/contributions/602/attachments/344/515/EEE_Erice_2018.pdf)).

### Inferences
- Opzione A, più veloce: una sola org Grafana per scuola, un datasource per scuola con un ruolo Postgres dedicato e policy RLS `station_id IN (scuola)`, utenti scuola con ruolo Viewer, team di progetto Admin su una org "Progetto" con un datasource completo. Con 100 scuole sono 100 org da automatizzare via API o Terraform.
- Opzione B, consigliata a medio termine:
  - API FastAPI o Django REST che applica il tenant dai claim JWT
  - frontend React/Vue con plot (Plotly/uPlot), export CSV, pagine didattiche
  - Grafana solo interno per il team e per il monitoraggio operativo (Prometheus/Loki)
- Autenticazione: Keycloak (realm unico, gruppi per scuola, ruoli `teacher`, `student`, `project-admin`) come provider OIDC sia per la web app sia per Grafana (generic OAuth con mapping di org e ruoli).
- Per gli studenti minorenni conviene evitare account nominativi. Bastano account di classe gestiti dal docente o accesso in sola lettura. Così si riducono i dati personali (vedi sezione 6).
- Pagine pubbliche: mappa delle stazioni (posizione approssimata), rate live, download open data. Nessun login.

### Gaps
- Non ho trovato una guida ufficiale Grafana sull'esatto pattern Postgres RLS + org. Sopra c'è una sintesi.
- Il mapping OIDC→Org di Grafana per più org non è stato verificato sulla documentazione in questa sessione.

## 5. Coincidenze tra scuole (sciami estesi): timing necessario e come lo fanno HiSPARC, EEE e MuonPi

### Takeaway
Servono **timestamp assoluti GPS/GNSS con PPS, precisione ~10–50 ns**. NTP (ms) e i timestamp del kernel Linux da soli non bastano. Le reti di riferimento raggiungono 15–20 ns (HiSPARC), qualche decina di ns (EEE, MuonPi) e usano finestre di coincidenza da µs (singolo sciame tra stazioni vicine) fino a ms (correlazioni a lunga distanza).

### Cited Findings
- HiSPARC: un contatore a 200 MHz (passi da 5 ns) conta dal PPS GPS all'evento — [HiSPARC firmware messages](https://docs.hisparc.nl/firmware/messages.html)
- HiSPARC: il costruttore del GPS dichiara 15 ns (1σ). Gli offset tra circa 100 coppie di stazioni hanno distribuzione gaussiana con μ=2,7 ns e σ=18,9 ns. Il GPS fa un self-survey di 24 h all'installazione — [arXiv:1908.01622](https://arxiv.org/pdf/1908.01622)
- HiSPARC: una coincidenza tra stazioni è definita da eventi entro **2 µs** — [HiSPARC news 2014](https://www.hisparc.nl/oud/en/news/newsitem/article/translate-to-english-coincidenties-showers-gemeten-door-meerdere-stations/cache/925fcbc3137c1ee163a593068b48bfb6/)
- EEE: tempo assoluto da GPS con precisione di qualche decina di ns. Il PPS resetta i TDC che danno il sub-secondo, e la stringa NMEA dà il tempo — [DESY talk EEE](https://video.desy.de/media/downloadAttachment/key/a5de2ee00ea7edc164206a9ec6b13f66/maid/1860); [Abbrescia CF 2018](https://agenda.centrofermi.it/event/54/contributions/355/attachments/277/380/AbbresciaCFMar18.pdf)
- EEE: coincidenze osservate tra stazioni a ~1,5 km. Ricerca di correlazioni a lunga distanza (Bologna–Cagliari, 610 km) con finestre fino a ms. Studi ICRC 2021 su coppie distanti più di 5 km con finestre fino a 10⁻⁵ s — [Abbrescia CF 2018](https://agenda.centrofermi.it/event/54/contributions/355/attachments/277/380/AbbresciaCFMar18.pdf); [MPP Elba 2018](https://agenda.centrofermi.it/event/79/contributions/516/attachments/312/459/MPP_Elba2018_v1.pdf)
- MuonPi: timemark u-blox NEO-M8N con precisione di qualche decina di ns (fino a ~20 ns), comunicazione UBX su seriale. Le coincidenze sono calcolate centralmente da un servizio collegato al broker MQTT — [wiki.muonpi.org](https://wiki.muonpi.org/); [GitHub muondetector](https://github.com/MuonPi/muondetector)

### Inferences
- I timestamp dei GPIO nel kernel del Raspberry Pi hanno jitter da µs (interrupt latency) e un'origine legata al clock di sistema. Per le coincidenze tra scuole servono un modulo GNSS di timing (es. u-blox NEO-M8T/ZED-F9T o M8N con timemark) che marchi l'evento in hardware, oppure il PPS su GPIO con chrony/PPS e interpolazione. Il secondo approccio è solo a livello µs. Va coordinato con la ricerca sull'elettronica.
- La piattaforma deve salvare ogni evento con tempo in ns (int64 dall'epoca GPS/UTC più flag di qualità GPS: fix, numero di satelliti, stato del survey), con una tabella per gli offset di cavo/antenna di ogni stazione. Il coincidence finder centrale (job batch su finestre di tempo, tolleranza ±(d/c + 2σ_t), ad esempio pochi µs per stazioni a ~1 km) deve girare dopo l'arrivo dei dati in ritardo dal buffer. Va quindi rieseguito sulle finestre di tempo chiuse (es. T+24h), come l'ESD notturno di HiSPARC.
- Le scuole sono di solito a km di distanza: le coincidenze vere saranno rare e servono studi di accidentali, come in EEE.

### Gaps
- Il modello GPS di HiSPARC e la calibrazione degli offset di ritardo cavo non sono confermati dalle fonti lette.
- Non ho trovato il paper finale EEE sulle correlazioni a lunga distanza (EPJ Plus 2018) né i suoi numeri definitivi.

## 6. Sicurezza e privacy: GDPR per scuole e minori, DPA, hosting UE, identità dei dispositivi, vincoli delle reti scolastiche italiane

### Takeaway
I dati del rivelatore non sono personali. Lo sono invece account, log, IP e eventuali nomi e foto degli studenti. La scuola (titolare) deve nominare il gestore della piattaforma **responsabile ex art. 28 GDPR** con un accordo specifico, a meno che la piattaforma non sia gestita dall'Università o dall'INFN come contitolare o titolare autonomo (da definire). Conviene hosting UE, minimizzazione (nessun account nominativo per i minori), sub-responsabili elencati e identità del dispositivo con chiavi o certificati per ogni dispositivo.

### Cited Findings
- Come regola, la scuola titolare nomina il fornitore responsabile ex art. 28 con contratto. Se la scuola usa strumenti gestiti in autonomia senza soggetti esterni, la nomina non serve. I dati vanno usati solo per finalità didattiche — [Cybersecurity360](https://www.cybersecurity360.it/legal/privacy-dati-personali/privacy-e-didattica-a-distanza-una-buona-prassi-per-i-dpo-degli-istituti-scolastici/)
- Il Garante ha inserito "piattaforme di registro elettronico e suite digitali" tra gli ambiti delle ispezioni nelle scuole (gen–lug 2024). Le scuole devono conservare la nomina del fornitore — [Agenda Digitale](https://www.agendadigitale.eu/?p=204552)
- Per singole scuole con piattaforme ordinarie la DPIA in genere non è richiesta (no larga scala), e il DPO supporta privacy by design — [Agenda Digitale, governance DDI](https://www.agendadigitale.eu/scuola-digitale/la-privacy-nella-didattica-a-distanza-linee-guida-e-ruoli-chiave-per-una-governance-corretta/)
- Gli indirizzi IP sono in genere dati personali perché combinabili per identificare — [TechGDPR](https://techgdpr.com/blog/is-an-ip-address-considered-personal-data/)
- Le linee guida EDPB sull'art. 5(3) ePrivacy si applicano anche ai dispositivi IoT a prescindere dalla natura personale dei dati — [BCLP briefing](https://www.bclplaw.com/print/v2/content/1535958/edpb-explains-eu-eprivacy-cookie-rules-apply-to-emerging-online-tracking-tools.pdf)
- Caso EDPB: l'autorità islandese ha multato un comune (16.590 €) per Google Workspace for Education, anche per un DPA che non rispettava l'art. 28(3)(a) — [EDPB news](https://www.edpb.europa.eu/news/icelandic-sa-the-municipality-of-reykjanesbaer-fined-eur-16590-for-the-use-of-google-workspace_it)
- Precedente: HiSPARC usa OpenVPN per la gestione remota delle stazioni — [ICALEPCS 2013](https://accelconf.web.cern.ch/ICALEPCS2013/papers/thppc064.pdf). Per 802.1X sul Pi bisogna configurare il certificato CA e non disattivare la verifica, che espone a MITM — [UNIBS eduroam guide](https://www.unibs.it/sites/default/files/2026-09/Guida_Eduroam_Debian_Ubuntu_EN.pdf); [AC Training Lab](https://ac-training-lab.readthedocs.io/en/latest/raspberry-pi-wpa2-enterprise.html)

### Inferences
- Identità del dispositivo:
  - ogni Pi genera la propria chiave privata al primo avvio (meglio se in un secure element ATECC608 o TPM opzionale) e riceve un certificato X.509 da una CA privata di progetto (es. step-ca o Vault PKI) con CN=`station-<id>`
  - mTLS verso il broker e l'API, oppure token per dispositivo se c'è un proxy con ispezione TLS
  - ACL MQTT per topic `stations/<id>/#` e revoca centralizzata
  - provisioning con un'immagine SD standard + codice di enrollment monouso
- Rete di gestione: WireGuard o Headscale/Tailscale (solo uscita UDP o 443 con DERP) per SSH e aggiornamenti. Aggiornamenti con pacchetti .deb firmati o Mender/RAUC.
- Minimizzazione: i log del server tengono gli IP per tempi brevi (es. 30–90 giorni), le posizioni pubblicate sono arrotondate, gli studenti hanno account di classe o pseudonimi, non si raccolgono dati sensibili.
- Ruoli GDPR da definire con il DPO dell'Ateneo: se UniTo o il progetto offre il servizio alle scuole, scrivere un accordo art. 28 tipo (o un accordo di contitolarità art. 26) e un'informativa. Tenere l'elenco dei sub-responsabili (hosting UE come Hetzner, OVH, Aruba o GARR Cloud).
- Per enti pubblici italiani il cloud deve rispettare il quadro ACN/AgID di qualificazione dei servizi cloud per la PA. Vedi il gap sotto.

### Gaps
- Non ho trovato un provvedimento specifico del Garante su progetti IoT o scientifici nelle scuole, né le linee guida EDPB definitive su art. 5(3) (verificare se adottate).
- Non ho verificato se un servizio offerto da un'Università alle scuole rientri negli obblighi di qualificazione ACN (ex AgID) per il cloud PA, né se GARR Cloud sia qualificato. Va chiesto al DPO o ufficio ICT di UniTo.
- Non ho trovato linee guida AgID su vincoli di rete nelle scuole (firewall o porte).

## 7. Costi indicativi di hosting (EU) per 10–100 rivelatori

### Takeaway
Il carico (≤ qualche GB al giorno, centinaia di messaggi al secondo) sta su **1–2 VPS UE da 4–8 GB RAM** più object storage e backup. L'ordine di grandezza è **decine di €/mese**, non centinaia. Hetzner ha aumentato i prezzi nel 2026 e le cifre riportate variano molto, quindi vanno verificate sul listino ufficiale.

### Cited Findings
- Hetzner: nuovi prezzi per i cloud server dal 15 giugno 2026 per nuovi ordini e rescale. I server esistenti non sono toccati — [Hetzner Cloud What's New](https://docs.hetzner.cloud/whats-new)
- Fonti terze danno CPX22 da €5,99 a €7,99/mese (annuncio con data 1 aprile 2026) — [Better Stack review](https://betterstack.com/community/guides/web-servers/hetzner-cloud-review/). Un'altra fonte (settembre 2026) riporta aumenti del 33–38% sulle linee CX e CAX, rincari maggiori su CPX e CCX, CPX22 a €19,99 e le linee economiche non disponibili — [Findstack](https://findstack.com/resources/hetzner-price-increase-2026). Le fonti sono in conflitto.
- Ottobre 2025: i piani EU sono distinti per generazione hardware (CX23 ecc.) — [Hetzner What's New](https://docs.hetzner.cloud/whats-new)

### Inferences
- Stack indicativo (cifre da verificare, mio ordine di grandezza):
  - VPS principale 4 vCPU/8–16 GB con broker, API, Postgres+Timescale e Grafana: ~20–50 €/mese
  - seconda VPS o DB gestito per HA/replica: +20–50 €/mese
  - object storage 1 TB: ~5–15 €/mese
  - backup off-site: ~5–10 €/mese
  - dominio e TLS (Let's Encrypt) quasi gratis
  - totale ~50–130 €/mese per 100 rivelatori
- Alternative pubbliche e accademiche: **GARR Cloud** o INFN Cloud (come EEE su CNAF), forse senza costi diretti per UniTo. Va verificato.
- Servizi MQTT gestiti (HiveMQ Cloud, EMQX Cloud) non sono necessari a questa scala. Mosquitto o EMQX open source self-hosted bastano.

### Gaps
- Non ho prezzi ufficiali e aggiornati (ottobre 2026) di Hetzner, OVHcloud, Scaleway, Aruba o GARR. Le fonti trovate sono in conflitto.
- Non ho trovato costi di servizi gestiti (Timescale/Tiger Cloud, Aiven Postgres UE).

---

### Architettura consigliata (sintesi, inferenza basata sulle fonti sopra)
1. **Edge (Raspberry Pi)**:
   - acquisizione → spool locale (SQLite WAL o file orari compressi)
   - timing GNSS con PPS/timemark per le coincidenze
   - uploader HTTPS batch idempotente (443) più MQTT 5 su WSS:443 per stato, rate e slow control (LWT online/offline)
   - certificato o chiave per ogni dispositivo
   - WireGuard o Headscale per la manutenzione
   - aggiornamenti firmati
   - Wi-Fi via NetworkManager (PSK o 802.1X PEAP con CA), whitelist MAC per i captive portal, fallback 4G
2. **Ingest**:
   - reverse proxy (Caddy/Traefik/nginx) su 443
   - broker Mosquitto o EMQX con ACL per topic e stazione
   - servizio ingest (FastAPI) che valida, deduplica e scrive su Postgres/Timescale e archivia il batch grezzo su object storage S3 UE
3. **Processing**:
   - job periodici (aggregati di rate, DQM, allarmi su bias e temperatura)
   - coincidence finder notturno su finestre chiuse
   - esportazione open data (HDF5/Parquet + CSV) e release annuali su Zenodo
4. **Accesso**:
   - Keycloak OIDC (ruoli project-admin, teacher, student)
   - web app scuola (FastAPI/Django + React) con isolamento per tenant in API e Postgres RLS
   - Grafana per il team e il monitoraggio operativo
   - pagine pubbliche senza login
5. **Ops**:
   - Prometheus, Loki e Alertmanager (equivalente moderno di Nagios di HiSPARC)
   - e-mail ai docenti referenti quando la stazione è offline da più di X ore
   - backup giornalieri
   - infrastruttura come codice
