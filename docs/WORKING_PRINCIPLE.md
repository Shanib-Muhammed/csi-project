# How Wi-Fi Sense Radar works

## 1. Transmitter

The first ESP32 creates a password-protected 2.4 GHz Wi-Fi SoftAP. It sends a small UDP broadcast probe about every 30 milliseconds. These are ordinary local Wi-Fi packets; no internet or external router is involved.

## 2. Receiver and CSI

The second ESP32 joins the transmitter's SoftAP as a station. The receiver enables the ESP-IDF Channel State Information (CSI) receive callback. When Wi-Fi frames arrive, the driver provides complex channel samples represented as signed I/Q values, together with metadata such as RSSI and channel.

The callback does only a short copy into a FreeRTOS queue. The Arduino loop prints queued records as one JSON line per packet over USB serial.

## 3. Python signal processing

The laptop reads JSON lines from the receiver's COM port. It skips the invalid first CSI word when flagged, groups I/Q values into pairs, and computes amplitude features. A scalar summary is passed to the first baseline detector.

The detector:
- collects a fixed number of samples while the area is empty;
- calculates a median baseline and robust noise floor;
- smooths recent changes;
- uses separate enter/exit thresholds (hysteresis);
- requires multiple consecutive samples before changing presence state;
- slowly adapts the baseline only when the area is judged empty.

This is a starting algorithm. It must be tuned against real recordings from the actual room and board placement.

## 4. Movement and stationary presence

Movement can change CSI rapidly, so recent sample-to-sample variation is reported as a movement score. A person or object entering the RF path can also change the channel response and create a persistent offset.

Stationary detection is more difficult: if a person causes no measurable channel change, or the signal drifts back toward the baseline, this one-link prototype may miss them. The detector reports RF-environment change, not a guaranteed semantic classification of a human.

## 5. 2D visualization

The dashboard maps the current deviation score to a blue/yellow/red visual field. It is intentionally labelled a qualitative signal activity map. With only one transmitter and one receiver, the system does not have enough independent spatial measurements to infer a true object coordinate, shape, or silhouette.

The visual is driven by live CSI measurements, not a prerecorded animation. The fixed hotspot is an indicator of signal-change intensity, not the measured position of an object.

## 6. Local website

FastAPI serves the dashboard on 127.0.0.1:8000. A background serial thread processes CSI lines. WebSocket messages publish the latest state to the browser. SQLite stores presence-state transitions locally.

The complete sensor-to-dashboard path is:

ESP32 transmitter → 2.4 GHz Wi-Fi packets → ESP32 CSI receiver → USB serial → Python processing → WebSocket → browser dashboard.

No cloud service is used.
