"""Convert raw ESP32 CSI I/Q bytes into signal features."""
from __future__ import annotations

import math
from typing import Any


def extract_features(record: dict[str, Any]) -> dict[str, Any]:
    raw = record.get("csi") or []
    # ESP-IDF marks the first four bytes invalid on some receive paths.
    # Skip those bytes before pairing signed I/Q samples.
    if record.get("first_word_invalid") and len(raw) >= 4:
        raw = raw[4:]

    amplitudes: list[float] = []
    usable = len(raw) - (len(raw) % 2)
    for index in range(0, usable, 2):
        amplitudes.append(math.hypot(float(raw[index]), float(raw[index + 1])))

    if amplitudes:
        mean_amp = sum(amplitudes) / len(amplitudes)
        variance = sum((value - mean_amp) ** 2 for value in amplitudes) / len(amplitudes)
        std_amp = math.sqrt(variance)
        peak_amp = max(amplitudes)
    else:
        mean_amp = std_amp = peak_amp = 0.0

    return {
        "timestamp_us": int(record.get("ts_us", 0)),
        "rssi": int(record.get("rssi", 0)),
        "channel": int(record.get("channel", 0)),
        "subcarriers": len(amplitudes),
        "amplitudes": amplitudes,
        "amplitude_mean": mean_amp,
        "amplitude_std": std_amp,
        "amplitude_peak": peak_amp,
        "first_word_invalid": bool(record.get("first_word_invalid", False)),
        "dropped": int(record.get("dropped", 0)),
    }
