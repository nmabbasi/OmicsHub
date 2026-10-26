"""Pointer and keyboard feedback contracts for image-led Start Here route cards."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.items, self.text = [], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))

    def handle_data(self, text):
        self.text.append(text)


class StartHereHoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "start-here.css").read_text(encoding="utf-8")
        cls.main = re.search(r"<main\b[^>]*>.*?</main\s*>", cls.source, re.S | re.I).group()
        cls.elements = Elements(cls.main).items

    def test_route_cards_are_real_focusable_links_to_lesson_targets(self):
        cards = [attrs for tag, attrs in self.elements
                 if tag == "a" and "sh-route-card" in attrs.get("class", "").split()]
        self.assertEqual(len(cards), 4)
        for attrs in cards:
            with self.subTest(href=attrs.get("href")):
                self.assertTrue(attrs.get("href", "").startswith("tutorials/"))
                self.assertTrue((ROOT / attrs["href"]).is_file())
        self.assertIn(".sh-route-card:focus-visible", self.css)
        focus_rule = re.search(r"\.sh-route-card:focus-visible\s*\{([^}]*)\}", self.css, re.S)
        self.assertIsNotNone(focus_rule)
        self.assertRegex(focus_rule.group(1), r"(?i)(?:outline|box-shadow)")

    def test_pointer_hover_feedback_is_attached_to_cards_and_route_images(self):
        self.assertRegex(self.css, r"(?s)\.sh-route-card:hover\s*\{[^}]*transform:\s*translateY\(-4px\)")
        self.assertRegex(self.css, r"(?s)\.sh-route-card:hover\s+\.sh-route-img\s*\{[^}]*transform:\s*scale\(1\.04\)")

    def test_focus_brand_colors_and_reduced_motion_are_preserved(self):
        self.assertRegex(self.css, r"(?i):focus-visible")
        self.assertRegex(self.css, r"(?i)(?:#123b5d|#0b2741|--sh-navy)")
        self.assertRegex(self.css, r"(?i)(?:#22d3ee|--sh-cyan)")
        self.assertRegex(self.css, r"(?i)@media\s*\(prefers-reduced-motion:\s*reduce\)")
        self.assertRegex(self.css, r"(?i)transition:\s*none")

    def test_native_navigation_has_no_progress_state_or_circle_controls(self):
        text = " ".join(Elements(self.main).text).lower()
        self.assertNotRegex(text, r"\b(?:completed|completion|percent complete|progress bar)\b")
        self.assertNotRegex(self.css, r"(?i)progressbar")
        self.assertNotIn("sh-orbit", self.main)
        self.assertNotIn("data-sh-step", self.main)
        self.assertNotRegex(self.source, r"start-here\.js\?v=")


if __name__ == "__main__":
    unittest.main()
