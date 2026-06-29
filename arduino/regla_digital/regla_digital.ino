#include <Wire.h>
#include <LiquidCrystal_I2C.h>

const byte TRIG_PIN = 9;
const byte ECHO_PIN = 10;
const byte LCD_ADDRESS = 0x27;
const unsigned long SAMPLE_INTERVAL_MS = 100;
const unsigned long ECHO_TIMEOUT_US = 25000;
const float MIN_DISTANCE_CM = 2.0;
const float MAX_DISTANCE_CM = 100.0;

LiquidCrystal_I2C lcd(LCD_ADDRESS, 16, 2);

float samples[5] = {0, 0, 0, 0, 0};
byte sampleCount = 0;
byte sampleIndex = 0;
unsigned long lastSampleAt = 0;

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
  if (duration == 0) return -1.0;
  return duration * 0.0343 / 2.0;
}

float medianOfValidSamples() {
  float values[5];
  byte count = 0;

  for (byte i = 0; i < sampleCount; i++) {
    if (samples[i] >= MIN_DISTANCE_CM && samples[i] <= MAX_DISTANCE_CM) {
      values[count++] = samples[i];
    }
  }
  if (count == 0) return -1.0;

  for (byte i = 0; i < count - 1; i++) {
    for (byte j = i + 1; j < count; j++) {
      if (values[j] < values[i]) {
        float temp = values[i];
        values[i] = values[j];
        values[j] = temp;
      }
    }
  }
  return values[count / 2];
}

float sampleSpread() {
  float minimum = 9999.0;
  float maximum = -1.0;
  byte validCount = 0;
  for (byte i = 0; i < sampleCount; i++) {
    if (samples[i] >= MIN_DISTANCE_CM && samples[i] <= MAX_DISTANCE_CM) {
      minimum = min(minimum, samples[i]);
      maximum = max(maximum, samples[i]);
      validCount++;
    }
  }
  return validCount > 1 ? maximum - minimum : 99.0;
}

void showOnLcd(float distance, bool valid, bool stable) {
  lcd.setCursor(0, 0);
  lcd.print("REGLA DIGITAL  ");
  lcd.setCursor(0, 1);

  if (!valid) {
    lcd.print("SIN MEDICION    ");
    return;
  }

  lcd.print(distance, 1);
  lcd.print(" cm ");
  lcd.print(stable ? "OK " : "... ");
  for (byte i = 0; i < 4; i++) lcd.print(' ');
}

void sendMeasurement(float distance, bool valid, bool stable, float spread) {
  Serial.print("{\"distance\":");
  if (valid) Serial.print(distance, 1);
  else Serial.print("null");
  Serial.print(",\"valid\":");
  Serial.print(valid ? "true" : "false");
  Serial.print(",\"stable\":");
  Serial.print(stable ? "true" : "false");
  Serial.print(",\"spread\":");
  Serial.print(valid ? spread : 0.0, 1);
  Serial.println("}");
}

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);
  Serial.begin(9600);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("REGLA DIGITAL");
  lcd.setCursor(0, 1);
  lcd.print("INICIANDO...");
  delay(800);
  lcd.clear();
}

void loop() {
  if (millis() - lastSampleAt < SAMPLE_INTERVAL_MS) return;
  lastSampleAt = millis();

  samples[sampleIndex] = readDistanceCm();
  sampleIndex = (sampleIndex + 1) % 5;
  if (sampleCount < 5) sampleCount++;

  float filtered = medianOfValidSamples();
  bool valid = filtered >= MIN_DISTANCE_CM && filtered <= MAX_DISTANCE_CM;
  float spread = sampleSpread();
  bool stable = valid && sampleCount == 5 && spread <= 1.5;

  showOnLcd(filtered, valid, stable);
  sendMeasurement(filtered, valid, stable, spread);
}
