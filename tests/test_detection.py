import unittest
from backend.detection import PresenceDetector

class DetectionTests(unittest.TestCase):
    def test_calibration_then_presence_and_clear(self):
        detector = PresenceDetector(calibration_samples=20, window_size=5)
        for _ in range(20):
            state = detector.update(100.0)
        self.assertTrue(state["calibrated"])
        for _ in range(8):
            state = detector.update(150.0)
        self.assertTrue(state["presence"])
        for _ in range(20):
            state = detector.update(100.0)
        self.assertFalse(state["presence"])

if __name__ == "__main__":
    unittest.main()
