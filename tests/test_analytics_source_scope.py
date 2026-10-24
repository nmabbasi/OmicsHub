"""Pin the single authorized analytics.js source revision for this review."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "9782b635269171240c65abb942bd9bdf400e03d0"
AUTHORIZED_SHA256 = "2a009664425fcf98b05101e7945e2b6b4ae1bcbc1b88ade116b797c82bd857e4"


class AnalyticsSourceScopeTests(unittest.TestCase):
    def test_only_the_reviewed_analytics_source_revision_is_authorized(self):
        original = subprocess.run(
            ["git", "show", f"{BASELINE}:analytics.js"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        self.assertEqual(original.returncode, 0, "the published analytics.js baseline must exist")
        current = (ROOT / "analytics.js").read_bytes()
        self.assertNotEqual(current, original.stdout, "the authorized source change must be present")
        self.assertEqual(
            hashlib.sha256(current).hexdigest(), AUTHORIZED_SHA256,
            "analytics.js must match the exact consent-order source reviewed for this PR",
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the runtime consent fixtures")
    def test_offline_consent_runtime_regressions(self):
        result = subprocess.run(
            ["node", "--test", "tests/test_analytics_load_order.js", "tests/test_advertising_consent.js"],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
