"""Strict adapter contracts for the Start Here desktop readability revision."""
import hashlib
from pathlib import Path
import re
import subprocess
import unittest

from start_here_desktop_baseline import (
    DESKTOP_BASELINE_COMMIT,
    DESKTOP_CSS_HREF,
    DESKTOP_CSS_SHA256,
    normalize_start_here_desktop_html,
    restore_start_here_desktop_asset,
)

ROOT = Path(__file__).resolve().parents[1]


def baseline(path):
    return subprocess.check_output(
        ["git", "show", f"{DESKTOP_BASELINE_COMMIT}:{path}"], cwd=ROOT
    )


class StartHereDesktopBaselineTests(unittest.TestCase):
    def test_final_css_hash_is_pinned_and_restores_exact_e846ce3_bytes(self):
        current = (ROOT / "start-here.css").read_bytes()
        self.assertEqual(hashlib.sha256(current).hexdigest(), DESKTOP_CSS_SHA256)
        self.assertEqual(restore_start_here_desktop_asset("start-here.css", current), baseline("start-here.css"))
        self.assertEqual(restore_start_here_desktop_asset("start-here.css", baseline("start-here.css")), baseline("start-here.css"))

    def test_css_mutation_is_rejected(self):
        current = (ROOT / "start-here.css").read_bytes()
        with self.assertRaisesRegex(AssertionError, "desktop CSS fingerprint mismatch"):
            restore_start_here_desktop_asset("start-here.css", current + b"\n")

    def test_only_exact_new_href_normalizes_to_e846ce3_href(self):
        current = (ROOT / "start-here.html").read_text(encoding="utf-8")
        original = baseline("start-here.html").decode("utf-8")
        old_href = re.findall(r'<link\b[^>]*href="(start-here\.css\?v=[^"]+)"[^>]*>', original)
        self.assertEqual(len(old_href), 1)
        self.assertEqual(current.count(DESKTOP_CSS_HREF), 1)
        expected = current.replace(DESKTOP_CSS_HREF, old_href[0], 1)
        self.assertEqual(normalize_start_here_desktop_html("start-here.html", current), expected)
        unrelated = current.replace(DESKTOP_CSS_HREF, DESKTOP_CSS_HREF.replace("readability-v1", "unapproved"), 1)
        self.assertEqual(normalize_start_here_desktop_html("start-here.html", unrelated), unrelated)

    def test_duplicate_exact_href_is_rejected(self):
        current = (ROOT / "start-here.html").read_text(encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "duplicate exact Start Here desktop CSS href"):
            normalize_start_here_desktop_html("start-here.html", current + DESKTOP_CSS_HREF)


if __name__ == "__main__":
    unittest.main()
