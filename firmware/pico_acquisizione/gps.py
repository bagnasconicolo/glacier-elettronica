# -*- coding: utf-8 -*-
"""GPS: frasi NMEA dalla seriale del modulo, per dare un nome (l'ora UTC) a ogni PPS.

Il modulo GPS manda un impulso (PPS) esattamente all'inizio di ogni secondo; il Pico ne
annota l'istante con lo stesso contatore degli ingressi (main.py). Poco dopo il modulo
manda le frasi NMEA che descrivono quel secondo: da $xxRMC si prendono data, ora e
validita', da $xxGGA il numero di satelliti. Funziona con qualunque modulo che abbia
seriale NMEA e uscita PPS (u-blox NEO-M8T, NEO-F10T, M9/M10, ...).
"""


def controlla(frase):
    """True se il checksum NMEA ("*hh" finale) e' giusto"""
    if not frase.startswith("$") or "*" not in frase:
        return False
    corpo, cs = frase[1:].split("*", 1)
    x = 0
    for c in corpo:
        x ^= ord(c)
    try:
        return x == int(cs[:2], 16)
    except ValueError:
        return False


def giorni_da_1970(a, m, g):
    """giorni dal 1/1/1970 (calendario gregoriano), senza dipendere dall'orologio del Pico"""
    a -= m <= 2
    era = a // 400
    yoe = a - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + g - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


class NMEA:
    def __init__(self):
        self.buf = b""
        self.utc = None          # secondi UTC dal 1970 dell'ultimo RMC valido
        self.valido = False
        self.satelliti = 0

    def dati(self, b):
        """aggiunge byte dalla seriale; restituisce la lista dei secondi UTC completati (RMC)"""
        self.buf += b
        fatti = []
        while b"\n" in self.buf:
            riga, self.buf = self.buf.split(b"\n", 1)
            try:
                f = riga.decode().strip()
            except UnicodeError:
                continue
            if not controlla(f):
                continue
            c = f.split("*")[0].split(",")
            tipo = c[0][3:]
            if tipo == "RMC" and len(c) >= 10 and c[1] and c[9]:
                hh, mm, ss = int(c[1][0:2]), int(c[1][2:4]), int(float(c[1][4:]))
                g, me, a = int(c[9][0:2]), int(c[9][2:4]), 2000 + int(c[9][4:6])
                self.utc = giorni_da_1970(a, me, g) * 86400 + hh * 3600 + mm * 60 + ss
                self.valido = c[2] == "A"
                fatti.append(self.utc)
            elif tipo == "GGA" and len(c) >= 8 and c[7]:
                self.satelliti = int(c[7])
        if len(self.buf) > 300:  # spazzatura senza fine riga
            self.buf = b""
        return fatti
