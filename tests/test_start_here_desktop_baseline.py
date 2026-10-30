"""Strict adapter contracts for the Start Here image-led restoration."""
import hashlib
from pathlib import Path
import re
import subprocess
import unittest

from latest_review_baseline import normalize_latest_review
from start_here_desktop_baseline import (
    DESKTOP_BASELINE_COMMIT,
    DESKTOP_CSS_HREF,
    DESKTOP_CSS_SHA256,
    _normalize_approved_screenshot_copy,
    normalize_start_here_desktop_html,
    restore_start_here_desktop_asset,
)

ROOT = Path(__file__).resolve().parents[1]


def baseline(path):
    return subprocess.check_output(
        ["git", "show", f"{DESKTOP_BASELINE_COMMIT}:{path}"], cwd=ROOT
    )


class StartHereDesktopBaselineTests(unittest.TestCase):
    def test_historical_css_hash_is_pinned_and_restores_exact_base_bytes(self):
        current = (ROOT / "start-here.css").read_bytes()
        self.assertEqual(hashlib.sha256(current).hexdigest(), DESKTOP_CSS_SHA256)
        self.assertEqual(restore_start_here_desktop_asset("start-here.css", current), baseline("start-here.css"))
        self.assertEqual(restore_start_here_desktop_asset("start-here.css", baseline("start-here.css")), baseline("start-here.css"))

    def test_css_mutation_is_rejected(self):
        current = (ROOT / "start-here.css").read_bytes()
        with self.assertRaisesRegex(AssertionError, "restoration CSS fingerprint mismatch"):
            restore_start_here_desktop_asset("start-here.css", current + b"\n")

    def test_exact_image_led_restoration_normalizes_to_base_but_unapproved_text_does_not(self):
        current = normalize_latest_review(
            "start-here.html", (ROOT / "start-here.html").read_text(encoding="utf-8")
        )
        original = baseline("start-here.html").decode("utf-8")
        self.assertEqual(normalize_start_here_desktop_html("start-here.html", current), original)

        old_href = re.findall(r'<link\b[^>]*href="(start-here\.css\?v=[^"]+)"[^>]*>', original)
        self.assertEqual(len(old_href), 1)
        mutations = (
            ("You have the biology.", "Unapproved new claim."),
            ("images/sh-three-laptop-learner-banner-with-copy.webp", "images/unapproved-start-here-image.webp"),
            ("Recreate your environment, record versions, and run a small check.", "Record versions and rerun checks."),
        )
        for before, after in mutations:
            with self.subTest(before=before):
                self.assertEqual(current.count(before), 1)
                changed = current.replace(before, after, 1)
                self.assertNotEqual(changed, current)
                expected = _normalize_approved_screenshot_copy(changed)
                expected = expected.replace(DESKTOP_CSS_HREF, old_href[0], 1)
                normalized = normalize_start_here_desktop_html("start-here.html", changed)
                self.assertEqual(normalized, expected)
                self.assertNotEqual(normalized, original)

    def test_duplicate_exact_href_is_rejected(self):
        current = normalize_latest_review(
            "start-here.html", (ROOT / "start-here.html").read_text(encoding="utf-8")
        )
        with self.assertRaisesRegex(AssertionError, "duplicate exact Start Here restoration CSS href"):
            normalize_start_here_desktop_html("start-here.html", current + DESKTOP_CSS_HREF)


if __name__ == "__main__":
    unittest.main()
