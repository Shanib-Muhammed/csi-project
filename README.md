# Wi-Fi Sense Radar

An offline Wi-Fi Channel State Information (CSI) sensing project built around two ESP32-WROOM-32D development boards and a Windows laptop.

> Reality check: this project measures real Wi-Fi CSI/RSSI changes. With one transmitter/receiver link it can estimate whether the monitored RF environment has changed and whether motion is present. It cannot reconstruct a human silhouette or guarantee accurate X/Y coordinates. The 2D heatmap is a calibrated visualization of signal-change zones, not a camera-like image.

## Architecture
- ESP32 #1 — transmitter: creates a private 2.4 GHz SoftAP and periodically broadcasts UDP probe packets.
- ESP32 #2 — receiver: joins that SoftAP, enables the ESP-IDF CSI receive API through Arduino-ESP32, and streams CSI samples over USB serial.
- Laptop — Python: reads serial CSI records, filters measurements, calibrates an empty-area baseline, estimates presence/motion, stores events in SQLite, and serves the dashboard.
- Website — HTML/CSS/JavaScript: receives live updates over WebSocket and renders signal charts and a 2D signal-change heatmap.

No router, cloud account, or internet connection is needed during normal operation. Internet is only needed to install development tools and Python packages.

## Hardware
- 2 × ESP32-WROOM-32D boards (classic ESP32)
- 2 × USB data cables
- Windows laptop
- A clear test area; begin with boards about 1 metre apart and facing each other.

The built-in PCB antennas are sufficient for initial experiments. Keep both boards stationary during calibration and avoid placing them directly against metal.

## Firmware compatibility
The receiver uses ESP-IDF Wi-Fi CSI APIs exposed by Arduino-ESP32: esp_wifi_set_csi_rx_cb, esp_wifi_set_csi_config, and esp_wifi_set_csi. Use an Arduino-ESP32 3.x board package and select ESP32 Dev Module. Compile and flash on the actual board before assuming compatibility. If CSI symbols are unavailable in a particular package, use Espressif's Arduino-as-an-ESP-IDF-component workflow or official ESP-CSI ESP-IDF examples. Do not silently replace CSI with simulated data.

## Repository layout
- firmware/transmitter/transmitter.ino
- firmware/receiver/receiver.ino
- backend/main.py
- backend/csi_processor.py
- backend/detection.py
- backend/database.py
- website/index.html, style.css, app.js
- tests/test_detection.py
- requirements.txt, config.json, .gitignore

## 1. Install Arduino IDE and flash the boards
1. Install Arduino IDE 2.x.
2. In File → Preferences → Additional Boards Manager URLs, add https://espressif.github.io/arduino-esp32/package_esp32_index.json
3. In Boards Manager, install esp32 by Espressif Systems (3.x).
4. Connect board #1, select ESP32 Dev Module and its COM port, open firmware/transmitter/transmitter.ino, compile and upload.
5. Connect board #2, select its COM port, open firmware/receiver/receiver.ino, compile and upload.
6. Close Arduino Serial Monitor before starting Python; only one program can own the COM port at a time.

Default settings (must match in both sketches): SSID CSI-RADAR-LINK; password radar-demo-32; channel 6; UDP port 3333; serial baud 921600. The transmitter creates a local Wi-Fi network with no internet access.

## 2. Install Python application (Windows PowerShell)
From the repository root, run:

    py -3 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt

If activation is blocked, run:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\.venv\Scripts\Activate.ps1

Find the receiver COM port in Device Manager → Ports (COM & LPT). Edit config.json and set serial_port, for example COM6. Set serial_port to null to run the dashboard in demo/simulator mode; simulator data is clearly marked and is not real sensing.

## 3. Run
    python -m backend.main

Open http://127.0.0.1:8000. The app binds to localhost by default and does not expose the dashboard to your Wi-Fi network. Stop with Ctrl+C.

## 4. Calibrate and test
1. Place boards in the selected positions; start around 1 metre apart.
2. Keep the monitored area empty and still.
3. Wait until the dashboard shows live serial data.
4. Press Calibrate empty area and remain still for the full calibration interval.
5. Walk through the link, hold a hand in the area, move a hand, then leave.
6. Repeat tests and record false positives and missed detections.
7. Recalibrate after moving either board, changing the room layout, or changing the Wi-Fi channel.

The detection engine uses rolling baseline, robust smoothing, adaptive deviation, hysteresis and persistence. A stationary object can create a persistent channel offset, but one RF link cannot always distinguish a person from furniture or other environmental changes. Stationary human presence must be evaluated experimentally.

## Dashboard sections
- Presence: calibrated empty/occupied estimate and a signal score (not a probability).
- Movement: recent signal variation.
- CSI stream: packet count, RSSI, channel and CSI amplitude summary.
- 2D heatmap: visualizes calibrated signal-change zones; with one link it is qualitative, not true spatial reconstruction.
- Calibration: captures the empty-area reference.
- History: local SQLite events and timestamps.

## Troubleshooting
- No serial data: check USB data cable, COM port, baud rate, receiver firmware, and close Arduino Serial Monitor.
- Receiver cannot join transmitter: check SSID/password/channel, power-cycle both boards, and keep them close during initial pairing.
- No CSI callback: confirm receiver is connected to transmitter SoftAP, use a supported Arduino-ESP32 3.x package, and inspect compile logs. CSI callbacks require received Wi-Fi frames.
- Noisy detection: keep boards fixed, move cables away from antennas, increase calibration time, reduce nearby 2.4 GHz traffic, and recalibrate.
- Website disconnected: confirm Python is running and open the local URL above.
- Port access denied: close Serial Monitor and other serial terminals.

## Safety, privacy and limitations
This is an educational RF sensing prototype, not a security system, medical device, life-safety sensor, or reliable people counter. It does not identify individuals and does not capture camera or microphone data. Use only in spaces where you have permission to conduct RF experiments.

## Development status
This is an initial implementation for hardware bring-up. It must be compiled with the installed Arduino core and validated on the actual boards. A GitHub commit or website launch does not prove CSI is being received; confirm live CSI packet counts and perform repeatable tests.

## References
- https://github.com/espressif/esp-csi
- https://github.com/espressif/esp-csi/tree/master/examples/get-started
- https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/wifi-driver/wifi-vendor-features.html
- https://docs.espressif.com/projects/arduino-esp32/en/latest/

## License
MIT. See LICENSE.