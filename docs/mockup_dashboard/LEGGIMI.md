# Mock-up del software per gli studenti

Schermate di esempio (dati finti ma plausibili) di come potrebbe essere il software sul Raspberry Pi.
Si aprono direttamente nel browser; `node shoot.mjs` rigenera gli screenshot PNG.

| file | schermata |
|---|---|
| `dashboard.html` | dati in diretta: muoni (coincidenze triple), conteggi delle tre barre, stato della scheda dal monitor I²C (bias, soglie, alta tensione, temperatura), ultimi eventi, istogrammi |
| `esperienze.html` | menu delle esperienze guidate (flusso, Poisson, plateau, soglia, cos²θ, misura lunga) |
| `plateau.html` | esperienza guidata: plateau di efficienza della barra 2 regolando V1, con il bias letto dal monitor |
| `poisson.html` | lezione concettuale: statistica di Poisson sui dati della classe |

Colori: barra 1 blu, barra 2 verde acqua, barra 3 arancio, coincidenza viola (palette verificata per daltonismo).
