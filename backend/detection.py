"""Baseline calibration and conservative presence/motion estimation."""
from __future__ import annotations
from collections import deque
from statistics import median
from typing import Any

class PresenceDetector:
    def __init__(self, calibration_samples: int = 120, window_size: int = 15):
        self.calibration_samples = calibration_samples
        self.samples: deque[float] = deque(maxlen=calibration_samples)
        self.history: deque[float] = deque(maxlen=window_size)
        self.baseline: float | None = None
        self.noise_floor = 1.0
        self.present_frames = 0
        self.empty_frames = 0
        self.present = False

    def reset_calibration(self) -> None:
        self.samples.clear()
        self.history.clear()
        self.baseline = None
        self.noise_floor = 1.0
        self.present_frames = self.empty_frames = 0
        self.present = False

    @property
    def calibrated(self) -> bool:
        return self.baseline is not None

    def update(self, value: float) -> dict[str, Any]:
        value = float(value)
        self.history.append(value)
        if self.baseline is None:
            self.samples.append(value)
            if len(self.samples) >= self.calibration_samples:
                self.baseline = median(self.samples)
                deviations = [abs(item - self.baseline) for item in self.samples]
                self.noise_floor = max(1.0, median(deviations) * 1.4826)
            return self._state("CALIBRATING", 0.0, 0.0)

        deviation = abs(value - self.baseline)
        threshold = max(4.0, self.noise_floor * 3.5)
        score = min(100.0, deviation / threshold * 50.0)
        motion = (sum(abs(self.history[i] - self.history[i - 1])
                      for i in range(1, len(self.history))) / (len(self.history) - 1)
                  if len(self.history) >= 3 else 0.0)
        motion_score = min(100.0, motion / max(2.0, self.noise_floor * 2.0) * 50.0)

        if score >= 50.0:
            self.present_frames += 1
            self.empty_frames = 0
        elif score <= 22.0:
            self.empty_frames += 1
            self.present_frames = max(0, self.present_frames - 1)

        if not self.present and self.present_frames >= 5:
            self.present = True
        elif self.present and self.empty_frames >= 12:
            self.present = False
            self.present_frames = 0

        if not self.present and score < 22.0:
            self.baseline = self.baseline * 0.995 + value * 0.005
            self.noise_floor = max(1.0, self.noise_floor * 0.995 + deviation * 0.005)

        return self._state("PRESENT" if self.present else "EMPTY", score, motion_score)

    def _state(self, status: str, score: float, motion: float) -> dict[str, Any]:
        return {
            "calibrated": self.calibrated,
            "presence": self.present,
            "status": status,
            "signal_score": round(score, 2),
            "motion_score": round(motion, 2),
            "baseline": round(self.baseline, 3) if self.baseline is not None else None,
            "noise_floor": round(self.noise_floor, 3),
        }
