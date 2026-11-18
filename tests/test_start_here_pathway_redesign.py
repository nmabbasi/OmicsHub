"""Regression tests for the connected visual pathway Start Here redesign."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StartHereParser(HTMLParser):
    def __init__(self, markup: str):
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[str] = []
        self.text: list[str] = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.append(d["id"])
        if tag == "a" and d.get("href"):
            self.links.append(d["href"])

    def handle_data(self, data):
        self.text.append(data)


class StartHerePathwayRedesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "start-here.css").read_text(encoding="utf-8")
        cls.main = re.search(r"<main\b[^>]*>.*?</main\s*>", cls.html, re.S | re.I).group(0)
        cls.parsed = StartHereParser(cls.main)

    def test_ocean_blue_hero_and_pipe_separators_without_middle_dots(self):
        self.assertIn('id="sh-hero-title"', self.main)
        self.assertIn("Build the core skills once.", " ".join(self.parsed.text))
        self.assertIn('class="o3-pipe"', self.main)
        self.assertNotIn("·", self.main)
        self.assertNotIn("\u2014", self.main)
        self.assertIn("linear-gradient(120deg, #2C5C8B 0%, #1A456E 49%, #0B2741 100%)", self.css)
        self.assertRegex(self.css, r"\.o3-stem\s*\{[^}]*display:\s*block")

    def test_all_learning_path_manifest_anchors_are_unique_and_links_resolve(self):
        targets = json.loads((ROOT / "tools/learning-paths.json").read_text(encoding="utf-8"))["start_targets"]
        for anchor in targets:
            with self.subTest(anchor=anchor):
                self.assertEqual(self.parsed.ids.count(anchor), 1)
        self.assertEqual(len(self.parsed.ids), len(set(self.parsed.ids)))
        for href in self.parsed.links:
            if href.startswith("#"):
                self.assertIn(href[1:], self.parsed.ids)
            else:
                target = ROOT / href.split("#", 1)[0].split("?", 1)[0]
                self.assertTrue(target.is_file(), f"Missing link target: {href}")

    def test_mobile_single_line_badge_focus_and_reduced_motion_rules_exist(self):
        self.assertRegex(self.css, r"@media\s*\(max-width:\s*640px\)[\s\S]*?\.o3-badge-top[\s\S]*?white-space:\s*nowrap")
        self.assertIn(":focus-visible", self.css)
        self.assertRegex(self.css, r"@media\s*\(prefers-reduced-motion:\s*reduce\)")


if __name__ == "__main__":
    unittest.main()
