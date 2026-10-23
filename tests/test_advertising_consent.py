"""Run the advertising consent JavaScript suite from the Python CI discovery."""
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AdvertisingConsentNodeTests(unittest.TestCase):
    def test_node_advertising_consent_suite(self):
        result = subprocess.run(
            ["node", "--test", "tests/test_advertising_consent.js"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout)


if __name__ == "__main__":
    unittest.main()
