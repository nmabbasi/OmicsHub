"""Visual hierarchy, responsive behavior, and accessibility contracts for learner-first Start Here."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IMAGES = {
    "images/sh-three-laptop-learner-banner-with-copy.webp",
    "images/sh-route-single-cell-laptop-v3.webp",
    "images/sh-route-genomics-laptop-v3.webp",
    "images/sh-route-microbial-laptop-v3.webp",
    "images/sh-route-evolution-laptop-v3.webp",
}


class PageFacts(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.elements, self.links, self.text = [], [], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag == "a":
            self.links.append(attrs.get("href", ""))

    def handle_data(self, text):
        self.text.append(text)


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
        cls.facts = PageFacts(cls.main)

    def test_editorial_hero_and_learner_banner_are_present(self):
        hero = re.search(r'<section\b[^>]*class="[^"]*\bsh-hero\b[^"]*".*?</section\s*>', self.main, re.S)
        self.assertIsNotNone(hero)
        self.assertRegex(hero.group(), r"<h1\b[^>]*id=\"sh-hero-title\"")
        self.assertIn("background: #123b5d", rule(self.css, ".sh-hero"))
        banner = re.search(r'<figure\b[^>]*class="[^"]*\bsh-audience-visual\b[^"]*"[^>]*>.*?</figure\s*>', self.main, re.S)
        self.assertIsNotNone(banner)
        self.assertIn("images/sh-three-laptop-learner-banner-with-copy.webp", banner.group())

    def test_four_route_cards_keep_their_original_images_and_lesson_destinations(self):
        cards = re.findall(
            r'<a\b(?=[^>]*\bclass="[^"]*\bsh-route-card\b)[^>]*>.*?</a\s*>',
            self.main, re.S | re.I,
        )
        self.assertEqual(len(cards), 4)
        sources, destinations = set(), set()
        for card in cards:
            image = re.search(r'<img\b[^>]*\bsrc="([^"]+)"', card)
            href = re.search(r'\bhref="([^"]+)"', card)
            self.assertIsNotNone(image)
            self.assertIsNotNone(href)
            sources.add(image.group(1))
            destinations.add(href.group(1))
            self.assertTrue((ROOT / image.group(1)).is_file())
            self.assertTrue((ROOT / href.group(1)).is_file())
        self.assertEqual(sources, EXPECTED_IMAGES - {"images/sh-three-laptop-learner-banner-with-copy.webp"})
        self.assertEqual(destinations, {
            "tutorials/scrna-seq-basics.html",
            "tutorials/wes-variant-calling-pipeline.html",
            "tutorials/16s-rrna-prokka-annotation.html",
            "tutorials/evolutionary-phylogeny-analysis.html",
        })

    def test_images_have_alternative_text_and_native_links_remain_accessible(self):
        images = [attrs for tag, attrs in self.facts.elements if tag == "img"]
        self.assertEqual({attrs.get("src") for attrs in images}, EXPECTED_IMAGES)
        self.assertTrue(all(attrs.get("alt", "").strip() for attrs in images))
        self.assertIn(":focus-visible", self.css)
        self.assertIn("sh-route-card:focus-visible", self.css)
        self.assertIn('href="tutorials/introduction-to-bioinformatics.html"', self.main)
        self.assertIn('href="#sh-foundation"', self.main)

    def test_small_route_labels_meet_wcag_aa_contrast_on_white(self):
        root = rule(self.css, ":root")
        colors = dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-f]{6})", root, re.I))

        def luminance(value):
            channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
                      for channel in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        for selector, token in (
            (".sh-label-violet", "--sh-violet-ink"),
            (".sh-tag-violet", "--sh-violet-ink"),
            (".sh-tag-cyan", "--sh-cyan-ink"),
            (".sh-tag-gold", "--sh-gold-ink"),
        ):
            with self.subTest(selector=selector):
                declaration = rule(self.css, selector)
                self.assertIn(f"color: var({token})", declaration)
                ratio = 1.05 / (luminance(colors[token]) + 0.05)
                self.assertGreaterEqual(ratio, 4.5, f"{selector} contrast is {ratio:.2f}:1")

    def test_responsive_reduced_motion_and_static_learning_loop(self):
        self.assertRegex(self.css, r"(?i)@media\s*\(max-width:")
        self.assertRegex(self.css, r"(?i)@media\s*\(prefers-reduced-motion:\s*reduce\)")
        self.assertIn("object-fit: cover", rule(self.css, ".sh-route-img"))
        self.assertIn("aspect-ratio: 16 / 9", rule(self.css, ".sh-route-img"))
        self.assertIn('class="sh-loop-map"', self.main)
        self.assertIn('aria-label="Suggested beginner route, follow clockwise"', self.main)
        self.assertEqual(self.main.count('class="sh-loop-arrow"'), 4)
        self.assertIn('class="sh-loop-return"', self.main)
        self.assertNotIn("sh-orbit", self.main)
        self.assertNotIn("data-sh-step", self.main)
        self.assertNotRegex(self.source, r"start-here\.js\?v=")

    def test_learning_copy_and_historical_tutorial_destinations_remain(self):
        links = {href for href in self.facts.links if href.startswith("tutorials/")}
        self.assertEqual(len(links), 33)
        self.assertTrue(all((ROOT / href.split("#", 1)[0]).is_file() for href in links))
        self.assertIn("You have the biology.", " ".join(self.facts.text))
        self.assertIn("Start with one lesson", " ".join(self.facts.text))
        self.assertIn("R + R Markdown", " ".join(self.facts.text))
        self.assertIn("equivalent route", " ".join(self.facts.text))
        self.assertIn("tutorials/research-reporting-interpretation.html", links)
        self.assertIn('class="sh-step sh-step--start"', self.main)


if __name__ == "__main__":
    unittest.main()
