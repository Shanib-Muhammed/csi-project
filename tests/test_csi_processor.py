import unittest
from backend.csi_processor import extract_features

class CsiProcessorTests(unittest.TestCase):
    def test_iq_pairs_are_converted_to_amplitudes(self):
        features = extract_features({"csi": [3, 4, 0, 5], "rssi": -42, "channel": 6})
        self.assertEqual(features["subcarriers"], 2)
        self.assertAlmostEqual(features["amplitudes"][0], 5.0)
        self.assertEqual(features["rssi"], -42)

    def test_invalid_first_word_is_skipped(self):
        features = extract_features({
            "csi": [99, 99, 99, 99, 3, 4],
            "first_word_invalid": True
        })
        self.assertEqual(features["subcarriers"], 1)
        self.assertAlmostEqual(features["amplitude_mean"], 5.0)

if __name__ == "__main__":
    unittest.main()
