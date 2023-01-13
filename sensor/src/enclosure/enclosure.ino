void setup() {
  Serial.begin(9600);
}

void loop() {
  Serial.println("Hello, world?!");
  delay(500);
}

// arduino-cli compile -v -b arduino:avr:nano:cpu=atmega328old /Users/moritz/Documents/research/insert-name-here/sensor/src/enclosure/enclosure.ino --output-dir /Users/moritz/Documents/research/insert-name-here/sensor/src/enclosure/
// arduino-cli upload -v -b arduino:avr:nano:cpu=atmega328old -p /dev/cu.usbserial-AB0O2OIH /Users/moritz/Documents/research/insert-name-here/sensor/src/enclosure