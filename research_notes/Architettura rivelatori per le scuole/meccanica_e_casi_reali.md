# Mechanical design, enclosure, cabling and real-world educational cosmic-ray detectors

Scope: a 3-channel stacked plastic-scintillator muon detector (3 bars, each read by a Broadcom AFBR-S4N22P014M 2x2 mm SiPM on a small carrier PCB), a 103 x 215 mm readout PCB (LEMO 00 per channel + AND output, scope test points, 8 x M3 holes), Raspberry Pi (GPIO + I2C ADC). Materials: FDM/resin 3D printing, laser-cut PMMA, aluminium. Users: students; teachers carry it between rooms.

Method note: the research ran in a sandbox where arxiv.org, ar5iv and muonpi.org could not be fetched directly (DNS failures). Most findings come from search-engine extracts of the primary papers and pages (arXiv PDFs, project sites, distributor listings). They are cited to those primary URLs. Anything not confirmed by a source is under Inferences or Gaps.

## 1. How do existing educational/outreach detectors handle the mechanics?

### Takeaway
Every successful outreach detector uses the same recipe: a reflective inner wrap (foil, Tyvek or reflective film), then a separate opaque light seal (black tape, black paper or pond liner), then a rigid box that gives mechanical protection. Small SiPM designs (CosmicWatch, CosMO, Cosmic Pi, MuonPi, INSULAB) keep the sensor and the first electronics in the same box or on the same PCB, with very short connections. Long cables are used only by PMT systems (QuarkNet, HiSPARC), where the signals are large. The closest model for a robust, portable school product is a commercial aluminium extrusion or suitcase with acrylic end plates (CosmicWatch, INSULAB).

### Cited Findings

**CosmicWatch (MIT/UW-Madison/UDel; Axani et al., Am. J. Phys. 2018; v2; v3X 2025)**
- Original design: a 5x5x1 cm³ extruded plastic scintillator with a 6x6 mm² SensL C-Series MicroFB-60035 SiPM. The SiPM was chosen for low operating voltage, compactness, single-photon sensitivity, temperature stability and low cost — [arXiv:1801.03029](https://arxiv.org/pdf/1801.03029)
- The SiPM is optically coupled to the scintillator with optical gel, wrapped in reflective foil, and optically isolated with black electrical tape — [arXiv:1801.03029](https://arxiv.org/pdf/1801.03029); [ar5iv 1801.03029](https://ar5iv.arxiv.org/html/1801.03029)
- The PCBs were shaped to fit a small, commercially available aluminium electronics enclosure. Front and back plates are laser cut from 2.5 mm acrylic, and the SiPM assembly slides onto the enclosure's internal rails — [arXiv:1801.03029](https://arxiv.org/pdf/1801.03029)
- In the earlier university version, the SiPM board is screwed to the scintillator with optical gel and sits in a light-tight aluminium enclosure. The enclosure mating faces were machined square to give a light-tight seal. Low-amplitude pulses are listed as a sign of a non-light-tight enclosure or poor SiPM contact — [arXiv:1606.01196](https://arxiv.org/pdf/1606.01196)
- Early units used 3D-printed cases. The design later moved to "cheaper, non-3D printed parts" (extrusion plus acrylic plates) — [CosmicWatch v3X paper, arXiv:2508.12111](https://arxiv.org/html/2508.12111v2) (via search extract); [all3dp article](https://all3dp.com/diy-muon-cosmic-particle-detector/)
- The main board has an LT3461-based boost converter that raises USB 5 V to about 30 V SiPM bias, plus an amplifier and peak detector. The whole unit runs from USB — [RS DesignSpark build log part 1](https://www.rs-online.com/designspark/building-a-cosmic-ray-detector-part-1-introduction-and-planning)
- Materials cost is under US$100 per detector; the AAPT wiki gives about $100 for v2 — [arXiv:1801.03029](https://arxiv.org/pdf/1801.03029); [AAPT Advanced Labs wiki](https://advlabs.aapt.org/wiki/Cosmic_Watch_Muon_Detectors)
- v3X (2025) has an OLED display, onboard storage, environmental sensors and USB. Its front and rear faceplates give access to the SiPM output, microSD, microUSB and coincidence ports. Two units connected by a network cable form a coincidence "muon telescope". Component cost is under $100, and the build is suitable for high school students — [arXiv:2508.12111v2](https://arxiv.org/html/2508.12111v2)
- Third-party builders swapped the enclosure for an RS Pro extrusion (195-1545) of similar design. Another builder laser cut 3 mm acrylic front and rear panels. The builder found no light leaks after assembly — [RS DesignSpark part 2](https://www.rs-online.com/designspark/building-a-cosmic-ray-detector-part-2-assembly-and-initial-testing); [part 3](https://www.rs-online.com/designspark/building-a-cosmic-ray-detector-part-3-completion-and-testing)

**Cosmic Pi (CERN after-hours project, CERN OHL)**
- Plastic scintillator with optical fibre, read by an SiPM at each end. A Raspberry Pi stores and analyses the data — [Raspberry Pi blog](https://www.raspberrypi.com/news/raspberry-pi-cosmic-ray-detector-from-cern/); [OHWR wiki](https://www.ohwr.org/projects/cosmic-pi/wiki)
- Pi HAT form factor with coincidence trigger, 2-channel 12-bit ADC, GPS, MEMS barometer and I2C temperature/humidity sensor. Prototype v1 had a hard 1 Hz event-rate limit and a power supply "too noisy for the SiPM". Later versions put everything on one PCB with a snap-off section for the SiPMs — [OHWR wiki](https://www.ohwr.org/projects/cosmic-pi/wiki); [GitHub CosmicPiV1.7PCB](https://github.com/CosmicPi/CosmicPiV1.7PCB)
- The first 40 v1 units were assembled and distributed by March 2017 — [OHWR wiki](https://www.ohwr.org/projects/cosmic-pi/wiki)
- Note the lesson that a noisy supply hurts SiPMs: a Pi switching supply needs filtering before the SiPM bias and front end.

**HiSPARC (Nikhef, roof-mounted)**
- Each detector is a 1.0 x 0.5 m, 2 cm thick scintillator plate glued to a triangular light guide that feeds a PMT. An adapter mates the round PMT to the square light-guide end — [HiSPARC experiment paper, arXiv:1908.01622](https://www.arxiv.org/pdf/1908.01622); [The HiSPARC Detector](https://docs.hisparc.nl/routenet/en/The_HiSPARC_Detector.pdf)
- Assembly: clean with alcohol, wrap partly in aluminium foil and black light-proof film, glue, and cure for at least 48 h. The assembly is then wrapped in aluminium foil plus black pond liner. "Even the tiniest leak can spoil the measurements" — [Detector mounting (translated)](https://www.hisparc.nl/oud/fileadmin/HiSPARC/Handleidingen/Detector_mounting_translated.pdf); [Pavlidou page](https://www.hisparc.nl/en/?p=290)
- Housed in a commercial ski box with foam support so the plate does not bend. A hole is drilled in the bottom for the cable, and the lid is locked. Cables run to an indoor HiSPARC box (DAQ + HV) with GPS — [HiSPARC Detector Installation](https://www.hisparc.nl/oud/fileadmin/HiSPARC/Handleidingen/HiSPARC_Detector_Installation.pdf); [ICALEPCS 2013](https://accelconf.web.cern.ch/ICALEPCS2013/papers/thppc064.pdf)

**EEE – Extreme Energy Events (Centro Fermi/INFN, Italian high schools)**
- Telescopes of 3 MRPCs in a mechanical structure that allows the gap between chambers to vary. A full telescope (PC, lab equipment, cables, gas system) costs about €50,000. Costs are kept low by installing in existing school buildings — [CERN Courier](https://cerncourier.com/a/the-eee-project-big-science-goes-to-school/); [arXiv:2006.02002](https://arxiv.org/pdf/2006.02002)
- This is not a portable product. It is a fixed lab installation with a gas system, so it serves as a didactic and network model, not a mechanical one.

**QuarkNet CRMD (Fermilab)**
- Scintillator counters read by PMTs with Cockcroft-Walton bases powered from the DAQ board (up to 4 channels, programmable coincidence). Counters are wrapped in foil (light collection) plus black paper (light tightness). Do not handle the scintillator with bare hands — [QuarkNet poster](https://quarknet.org/sites/default/files/cosmic_ray_poster_for_qcc_urd_2016_-_sent_to_quarknet_staff.pdf); [CRMD assembly instructions](https://web.quarknet.org/files/cosmics/cf_crmdassemblyinstructions-small.pdf)
- The kit inventory lists 50 ft (15.24 m) PMT signal cables, a GPS antenna with 5 m cable and a 100 ft CAT-5e GPS cable. Older kits used LEMO cables — [CRMD Inventory 2024](https://new.quarknet.org/sites/default/files/content/document/file/2024-06/CRMD%20Inventory.docx)
- A teacher team found that a BNC end came off a cable and the poor connection was skewing their data — [Iowa QuarkNet 2017 write-up](https://new.quarknet.org/sites/default/files/Iowa%20Quarknet%202017%20Cosmic%20Ray%20Detector%20Writeup.docx)
- A cable-delay (T0) calibration is done by stacking counters and running about a day — [Cable Length Zeroing Tutorial](https://quarknet.i2u2.org/sites/default/files/content/document/file/2024-06/Cable%20Length%20Zeroing%20Tutorial%20.docx)
- QuarkNet noise studies identify room light and PMT dark rate as things that obscure the muon signal — [Noise in cosmic ray plastic scintillator detectors, part 2](https://new.quarknet.org/sites/default/files/Noise%20in%20cosmic%20ray%20plastic%20scintillator%20detectors%20-%20Part%202%20of%202.pdf)

**CosMO (DESY Zeuthen / Netzwerk Teilchenwelt)**
- Three plastic scintillator plates, each 20x20x1.2 cm³. Light is carried by 9 optical fibres per plate to an MPPC (SiPM). The DAQ card has software-set thresholds and coincidences, read out by a netbook. Designed to be student-operable and easy to transport — [CosMO paper, arXiv:1309.3391](https://arxiv.org/pdf/1309.3391); [DESY school lab CosMO page](https://desy.de/school/school_lab/zeuthen_site/cosmic_particles/experiments/cosmo_experiment/index_eng.html)
- Teachers can borrow the experiments from about 20 to 30 Netzwerk Teilchenwelt institutes after training — [DESY experiments page](https://www.desy.de/school/school_lab/zeuthen_site/cosmic_particles/experiments/index_eng.html); [NTW presentation 2018](https://indico.desy.de/event/19356/attachments/22472/28687/praes-NTW-kurz-Jugendliche-20180215.pdf)

**Kamiokanne (Netzwerk Teilchenwelt)**
- A commercial thermos flask filled with water, with a PMT replacing the lid to detect Cherenkov light. Some setups use two flasks in coincidence. The flask itself is the light-tight, mirrored enclosure — [DESY experiments page](https://www.desy.de/school/school_lab/zeuthen_site/cosmic_particles/experiments/index_eng.html); [teilchenwelten nr.5](https://www.teilchenwelt.de/wp-content/uploads/2023/06/teilchenwelten-nr.5-03-2012.pdf)

**MuonPi (Giessen)**
- A Raspberry Pi-based network using an inexpensive plastic scintillator plus SiPM, with timestamps accurate to tens of ns. The wiki has a "How our detectors are assembled" page, which could not be fetched here — [wiki.muonpi.org](https://wiki.muonpi.org/); [muonpi.org/muondetector.html](https://muonpi.org/muondetector.html)

**INSULAB portable school detector (Univ. Insubria + INFN Milano-Bicocca, Bomben et al. 2021)**
- A compact aluminium suitcase holding three plastic-scintillator modules with PMTs, a custom compact electronics chain and a power bank. A Raspberry Pi with a touch screen handles live monitoring. It records arrival time and time-over-threshold per module, and was used outdoors for rate versus altitude and zenith-angle measurements — [arXiv:2111.10151](https://arxiv.org/pdf/2111.10151); [IRIS Insubria](https://irinsubria.uninsubria.it/handle/11383/2143571)
- This is the closest existing analogue to the target product: 3 stacked channels, Raspberry Pi, portable, aluminium case.

**INFN OCRA and other INFN SiPM projects**
- OCRA is INFN's national outreach programme on cosmic rays, started in 2018 and covering 24 INFN divisions. Its activities used a "Cosmic Ray Cube" detector (4 scintillator layers with SiPM readout) at the LNGS student camp, and ArduSiPM on a balloon — [PoS ICRC2019 358/173](https://pos.sissa.it/358/173); [IPPOG OCRA](https://ippog-resources-portal.web.cern.ch/?p=2441)
- INFN Bari built a portable tracker from scintillator bars with WLS fibres and SiPMs, read out by a Raspberry Pi 4 with GPS — [PoS ICRC2021 395/1371](https://pos.sissa.it/395/1371)

### Inferences
- No surveyed project uses a transparent box as the light seal. Where acrylic appears (CosmicWatch), it only closes the ends of an opaque box, and the scintillator is already taped black. A didactic transparent window is therefore safe only over the electronics compartment, never over the scintillator stack.
- The INSULAB suitcase and CosmicWatch together suggest a layout: an aluminium body for robustness and shielding, a Raspberry Pi with display on top, and a power bank or USB supply.

### Gaps
- No primary details were found for the MuonPi housing, the Cosmic Ray Cube mechanics, Muonlab (Nikhef), or the CREDO smartphone approach. Searches returned no relevant or fetchable pages.
- Itemised costs for Cosmic Pi, CosMO and MuonPi were not found.

## 2. SiPM-to-electronics cabling: how long can it be, and where should the amplifier go?

### Takeaway
For a single small SiPM like the 2x2 mm AFBR-S4N22P014M, keep the analog link to the first amplifier as short as practical: a few cm to about 20 cm of shielded, ideally coaxial 50 Ω cable. Real systems that send raw SiPM signals over metres either accept degraded performance or use special techniques (series connection, pole-zero cancellation, charge amplifiers). Systems that need long runs amplify or discriminate next to the sensor and send larger or digital (LVDS) signals. In a stacked desktop detector, the readout PCB should sit directly against the bar stack, so analog cables stay within roughly 10 to 30 cm.

### Cited Findings
- The KOTO experiment put the preamplifier close to the detector: a 20 cm coax to a x50 preamp, then shielded twisted pair to the digitizer — [arXiv:1512.04524](https://arxiv.org/pdf/1512.04524) (via search extract)
- One beam monitor amplifies each MPPC signal about 20-fold with an op-amp, then converts it to LVDS with a fast comparator before transmission — [arXiv:2405.17904](https://arxiv.org/pdf/2405.17904)
- The Fermilab IFR prototype found that long (4 m) coaxial cables from SiPM to front-end cards were "not optimal" but gave a reliably working system — [SuperB TDR, arXiv:1306.5655](https://arxiv.org/pdf/1306.5655)
- SuperB's ASIC readout used one differential pair of an 8 m double-shielded multi-twisted-pair cable — [SuperB TDR](https://arxiv.org/pdf/1306.5655)
- In GERDA, about 20 m of cable plus large SiPM-array capacitance cut peak amplitude considerably, which led them to choose charge-sensitive amplifiers — [arXiv:1711.01452](https://arxiv.org/pdf/1711.01452)
- MEG II transmits unamplified SiPM signals over about 10 m of 50 Ω coax only because series-connected SiPMs have low capacitance. They also needed pole-zero cancellation for timing. The MEG upgrade measured pulse height, width and rise time versus coax length — [arXiv:1801.04688](https://arxiv.org/pdf/1801.04688); [MEG Upgrade proposal, arXiv:1301.7225](https://arxiv.org/pdf/1301.7225)
- CAEN sells SiPM "remoting" cables rated only for relocation up to 1 m with controlled impedance — [CAEN](https://caen.it/?p=52173)
- Hamamatsu sells MPPC modules with the amplifier, HV supply and temperature compensation built in. The C13367 flexible-cable variant lets the MPPC sit away from the electronics — [Hamamatsu MPPC modules catalogue](https://www.hamamatsu.com/resources/pdf/ssd/mppc_modules_kacc9019e.pdf); [C13367](https://shop.hamamatsu.com/products/mppc-module-c13367-3050ea)
- Simply paralleling MPPCs widens pulses because of the capacitance of the inactive (spectator) pixels. A head amplifier per MPPC fixes this — [Hamamatsu-based CV readout, via search extract; see arXiv:1611.03180](https://arxiv.org/pdf/1611.03180)
- Cosmic Pi removed the cabling question by putting the SiPMs on a snap-off section of the main PCB — [OHWR wiki](https://www.ohwr.org/projects/cosmic-pi/wiki)
- QuarkNet's 15 m LEMO/BNC cables work because PMT pulses are large (tens of mV, with a x10 amplifier and 3-7 mV discriminator thresholds). Even there, connector failures corrupted data — [FNAL QuarkNet toolkit](https://quarknet.fnal.gov/toolkits/ati/fnaldet.html); [Iowa QuarkNet 2017](https://new.quarknet.org/sites/default/files/Iowa%20Quarknet%202017%20Cosmic%20Ray%20Detector%20Writeup.docx)

### Inferences
- **Recommended for this product.** Mount the 103x215 mm readout PCB directly on top of or beside the bar stack, so each SiPM carrier-to-J1 cable is ≤20 to 30 cm. Use a thin 50 Ω coax for the signal (RG174 or RG316, or a micro-coax pigtail with U.FL/MMCX). Run the bias as a separate wire, or as a shielded twisted pair with the coax shield as return. Plain ribbon or unshielded jumper wire picks up Raspberry Pi and switching-supply noise; this is a general practice inference, compare the Cosmic Pi supply-noise lesson.
- **Second-best layout.** If the electronics must sit far from the bars (over 0.5 to 1 m), move the transimpedance amplifier and ideally the comparator onto each SiPM carrier. Then send discriminated LVDS or CMOS pulses over twisted pair or CAT-5/6, as CosmicWatch v3X does for its coincidence link. That makes cable length uncritical.
- Bias filtering (an RC low-pass close to the SiPM, plus a local decoupling capacitor) matters more as the cable gets longer. Measure amplitude and rise time versus cable length as MEG did.
- Use LEMO 00 only for user-facing outputs (already digital or buffered). Internal analog links should be soldered or locked micro-coax so students cannot unplug or swap them.

### Gaps
- No Broadcom application note with an explicit maximum cable length for the NUV-MT family was found. The AFBR-S4N22P014M terminal capacitance (needed to estimate cable effects) was not retrieved here; see the datasheet: [Broadcom DS103](https://www.mouser.lt/datasheet/2/678/AFBR_S4N22P014M_DS103-3367010.pdf).
- No source gave measured pickup comparisons for RG174 vs RG316 vs twisted pair at SiPM signal levels.

## 3. Light tightness: wrapping, enclosure leaks, testing

### Takeaway
Use two layers on each bar: a reflective wrap (aluminium foil, Tyvek or ESR-type film) that keeps light in, then an opaque wrap (black PVC electrical tape, black paper or pond liner) that keeps room light out. Then put the bars in an opaque box with tight joints or foam gaskets. Test by comparing the dark/trigger rate with lights on and off, and by sweeping a bright torch along the seams.

### Cited Findings
- CosmicWatch: reflective foil plus black electrical tape around the scintillator and SiPM; optical gel coupling — [arXiv:1801.03029](https://arxiv.org/pdf/1801.03029)
- HiSPARC: aluminium foil plus black pond liner; "even the tiniest leak can spoil the measurements" — [HiSPARC mounting guide](https://www.hisparc.nl/oud/fileadmin/HiSPARC/Handleidingen/Detector_mounting_translated.pdf)
- QuarkNet: foil plus black paper — [QuarkNet poster](https://quarknet.org/sites/default/files/cosmic_ray_poster_for_qcc_urd_2016_-_sent_to_quarknet_staff.pdf)
- A Tel Aviv design paints the four long side faces black and keeps the top and bottom polished — [via search extract of arXiv:1606.01196-adjacent results; Afeka NIM A](https://www.afeka.ac.il/en/industry-relations/research-authority/scintillator-sipm-detector-for-tracking-and-energy-deposition-measurements/)
- Machined, square mating faces were used to make the aluminium enclosure light-tight — [arXiv:1606.01196](https://arxiv.org/pdf/1606.01196)
- Leak test used by QuarkNet (Suffolk CCC): compare the rate with the box covered by a black tarp and lights off against the box uncovered with room lights on — [Making a Dark Box Light Tight](https://new.quarknet.org/sites/default/files/Making%20a%20Dark%20box%20Light%20Tight%20-%2020171019.pdf)
- A rapid leak-finding method turns the photosensor output into an audio tone, like a Geiger counter, so seams can be scanned with a torch — [McMillan, arXiv:1907.03023](https://arxiv.org/pdf/1907.03023)
- A 3D-printed dark box was enough for MPPC readout of 3D-printed scintillator elements (material not stated) — [arXiv:2202.10961](https://arxiv.org/pdf/2202.10961)
- Do not touch scintillator with bare hands, and clean it with alcohol before wrapping — [QuarkNet CRMD assembly](https://web.quarknet.org/files/cosmics/cf_crmdassemblyinstructions-small.pdf); [HiSPARC mounting](https://www.hisparc.nl/oud/fileadmin/HiSPARC/Handleidingen/Detector_mounting_translated.pdf)

### Inferences
- **Design rule: light-tight at the bar level, not the box level.** Wrap each bar and its SiPM carrier fully, foil plus 2 layers of black tape, as CosmicWatch does. Then the outer enclosure can include a PMMA window over the electronics without risk. The box gives a second barrier only.
- Cable exits from the wrapped bar must be sealed (black tape, heat-shrink, or a black potted grommet). Classically these are the worst leak points.
- 3D-printed parts in contact with the light path should be black, opaque material with ≥2 mm wall and 100% perimeters at the joints, plus foam or EPDM gaskets. Unpigmented PETG and PLA are translucent (general knowledge, not sourced here).
- Acceptance test for each finished unit: singles rate per channel with the room dark vs a 1000-lux lamp on the case. Any change beyond statistical error means a leak. With 3-fold coincidence the rate will hide leaks, so always test singles.

### Gaps
- No quantitative study of light transmission through printed PETG/ASA versus wall thickness was found.

## 4. Enclosure materials and commercial enclosures (aluminium, PMMA, 3D print, combinations)

### Takeaway
A hybrid design is best. Use an aluminium extrusion or folded aluminium body as the main structure and electromagnetic shield, with the wrapped bars and readout PCB inside. Add laser-cut PMMA end or top plates for the didactic view of the electronics, and use 3D-printed internal parts (bar cradles, SiPM carrier holders, cable clamps, Pi bracket), preferably in a flame-retardant grade. This is the CosmicWatch formula (aluminium extrusion plus 2.5 to 3 mm acrylic end plates, abandoning all-3D-printed cases) and the INSULAB formula (aluminium suitcase).

### Cited Findings
- CosmicWatch: aluminium extrusion plus 2.5 mm laser-cut acrylic plates. Early 3D-printed cases were replaced by cheaper non-printed parts — [arXiv:1801.03029](https://arxiv.org/pdf/1801.03029); [arXiv:2508.12111v2](https://arxiv.org/html/2508.12111v2)
- INSULAB school detector: compact aluminium suitcase — [arXiv:2111.10151](https://arxiv.org/pdf/2111.10151)
- HiSPARC: a commercial ski box with foam — [HiSPARC installation](https://www.hisparc.nl/oud/fileadmin/HiSPARC/Handleidingen/HiSPARC_Detector_Installation.pdf)
- Hammond 1455 extrusions: the PCB slides in internal slots, IP54. Listed sizes include 1455N2201 (103 mm external width x 53 mm x 220 mm), 1455Q2201/2 (125 x 52 x 220 mm), 1455R2202 (160 x 31 x 220 mm) and 1455T2201/2 (165 x 52 x 220 mm). Black, clear-anodised and red finishes exist. The 1455T2201RD is about US$43.62 each at one distributor — [element14 1455T2201RD](https://au.element14.com/hammond/1455t2201rd/pcb-box-enclosure-alum-red/dp/2469311); [Farnell 1455R2202](https://ie.farnell.com/hammond/1455r2202/case-aluminium-31x160x220mm/dp/2763777); [element14 1455Q2201](https://my.element14.com/hammond/1455q2201/case-aluminium-52x120x220mm/dp/1511223); [RS 1455 black 220x165x52](https://my.rs-online.com/web/p/general-purpose-enclosures/8685034); [RS 1455Q2202](https://ph.rs-online.com/web/p/general-purpose-enclosures/2256353); [Newark](https://www.newark.com/hammond/1455t2201rd/pcb-box-enclosure-aluminum-red/dp/30Y9630)
- Flame-retardant FDM filaments rated UL94 V-0 exist: Polymaker PolyMax PC-FR, Elegoo/Bambu PC-FR, Spectrum PC/ABS FR V0 (Vicat 104 °C), 3DXTech FireWire PC-ABS-FR (V-0 at 1.5 and 2.0 mm, 5VB at 2.0 mm), and McMaster FR ABS. Prusa PETG "Black Jet V0" is the only V-0 PETG noted. "Certified to the standard" is often not a UL listing (Bambu tested but did not obtain official UL certification). V-0 depends on wall thickness, and FR filaments need an enclosed printer and ventilation — [Polymaker PC-FR](https://shop.thevirtualfoundry.com/products/polymaker-polymax-pc-fr-tough-ul94-flame-retardent-filament-3d-printer-filament-1kg-1-75mm); [Elegoo PC-FR](https://www.elegoo.com/products/pc-fr); [Spectrum PC/ABS FR V0](https://spectrumfilaments.com/en/filament/pc-abs-fr-v0/); [3DXTech FireWire](https://www.matterhackers.com/store/l/3dxtech-firewire-flame-retardant-pc-abs-filament/sk/MUZX4DGR); [Bambu forum](https://forum.bambulab.com/t/filament-resistance-to-flammability-ul94-v0/82057); [McMaster](https://www.mcmaster.com/products/3d-printer-filaments/flame-retardant-impact-resistant-3d-printer-filaments/)

### Inferences
- **Fit check.** The 215 mm PCB fits the 220 mm-deep Hammond 1455 family only if the internal slot length and end-plate thickness allow it. A 103 mm-wide PCB needs the ≥125 mm-wide (Q) or 160/165 mm-wide (R/T) bodies, since the N body is 103 mm external. A 1455T2201/2 (165 x 52 x 220) would hold the readout board in the slots with space for a Pi beside it, but the bars must then go in a separate housing. Verify against the Hammond drawings.
- **Preferred layout (two-zone box, "sandwich").**
  - Lower zone: an opaque aluminium (or black FR-PC-printed) tray holding the 3 wrapped bars stacked in printed cradles with foam, with the SiPM carriers at one end.
  - Upper zone: the readout PCB on M3 standoffs right above the SiPM end, keeping the analog cables to 10 to 20 cm, under a 3 to 4 mm clear PMMA lid (didactic window) with countersunk tamper screws.
  - Pi compartment: at the opposite end or in a separate printed or aluminium pod with vents, giving thermal and noise isolation. LEMO 00 outputs and the AND output on a front aluminium panel; USB-C or DC power and Ethernet on the rear.
- **Aluminium pros:** EMI shield (important near a Pi), heat spreading, robust, easy to anodise; machined or folded joints are light-tight. **Cons:** cost, and edges must be deburred.
- **PMMA pros:** transparent, laser-cut, looks great. **Cons:** no shielding, brittle (cracks at screw holes if over-tightened; PC is tougher for a school product), and must never be the light seal.
- **3D-print pros:** custom shapes and branding. **Cons:** light leaks through thin or translucent walls, layer delamination, creep, and flammability unless an FR grade is used.

### Gaps
- Bopla, Fischer Elektronik and Teko catalogue entries were not retrieved in this session. Only Hammond data is sourced.
- No source compared PMMA and polycarbonate breakage in school use.

## 5. Thermal management: SiPM gain drift and heat from the Raspberry Pi

### Takeaway
The AFBR-S4N22P014M breakdown voltage drifts about +30 mV/°C. At fixed bias, gain (and therefore pulse amplitude above a fixed threshold) changes with temperature, so the Pi's heat must be kept away from the bars, and temperature should be logged or compensated.

### Cited Findings
- AFBR-S4N22P014M: V_BR 32.5 V typical; temperature coefficient of V_BR about 30 mV/°C; PDE 63%; dark current 0.98 µA (at 12 V overvoltage, 25 °C); operating range −20 to +60 °C — [Farnell listing](https://be.farnell.com/broadcom/afbr-s4n22p014m/silicon-photomultiplier-1-ch-420nm/dp/4351470); [Broadcom DS103 datasheet](https://www.mouser.lt/datasheet/2/678/AFBR_S4N22P014M_DS103-3367010.pdf)
- Hamamatsu MPPC modules include temperature compensation of the bias — [Hamamatsu MPPC modules](https://www.hamamatsu.com/resources/pdf/ssd/mppc_modules_kacc9019e.pdf)
- Cosmic Pi includes an I2C temperature/humidity sensor and a barometer on the HAT — [OHWR wiki](https://www.ohwr.org/projects/cosmic-pi/wiki)

### Inferences
- At an overvoltage of a few volts, a 10 °C rise costs 0.3 V of overvoltage. That is a gain change of several percent to about 10% (inference from 30 mV/°C; the exact gain-vs-OV slope is in the DS103 datasheet). For a fixed-threshold discriminator, this changes efficiency near threshold.
- Mitigations:
  - Put the Pi in a separately ventilated compartment, or outside the light-tight zone (vents with a labyrinth or chevron baffle only on the Pi pod).
  - Put an NTC or I2C temperature sensor on the SiPM end and log it with the data.
  - Optionally use firmware or DAC bias compensation (+30 mV/°C).
  - Choose a low-power Pi (Pi Zero 2 W, about 1 to 3 W, vs Pi 4/5 at 3 to 7 W+; general knowledge, not sourced here).
- The scintillator zone can stay sealed, because the SiPMs dissipate microwatts.

### Gaps
- No measured temperature rise inside a closed Pi-plus-detector enclosure was found.

## 6. Safety for schools (SELV, edges, connectors, strain relief, tamper resistance)

### Takeaway
A 41 V internal bias is below the common 60 V DC SELV threshold (to be confirmed against the standard). Real projects still enclose all bias circuitry, use locking or robust connectors, and power from USB or a power bank. Field experience (QuarkNet) shows that connectors and cables are the most common failure points in classrooms.

### Cited Findings
- CosmicWatch generates the about 30 V bias internally from USB 5 V, so no external HV is exposed — [RS DesignSpark part 1](https://www.rs-online.com/designspark/building-a-cosmic-ray-detector-part-1-introduction-and-planning)
- The INSULAB school detector runs from a power bank — [arXiv:2111.10151](https://arxiv.org/pdf/2111.10151)
- A QuarkNet school team lost data because a BNC connector came off a cable — [Iowa QuarkNet 2017](https://new.quarknet.org/sites/default/files/Iowa%20Quarknet%202017%20Cosmic%20Ray%20Detector%20Writeup.docx)
- HiSPARC instructions stress mechanically supporting the plate with foam, avoiding stress on the glue joints, and locking the box — [HiSPARC installation](https://www.hisparc.nl/oud/fileadmin/HiSPARC/Handleidingen/HiSPARC_Detector_Installation.pdf)

### Inferences
- Generate the bias on-board from 5 V and never bring it to an external connector. Add current limiting (series resistor) so a fault is harmless.
- Use a USB-C PD or 5 V DC barrel jack with a polyfuse and reverse-polarity protection, plus a CE-marked external supply, so mains never enters the box.
- Use LEMO 00 (push-pull, latching) for outputs and recessed or guarded scope test points. Put a cable gland or printed strain-relief clamp on every internal cable. Mount the bars so they cannot shift when the unit is carried: foam plus printed cradles, with a carry handle on the aluminium body.
- Round or deburr aluminium edges, use rubber feet and corner bumpers, and fix the PMMA lid with Torx-pin or Pentalobe security screws.
- Use UL94 V-0 or at least HB-rated materials around the electronics (FR-PC or PC/ABS printed parts).

### Gaps
- I did not retrieve the text of IEC 62368-1 or IEC 61140 for the exact ES1/SELV limits (commonly cited as 60 V DC). The caller should verify this before claiming compliance.
- No sources on CE marking obligations for educational kits were retrieved.

## 7. Making it attractive and didactic, plus indicative costs (EUR)

### Takeaway
Successful outreach products combine visible electronics (CosmicWatch's acrylic plates and OLED, INSULAB's touch screen), real-time feedback, and portability. Detector BOMs are around US$100 for single-channel SiPM units. A robust 3-channel school product with aluminium plus PMMA will likely cost a few hundred euros in materials.

### Cited Findings
- CosmicWatch v3X: OLED display, coincidence via network cable, under $100 components, buildable by high school students — [arXiv:2508.12111v2](https://arxiv.org/html/2508.12111v2)
- INSULAB: Raspberry Pi with touch screen for live monitoring in a portable aluminium suitcase — [arXiv:2111.10151](https://arxiv.org/pdf/2111.10151)
- Typical part prices: Hammond 1455 extrusion about US$44 each — [Newark](https://www.newark.com/hammond/1455t2201rd/pcb-box-enclosure-aluminum-red/dp/30Y9630). A CosmicWatch unit is about US$100 — [AAPT wiki](https://advlabs.aapt.org/wiki/Cosmic_Watch_Muon_Detectors). A full EEE telescope is about €50,000 — [CERN Courier](https://cerncourier.com/a/the-eee-project-big-science-goes-to-school/)

### Inferences
- **Didactic features:**
  - A PMMA window over the readout PCB, with silk-screen labels for "SiPM bias", "amplifier", "comparator" and "AND".
  - Edge-lit PMMA or per-channel LEDs flashing on each hit, with a buzzer for coincidences.
  - An engraved cut-away diagram of the stacked bars on the lid.
  - Scope test points exposed under a hinged guard.
  - A small display, or a web dashboard from the Pi.
  - A rotatable stack (zenith-angle studies, as INSULAB did) via a printed pivot.
- **Indicative EUR costs per unit (estimates, not sourced unless noted):**
  - Option A, all-3D-printed FR-PC with PMMA lid: about €40-80 (filament, PMMA, gaskets, screws).
  - Option B, Hammond-type aluminium extrusion plus PMMA end and top plates plus printed internals: about €80-150. The extrusion itself is about €40-60; see the Newark price above.
  - Option C, custom folded and anodised aluminium chassis or aluminium suitcase plus PMMA window: about €150-300 in small series.
  - Add cabling (3 short micro-coax pigtails, LEMO 00 panel sockets, which are relatively expensive at roughly €15-30 each, so 4 of them ≈ €60-120), foam, handle and feet: about €80-150.

### Gaps
- No verified EUR prices for LEMO 00 panel connectors, PMMA laser cutting or anodising were retrieved; the figures above are rough estimates to confirm with suppliers (e.g., Farnell, RS, local laser-cut services).
