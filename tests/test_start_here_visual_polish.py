"""Visual hierarchy, responsive behavior, and accessibility contracts for Start Here."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS_VERSION = "20261025-circular-path-v1"
JS_VERSION = "20261025-circular-path-v1"


class ReadingText(HTMLParser):
    """Collect page text and link targets while omitting decorative SVG paths."""
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.words = []
        self.links = []
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        skip = tag == "svg" or (self.stack[-1][1] if self.stack else False)
        self.stack.append((tag, skip))
        self.elements.append((tag, attrs))
        if tag == "a":
            self.links.append(attrs.get("href"))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, text):
        if not self.stack or not self.stack[-1][1]:
            self.words.extend(text.split())


def main(source):
    match = re.search(r"<main\b.*?</main\s*>", source, re.S | re.I)
    if not match:
        raise AssertionError("expected a main element")
    return match.group()


def rule(css, selector):
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css, re.S | re.I)
    if not match:
        raise AssertionError(f"missing CSS rule: {selector}")
    return re.sub(r"\s+", " ", match.group(1)).strip().lower()


class StartHereVisualPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.main = main(cls.source)
        cls.css = (ROOT / "start-here.css").read_text(encoding="utf-8")
        cls.js = (ROOT / "start-here.js").read_text(encoding="utf-8")
        cls.facts = ReadingText(cls.main)

    def test_compact_gradient_hero_has_clear_heading_and_no_cta(self):
        hero = re.search(r'<section\b[^>]*class="[^"]*\bsh-hero\b[^"]*".*?</section\s*>', self.main, re.S)
        self.assertIsNotNone(hero)
        content = hero.group()
        self.assertRegex(content, r"<h1\b")
        self.assertRegex(content.lower(), r"bioinformatics")
        self.assertEqual(len(re.findall(r"<a\b", content)), 0)
        hero_css = rule(self.css, ".sh-hero")
        self.assertRegex(hero_css, r"background(?:-image)?\s*:\s*[^;]*gradient\(")
        self.assertRegex(self.css.lower(), r"#(?:123b5d|19546b|08696d|dff2ff)")

    def test_circular_orbit_has_four_ordered_steps_and_four_lesson_panels(self):
        orbit_facts = ReadingText(self.main)
        orbit_attrs = next(attrs for tag, attrs in orbit_facts.elements
                           if "sh-orbit" in attrs.get("class", "").split())
        self.assertIn("hidden", orbit_attrs)
        anchors = [(tag, attrs) for tag, attrs in orbit_facts.elements
                   if tag == "a" and "sh-orbit-stop" in attrs.get("class", "").split()]
        self.assertEqual(len(anchors), 4)
        for step, (_, attrs) in enumerate(anchors, 1):
            self.assertEqual(attrs.get("href"), f"#sh-step-{step}")
            self.assertEqual(attrs.get("data-sh-step"), str(step))
            self.assertNotIn("hidden", attrs)
        orbit_text = " ".join(orbit_facts.words)
        for label in ("01", "02", "03", "04"):
            with self.subTest(number=label):
                self.assertIn(label, orbit_text)
        for step in range(1, 5):
            self.assertRegex(self.main, rf'<article\b(?=[^>]*\bid="sh-step-{step}")')
        self.assertRegex(self.source, r'(?is)<path\b[^>]*\bd="[^"]*A[^"]*"')

    def test_language_choice_and_terminal_before_files_are_explicit(self):
        command = re.search(r'<article\b(?=[^>]*\bid="sh-step-2")[^>]*>.*?</article\s*>', self.main, re.S)
        files = re.search(r'<article\b(?=[^>]*\bid="sh-step-3")[^>]*>.*?</article\s*>', self.main, re.S)
        language = re.search(r'<article\b(?=[^>]*\bid="sh-step-4")[^>]*>.*?</article\s*>', self.main, re.S)
        self.assertIsNotNone(command)
        self.assertIsNotNone(files)
        self.assertIsNotNone(language)
        self.assertIn("command-line-part1.html", command.group())
        self.assertIn("computer-data-fundamentals.html", files.group())
        self.assertLess(command.start(), files.start())
        self.assertIn('id="sh-language-choice"', language.group())
        self.assertIn("tutorials/r-tidyverse-fundamentals.html", language.group())
        self.assertIn("tutorials/python-fundamentals-bioinformatics.html", language.group())

    def test_reading_copy_is_concise_and_all_existing_tutorial_destinations_remain(self):
        self.assertLess(len(self.facts.words), 650)
        self.assertEqual(len({url for url in self.facts.links if url and url.startswith("tutorials/")}), 32)
        self.assertNotIn("\u2014", self.main)

    def test_guide_navigation_status_and_previous_next_controls_are_accessible(self):
        guide = re.search(r'<aside\b[^>]*class="[^"]*\bsh-guide\b[^"]*".*?</aside\s*>', self.main, re.S)
        self.assertIsNotNone(guide)
        self.assertRegex(guide.group(), r'aria-live="polite"')
        self.assertRegex(guide.group(), r"(?is)<button\b[^>]*(?:prev|previous)|(?:prev|previous)[^<]*</button>")
        self.assertRegex(guide.group(), r"(?is)<button\b[^>]*>[^<]*next[^<]*</button>")
        self.assertIn(":focus-visible", self.css)

    def test_brand_color_focus_responsive_reduced_motion_and_progressive_enhancement(self):
        self.assertRegex(self.css, r"(?i)(?:#123b5d|--sh-navy)")
        self.assertRegex(self.css, r"(?i)(?:#19546b|#08696d|--sh-ocean|--sh-teal)")
        self.assertIn(":focus-visible", self.css)
        self.assertRegex(self.css, r"(?i)@media\s*\(prefers-reduced-motion:\s*reduce\)")
        self.assertRegex(self.css, r"(?i)@media\s*\(max-width:")
        self.assertIn("hidden", self.js)
        self.assertIn("data-sh-step", self.js)
        self.assertIn(f"start-here.css?v={CSS_VERSION}", self.source)
        self.assertIn(f"start-here.js?v={JS_VERSION}", self.source)

    def test_orbit_and_navigation_do_not_claim_completion_or_progress(self):
        text = " ".join(self.facts.words).lower()
        self.assertNotRegex(text, r"\b(?:completed|completion|percent complete|progress bar)\b")

    def test_circle_stays_label_free_and_protects_reading_and_footer_actions(self):
        circle = (ROOT / "back-to-top.css").read_text(encoding="utf-8")
        script = (ROOT / "subscribe-fab.js").read_text(encoding="utf-8")
        self.assertRegex(circle, r"#back-to-top > span:last-child\s*\{\s*display: none;")
        self.assertIn('aria-label="Back to top"', self.source)
        self.assertIn("border-radius: 50%", circle)
        self.assertIn("range.getClientRects()", script)
        self.assertIn("body h1, body h2, body h3", script)
        self.assertIn("body a[href], body button", script)
        self.assertIn("if (block.contains(existing) || !block.getClientRects().length) return false;", script)


if __name__ == "__main__":
    unittest.main()
