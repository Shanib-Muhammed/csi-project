#include <WiFi.h>
#include <WiFiUdp.h>

static const char *RADAR_SSID = "CSI-RADAR-LINK";
static const char *RADAR_PASSWORD = "radar-demo-32";
static constexpr uint8_t WIFI_CHANNEL = 6;
static constexpr uint16_t UDP_PORT = 3333;
static constexpr uint32_t SEND_INTERVAL_MS = 30;

WiFiUDP udp;
uint32_t sequenceNumber = 0;
uint32_t lastSend = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
  WiFi.mode(WIFI_AP);
  WiFi.setSleep(false);
  const bool started = WiFi.softAP(RADAR_SSID, RADAR_PASSWORD, WIFI_CHANNEL, false, 4);
  if (!started) {
    Serial.println("ERROR,softap_start_failed");
    while (true) delay(1000);
  }
  const IPAddress ip = WiFi.softAPIP();
  Serial.printf("TX_READY,ssid=%s,ip=%s,channel=%u\n", RADAR_SSID, ip.toString().c_str(), WIFI_CHANNEL);
  udp.begin(UDP_PORT);
}

void loop() {
  const uint32_t now = millis();
  if (now - lastSend >= SEND_INTERVAL_MS) {
    lastSend = now;
    char payload[64];
    const int length = snprintf(payload, sizeof(payload), "CSI_RADAR,%lu,%lu",
                                static_cast<unsigned long>(sequenceNumber++),
                                static_cast<unsigned long>(now));
    const IPAddress broadcast(192, 168, 4, 255);
    if (udp.beginPacket(broadcast, UDP_PORT)) {
      udp.write(reinterpret_cast<const uint8_t *>(payload), length);
      udp.endPacket();
    }
  }
  delay(1);
}
