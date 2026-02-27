#include <DHT.h>

#define DHTPIN 2 // دبوس حساس الحرارة والرطوبة
#define DHTTYPE DHT11
#define SOIL_PIN A0 // دبوس حساس رطوبة التربة (المقاومة)
#define PUMP_PIN 8  // دبوس الريلاي للمضخة

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN,
               HIGH); // إيقاف المضخة في البداية (لو كان الريلاي Active Low)
}

void loop() {
  // 1. قراءة الحساسات
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  int soilRes = analogRead(SOIL_PIN); // قراءة المقاومة (Ohm تقريبية)

  // التأكد من سلامة القراءة
  if (isnan(h) || isnan(t)) {
    return;
  }

  // 2. إرسال البيانات بصيغة JSON ليفهمها Node-RED بسهولة
  Serial.print("{");
  Serial.print("\"soil_resistance\":");
  Serial.print(soilRes);
  Serial.print(",\"temperature\":");
  Serial.print(t);
  Serial.print(",\"humidity\":");
  Serial.print(h);
  Serial.println("}");

  // 3. استقبال أمر المضخة من Node-RED
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '1') {
      digitalWrite(PUMP_PIN, LOW); // تشغيل المضخة
    } else if (command == '0') {
      digitalWrite(PUMP_PIN, HIGH); // إيقاف المضخة
    }
  }

  delay(2000); // إرسال بيانات كل ثانيتين
}