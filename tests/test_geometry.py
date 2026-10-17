import unittest
import numpy as np
from cracklens.quantification.geometry import measure_crack, skeleton_length_px, width_profile_px

class GeometryTests(unittest.TestCase):
    def test_vertical_strip_length_and_width(self):
        mask = np.zeros((40, 30), dtype=bool)
        mask[5:26, 12:17] = True
        measured = measure_crack(mask, scale_mm=100, scale_pixels=100)
        self.assertGreaterEqual(measured.length_px, 18.0)
        self.assertLessEqual(measured.length_px, 22.0)
        self.assertAlmostEqual(measured.max_width_px, 5.0, delta=0.6)
        self.assertEqual(measured.classification, "flexural")

    def test_diagonal_angle(self):
        mask = np.zeros((40, 40), dtype=bool)
        for i in range(8, 28):
            mask[i, i] = True
        measured = measure_crack(mask, scale_mm=100, scale_pixels=100)
        self.assertAlmostEqual(measured.angle_deg_from_vertical, 45.0, delta=2.0)
        self.assertEqual(measured.classification, "shear")

    def test_empty_length(self):
        self.assertEqual(skeleton_length_px(np.zeros((4, 4), dtype=bool)), 0.0)
        self.assertEqual(width_profile_px(np.zeros((4, 4), dtype=bool)).size, 0)

if __name__ == "__main__":
    unittest.main()
