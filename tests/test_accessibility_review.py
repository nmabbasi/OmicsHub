from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [p for p in ROOT.rglob("*.html") if "/.git/" not in str(p)]


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
            if "Join us on Telegram" in text and "telegram-community-button" in text:
                self.assertIn(
                    'aria-label="Join us on Telegram — The Omics Hub"', text, str(path)
                )
                self.assertNotIn('aria-label="Join The Omics Hub on Telegram"', text, str(path))

    def test_subscribe_markup_targets_indexed_contact_newsletter(self):
        pattern = re.compile(r'<a\b(?=[^>]*\bsubscribe-community-button\b)[^>]*>.*?</a>', re.I | re.S)
        canonical_pages = (
            *(ROOT / name for name in ("index.html", "start-here.html", "tutorials.html", "about.html", "contact.html", "services.html", "success.html", "404.html")),
            *sorted((ROOT / "pages").glob("*.html")),
            *sorted((ROOT / "tutorials").glob("*.html")),
        )
        self.assertEqual(len(canonical_pages), 39)
        for path in canonical_pages:
            relative = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            links = pattern.findall(text)
            self.assertEqual(len(links), 1, relative)
            self.assertNotIn("services.html#newsletter-title", links[0], relative)
            if path.name == "404.html":
                expected_href = 'href="/contact.html#newsletter-title"'
            elif path.parent == ROOT:
                expected_href = 'href="contact.html#newsletter-title"'
            else:
                expected_href = 'href="../contact.html#newsletter-title"'
            self.assertIn(expected_href, links[0], relative)
            self.assertIn("Subscribe &amp; Get Cheat Sheet", links[0], relative)
        contact_text = (ROOT / "contact.html").read_text(encoding="utf-8")
        self.assertIn('id="newsletter-title"', contact_text)
        self.assertIn('action="contact.html#newsletter-title"', contact_text)


if __name__ == "__main__":
    unittest.main()
