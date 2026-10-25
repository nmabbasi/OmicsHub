"""Pointer and keyboard interaction feedback contracts for Start Here navigation."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.items = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


def media_block(css, media):
    """Return one balanced media block body without relying on whitespace formatting."""
    match = re.search(re.escape(media) + r"\s*\{", css, re.I)
    if not match:
        raise AssertionError(f"missing media query {media}")
    start = match.end()
    depth = 1
    for index in range(start, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[start:index]
    raise AssertionError(f"unterminated media query {media}")


class StartHereHoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "start-here.css").read_text(encoding="utf-8")
        cls.js = (ROOT / "start-here.js").read_text(encoding="utf-8")
        cls.main = re.search(r"<main\b[^>]*>.*?</main\s*>", cls.source, re.S | re.I).group()
        cls.elements = Elements(cls.main).items

    def test_orbit_and_sidebar_links_are_real_and_have_focusable_targets(self):
        links = [(tag, attrs) for tag, attrs in self.elements if tag == "a" and attrs.get("data-sh-step")]
        self.assertEqual(len(links), 8, "each step is linked from both the orbit and guide navigation")
        for step in range(1, 5):
            matches = [attrs for _, attrs in links if attrs.get("data-sh-step") == str(step)]
            self.assertEqual(len(matches), 2)
            self.assertTrue(all(attrs.get("href") == f"#sh-step-{step}" for attrs in matches))
        orbit = next(attrs for tag, attrs in self.elements if "sh-orbit" in attrs.get("class", "").split())
        self.assertIn("hidden", orbit, "orbit is revealed as an enhancement")
        self.assertIn(":focus-visible", self.css)
        self.assertRegex(self.css, r"(?i)(?:outline|box-shadow)[^;}]*")

    def test_previous_next_buttons_and_polite_status_support_non_pointer_navigation(self):
        guide = re.search(r'<aside\b[^>]*class="[^"]*\bsh-guide\b[^"]*".*?</aside\s*>', self.main, re.S)
        self.assertIsNotNone(guide)
        content = guide.group().lower()
        self.assertRegex(content, r"<button\b[^>]*(?:prev|previous)|(?:prev|previous)[^<]*</button>")
        self.assertRegex(content, r"(?is)<button\b[^>]*>[^<]*next[^<]*</button>")
        self.assertRegex(content, r'aria-live="polite"')
        self.assertIn("data-sh-step", self.js)
        self.assertIn("aria-current", self.js)
        self.assertRegex(self.js, r"(?s)(?:addEventListener|onclick)")

    def test_pointer_hover_feedback_is_limited_to_devices_that_support_hover(self):
        hover_media = "@media (hover: hover) and (pointer: fine)"
        body = media_block(self.css, hover_media)
        self.assertRegex(body, r"(?i):hover")
        self.assertIn(":hover", body)
        self.assertIn(":focus-visible", self.css)

    def test_focus_and_active_feedback_work_without_hover_and_use_site_brand_colors(self):
        self.assertRegex(self.css, r"(?i):focus-visible")
        self.assertRegex(self.css, r"(?i):active")
        self.assertRegex(self.css, r"(?i)(?:#123b5d|--sh-navy)")
        self.assertRegex(self.css, r"(?i)(?:#9be4d8|#55c7d9|--sh-mint|--sh-accent)")
        self.assertRegex(self.css, r"(?i)@media\s*\(prefers-reduced-motion:\s*reduce\)")

    def test_interaction_does_not_suggest_completion_or_persistent_progress(self):
        text = " ".join(re.sub(r"<[^>]*>", " ", self.main).split()).lower()
        self.assertNotRegex(text, r"\b(?:completed|completion|percent complete|progress bar)\b")
        self.assertNotRegex(self.css, r"(?i)progressbar")


if __name__ == "__main__":
    unittest.main()
