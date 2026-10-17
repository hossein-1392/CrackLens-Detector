import unittest
from cracklens.classify.orientation import classify_orientation, principal_angle_from_vertical

class ClassificationTests(unittest.TestCase):
    def test_vertical_and_diagonal(self):
        self.assertAlmostEqual(principal_angle_from_vertical([[0, 2], [5, 2], [10, 2]]), 0.0, delta=1e-6)
        self.assertAlmostEqual(principal_angle_from_vertical([[0, 0], [1, 1], [2, 2]]), 45.0, delta=1e-6)
        self.assertEqual(classify_orientation(30.0), "flexural")
        self.assertEqual(classify_orientation(30.01), "shear")

if __name__ == "__main__":
    unittest.main()
