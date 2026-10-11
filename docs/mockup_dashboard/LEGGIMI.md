# Mock-up del software per gli studenti

Schermate di esempio (dati finti ma plausibili) di come potrebbe essere il software sul Raspberry Pi.
Le pagine usano three.js (moduli ES): aprirle con un server locale, per esempio
`python3 -m http.server` in questa cartella e poi http://localhost:8000/dashboard.html.
`node shoot.mjs` rigenera gli screenshot PNG.

In corso: `dashboard.html` ed `esperienze.html` sono gia' nella nuova grafica (scena 3D, stile.css);
`plateau.html` e `poisson.html` sono ancora da rifare (gli screenshot sono della versione precedente).

| file | schermata |
|---|---|
| `dashboard.html` | dati in diretta: muoni (coincidenze triple), conteggi delle tre barre, stato della scheda dal monitor I²C (bias, soglie, alta tensione, temperatura), ultimi eventi, istogrammi |
| `esperienze.html` | menu delle esperienze guidate (flusso, Poisson, plateau, soglia, cos²θ, misura lunga) |
| `plateau.html` | esperienza guidata: plateau di efficienza della barra 2 regolando V1, con il bias letto dal monitor |
| `poisson.html` | lezione concettuale: statistica di Poisson sui dati della classe |

Colori: barra 1 blu, barra 2 verde acqua, barra 3 arancio, coincidenza viola (palette verificata per daltonismo).
