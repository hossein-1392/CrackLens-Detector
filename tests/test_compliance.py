import unittest
from cracklens.compliance.limits import assess_crack_width, limits_for

class ComplianceTests(unittest.TestCase):
    def test_aci_humidity_bands(self):
        self.assertEqual(assess_crack_width(0.10)["verdict"], "PASS")
        self.assertEqual(assess_crack_width(0.26)["verdict"], "CAUTION")
        self.assertEqual(assess_crack_width(0.31)["verdict"], "FAIL")

    def test_mabhas9_is_configurable(self):
        result = assess_crack_width(0.25, code="Mabhas9", mabhas9_limit_mm=0.40)
        self.assertEqual(result["verdict"], "PASS")
        self.assertAlmostEqual(limits_for("Mabhas9", mabhas9_limit_mm=0.40).limit_mm, 0.40)

if __name__ == "__main__":
    unittest.main()
