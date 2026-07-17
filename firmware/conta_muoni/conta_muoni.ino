/*
 * conta_muoni — conteggio di muoni cosmici con Arduino
 * -----------------------------------------------------
 * Collega l'uscita del buffer della scheda "Riv. Cosmici 2024" (connettore J4,
 * 0->5 V) al pin 2 di un Arduino Uno/Nano (logica 5 V). Ogni muone sopra soglia
 * genera un impulso; l'interrupt hardware ne conta il fronte di salita.
 *
 * Collegamenti:
 *   J4 (segnale) --> [resistenza serie 330 ohm consigliata] --> Arduino D2
 *   J4 (GND)     --> Arduino GND
 *
 * Rate atteso su paletta 10x10 cm a livello del mare: ~1,7 conteggi/s.
 *
 * NB: solo per Arduino a 5 V (Uno/Nano/Mega). Per board a 3,3 V (Due/MKR/Nano 33)
 *     NON applicare i 5 V al pin: alimentare il buffer a 3,3 V o prendere da CMP_Q.
 */

const uint8_t PIN_MUONE = 2;          // pin con interrupt (D2 su Uno/Nano)
volatile unsigned long conteggi = 0;  // incrementato dall'interrupt
unsigned long totale = 0;
unsigned long t0 = 0;

void ISR_muone() {
  conteggi++;                          // l'ISR aggancia il fronte anche se breve
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_MUONE, INPUT);           // il buffer pilota gia' il livello
  attachInterrupt(digitalPinToInterrupt(PIN_MUONE), ISR_muone, RISING);
  Serial.println(F("t[s]\tconteggi_al_secondo\ttotale\trate_medio[Hz]"));
  t0 = millis();
}

void loop() {
  static unsigned long ultimo = 0;
  if (millis() - ultimo >= 1000) {     // ogni secondo
    ultimo += 1000;
    noInterrupts();
    unsigned long n = conteggi;
    conteggi = 0;
    interrupts();
    totale += n;
    float t = (millis() - t0) / 1000.0;
    Serial.print(t, 0);      Serial.print('\t');
    Serial.print(n);         Serial.print('\t');
    Serial.print(totale);    Serial.print('\t');
    Serial.println(totale / t, 3);     // rate medio cumulativo
  }
}
