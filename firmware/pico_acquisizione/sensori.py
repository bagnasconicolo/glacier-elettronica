# -*- coding: utf-8 -*-
"""Sensori I2C dietro l'hub (multiplexer TCA9548A, 8 porte), letti dal Pico.

Ogni porta dell'hub e' un bus separato: si possono collegare piu' dispositivi con lo
stesso indirizzo (per esempio due schede rivelatore, entrambe con l'ADC a 0x68) purche'
stiano su porte diverse. Il firmware cerca da solo cosa c'e' su ogni porta, all'avvio e
ogni minuto (collegamento "a caldo").

Dispositivi riconosciuti:
  scheda rivelatore (monitor):  MCP3424 a 0x68 (U11: bias 1-3, alta tensione) e, se c'e',
                                il secondo MCP3424 tra 0x69 e 0x6F (U12: soglie 1-3, NTC)
  modulo meteo:                 SHT45 a 0x44 (temperatura, umidita'), BMP390 a 0x76/0x77
                                (pressione, temperatura)

Formule: MCP3424 come software/monitor_tensioni.py (si mandano le tensioni all'ingresso
dell'ADC, la conversione in bias/soglie/temperatura la fa lo Zero); SHT45 e BMP390 come
i driver Adafruit (CircuitPython SHT4x e BMP3XX).

Tutte le letture sono "a passi": le funzioni sono generatori che restituiscono quanti
millisecondi aspettare, cosi' la CPU continua a svuotare le code degli impulsi.
"""
import struct

MUX_BASE = 0x70
ADDR_U11 = 0x68
ADDR_SHT45 = 0x44
ADDR_BMP = (0x77, 0x76)


def crc8(dati):
    """CRC dei sensori Sensirion (polinomio 0x31, partenza 0xFF)"""
    crc = 0xFF
    for b in dati:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


class Hub:
    def __init__(self, i2c, indirizzo=MUX_BASE, reset_pin=None):
        self.i2c, self.addr, self.reset = i2c, indirizzo, reset_pin
        self.porta = None

    def seleziona(self, porta):
        if porta != self.porta:
            self.i2c.writeto(self.addr, bytes([1 << porta]))
            self.porta = porta

    def nessuna(self):
        self.i2c.writeto(self.addr, b"\x00")
        self.porta = None

    def sblocca(self):
        """dopo un errore di bus: impulso sul RESET del TCA9548A (se collegato)"""
        if self.reset is not None:
            self.reset.value(0)
            self.reset.value(1)
        self.porta = None

    def mappa(self):
        """{porta: [indirizzi]} escluso l'hub stesso (che risponde su tutte le porte)"""
        m = {}
        for p in range(8):
            try:
                self.seleziona(p)
                trovati = [a for a in self.i2c.scan() if a != self.addr]   # non 0x70-0x77: il BMP390 sta a 0x76/0x77
            except OSError:
                self.sblocca()
                continue
            if trovati:
                m[p] = trovati
        try:
            self.nessuna()
        except OSError:
            self.sblocca()
        return m


# ---------------------------------------------------------------- MCP3424 (monitor)
def mcp3424(i2c, addr, ch):
    """generatore: conversione one-shot 16 bit, guadagno 1; alla fine restituisce i volt"""
    i2c.writeto(addr, bytes([0x80 | ((ch - 1) << 5) | (0b10 << 2)]))
    yield 70                                              # ~67 ms a 16 bit
    for _ in range(10):
        hi, lo, st = i2c.readfrom(addr, 3)
        if not st & 0x80:
            raw = (hi << 8) | lo
            if raw >= 0x8000:
                raw -= 0x10000
            return raw * 2.048 / 32768
        yield 10
    raise OSError("MCP3424 0x%02x: canale %d non pronto" % (addr, ch))


# ---------------------------------------------------------------- SHT45 (meteo)
def sht45(i2c, addr=ADDR_SHT45):
    """generatore: misura ad alta precisione, senza riscaldatore -> (gradi C, umidita' %)"""
    i2c.writeto(addr, b"\xfd")
    yield 10
    d = i2c.readfrom(addr, 6)
    if crc8(d[0:2]) != d[2] or crc8(d[3:5]) != d[5]:
        raise OSError("SHT45: CRC errato")
    t = -45.0 + 175.0 * ((d[0] << 8) | d[1]) / 65535.0
    rh = -6.0 + 125.0 * ((d[3] << 8) | d[4]) / 65535.0
    return t, min(100.0, max(0.0, rh))


# ---------------------------------------------------------------- BMP390 (meteo)
class BMP390:
    def __init__(self, i2c, addr):
        self.i2c, self.addr = i2c, addr
        if self._leggi(0x00, 1)[0] not in (0x50, 0x60):    # BMP388 / BMP390
            raise OSError("BMP3xx non trovato a 0x%02x" % addr)
        c = struct.unpack("<HHbhhbbHHbbhbb", self._leggi(0x31, 21))
        self.t = (c[0] / 2 ** -8, c[1] / 2 ** 30, c[2] / 2 ** 48)
        self.p = ((c[3] - 2 ** 14) / 2 ** 20, (c[4] - 2 ** 14) / 2 ** 29, c[5] / 2 ** 32,
                  c[6] / 2 ** 37, c[7] / 2 ** -3, c[8] / 2 ** 6, c[9] / 2 ** 8,
                  c[10] / 2 ** 15, c[11] / 2 ** 48, c[12] / 2 ** 48, c[13] / 2 ** 65)
        self.i2c.writeto(self.addr, bytes([0x1C, 0x03]))   # sovracampionamento: pressione x8, temperatura x1

    def _leggi(self, reg, n):
        self.i2c.writeto(self.addr, bytes([reg]))
        return self.i2c.readfrom(self.addr, n)

    def compensa(self, adc_p, adc_t):
        """formule del datasheet Bosch (sez. 9.2-9.3), come il driver Adafruit -> (Pa, gradi C)"""
        T1, T2, T3 = self.t
        P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11 = self.p
        d1 = adc_t - T1
        t = d1 * T2 + d1 * d1 * T3
        o1 = P5 + P6 * t + P7 * t ** 2 + P8 * t ** 3
        o2 = adc_p * (P1 + P2 * t + P3 * t ** 2 + P4 * t ** 3)
        o3 = adc_p ** 2 * (P9 + P10 * t) + P11 * adc_p ** 3
        return o1 + o2 + o3, t

    def misura(self):
        """generatore: una misura in modo "forzato" -> (hPa, gradi C)"""
        self.i2c.writeto(self.addr, bytes([0x1B, 0x13]))   # pressione + temperatura, modo forzato
        yield 25
        for _ in range(10):
            if self._leggi(0x03, 1)[0] & 0x60 == 0x60:
                break
            yield 5
        d = self._leggi(0x04, 6)
        pa, t = self.compensa(d[2] << 16 | d[1] << 8 | d[0], d[5] << 16 | d[4] << 8 | d[3])
        return pa / 100.0, t


# ---------------------------------------------------------------- ciclo di lettura
def ciclo(hub, i2c, uscita, ora_ns, adesso_ms, periodo_ms=5000, scansione_ms=60000):
    """generatore senza fine: scansione delle porte, poi letture periodiche; restituisce
    i millisecondi da aspettare. uscita(riga) riceve le righe:
      I <porta>:<indirizzi> ...                 cosa c'e' su ogni porta (dopo ogni scansione)
      M <t_ns> <porta> <v1> ... <v8>            monitor: tensioni all'ingresso degli ADC (V)
      W <t_ns> <porta> <T> <UR> <P> <T_bmp>     meteo: gradi C, %, hPa, gradi C ("-" se manca)
      X <porta> <errore>                        errore di lettura (si riscansiona)"""
    mappa, bmp, ultima_scan = {}, {}, None
    f = lambda x, d: "-" if x is None else ("%." + str(d) + "f") % x
    while True:
        if ultima_scan is None or adesso_ms() - ultima_scan >= scansione_ms:
            mappa, ultima_scan, bmp = hub.mappa(), adesso_ms(), {}
            uscita("I " + " ".join("%d:%s" % (p, ",".join("%02x" % a for a in ind))
                                   for p, ind in sorted(mappa.items())))
        for porta, ind in sorted(mappa.items()):
            try:
                hub.seleziona(porta)
                if ADDR_U11 in ind:                        # scheda rivelatore
                    v = []
                    for ch in (1, 2, 3, 4):
                        v.append((yield from mcp3424(i2c, ADDR_U11, ch)))
                    u12 = [a for a in ind if 0x69 <= a <= 0x6F]
                    if u12:
                        for ch in (1, 2, 3, 4):
                            v.append((yield from mcp3424(i2c, u12[0], ch)))
                    uscita("M %d %d " % (ora_ns(), porta) + " ".join("%.6f" % x for x in v))
                ab = [a for a in ADDR_BMP if a in ind]
                if ADDR_SHT45 in ind or ab:                # modulo meteo
                    t = rh = p = tb = None
                    if ADDR_SHT45 in ind:
                        t, rh = yield from sht45(i2c)
                    if ab:
                        if porta not in bmp:
                            bmp[porta] = BMP390(i2c, ab[0])
                        p, tb = yield from bmp[porta].misura()
                    uscita("W %d %d %s %s %s %s" % (ora_ns(), porta, f(t, 3), f(rh, 2), f(p, 3), f(tb, 2)))
            except OSError as e:
                uscita("X %d %s" % (porta, e))
                hub.sblocca()
                ultima_scan = None                          # qualcosa e' stato staccato: si riscansiona
                bmp.pop(porta, None)
        yield periodo_ms
