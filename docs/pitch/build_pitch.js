// Pitch: rivelatore di muoni a 3 canali per attivita' STEM
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("/root/.claude/skills/synced/433055a4-7d3c-41b2-a2fd-13f061a284ba_e1bb5bb9-2414-40dc-9636-c4f6f6b89b12/pptx/scripts/apply_theme.js");

const THEME = {
  name: "Muoni",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A1F27", lt1: "FFFFFF", dk2: "262D38", lt2: "C9D1DB",
    accent1: "35C6E8", accent2: "F2A93B", accent3: "8C98A8", accent4: "5BD18B",
    accent5: "E5534B", accent6: "3A4452", hlink: "35C6E8", folHlink: "8C98A8",
  },
};
const HEX = THEME.colors;
const IMG = __dirname + "/img/";

async function icon(Comp, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";            // 13.333 x 7.5
  pres.title = "Rivelatore di muoni a 3 canali";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;
  const W = 13.333;

  // ---------------------------------------------------------------- layout
  pres.defineSlideMaster({
    title: "TITOLO",
    background: { color: C.text1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 2.0, w: 5.6, h: 1.6,
        fontSize: 44, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.75, w: 5.4, h: 1.4,
        fontSize: 20, color: C.background2, valign: "top", align: "left", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENUTO",
    background: { color: C.text1 },
    margin: [0.5, 0.6, 0.6, 0.6],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.4, w: 12.1, h: 0.85,
        fontSize: 34, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
      { text: { text: "Rivelatore di muoni · 3 canali · attività STEM",
        options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent3, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent3, align: "right" },
  });

  const content = (sec) => pres.addSlide({ masterName: "CONTENUTO", sectionTitle: sec });
  const tb = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, margin: 0 }, o));
  const card = (s, x, y, w, h, name) => s.addShape(pres.shapes.ROUNDED_RECTANGLE,
    { x, y, w, h, rectRadius: 0.12, fill: { color: C.text2 }, line: { type: "none" }, objectName: name });
  const circle = (s, x, y, d, color, name) => s.addShape(pres.shapes.OVAL,
    { x, y, w: d, h: d, fill: { color }, line: { type: "none" }, objectName: name });

  const ic = {
    atom: await icon(fa.FaAtom), chip: await icon(fa.FaMicrochip), layers: await icon(fa.FaLayerGroup),
    tag: await icon(fa.FaTag), book: await icon(fa.FaBookOpen), bolt: await icon(fa.FaBolt),
    clock: await icon(fa.FaHourglassHalf), warn: await icon(fa.FaExclamationTriangle),
    ruler: await icon(fa.FaRulerCombined), check: await icon(fa.FaCheckCircle),
    cart: await icon(fa.FaShoppingCart), tools: await icon(fa.FaTools), wave: await icon(fa.FaWaveSquare),
    school: await icon(fa.FaChalkboardTeacher), pi: await icon(fa.FaRaspberryPi), ring: await icon(fa.FaDotCircle),
  };

  // ================================================================ 1 titolo
  pres.addSection({ title: "Apertura" });
  let s = pres.addSlide({ masterName: "TITOLO", sectionTitle: "Apertura" });
  s.addText("Muoni in classe", { placeholder: "title" });
  s.addText("Un rivelatore di raggi cosmici a 3 canali, progettato per le attività STEM nelle scuole",
    { placeholder: "body" });
  tb(s, "5 schede · 15 canali · budget completo €745", {
    x: 0.6, y: 5.45, w: 5.4, h: 0.4, fontSize: 16, bold: true, color: C.accent1 });
  s.addImage({ path: IMG + "iso.png", x: 6.6, y: 1.4, w: 6.3, h: 6.3 / 1.551, objectName: "render scheda iso" });
  s.addNotes("Presentiamo una scheda per rivelare i muoni dei raggi cosmici, pensata per portare la fisica delle particelle nelle scuole. Tre canali, uscita in coincidenza, tutto leggibile direttamente sulla scheda.");

  // ================================================================ 2 il fenomeno
  pres.addSection({ title: "Perché" });
  s = content("Perché");
  s.addText("Ogni secondo un muone attraversa la tua mano", { placeholder: "title" });
  const stats = [
    ["≈ 1", "muone per cm² al minuto, al livello del mare", ic.atom],
    ["15 km", "la quota a cui nascono, quando i raggi cosmici urtano l'atmosfera", ic.layers],
    ["2,2 µs", "la loro vita media: arrivano a terra solo grazie alla relatività", ic.clock],
  ];
  stats.forEach(([big, txt, im], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.6, 3.8, 4.1, "stat " + i);
    circle(s, x + 0.4, 1.95, 0.75, C.accent1, "icona " + i);
    s.addImage({ data: im, x: x + 0.57, y: 2.12, w: 0.41, h: 0.41 });
    tb(s, big, { x: x + 0.4, y: 2.95, w: 3.1, h: 1.0, fontSize: 54, bold: true, color: C.background1,
      fontFace: THEME.headFontFace });
    tb(s, txt, { x: x + 0.4, y: 4.05, w: 3.1, h: 1.3, fontSize: 16, color: C.background2, valign: "top" });
  });
  tb(s, "Un fenomeno invisibile che gli studenti possono contare, misurare e collegare alla relatività ristretta.",
    { x: 0.6, y: 6.05, w: 12.1, h: 0.5, fontSize: 16, italic: true, color: C.accent1 });
  s.addNotes("Il flusso di muoni al suolo è circa un muone per centimetro quadrato al minuto: sulla superficie di una mano, circa uno al secondo. Nascono a circa 15 km di quota e vivono 2,2 microsecondi: senza la dilatazione dei tempi non arriverebbero a terra. È un aggancio naturale con il programma di fisica.");

  // ================================================================ 3 come funziona
  s = content("Perché");
  s.addText("Dalla luce al segnale digitale in quattro passi", { placeholder: "title" });
  const steps = [
    ["1", "SiPM", "trasforma il lampo di luce della barra in un impulso di corrente"],
    ["2", "Amplificatore", "due transistor ingrandiscono l'impulso"],
    ["3", "Comparatore", "decide: l'impulso supera la soglia? sì / no"],
    ["4", "Uscita", "impulso digitale 0–3,3 V sul connettore LEMO"],
  ];
  steps.forEach(([n, t, d], i) => {
    const x = 0.6 + i * 3.1;
    card(s, x, 1.6, 2.75, 2.55, "passo " + n);
    circle(s, x + 0.3, 1.85, 0.6, C.accent1, "numero " + n);
    tb(s, n, { x: x + 0.3, y: 1.85, w: 0.6, h: 0.6, fontSize: 22, bold: true, color: C.text1, align: "center", valign: "middle" });
    tb(s, t, { x: x + 0.3, y: 2.6, w: 2.2, h: 0.45, fontSize: 20, bold: true, color: C.background1 });
    tb(s, d, { x: x + 0.3, y: 3.1, w: 2.2, h: 0.95, fontSize: 14, color: C.background2, valign: "top" });
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.8, y: 2.7, w: 0.25, h: 0.35,
      fill: { color: C.accent1 }, line: { type: "none" }, objectName: "freccia " + i });
  });
  const sup = [
    ["A", "Alimentazione SiPM", "genera ~38 V; V1 la regola, un diodo la corregge con la temperatura", 0],
    ["B", "Soglia", "V2 fissa il livello che separa segnale e rumore", 2],
    ["C", "LED", "si accende per ~10 ms a ogni evento", 3],
  ];
  sup.forEach(([n, t, d, col]) => {
    const x = 0.6 + col * 3.1;
    card(s, x, 4.5, 2.75, 2.15, "supporto " + n);
    circle(s, x + 0.3, 4.75, 0.6, C.accent2, "lettera " + n);
    tb(s, n, { x: x + 0.3, y: 4.75, w: 0.6, h: 0.6, fontSize: 22, bold: true, color: C.text1, align: "center", valign: "middle" });
    tb(s, t, { x: x + 1.05, y: 4.8, w: 1.6, h: 0.5, fontSize: 17, bold: true, color: C.background1, valign: "middle" });
    tb(s, d, { x: x + 0.3, y: 5.5, w: 2.25, h: 1.05, fontSize: 14, color: C.background2, valign: "top" });
  });
  tb(s, "Riga alta: il percorso del segnale.\nRiga bassa: i circuiti che lo servono, sotto il blocco a cui servono — come sulla scheda.",
    { x: 3.7 + 0.15, y: 4.6, w: 2.6, h: 1.9, fontSize: 14, italic: true, color: C.accent3, valign: "middle" });
  s.addNotes("La catena di un canale ha quattro blocchi numerati, gli stessi numeri stampati sulla scheda. Sotto ci sono i tre circuiti di supporto, con le lettere A, B, C. Gli studenti possono seguire il segnale con l'oscilloscopio da un blocco al successivo.");

  // ================================================================ 4 scheda didattica
  pres.addSection({ title: "La scheda" });
  s = content("La scheda");
  s.addText("Una scheda che si spiega da sola", { placeholder: "title" });
  s.addImage({ path: IMG + "top.png", x: 0.6, y: 1.4, w: 5.45 * 0.553, h: 5.45, objectName: "render scheda dall'alto" });
  const feats = [
    [ic.layers, "Fasce dall'alto in basso", "alimentazione → tre canali identici → coincidenza"],
    [ic.chip, "Blocchi numerati come nello schema", "1–4 percorso del segnale, A–C circuiti di supporto"],
    [ic.tag, "Ogni componente ha il suo nome", "tutti i riferimenti e i nomi dei test point stampati in serigrafia"],
    [ic.book, "Una legenda sul retro", "«Come funziona», da leggere girando la scheda"],
  ];
  feats.forEach(([im, t, d], i) => {
    const y = 1.55 + i * 1.3;
    circle(s, 4.1, y, 0.75, C.accent1, "icona " + t);
    s.addImage({ data: im, x: 4.27, y: y + 0.17, w: 0.41, h: 0.41 });
    tb(s, t, { x: 5.15, y: y - 0.02, w: 7.5, h: 0.42, fontSize: 20, bold: true, color: C.background1 });
    tb(s, d, { x: 5.15, y: y + 0.42, w: 7.5, h: 0.45, fontSize: 16, color: C.background2 });
  });
  tb(s, "PCB 103 × 215 mm, 2 strati, 8 fori M3 · 147 componenti montati in fabbrica",
    { x: 4.1, y: 6.45, w: 8.6, h: 0.35, fontSize: 12, color: C.accent3 });
  s.addNotes("La scheda è organizzata come lo schema: in alto l'alimentazione, poi tre canali identici, in fondo la coincidenza. Ogni blocco ha il suo nome e il suo numero, ogni componente il suo riferimento. Sul retro c'è una legenda che spiega il funzionamento.");

  // ================================================================ 5 test point
  s = content("La scheda");
  s.addText("Gli studenti misurano dove serve", { placeholder: "title" });
  s.addImage({ path: IMG + "tp.png", x: 0.6, y: 1.45, w: 7.6, h: 7.6 / 1.6, objectName: "test point Keystone" });
  const tps = [
    ["24", "test point per scheda, rossi per i segnali e neri per la massa"],
    ["9 mm", "di pista dal nodo al test point (erano 94): la sonda non disturba il segnale"],
    ["× 3", "stessi punti nello stesso posto in ogni canale"],
  ];
  tps.forEach(([big, d], i) => {
    const y = 1.45 + i * 1.62;
    card(s, 8.6, y, 4.1, 1.45, "callout " + i);
    tb(s, big, { x: 8.85, y: y + 0.15, w: 1.6, h: 1.15, fontSize: 36, bold: true, color: C.accent1,
      fontFace: THEME.headFontFace, valign: "middle" });
    tb(s, d, { x: 10.4, y: y + 0.15, w: 2.15, h: 1.15, fontSize: 14, color: C.background2, valign: "middle" });
  });
  s.addNotes("Ogni canale ha sei test point accanto al punto che misurano: segnale del SiPM, ingresso del comparatore, soglia, uscita, bias e massa. Le piste sono corte, quindi l'oscilloscopio vede il segnale vero. Gli anelli Keystone sono opzionali: in alternativa si usano pin di strip, già nel budget.");

  // ================================================================ 6 coincidenza
  s = content("La scheda");
  s.addText("La coincidenza separa i muoni dal rumore", { placeholder: "title" });
  s.addImage({ path: IMG + "coinc.png", x: 6.0, y: 1.45, w: 6.7, h: 6.7 / 1.6, objectName: "zona coincidenza" });
  const co = [
    [ic.layers, "Tre barre impilate", "un muone le attraversa tutte e tre nello stesso istante"],
    [ic.wave, "AND a tre ingressi", "l'uscita va a 1 solo se i canali inclusi vedono un evento insieme"],
    [ic.ring, "Jumper CH1–CH3", "coincidenza doppia o tripla, scelta dagli studenti"],
    [ic.pi, "Lettura con Raspberry Pi", "4 uscite LEMO; conteggi e tempi registrati via GPIO"],
  ];
  co.forEach(([im, t, d], i) => {
    const y = 1.5 + i * 1.3;
    circle(s, 0.6, y, 0.7, C.accent1, "icona " + t);
    s.addImage({ data: im, x: 0.76, y: y + 0.16, w: 0.38, h: 0.38 });
    tb(s, t, { x: 1.55, y: y - 0.03, w: 4.2, h: 0.4, fontSize: 18, bold: true, color: C.background1 });
    tb(s, d, { x: 1.55, y: y + 0.38, w: 4.2, h: 0.75, fontSize: 14, color: C.background2, valign: "top" });
  });
  s.addNotes("Il rumore termico del SiPM produce impulsi in un canale alla volta; un muone invece attraversa tutte le barre insieme. La porta AND conta solo gli eventi simultanei. Con i jumper si sceglie quali canali includere. Le quattro uscite si leggono con un Raspberry Pi.");

  // ================================================================ 7 verifiche
  s = content("La scheda");
  s.addText("Simulato e verificato prima della produzione", { placeholder: "title" });
  const ver = [
    ["41,7 V", "alta tensione dal survoltore (simulata 41,65 V)"],
    ["38,4 V", "bias del SiPM, regolabile con V1"],
    ["3,27 V", "impulso di un muone all'uscita, pronto per il Raspberry Pi"],
    ["10,9 ms", "lampeggio del LED a ogni evento"],
    ["0", "errori DRC sul PCB"],
    ["0", "errori di connettività tra schema e PCB"],
  ];
  ver.forEach(([big, d], i) => {
    const x = 0.6 + (i % 3) * 4.1, y = 1.55 + Math.floor(i / 3) * 2.45;
    card(s, x, y, 3.8, 2.2, "verifica " + i);
    tb(s, big, { x: x + 0.35, y: y + 0.25, w: 3.1, h: 0.95, fontSize: 44, bold: true,
      color: i < 4 ? C.accent1 : C.accent4, fontFace: THEME.headFontFace });
    tb(s, d, { x: x + 0.35, y: y + 1.2, w: 3.1, h: 0.85, fontSize: 15, color: C.background2, valign: "top" });
  });
  tb(s, "Simulazione LTspice/ngspice della scheda completa: impulsi dei muoni accettati, conteggi di buio rifiutati.",
    { x: 0.6, y: 6.5, w: 12.1, h: 0.35, fontSize: 12, color: C.accent3 });
  s.addNotes("Prima di ordinare abbiamo simulato tutta la scheda con modelli dei componenti: alimentazioni, alta tensione, bias, impulsi e LED tornano con i valori attesi. Il PCB passa il controllo geometrico e la verifica di connettività rispetto allo schema.");

  // ================================================================ 8 budget
  pres.addSection({ title: "Budget" });
  s = content("Budget");
  s.addText("Circa €745 per cinque schede complete", { placeholder: "title" });
  s.addChart(pres.charts.DOUGHNUT, [{
    name: "Budget (€, IVA inclusa)",
    labels: ["SiPM (15)", "Componenti da saldare", "PCB e montaggio JLCPCB"],
    values: [312.01, 268.55, 164.08],
  }], {
    x: 0.6, y: 1.4, w: 5.8, h: 5.2, holeSize: 58,
    chartColors: [HEX.accent1, HEX.accent2, HEX.accent3],
    showLegend: true, legendPos: "b", legendFontSize: 14, legendColor: HEX.lt2, legendFontFace: "+mn-lt",
    showValue: true, showPercent: false, dataLabelColor: HEX.dk1, dataLabelFontSize: 13,
    dataLabelFontFace: "+mn-lt", dataLabelFormatCode: "€#,##0", dataLabelFontBold: true,
    showTitle: false, dataBorder: { pt: 1, color: HEX.dk1 },
  });
  const bud = [
    ["€149", "per scheda, con i 3 SiPM"],
    ["€87", "per scheda senza SiPM: elettronica e PCB"],
    ["42%", "del costo sono i sensori"],
  ];
  bud.forEach(([big, d], i) => {
    const y = 1.5 + i * 1.55;
    card(s, 7.0, y, 5.7, 1.35, "budget " + i);
    tb(s, big, { x: 7.3, y: y + 0.12, w: 2.2, h: 1.1, fontSize: 40, bold: true,
      color: i === 2 ? C.accent1 : C.background1, fontFace: THEME.headFontFace, valign: "middle" });
    tb(s, d, { x: 9.55, y: y + 0.12, w: 3.0, h: 1.1, fontSize: 16, color: C.background2, valign: "middle" });
  });
  tb(s, "IVA inclusa. Esclusi: alimentatore 5 V, cavi, scintillatori. LEMO già disponibili.",
    { x: 7.0, y: 6.25, w: 5.7, h: 0.5, fontSize: 12, color: C.accent3 });
  s.addNotes("Il totale per cinque schede è di circa 745 euro IVA inclusa: 164 per PCB e montaggio da JLCPCB, 581 per i componenti da Mouser, di cui 312 sono i 15 SiPM. Una scheda completa costa circa 149 euro, senza sensori circa 87.");

  // ================================================================ 9 preventivi
  s = content("Budget");
  s.addText("I preventivi", { placeholder: "title" });
  const H = (t) => ({ text: t, options: { bold: true, color: C.text1, fill: { color: C.accent1 } } });
  const row = (a, b, bold = false) => [
    { text: a, options: { bold, color: C.background1 } },
    { text: b, options: { bold, color: C.background1, align: "right" } }];
  const tblOpt = (x, w, cw) => ({ x, y: 1.75, w, colW: cw, fontSize: 13, fontFace: "Calibri",
    fill: { color: C.text2 }, border: { type: "solid", pt: 0.75, color: HEX.dk1 }, margin: [0.04, 0.1, 0.04, 0.1], rowH: 0.36 });
  tb(s, "JLCPCB · 5 PCB + montaggio di 131 componenti", { x: 0.6, y: 1.3, w: 4.6, h: 0.35, fontSize: 15, bold: true, color: C.accent1 });
  s.addTable([
    [H("Voce"), { text: "€", options: { bold: true, color: C.text1, fill: { color: C.accent1 }, align: "right" } }],
    row("Merce", "106,35"), row("Spedizione", "28,14"), row("Dogana e IVA", "29,59"),
    row("Totale", "164,08", true),
  ], tblOpt(0.6, 4.6, [3.4, 1.2]));
  tb(s, "Mouser · componenti da saldare e sensori", { x: 5.7, y: 1.3, w: 7.0, h: 0.35, fontSize: 15, bold: true, color: C.accent1 });
  s.addTable([
    [H("Parte"), { text: "Qtà", options: { bold: true, color: C.text1, fill: { color: C.accent1 }, align: "right" } },
     { text: "€", options: { bold: true, color: C.text1, fill: { color: C.accent1 }, align: "right" } }],
    ...[["SiPM AFBR-S4N22P014M", "15", "255,75"], ["MAX961ESA+ (comparatore)", "16", "94,40"],
      ["LT1636CS8 (op-amp)", "16", "70,72"], ["LT3461AES6 (alta tensione)", "6", "34,38"],
      ["Ponticelli, strip, LDO, diodi", "57", "20,62"]].map(([a, q, b]) => [
      { text: a, options: { color: C.background1 } }, { text: q, options: { color: C.background1, align: "right" } },
      { text: b, options: { color: C.background1, align: "right" } }]),
    [{ text: "Subtotale (spedizione gratuita, dazi inclusi)", options: { color: C.background1 } }, "", { text: "475,87", options: { color: C.background1, align: "right" } }],
    [{ text: "IVA 22%", options: { color: C.background1 } }, "", { text: "104,69", options: { color: C.background1, align: "right" } }],
    [{ text: "Totale", options: { bold: true, color: C.background1 } }, "", { text: "580,56", options: { bold: true, color: C.background1, align: "right" } }],
  ], tblOpt(5.7, 7.0, [4.6, 0.9, 1.5]));
  card(s, 0.6, 4.05, 4.6, 1.55, "totale generale");
  tb(s, "Totale generale", { x: 0.85, y: 4.2, w: 4.1, h: 0.4, fontSize: 16, color: C.background2 });
  tb(s, "€744,64", { x: 0.85, y: 4.6, w: 4.1, h: 0.85, fontSize: 40, bold: true, color: C.accent1, fontFace: THEME.headFontFace });
  s.addNotes("JLCPCB produce i PCB e monta i 131 componenti SMD standard. Da Mouser arrivano i componenti da saldare a mano e i sensori, in un solo ordine con spedizione gratuita e dazi inclusi.");

  // ================================================================ 10 rischi
  s = content("Budget");
  s.addText("Opzioni e rischi da gestire", { placeholder: "title" });
  const risks = [
    [ic.ring, "Anelli Keystone", "Opzionali: +€35–45. In alternativa pin di strip, già nel budget.", C.accent1],
    [ic.warn, "Componenti a fine vita", "MAX961, LT1636, LT3461A sono NCNR. Mouser ha solo 153 MAX961: comprarne qualcuno in più.", C.accent2],
    [ic.ruler, "Connettori LEMO", "Verificare il footprint con un LEMO vero sulla stampa in scala 1:1.", C.accent2],
    [ic.check, "Controllo finale", "DRC ufficiale in KiCad prima di confermare l'ordine.", C.accent1],
  ];
  risks.forEach(([im, t, d, col], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.55 + Math.floor(i / 2) * 2.55;
    card(s, x, y, 5.95, 2.3, "rischio " + i);
    circle(s, x + 0.35, y + 0.35, 0.75, col, "icona " + t);
    s.addImage({ data: im, x: x + 0.52, y: y + 0.52, w: 0.41, h: 0.41 });
    tb(s, t, { x: x + 1.35, y: y + 0.4, w: 4.4, h: 0.5, fontSize: 20, bold: true, color: C.background1 });
    tb(s, d, { x: x + 1.35, y: y + 0.95, w: 4.4, h: 1.15, fontSize: 15, color: C.background2, valign: "top" });
  });
  s.addNotes("Gli anelli Keystone sono una scelta di comodità. Il rischio vero è la disponibilità: tre chip del circuito sono a fine vita e non si possono rendere, quindi conviene comprare qualche scorta adesso. Prima dell'ordine si controllano il footprint dei LEMO e il DRC di KiCad.");

  // ================================================================ 11 prossimi passi
  pres.addSection({ title: "Prossimi passi" });
  s = content("Prossimi passi");
  s.addText("Dall'ordine alla classe", { placeholder: "title" });
  const next = [
    [ic.cart, "Ordine", "JLCPCB per PCB e montaggio, Mouser per componenti e SiPM"],
    [ic.tools, "Montaggio a mano", "chip SO-8, trimmer, connettori e test point"],
    [ic.bolt, "Collaudo", "un canale alla volta: alimentazioni, alta tensione, bias senza SiPM, soglia, SiPM"],
    [ic.school, "In classe", "conteggi, coincidenze, misure di flusso con il Raspberry Pi"],
  ];
  next.forEach(([im, t, d], i) => {
    const x = 0.6 + i * 3.1;
    circle(s, x + 0.95, 1.75, 1.0, C.accent1, "icona " + t);
    s.addImage({ data: im, x: x + 1.2, y: 2.0, w: 0.5, h: 0.5 });
    if (i < 3) s.addShape(pres.shapes.LINE, { x: x + 2.1, y: 2.25, w: 2.0, h: 0, line: { color: C.accent6, width: 2 }, objectName: "linea " + i });
    tb(s, (i + 1) + ". " + t, { x, y: 3.0, w: 2.9, h: 0.5, fontSize: 20, bold: true, color: C.background1, align: "center" });
    tb(s, d, { x: x + 0.1, y: 3.55, w: 2.7, h: 1.6, fontSize: 15, color: C.background2, align: "center", valign: "top" });
  });
  card(s, 0.6, 5.45, 12.1, 1.1, "decisione");
  tb(s, "Serve: approvazione del budget di €745 per avviare gli ordini.",
    { x: 0.9, y: 5.45, w: 11.5, h: 1.1, fontSize: 20, bold: true, color: C.accent1, valign: "middle" });
  s.addNotes("I file per JLCPCB e il carrello Mouser sono pronti. Dopo l'arrivo si saldano a mano i pochi componenti speciali e si collauda un canale alla volta, seguendo la procedura scritta. Chiediamo l'approvazione del budget per partire con gli ordini.");

  // ================================================================ 12 chiusura
  s = pres.addSlide({ masterName: "TITOLO", sectionTitle: "Prossimi passi" });
  s.addText("Pronta per l'ordine", { placeholder: "title" });
  s.addText("Schema, PCB, file di produzione e preventivi sono pronti", { placeholder: "body" });
  s.addImage({ path: IMG + "lemo.png", x: 6.7, y: 1.65, w: 6.2, h: 6.2 / 1.6, objectName: "uscite LEMO" });
  s.addNotes("Riepilogo: tutto il materiale per produrre le cinque schede è pronto; manca solo il via libera al budget.");

  const out = __dirname + "/pitch_rivelatore_muoni.pptx";
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("scritto", out);
})();
