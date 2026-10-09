# Render 3D della scheda montata

## Aprirlo nel browser

Serve solo un server web statico (il browser non carica i file da `file://`).
Dalla cartella `hardware/render3d`:

```
python3 -m http.server 8000
```

poi apri nel browser:

| Indirizzo | Cosa mostra |
|---|---|
| http://localhost:8000/viewer.html?v=3ch | scheda a 3 canali, maschera verde |
| http://localhost:8000/viewer.html?v=3ch&pcb=nero | maschera nera |
| http://localhost:8000/viewer.html?v=1ch | scheda a 1 canale |

Mouse: tasto sinistro ruota, rotella zoom, tasto destro sposta.
Altri parametri: `&view=iso|top|ch1|tp|tp2|coinc|lemo` (inquadrature pronte),
`&bg=1a1f27` (colore dello sfondo).

three.js arriva dal CDN jsDelivr, quindi serve la connessione a internet.
Su Windows, se `python3` non c'è, usa `py -m http.server 8000`.

## Rigenerare la scena e le immagini

```
python3 scene.py 3ch          # out/3ch/scene.json + top.png (dopo modifiche al PCB)
python3 scene.py 3ch nero     # texture con maschera nera
npm install                   # three + playwright-core (solo per le immagini)
node shoot.mjs 3ch iso top    # PNG in out/3ch/ (Chromium headless)
PCB=nero node shoot.mjs 3ch iso
```
