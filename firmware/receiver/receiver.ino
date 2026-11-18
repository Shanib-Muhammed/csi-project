#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_wifi.h>
#include <esp_err.h>

static const char *RADAR_SSID = "CSI-RADAR-LINK";
static const char *RADAR_PASSWORD = "radar-demo-32";
static constexpr uint16_t UDP_PORT = 3333;
static constexpr uint32_t SERIAL_BAUD = 921600;
static constexpr size_t MAX_CSI_BYTES = 256;

WiFiUDP udp;

struct CsiRecord {
  uint32_t timestamp;
  int8_t rssi;
  uint8_t channel;
  uint16_t length;
  uint8_t firstWordInvalid;
  int8_t bytes[MAX_CSI_BYTES];
};

QueueHandle_t csiQueue = nullptr;
volatile uint32_t droppedRecords = 0;

void csiReceiveCallback(void *ctx, wifi_csi_info_t *info) {
  if (info == nullptr || info->buf == nullptr || csiQueue == nullptr) return;
  CsiRecord record{};
  record.timestamp = info->rx_ctrl.timestamp;
  record.rssi = info->rx_ctrl.rssi;
  record.channel = info->rx_ctrl.channel;
  record.firstWordInvalid = info->first_word_invalid ? 1 : 0;
  record.length = info->len > MAX_CSI_BYTES ? MAX_CSI_BYTES : info->len;
  memcpy(record.bytes, info->buf, record.length);
  if (xQueueSend(csiQueue, &record, 0) != pdTRUE) droppedRecords++;
}

static void printCsiRecord(const CsiRecord &record) {
  Serial.print("{\"type\":\"csi\",\"ts_us\":");
  Serial.print(record.timestamp);
  Serial.print(",\"rssi\":"); Serial.print(record.rssi);
  Serial.print(",\"channel\":"); Serial.print(record.channel);
  Serial.print(",\"first_word_invalid\":");
  Serial.print(record.firstWordInvalid ? "true" : "false");
  Serial.print(",\"dropped\":"); Serial.print(droppedRecords);
  Serial.print(",\"csi\":[");
  for (uint16_t i = 0; i < record.length; ++i) {
    if (i) Serial.print(',');
    Serial.print(static_cast<int>(record.bytes[i]));
  }
  Serial.println("]}");
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(700);
  csiQueue = xQueueCreate(24, sizeof(CsiRecord));
  if (csiQueue == nullptr) {
    Serial.println("{\"type\":\"error\",\"message\":\"queue_allocation_failed\"}");
    while (true) delay(1000);
  }
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(RADAR_SSID, RADAR_PASSWORD);
  Serial.println("{\"type\":\"status\",\"state\":\"connecting_to_transmitter\"}");
  const uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) delay(250);
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("{\"type\":\"error\",\"message\":\"transmitter_connection_timeout\"}");
    return;
  }
  Serial.print("{\"type\":\"status\",\"state\":\"connected\",\"ip\":\"");
  Serial.print(WiFi.localIP());
  Serial.println("\"}");

  const esp_err_t callbackResult = esp_wifi_set_csi_rx_cb(&csiReceiveCallback, nullptr);
  if (callbackResult != ESP_OK) {
    Serial.printf("{\"type\":\"error\",\"message\":\"csi_callback_failed\",\"code\":%d}\n", callbackResult);
    return;
  }
  wifi_csi_config_t config{};
  config.lltf_en = true;
  config.htltf_en = true;
  config.stbc_htltf2_en = true;
  config.ltf_merge_en = true;
  config.channel_filter_en = false;
  config.manu_scale = false;
  config.shift = 0;

  const esp_err_t configResult = esp_wifi_set_csi_config(&config);
  if (configResult != ESP_OK) {
    Serial.printf("{\"type\":\"error\",\"message\":\"csi_config_failed\",\"code\":%d}\n", configResult);
    return;
  }
  const esp_err_t enableResult = esp_wifi_set_csi(true);
  if (enableResult != ESP_OK) {
    Serial.printf("{\"type\":\"error\",\"message\":\"csi_enable_failed\",\"code\":%d}\n", enableResult);
    return;
  }
  udp.begin(UDP_PORT);
  Serial.println("{\"type\":\"status\",\"state\":\"csi_enabled\"}");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) { delay(250); return; }
  const int packetSize = udp.parsePacket();
  if (packetSize > 0) while (udp.available()) udp.read();
  CsiRecord record;
  if (csiQueue != nullptr && xQueueReceive(csiQueue, &record, pdMS_TO_TICKS(20)) == pdTRUE) {
    printCsiRecord(record);
  }
}
