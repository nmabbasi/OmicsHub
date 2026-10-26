from pathlib import Path
import re
import subprocess
import unittest

from reader_typography_baseline import normalize_reader_typography
from route_migration_baseline import is_redirect_stub

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [p for p in ROOT.rglob("*.html") if "/.git/" not in str(p) and not is_redirect_stub(p)]


class AccessibilityReviewTests(unittest.TestCase):
    def test_homepage_difficulty_labels_use_dark_text(self):
        text = (ROOT / "index.html").read_text()
        labels = re.findall(
            r'<span class="text-xs ([^"]+) font-medium">'
            r'(Beginner|Intermediate|Advanced)</span>', text
        )
        self.assertEqual(len(labels), 6)
        self.assertEqual({color for color, _ in labels}, {"text-gray-600"})

    def test_footer_section_headings_are_consistently_level_two(self):
        checked = 0
        for path in HTML_FILES:
            text = path.read_text(errors="ignore")
            if ">Explore</h" not in text and ">Policies</h" not in text:
                continue
            checked += 1
            for title in ("Explore", "Policies"):
                self.assertRegex(text, rf'<h2\b[^>]*>{title}</h2>', str(path))
                self.assertNotRegex(text, rf'<h4[^>]*>{title}</h4>', str(path))
        self.assertGreater(checked, 0)

    def test_telegram_accessible_name_contains_visible_text_and_site(self):
        for path in HTML_FILES:
            text = path.read_text(errors="ignore")
            relative = path.relative_to(ROOT).as_posix()
            text = normalize_reader_typography(relative, text)
            if "Join us on Telegram" in text and "telegram-community-button" in text:
                self.assertIn(
                    'aria-label="Join us on Telegram — The Omics Hub"', text, str(path)
                )
                self.assertNotIn('aria-label="Join The Omics Hub on Telegram"', text, str(path))

    def test_subscribe_markup_matches_committed_baseline(self):
        pattern = re.compile(r'<a\b(?=[^>]*\bSubscribe\b)[^>]*>.*?</a>', re.I | re.S)
        checked = 0
        for path in HTML_FILES:
            relative = path.relative_to(ROOT).as_posix()
            baseline = subprocess.run(
                ["git", "show", f"HEAD:{relative}"], cwd=ROOT,
                text=True, capture_output=True, check=False,
            )
            if baseline.returncode:
                continue
            before = pattern.findall(baseline.stdout)
            if not before:
                continue
            checked += 1
            self.assertEqual(pattern.findall(path.read_text(errors="ignore")), before, relative)
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
